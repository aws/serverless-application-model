from unittest import TestCase

from parameterized import param, parameterized
from samtranslator.feature_toggle.dialup import DisabledDialup, SimpleAccountPercentileDialup, ToggleDialup


class TestDisabledDialup(TestCase):
    def test_is_enabled(self):
        region_config = {}
        dialup = DisabledDialup(region_config)
        self.assertFalse(dialup.is_enabled())

    def test___str__(self):
        region_config = {}
        dialup = DisabledDialup(region_config)
        self.assertEqual(str(dialup), "DisabledDialup")


class TestToggleDialUp(TestCase):
    @parameterized.expand(
        [
            param({"type": "toggle", "enabled": True}, True),
            param({"type": "toggle", "enabled": False}, False),
            param({"type": "toggle"}, False),  # missing "enabled" key
        ]
    )
    def test_is_enabled(self, region_config, expected):
        dialup = ToggleDialup(region_config)
        self.assertEqual(dialup.is_enabled(), expected)

    def test___str__(self):
        dialup = ToggleDialup({})
        self.assertEqual(str(dialup), "ToggleDialup")


class TestSimpleAccountPercentileDialup(TestCase):
    @parameterized.expand(
        [
            param({"type": "account-percentile", "enabled-%": 10}, "feature-1", "123456789100", True),
            param({"type": "account-percentile", "enabled-%": 10}, "feautre-1", "123456789123", False),
            param({"type": "account-percentile", "enabled": True}, "feature-1", "123456789100", False),
        ]
    )
    def test_is_enabled(self, region_config, feature_name, account_id, expected):
        dialup = SimpleAccountPercentileDialup(
            region_config=region_config,
            account_id=account_id,
            feature_name=feature_name,
        )
        self.assertEqual(dialup.is_enabled(), expected)

    @parameterized.expand(
        [
            param("feature-1", "123456789123"),
            param("feature-2", "000000000000"),
            param("feature-3", "432187654321"),
            param("feature-4", "111222333444"),
        ]
    )
    def test__get_account_percentile(self, account_id, feature_name):
        region_config = {"type": "account-percentile", "enabled-%": 10}
        dialup = SimpleAccountPercentileDialup(
            region_config=region_config,
            account_id=account_id,
            feature_name=feature_name,
        )
        self.assertTrue(0 <= dialup._get_account_percentile() < 100)

    def test___str__(self):
        dialup = SimpleAccountPercentileDialup(
            region_config={},
            account_id="123456789012",
            feature_name="feat",
        )
        self.assertEqual(str(dialup), "SimpleAccountPercentileDialup")
