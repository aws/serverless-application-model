import boto3

from .translator.arn_generator import ArnGenerator, NoRegionFound


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
        SAR is not supported in some regions.
        https://aws.amazon.com/about-aws/global-infrastructure/regional-product-services/
        https://docs.aws.amazon.com/general/latest/gr/serverlessrepo.html

        :return: True, if SAR is supported in current region.
        """

        session = boto3.Session()

        # get the current region
        region = session.region_name

        # need to handle when region is None so that it won't break
        if region is None:
            if ArnGenerator.BOTO_SESSION_REGION_NAME is not None:
                region = ArnGenerator.BOTO_SESSION_REGION_NAME
            else:
                raise NoRegionFound("AWS Region cannot be found")

        # boto3 get_available_regions call won't return us-gov and cn regions even if SAR is available
        if region.startswith("cn") or region.startswith("us-gov"):
            return True

        # get all regions where SAR are available
        available_regions = session.get_available_regions("serverlessrepo")
        return region in available_regions
