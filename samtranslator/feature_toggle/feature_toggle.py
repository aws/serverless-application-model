import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, cast

import boto3
from botocore.config import Config

from samtranslator.feature_toggle.dialup import (
    DisabledDialup,
    SimpleAccountPercentileDialup,
    ToggleDialup,
)
from samtranslator.metrics.method_decorator import cw_timer
from samtranslator.utils.constants import BOTO3_CONNECT_TIMEOUT

LOG = logging.getLogger(__name__)


class FeatureToggle:
    """
    FeatureToggle is the class which will provide methods to query and decide if a feature is enabled based on where
    SAM is executing or not.
    """

    DIALUP_RESOLVER = {
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

    def _get_dialup(self, region_config, feature_name):  # type: ignore[no-untyped-def]
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
        LOG.warning(f"Dialup type '{dialup_type}' is None or is not supported.")
        return DisabledDialup(region_config)

    def is_enabled(self, feature_name: str) -> bool:
        """
        To check if feature is available

        :param feature_name: name of feature
        """
        if feature_name not in self.feature_config:
            LOG.warning(f"Feature '{feature_name}' not available in Feature Toggle Config.")
            return False

        stage = self.stage
        region = self.region
        account_id = self.account_id
        if not stage or not region or not account_id:
            LOG.warning(
                f"One or more of stage, region and account_id is not set. Feature '{feature_name}' not enabled."
            )
            return False

        stage_config = self.feature_config.get(feature_name, {}).get(stage, {})
        if not stage_config:
            LOG.info(f"Stage '{stage}' not enabled for Feature '{feature_name}'.")
            return False

        if account_id in stage_config:
            account_config = stage_config[account_id]
            region_config = account_config[region] if region in account_config else account_config.get("default", {})
        else:
            region_config = stage_config[region] if region in stage_config else stage_config.get("default", {})

        dialup = self._get_dialup(region_config, feature_name=feature_name)  # type: ignore[no-untyped-call]
        LOG.info(f"Using Dialip {dialup}")
        is_enabled: bool = dialup.is_enabled()

        LOG.info(f"Feature '{feature_name}' is enabled: '{is_enabled}'")
        return is_enabled


class FeatureToggleConfigProvider(ABC):
    """Interface for all FeatureToggle config providers"""

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

    def __init__(self, local_config_path: str) -> None:
        FeatureToggleConfigProvider.__init__(self)
        config_json = Path(local_config_path).read_text(encoding="utf-8")
        self.feature_toggle_config = cast(Dict[str, Any], json.loads(config_json))

    @property
    def config(self) -> Dict[str, Any]:
        return self.feature_toggle_config


class FeatureToggleAppConfigConfigProvider(FeatureToggleConfigProvider):
    """Feature toggle config provider which loads config from AppConfig."""

    @cw_timer(prefix="External", name="AppConfig")
    def __init__(self, application_id, environment_id, configuration_profile_id, app_config_client=None) -> None:  # type: ignore[no-untyped-def]
        FeatureToggleConfigProvider.__init__(self)
        try:
            LOG.info("Loading feature toggle config from AppConfig...")
            # Lambda function has 120 seconds limit
            # (5 + 5) * 2, 20 seconds maximum timeout duration
            # In case of high latency from AppConfig, we can always fall back to use an empty config and continue transform
            client_config = Config(
                connect_timeout=BOTO3_CONNECT_TIMEOUT, read_timeout=5, retries={"total_max_attempts": 2}
            )
            self.app_config_client = (
                app_config_client if app_config_client else boto3.client("appconfig", config=client_config)
            )
            response = self.app_config_client.get_configuration(
                Application=application_id,
                Environment=environment_id,
                Configuration=configuration_profile_id,
                ClientId="FeatureToggleAppConfigConfigProvider",
            )
            binary_config_string = response["Content"].read()
            self.feature_toggle_config = cast(Dict[str, Any], json.loads(binary_config_string.decode("utf-8")))
            LOG.info("Finished loading feature toggle config from AppConfig.")
        except Exception:
            LOG.exception("Failed to load config from AppConfig. Using empty config.")
            # There is chance that AppConfig is not available in a particular region.
            self.feature_toggle_config = {}

    @property
    def config(self) -> Dict[str, Any]:
        return self.feature_toggle_config
