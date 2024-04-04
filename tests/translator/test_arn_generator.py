from unittest import TestCase
from unittest.mock import Mock, patch

from parameterized import parameterized
from samtranslator.translator.arn_generator import ArnGenerator, NoRegionFound


class TestArnGenerator(TestCase):
    def setUp(self):
        ArnGenerator.BOTO_SESSION_REGION_NAME = None

    @parameterized.expand(
        [
            ("us-east-1", "aws"),
            ("cn-east-1", "aws-cn"),
            ("us-gov-west-1", "aws-us-gov"),
            ("us-isob-east-1", "aws-iso-b"),
            ("eu-isoe-west-1", "aws-iso-e"),
            ("US-EAST-1", "aws"),
            ("us-isof-east-1", "aws-iso-f"),
        ]
    )
    def test_get_partition_name(self, region, expected):
        actual = ArnGenerator.get_partition_name(region)

        self.assertEqual(actual, expected)

    @patch("samtranslator.translator.arn_generator._get_region_from_session", Mock(return_value=None))
    def test_get_partition_name_raise_NoRegionFound(self):
        with self.assertRaises(NoRegionFound):
            ArnGenerator.get_partition_name(None)

    def test_get_partition_name_from_boto_session(self):
        ArnGenerator.BOTO_SESSION_REGION_NAME = "us-east-1"

        actual = ArnGenerator.get_partition_name()

        self.assertEqual(actual, "aws")

        ArnGenerator.BOTO_SESSION_REGION_NAME = None

    def test_generate_dynamodb_table_arn(self):
        region = "us-west-1"

        actual = ArnGenerator.generate_dynamodb_table_arn(
            table_name="DdbTable", region=region, partition="${AWS::Partition}"
        )
        expected = f"arn:${{AWS::Partition}}:dynamodb:{region}:${{AWS::AccountId}}:table/DdbTable"

        self.assertEqual(expected, actual)

    def test_generate_arn_with_empty_region(self):
        actual = ArnGenerator.generate_arn(
            partition="aws",
            service="weirdo",
            resource="my_resource",
            region="",
        )
        expected = "arn:aws:weirdo::${AWS::AccountId}:my_resource"

        self.assertEqual(expected, actual)

    def test_generate_arn_without_region_provided(self):
        actual = ArnGenerator.generate_arn(
            partition="aws",
            service="weirdo",
            resource="my_resource",
        )
        expected = "arn:aws:weirdo:${AWS::Region}:${AWS::AccountId}:my_resource"

        self.assertEqual(expected, actual)
