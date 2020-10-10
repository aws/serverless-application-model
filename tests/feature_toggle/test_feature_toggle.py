from mock import patch, Mock
from parameterized import parameterized, param
from unittest import TestCase

from samtranslator.feature_toggle.feature_toggle import FeatureToggle, FeatureToggleLocalConfigProvider


class TestFeatureToggle(TestCase):
    @parameterized.expand(
        [
            param("feature-1", "beta", "default", False),
            param("feature-1", "beta", "us-west-2", True),
            param("feature-2", "beta", "us-west-2", False),  # because feature is missing
        ]
    )
    def test_feature_toggle_with_local_provider_for_stage(self, feature_name, stage, region, expected):
        feature_toggle = FeatureToggle(FeatureToggleLocalConfigProvider())
        self.assertEqual(feature_toggle.is_enabled_for_stage_in_region(feature_name, stage, region), expected)

    @parameterized.expand(
        [
            param("feature-1", "beta", "default", "123456789123", False),
            param("feature-1", "beta", "us-west-2", "123456789123", True),
            param("feature-2", "beta", "us-west-2", "123456789124", False),  # because feature is missing
        ]
    )
    def test_feature_toggle_with_local_provider_for_account_id(self, feature_name, stage, region, account_id, expected):
        feature_toggle = FeatureToggle(FeatureToggleLocalConfigProvider())
        self.assertEqual(
            feature_toggle.is_enabled_for_account_in_region(feature_name, stage, account_id, region), expected
        )
