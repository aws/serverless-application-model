from unittest import TestCase
from parameterized import parameterized
from mock import patch

from samtranslator.translator.arn_generator import ArnGenerator, NoRegionFound


class TestArnGenerator(TestCase):
    def setUp(self):
        ArnGenerator.BOTO_SESSION_REGION_NAME = None

    @parameterized.expand(
        [("us-east-1", "aws"), ("cn-east-1", "aws-cn"), ("us-gov-west-1", "aws-us-gov"), ("US-EAST-1", "aws")]
    )
    def test_get_partition_name(self, region, expected):
        actual = ArnGenerator.get_partition_name(region)

        self.assertEqual(actual, expected)

    @patch("boto3.session.Session.region_name", None)
    def test_get_partition_name_raise_NoRegionFound(self):
        with self.assertRaises(NoRegionFound):
            ArnGenerator.get_partition_name(None)

    def test_get_partition_name_from_boto_session(self):
        ArnGenerator.BOTO_SESSION_REGION_NAME = "us-east-1"

        actual = ArnGenerator.get_partition_name()

        self.assertEqual(actual, "aws")

        ArnGenerator.BOTO_SESSION_REGION_NAME = None
