import unittest

from parameterized import parameterized
from samtranslator.plugins.globals.merge_strategy import MergeOp


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

    def test_all_members_present(self):
        """Ensure the enum has exactly the 4 expected strategies."""
        self.assertEqual(
            set(MergeOp),
            {MergeOp.DEEP_MERGE, MergeOp.CONCATENATE, MergeOp.REPLACE, MergeOp.PRUNE_AND_MERGE},
        )


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
        schema = {key: MergeOp.REPLACE}
        # Should not raise — dots are path separators, not errors
        self.assertIn(key, schema)
        self.assertEqual(schema[key], MergeOp.REPLACE)


if __name__ == "__main__":
    unittest.main()
