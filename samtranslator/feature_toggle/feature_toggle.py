import os
import sys
import json
import boto3
import logging

my_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, my_path + "/..")

LOG = logging.getLogger(__name__)


class FeatureToggle:
    """
    FeatureToggle is the class which will provide methods to query and decide if a feature is enabled based on where
    SAM is executing or not.
    """

    def __init__(self, config_provider):
        self.feature_config = config_provider.config

    def is_enabled_for_stage_in_region(self, feature_name, stage, region="default"):
        """
        To check if feature is available for a particular stage or not.
        :param feature_name: name of feature
        :param stage: stage where SAM is running
        :param region: region in which SAM is running
        :return:
        """
        if feature_name not in self.feature_config:
            LOG.warning("Feature '{}' not available in Feature Toggle Config.".format(feature_name))
            return False
        stage_config = self.feature_config.get(feature_name, {}).get(stage, {})
        if not stage_config:
            LOG.info("Stage '{}' not enabled for Feature '{}'.".format(stage, feature_name))
            return False
        region_config = stage_config.get(region, {}) if region in stage_config else stage_config.get("default", {})
        is_enabled = region_config.get("enabled", False)
        LOG.info("Feature '{}' is enabled: '{}'".format(feature_name, is_enabled))
        return is_enabled

    def is_enabled_for_account_in_region(self, feature_name, stage, account_id, region="default"):
        """
        To check if feature is available for a particular account or not.
        :param feature_name: name of feature
        :param stage: stage where SAM is running
        :param account_id: account_id who is executing SAM template
        :param region: region in which SAM is running
        :return:
        """
        if feature_name not in self.feature_config:
            LOG.warning("Feature '{}' not available in Feature Toggle Config.".format(feature_name))
            return False
        stage_config = self.feature_config.get(feature_name, {}).get(stage, {})
        if not stage_config:
            LOG.info("Stage '{}' not enabled for Feature '{}'.".format(stage, feature_name))
            return False
        account_config = stage_config.get(account_id) if account_id in stage_config else stage_config.get("default", {})
        region_config = (
            account_config.get(region, {}) if region in account_config else account_config.get("default", {})
        )
        is_enabled = region_config.get("enabled", False)
        LOG.info("Feature '{}' is enabled: '{}'".format(feature_name, is_enabled))
        return is_enabled


class FeatureToggleConfigProvider:
    """Interface for all FeatureToggle config providers"""

    def __init__(self):
        pass

    @property
    def config(self):
        raise NotImplementedError


class FeatureToggleDefaultConfigProvider(FeatureToggleConfigProvider):
    """Default config provider, always return False for every query."""

    def __init__(self):
        FeatureToggleConfigProvider.__init__(self)

    @property
    def config(self):
        return {}


class FeatureToggleLocalConfigProvider(FeatureToggleConfigProvider):
    """Feature toggle config provider which uses a local file. This is to facilitate local testing."""

    def __init__(self, local_config_path):
        FeatureToggleConfigProvider.__init__(self)
        with open(local_config_path, "r") as f:
            config_json = f.read()
        self.feature_toggle_config = json.loads(config_json)

    @property
    def config(self):
        return self.feature_toggle_config


class FeatureToggleAppConfigConfigProvider(FeatureToggleConfigProvider):
    """Feature toggle config provider which loads config from AppConfig."""

    def __init__(self, application_id, environment_id, configuration_profile_id):
        FeatureToggleConfigProvider.__init__(self)
        self.app_config_client = boto3.client("appconfig")
        try:
            response = self.app_config_client.get_configuration(
                Application=application_id,
                Environment=environment_id,
                Configuration=configuration_profile_id,
                ClientId="FeatureToggleAppConfigConfigProvider",
            )
            binary_config_string = response["Content"].read()
            self.feature_toggle_config = json.loads(binary_config_string.decode("utf-8"))
        except Exception as ex:
            LOG.error("Failed to load config from AppConfig: {}. Using empty config.".format(ex))
            # There is chance that AppConfig is not available in a particular region.
            self.feature_toggle_config = json.loads("{}")

    @property
    def config(self):
        return self.feature_toggle_config
