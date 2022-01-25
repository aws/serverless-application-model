from unittest import TestCase

from unittest.mock import patch
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

    @parameterized.expand(
        [
            ["aws-cn"],
            ["aws-us-gov"],
            ["aws-iso"],
            ["aws-iso-b"],
        ]
    )
    def test_when_apigw_edge_configuration_is_not_supported(self, partition):
        with patch(
            "samtranslator.translator.arn_generator.ArnGenerator.get_partition_name"
        ) as get_partition_name_patch:
            get_partition_name_patch.return_value = partition

            self.assertFalse(RegionConfiguration.is_apigw_edge_configuration_supported())
