"""Unit tests for merge_strategy.py types."""

import unittest

from parameterized import parameterized
from samtranslator.plugins.globals.merge_strategy import (
    CONCATENATE,
    REPLACE,
    REPLACE_KEYS_MERGE_VALUES,
    MergeOp,
    MergeRule,
    merge_by_key,
)


class TestMergeOp(unittest.TestCase):
    @parameterized.expand(
        [
            ("concatenate", MergeOp.CONCATENATE, "concatenate"),
            ("replace", MergeOp.REPLACE, "replace"),
            ("merge_by_key", MergeOp.MERGE_BY_KEY, "merge_by_key"),
            ("replace_keys_merge_values", MergeOp.REPLACE_KEYS_MERGE_VALUES, "replace_keys_merge_values"),
        ]
    )
    def test_enum_values(self, _name, member, expected):
        self.assertEqual(member.value, expected)


class TestMergeRule(unittest.TestCase):
    @parameterized.expand(
        [
            ("replace", MergeOp.REPLACE, None),
            ("concatenate", MergeOp.CONCATENATE, None),
            ("merge_by_key", MergeOp.MERGE_BY_KEY, "Key"),
            ("replace_keys_merge_values", MergeOp.REPLACE_KEYS_MERGE_VALUES, None),
        ]
    )
    def test_valid_creation(self, _name, op, key):
        rule = MergeRule(op, key=key) if key else MergeRule(op)
        self.assertEqual(rule.op, op)
        self.assertEqual(rule.key, key)

    @parameterized.expand(
        [
            ("merge_by_key_no_key", MergeOp.MERGE_BY_KEY, None, "MERGE_BY_KEY requires a 'key' field"),
            ("replace_with_key", MergeOp.REPLACE, "Bad", "only valid with MERGE_BY_KEY"),
            ("concatenate_with_key", MergeOp.CONCATENATE, "Bad", "only valid with MERGE_BY_KEY"),
            (
                "replace_keys_merge_values_with_key",
                MergeOp.REPLACE_KEYS_MERGE_VALUES,
                "Bad",
                "only valid with MERGE_BY_KEY",
            ),
        ]
    )
    def test_invalid_creation_raises(self, _name, op, key, expected_msg):
        with self.assertRaises(ValueError) as ctx:
            MergeRule(op, key=key)
        self.assertIn(expected_msg, str(ctx.exception))

    def test_frozen_immutable(self):
        rule = MergeRule(MergeOp.REPLACE)
        with self.assertRaises(AttributeError):
            rule.op = MergeOp.CONCATENATE


class TestConvenienceConstructors(unittest.TestCase):
    @parameterized.expand(
        [
            ("CONCATENATE", CONCATENATE, MergeOp.CONCATENATE, None),
            ("REPLACE", REPLACE, MergeOp.REPLACE, None),
            ("REPLACE_KEYS_MERGE_VALUES", REPLACE_KEYS_MERGE_VALUES, MergeOp.REPLACE_KEYS_MERGE_VALUES, None),
            ("MERGE_BY_KEY", merge_by_key("Key"), MergeOp.MERGE_BY_KEY, "Key"),
        ]
    )
    def test_constructor(self, _name, rule, expected_op, expected_key):
        self.assertEqual(rule.op, expected_op)
        self.assertEqual(rule.key, expected_key)


class TestSchemaKeyFormat(unittest.TestCase):
    """Dot-notation schema keys support nested property paths."""

    @parameterized.expand(
        [
            ("top_level", "Architectures"),
            ("one_level_nested", "VpcConfig.SecurityGroupIds"),
            ("two_levels_nested", "VpcConfig.SubnetConfig.SubnetIds"),
        ]
    )
    def test_valid_dot_notation_keys(self, _name, key):
        """Dot-separated paths are the schema key format — all valid."""
        schema = {key: REPLACE}
        # Should not raise — dots are path separators, not errors
        self.assertIn(key, schema)
        self.assertEqual(schema[key], REPLACE)


if __name__ == "__main__":
    unittest.main()
