from unittest import TestCase
from unittest.mock import patch

import boto3
from parameterized import parameterized
from samtranslator.region_configuration import RegionConfiguration


class TestRegionConfiguration(TestCase):
    @parameterized.expand(
        [
            ["aws"],
        ]
    )
    def test_when_apigw_edge_configuration_supported(self, partition):
        with patch(
            "samtranslator.translator.arn_generator.ArnGenerator.get_partition_name"
        ) as get_partition_name_patch:
            get_partition_name_patch.return_value = partition

            self.assertTrue(RegionConfiguration.is_apigw_edge_configuration_supported())

    @parameterized.expand([["aws-cn"], ["aws-us-gov"], ["aws-iso"], ["aws-iso-b"], ["aws-iso-e"], ["aws-iso-f"]])
    def test_when_apigw_edge_configuration_is_not_supported(self, partition):
        with patch(
            "samtranslator.translator.arn_generator.ArnGenerator.get_partition_name"
        ) as get_partition_name_patch:
            get_partition_name_patch.return_value = partition

            self.assertFalse(RegionConfiguration.is_apigw_edge_configuration_supported())

    @parameterized.expand(
        [
            # use ec2 as it's just about everywhere
            ["ec2", "cn-north-1"],
            ["ec2", "us-west-2"],
            ["ec2", "us-gov-east-1"],
            ["ec2", "us-isob-east-1"],
            ["ec2", None],
            # test SAR since SAM uses that
            ["serverlessrepo", "us-east-1"],
            ["serverlessrepo", "ap-southeast-2"],
        ]
    )
    def test_is_service_supported_positive(self, service, region):
        self.assertTrue(RegionConfiguration.is_service_supported(service, region))

    def test_is_service_supported_positive_boto3_default_session(self):
        new_region = "us-west-2"
        boto3.setup_default_session(region_name=new_region)
        self.assertTrue(RegionConfiguration.is_service_supported("ec2", new_region))

    def test_is_service_supported_negative(self):
        # use an unknown service name
        self.assertFalse(RegionConfiguration.is_service_supported("ec1", "us-east-1"))
        # use a region that does not exist
        self.assertFalse(RegionConfiguration.is_service_supported("ec2", "us-east-0"))
        # hard to test with a real service, since the test may start failing once that
        # service is rolled out to more regions...
