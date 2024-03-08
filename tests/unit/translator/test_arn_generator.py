from unittest import TestCase
from unittest.mock import Mock, patch

from parameterized import parameterized
from samtranslator.translator.arn_generator import ArnGenerator


class TestArnGenerator(TestCase):
    @parameterized.expand(
        [
            ["us-east-1", "aws"],
            ["eu-west-1", "aws"],
            ["cn-north-1", "aws-cn"],
            ["us-gov-west-1", "aws-us-gov"],
            ["us-iso-east-1", "aws-iso"],
            ["us-isob-east-1", "aws-iso-b"],
            ["eu-isoe-west-1", "aws-iso-e"],
        ]
    )
    def test_get_partition_name(self, region, expected_partition):
        self.assertEqual(expected_partition, ArnGenerator.get_partition_name(region=region))

    @parameterized.expand(
        [
            ["us-east-1", "aws"],
            ["eu-west-1", "aws"],
            ["cn-north-1", "aws-cn"],
            ["us-gov-west-1", "aws-us-gov"],
            ["us-iso-east-1", "aws-iso"],
            ["us-isob-east-1", "aws-iso-b"],
            ["eu-isoe-west-1", "aws-iso-e"],
        ]
    )
    def test_get_partition_name_when_region_not_provided(self, region, expected_partition):
        with patch("samtranslator.translator.arn_generator._get_region_from_session", Mock(return_value=region)):
            self.assertEqual(expected_partition, ArnGenerator.get_partition_name())
