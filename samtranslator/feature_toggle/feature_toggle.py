import json
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, cast

import boto3
import logging

from botocore.client import BaseClient
from botocore.config import Config
from botocore.exceptions import ClientError

from samtranslator.feature_toggle.dialup import (
    BaseDialup,
    DisabledDialup,
    ToggleDialup,
    SimpleAccountPercentileDialup,
)
from samtranslator.metrics.method_decorator import cw_timer
from samtranslator.utils.constants import BOTO3_CONNECT_TIMEOUT

LOG = logging.getLogger(__name__)


FIVE_MINS_IN_SECS = 300


class FeatureToggle:
    """
    FeatureToggle is the class which will provide methods to query and decide if a feature is enabled based on where
    SAM is executing or not.
    """

    DIALUP_RESOLVER: Dict[str, Type[BaseDialup]] = {
        "toggle": ToggleDialup,
        "account-percentile": SimpleAccountPercentileDialup,
    }

    def __init__(
        self,
        config_provider: "FeatureToggleConfigProvider",
        stage: Optional[str],
        account_id: Optional[str],
        region: Optional[str],
    ) -> None:
        self.feature_config = config_provider.config
        self.stage = stage
        self.account_id = account_id
        self.region = region

    def _get_dialup(self, region_config: Dict[str, Any], feature_name: str) -> BaseDialup:
        """
        get the right dialup instance
        if no dialup type is provided or the specified dialup is not supported,
        an instance of DisabledDialup will be returned

        :param region_config: region config
        :param feature_name: feature_name
        :return: an instance of
        """
        dialup_type = region_config.get("type")
        if dialup_type in FeatureToggle.DIALUP_RESOLVER:
            return FeatureToggle.DIALUP_RESOLVER[dialup_type](
                region_config, account_id=self.account_id, feature_name=feature_name
            )
        LOG.warning("Dialup type '{}' is None or is not supported.".format(dialup_type))
        return DisabledDialup(region_config)  # type: ignore[no-untyped-call]

    def is_enabled(self, feature_name: str) -> bool:
        """
        To check if feature is available

        :param feature_name: name of feature
        """
        if feature_name not in self.feature_config:
            LOG.warning("Feature '{}' not available in Feature Toggle Config.".format(feature_name))
            return False

        stage = self.stage
        region = self.region
        account_id = self.account_id
        if not stage or not region or not account_id:
            LOG.warning(
                "One or more of stage, region and account_id is not set. Feature '{}' not enabled.".format(feature_name)
            )
            return False

        stage_config = self.feature_config.get(feature_name, {}).get(stage, {})
        if not stage_config:
            LOG.info("Stage '{}' not enabled for Feature '{}'.".format(stage, feature_name))
            return False

        if account_id in stage_config:
            account_config = stage_config[account_id]
            region_config = account_config[region] if region in account_config else account_config.get("default", {})
        else:
            region_config = stage_config[region] if region in stage_config else stage_config.get("default", {})

        dialup = self._get_dialup(region_config, feature_name=feature_name)
        LOG.info("Using Dialip {}".format(dialup))
        is_enabled: bool = dialup.is_enabled()

        LOG.info("Feature '{}' is enabled: '{}'".format(feature_name, is_enabled))
        return is_enabled


class FeatureToggleConfigProvider(ABC):
    """Interface for all FeatureToggle config providers"""

    def __init__(self) -> None:
        pass

    @property
    @abstractmethod
    def config(self) -> Dict[str, Any]:
        pass


class FeatureToggleDefaultConfigProvider(FeatureToggleConfigProvider):
    """Default config provider, always return False for every query."""

    def __init__(self) -> None:
        FeatureToggleConfigProvider.__init__(self)

    @property
    def config(self) -> Dict[str, Any]:
        return {}


class FeatureToggleLocalConfigProvider(FeatureToggleConfigProvider):
    """Feature toggle config provider which uses a local file. This is to facilitate local testing."""

    def __init__(self, local_config_path):  # type: ignore[no-untyped-def]
        FeatureToggleConfigProvider.__init__(self)
        with open(local_config_path, "r", encoding="utf-8") as f:
            config_json = f.read()
        self.feature_toggle_config = cast(Dict[str, Any], json.loads(config_json))

    @property
    def config(self) -> Dict[str, Any]:
        return self.feature_toggle_config


class FeatureToggleAppConfigConfigProvider(FeatureToggleConfigProvider):
    """Feature toggle config provider which loads config from AppConfig."""

    configuration_token: str
    feature_toggle_config: Dict[str, Any]
    next_poll_due_time: int

    successfully_loaded: bool

    @cw_timer(prefix="External", name="AppConfig")  # type: ignore[misc]
    def __init__(
        self,
        application_id: str,
        environment_id: str,
        configuration_profile_id: str,
        app_config_data_client: Optional[BaseClient] = None,
        required_min_poll_interval_in_secs: int = FIVE_MINS_IN_SECS,
    ) -> None:
        FeatureToggleConfigProvider.__init__(self)
        try:
            LOG.info("Loading feature toggle config from AppConfig...")
            # Lambda function has 120 seconds limit
            # (5 + 5) * 2, 20 seconds maximum timeout duration
            # In case of high latency from AppConfig,
            # we can always fall back to use an empty config and continue transform
            client_config = Config(
                connect_timeout=BOTO3_CONNECT_TIMEOUT, read_timeout=5, retries={"total_max_attempts": 2}
            )
            self.feature_toggle_config = {}

            self.application_id = application_id
            self.environment_id = environment_id
            self.configuration_profile_id = configuration_profile_id
            self.required_min_poll_interval_in_secs = required_min_poll_interval_in_secs

            self.app_config_data_client = (
                boto3.client("appconfigdata", config=client_config)
                if not app_config_data_client
                else app_config_data_client
            )

            self._reset_configuration_session()
            self._refresh_configuration()
            self.successfully_loaded = True
        except Exception as ex:
            LOG.error("Failed to load config from AppConfig: {}. Using empty config.".format(ex))
            # There is chance that AppConfig is not available in a particular region.
            self.successfully_loaded = False

    def _reset_configuration_session(self) -> None:
        """
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/appconfigdata.html#AppConfigData.Client.start_configuration_session
        """
        response = self.app_config_data_client.start_configuration_session(
            ApplicationIdentifier=self.application_id,
            EnvironmentIdentifier=self.environment_id,
            ConfigurationProfileIdentifier=self.configuration_profile_id,
            # We don't change feature flags very often, default 60s is too frequent
            RequiredMinimumPollIntervalInSeconds=self.required_min_poll_interval_in_secs,
        )

        self.configuration_token = cast(str, response["InitialConfigurationToken"])
        self.next_poll_due_time = 0  # set to VERY past so it needs to poll immediately

    def _refresh_configuration(self) -> None:
        try:
            response = self.app_config_data_client.get_latest_configuration(ConfigurationToken=self.configuration_token)
        except ClientError:
            LOG.exception("Fail to call get_latest_configuration, reset session and retry.")
            self._reset_configuration_session()
            response = self.app_config_data_client.get_latest_configuration(ConfigurationToken=self.configuration_token)

        self.configuration_token = response["NextPollConfigurationToken"]
        self.next_poll_due_time = cast(int, response["NextPollIntervalInSeconds"]) + int(time.time())
        binary_config_string = response["Configuration"].read()
        if not binary_config_string:
            # This may be empty if the client already has the latest version of configuration.
            LOG.info("The local feature toggle config is up-to-date.")
            return

        # We store feature toggles in the format of JSON:
        self.feature_toggle_config = cast(Dict[str, Any], json.loads(binary_config_string.decode("utf-8")))
        LOG.info("Finished loading feature toggle config from AppConfig.")

    @property
    def config(self) -> Dict[str, Any]:
        if self.successfully_loaded and int(time.time()) >= self.next_poll_due_time:
            self._refresh_configuration()
        return self.feature_toggle_config
