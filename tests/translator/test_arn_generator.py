from unittest import TestCase
from parameterized import parameterized
from mock import Mock, patch

from samtranslator.translator.arn_generator import ArnGenerator, NoRegionFound


class TestArnGenerator(TestCase):
    def setUp(self):
        ArnGenerator.class_boto_session = None

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
        boto_session_mock = Mock()
        boto_session_mock.region_name = "us-east-1"

        ArnGenerator.class_boto_session = boto_session_mock

        actual = ArnGenerator.get_partition_name()

        self.assertEqual(actual, "aws")

        ArnGenerator.class_boto_session = None
