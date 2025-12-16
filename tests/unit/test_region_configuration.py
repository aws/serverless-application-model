from unittest import TestCase
from unittest.mock import patch, Mock
from parameterized import parameterized
import boto3
from samtranslator.region_configuration import RegionConfiguration

class TestRegionConfiguration(TestCase):
    @parameterized.expand([
        ["aws"],
    ])
    def test_when_apigw_edge_configuration_supported(self, partition):
        with patch(
            "samtranslator.translator.arn_generator.ArnGenerator.get_partition_name"
        ) as get_partition_name_patch:
            get_partition_name_patch.return_value = partition
            self.assertTrue(RegionConfiguration.is_apigw_edge_configuration_supported())

    @parameterized.expand([
        ["aws-cn"], ["aws-us-gov"], ["aws-iso"], ["aws-iso-b"], ["aws-iso-e"], ["aws-iso-f"], ["aws-eusc"]
    ])
    def test_when_apigw_edge_configuration_is_not_supported(self, partition):
        with patch(
            "samtranslator.translator.arn_generator.ArnGenerator.get_partition_name"
        ) as get_partition_name_patch:
            get_partition_name_patch.return_value = partition
            self.assertFalse(RegionConfiguration.is_apigw_edge_configuration_supported())

    @parameterized.expand([
        ["ec2", "cn-north-1"],
        ["ec2", "us-west-2"],
        ["ec2", "us-gov-east-1"],
        ["ec2", "us-isob-east-1"],
        ["ec2", None],
        ["serverlessrepo", "us-east-1"],
        ["serverlessrepo", "ap-southeast-2"],
    ])
    @patch("boto3.Session")
    def test_is_service_supported_positive(self, service, region, BotoSessionMock):
        session_mock = Mock()
        session_mock.region_name = "us-east-1"
        session_mock.get_available_regions.return_value = [
            "us-east-1", "cn-north-1", "us-west-2", "us-gov-east-1", "us-isob-east-1", "ap-southeast-2"
        ]
        BotoSessionMock.return_value = session_mock
        self.assertTrue(RegionConfiguration.is_service_supported(service, region))

    def test_is_service_supported_positive_boto3_default_session(self):
        new_region = "us-west-2"
        boto3.setup_default_session(region_name=new_region)
        self.assertTrue(RegionConfiguration.is_service_supported("ec2", new_region))

    def test_is_service_supported_negative(self):
        self.assertFalse(RegionConfiguration.is_service_supported("ec1", "us-east-1"))
        self.assertFalse(RegionConfiguration.is_service_supported("ec2", "us-east-0"))