import os
import sys
from unittest import TestCase
from unittest.mock import Mock, patch

from parameterized import param, parameterized
from samtranslator.feature_toggle.dialup import DisabledDialup, SimpleAccountPercentileDialup, ToggleDialup
from samtranslator.feature_toggle.feature_toggle import (
    FeatureToggle,
    FeatureToggleAppConfigConfigProvider,
    FeatureToggleLocalConfigProvider,
)

my_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, my_path + "/..")


class TestFeatureToggle(TestCase):
    @parameterized.expand(
        [
            param("feature-1", "beta", "default", "123456789123", False),
            param("feature-1", "beta", "us-west-2", "123456789123", True),
            param("feature-2", "beta", "us-west-2", "123456789123", False),  # because feature is missing
            param("feature-1", "beta", "ap-south-1", "123456789124", False),  # because default is used
            param("feature-1", "alpha", "us-east-1", "123456789123", False),  # non-exist stage
            param("feature-1", "beta", "us-east-1", "123456789100", True),
            param("feature-1", "beta", "us-east-1", "123456789123", False),
            # any None for stage, region and account_id should return False
            param("feature-1", None, None, None, False),
            param("feature-1", "beta", None, None, False),
            param("feature-1", "beta", "us-west-2", None, False),
            param("feature-1", "beta", None, "123456789123", False),
        ]
    )
    def test_feature_toggle_with_local_provider(self, feature_name, stage, region, account_id, expected):
        feature_toggle = FeatureToggle(
            FeatureToggleLocalConfigProvider(os.path.join(my_path, "input", "feature_toggle_config.json")),
            stage=stage,
            region=region,
            account_id=account_id,
        )
        self.assertEqual(feature_toggle.is_enabled(feature_name), expected)

    @parameterized.expand(
        [
            param("toggle", ToggleDialup),
            param("account-percentile", SimpleAccountPercentileDialup),
            param("something-else", DisabledDialup),
        ]
    )
    def test__get_dialup(self, dialup_type, expected_class):
        feature_toggle = FeatureToggle(
            FeatureToggleLocalConfigProvider(os.path.join(my_path, "input", "feature_toggle_config.json")),
            stage=None,
            region=None,
            account_id=None,
        )
        region_config = {"type": dialup_type}
        dialup = feature_toggle._get_dialup(region_config, "some-feature")
        self.assertIsInstance(dialup, expected_class)


class TestFeatureToggleAppConfig(TestCase):
    def setUp(self):
        self.content_stream_mock = Mock()
        self.content_stream_mock.read.return_value = b"""
        {
            "feature-1": {
                "beta": {
                    "us-west-2": {"type": "toggle", "enabled": true},
                    "us-east-1": {"type": "account-percentile", "enabled-%": 10},
                    "default": {"type": "toggle", "enabled": false},
                    "123456789123": {
                        "us-west-2": {"type": "toggle", "enabled": true},
                        "default": {"type": "toggle", "enabled": false}
                    }
                },
                "gamma": {
                    "default": {"type": "toggle", "enabled": false},
                    "123456789123": {
                        "us-east-1": {"type": "toggle", "enabled": false},
                        "default": {"type": "toggle", "enabled": false}
                    }
                },
                "prod": {"default": {"type": "toggle", "enabled": false}}
            }
        }
        """
        self.app_config_mock = Mock()
        self.app_config_mock.get_configuration.return_value = {"Content": self.content_stream_mock}

    @parameterized.expand(
        [
            param("feature-1", "beta", "default", "123456789123", False),
            param("feature-1", "beta", "us-west-2", "123456789123", True),
            param("feature-2", "beta", "us-west-2", "123456789123", False),  # because feature is missing
            param("feature-1", "beta", "ap-south-1", "123456789124", False),  # because default is used
            param("feature-1", "alpha", "us-east-1", "123456789123", False),  # non-exist stage
            param("feature-1", "beta", "us-east-1", "123456789100", True),
            param("feature-1", "beta", "us-east-1", "123456789123", False),
            # any None for stage, region and account_id returns False
            param("feature-1", None, None, None, False),
            param("feature-1", "beta", None, None, False),
            param("feature-1", "beta", "us-west-2", None, False),
            param("feature-1", "beta", None, "123456789123", False),
        ]
    )
    @patch("samtranslator.feature_toggle.feature_toggle.boto3")
    @patch("samtranslator.feature_toggle.feature_toggle.Config")
    def test_feature_toggle_with_appconfig_provider(
        self, feature_name, stage, region, account_id, expected, config_mock, boto3_mock
    ):
        boto3_mock.client.return_value = self.app_config_mock
        config_object_mock = Mock()
        config_mock.return_value = config_object_mock
        feature_toggle_config_provider = FeatureToggleAppConfigConfigProvider(
            "test_app_id", "test_env_id", "test_conf_id"
        )
        feature_toggle = FeatureToggle(
            feature_toggle_config_provider, stage=stage, region=region, account_id=account_id
        )
        boto3_mock.client.assert_called_once_with("appconfig", config=config_object_mock)
        self.assertEqual(feature_toggle.is_enabled(feature_name), expected)

    @parameterized.expand(
        [
            param("feature-1", "beta", "default", "123456789123", False),
            param("feature-1", "beta", "us-west-2", "123456789123", True),
            param("feature-2", "beta", "us-west-2", "123456789123", False),  # because feature is missing
            param("feature-1", "beta", "ap-south-1", "123456789124", False),  # because default is used
            param("feature-1", "alpha", "us-east-1", "123456789123", False),  # non-exist stage
            param("feature-1", "beta", "us-east-1", "123456789100", True),
            param("feature-1", "beta", "us-east-1", "123456789123", False),
            # any None for stage, region and account_id returns False
            param("feature-1", None, None, None, False),
            param("feature-1", "beta", None, None, False),
            param("feature-1", "beta", "us-west-2", None, False),
            param("feature-1", "beta", None, "123456789123", False),
        ]
    )
    @patch("samtranslator.feature_toggle.feature_toggle.boto3")
    def test_feature_toggle_with_appconfig_provider_and_app_config_client(
        self, feature_name, stage, region, account_id, expected, boto3_mock
    ):
        feature_toggle_config_provider = FeatureToggleAppConfigConfigProvider(
            "test_app_id", "test_env_id", "test_conf_id", self.app_config_mock
        )
        feature_toggle = FeatureToggle(
            feature_toggle_config_provider, stage=stage, region=region, account_id=account_id
        )
        boto3_mock.client.assert_not_called()
        self.assertEqual(feature_toggle.is_enabled(feature_name), expected)


class TestFeatureToggleAppConfigConfigProvider(TestCase):
    @patch("samtranslator.feature_toggle.feature_toggle.boto3")
    def test_feature_toggle_with_exception(self, boto3_mock):
        boto3_mock.client.raiseError.side_effect = Exception()
        feature_toggle_config_provider = FeatureToggleAppConfigConfigProvider(
            "test_app_id", "test_env_id", "test_conf_id"
        )
        self.assertEqual(feature_toggle_config_provider.config, {})
