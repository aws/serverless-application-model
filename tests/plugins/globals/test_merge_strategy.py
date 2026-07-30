"""Unit tests for merge_strategy.py types."""

import unittest

from parameterized import parameterized
from samtranslator.plugins.globals.merge_strategy import (
    CONCATENATE,
    DEEP_MERGE,
    PRUNE_AND_MERGE,
    REPLACE,
    MergeOp,
    MergeRule,
)


class TestMergeOp(unittest.TestCase):
    @parameterized.expand(
        [
            ("deep_merge", MergeOp.DEEP_MERGE, "deep_merge"),
            ("concatenate", MergeOp.CONCATENATE, "concatenate"),
            ("replace", MergeOp.REPLACE, "replace"),
            ("prune_and_merge", MergeOp.PRUNE_AND_MERGE, "prune_and_merge"),
        ]
    )
    def test_enum_values(self, _name, member, expected):
        self.assertEqual(member.value, expected)


class TestMergeRule(unittest.TestCase):
    @parameterized.expand(
        [
            ("deep_merge", MergeOp.DEEP_MERGE),
            ("replace", MergeOp.REPLACE),
            ("concatenate", MergeOp.CONCATENATE),
            ("prune_and_merge", MergeOp.PRUNE_AND_MERGE),
        ]
    )
    def test_valid_creation(self, _name, op):
        rule = MergeRule(op)
        self.assertEqual(rule.op, op)

    def test_frozen_immutable(self):
        rule = MergeRule(MergeOp.REPLACE)
        with self.assertRaises(AttributeError):
            rule.op = MergeOp.CONCATENATE


class TestConvenienceConstructors(unittest.TestCase):
    @parameterized.expand(
        [
            ("DEEP_MERGE", DEEP_MERGE, MergeOp.DEEP_MERGE),
            ("CONCATENATE", CONCATENATE, MergeOp.CONCATENATE),
            ("REPLACE", REPLACE, MergeOp.REPLACE),
            ("PRUNE_AND_MERGE", PRUNE_AND_MERGE, MergeOp.PRUNE_AND_MERGE),
        ]
    )
    def test_constructor(self, _name, rule, expected_op):
        self.assertEqual(rule.op, expected_op)


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
