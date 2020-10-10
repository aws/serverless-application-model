import os
import sys
import json
import boto3
import logging

my_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, my_path + "/..")

LOG = logging.getLogger(__name__)


class FeatureToggle:
    def __init__(self, config_provider):
        self.feature_config = config_provider.config

    def is_enabled_for_stage_in_region(self, feature_name, stage, region="default"):
        if feature_name not in self.feature_config:
            LOG.warning('Feature \'{}\' not available in Feature Toggle Config.'.format(feature_name))
            return False
        stage_config = self.feature_config.get(feature_name, {}).get(stage, {})
        if not stage_config:
            LOG.info('Stage \'{}\' not enabled for Feature \'{}\'.'.format(stage, feature_name))
            return False
        region_config = stage_config.get(region, {}) if region in stage_config else stage_config.get('default', {})
        is_enabled = region_config.get("enabled", False)
        LOG.info('Feature \'{}\' is \'{}\''.format(feature_name, is_enabled))
        return is_enabled

    def is_enabled_for_account_in_region(self, feature_name, stage, account_id, region="default"):
        if feature_name not in self.feature_config:
            LOG.warning('Feature \'{}\' not available in Feature Toggle Config.'.format(feature_name))
            return False
        stage_config = self.feature_config.get(feature_name, {}).get(stage, {})
        if not stage_config:
            LOG.info('Stage \'{}\' not enabled for Feature \'{}\'.'.format(stage, feature_name))
            return False
        if not stage_config:
            return False
        account_config = stage_config.get(account_id) if account_id in stage_config else stage_config.get('default', {})
        region_config = account_config.get(region, {}) if region in account_config else account_config.get('default',
                                                                                                           {})
        return region_config.get("enabled", False)


class FeatureToggleConfigProvider:
    def __init__(self):
        pass

    @property
    def config(self):
        raise NotImplementedError


class FeatureToggleDefaultConfigProvider(FeatureToggleConfigProvider):
    def __init__(self):
        FeatureToggleConfigProvider.__init__(self)

    @property
    def config(self):
        return {}


class FeatureToggleLocalConfigProvider(FeatureToggleConfigProvider):

    def __init__(self, local_config_path=os.path.join(my_path, '..', '..', 'bin', 'feature_toggle_config.json')):
        FeatureToggleConfigProvider.__init__(self)
        with open(local_config_path, "r") as f:
            config_json = f.read()
        self.feature_toggle_config = json.loads(config_json)

    @property
    def config(self):
        return self.feature_toggle_config


class FeatureToggleAppConfigConfigProvider(FeatureToggleConfigProvider):
    def __init__(self, application_id, environment_id, configuration_profile_id):
        FeatureToggleConfigProvider.__init__(self)
        self.app_config_client = boto3.client('appconfig')
        try:
            response = self.app_config_client.get_configuration(Application=application_id,
                                                                Environment=environment_id,
                                                                Configuration=configuration_profile_id,
                                                                ClientId='FeatureToggleAppConfigConfigProvider')
            binary_config_string = response['Content'].read()
            self.feature_toggle_config = json.loads(binary_config_string.decode('utf-8'))
        except Exception as ex:
            LOG.error('Failed to load config from AppConfig: {}'.format(ex))
            LOG.info('Falling to empty config.')
            # There is chance that AppConfig is not available in a particular region.
            self.feature_toggle_config = json.loads('{}')

    @property
    def config(self):
        return self.feature_toggle_config

