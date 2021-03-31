import boto3

from .translator.arn_generator import ArnGenerator


class RegionConfiguration(object):
    """
    There are times when certain services, or certain configurations of a service are not supported in a region. This
    class abstracts all region/partition specific configuration.
    """

    @classmethod
    def is_apigw_edge_configuration_supported(cls):
        """
        # API Gateway defaults to EDGE endpoint configuration in all regions in AWS partition. But for other partitions,
        # such as GovCloud, they don't support Edge.

        :return: True, if API Gateway does not support Edge configuration
        """

        return ArnGenerator.get_partition_name() not in [
            "aws-us-gov",
            "aws-iso",
            "aws-iso-b",
            "aws-cn",
        ]

    @classmethod
    def is_sar_supported(cls):
        """
        SAR is not supported in af-south-1 at the moment.
        https://aws.amazon.com/about-aws/global-infrastructure/regional-product-services/

        :return: True, if SAR is supported in current region.
        """
        return boto3.Session().region_name not in [
            "af-south-1",
        ]
