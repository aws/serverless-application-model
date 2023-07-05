import boto3

from .translator.arn_generator import ArnGenerator, NoRegionFound


class RegionConfiguration:
    """
    There are times when certain services, or certain configurations of a service are not supported in a region. This
    class abstracts all region/partition specific configuration.
    """

    @classmethod
    def is_apigw_edge_configuration_supported(cls) -> bool:
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
    def is_service_supported(cls, service, region=None):  # type: ignore[no-untyped-def]
        """
        Not all services are supported in all regions.  This method returns whether a given
        service is supported in a given region.  If no region is specified, the current region
        (as identified by boto3) is used.
        https://aws.amazon.com/about-aws/global-infrastructure/regional-product-services/

        :param service: service code (string used to obtain a boto3 client for the service)
        :param region: region identifier (e.g., us-east-1)
        :return: True, if the service is supported in the region
        """

        # Attempt to re-use an existing session if present.
        session = boto3.Session() if not boto3.DEFAULT_SESSION else boto3.DEFAULT_SESSION

        if not region:
            # get the current region
            region = session.region_name

            # need to handle when region is None so that it won't break
            if region is None:
                if ArnGenerator.BOTO_SESSION_REGION_NAME is not None:
                    region = ArnGenerator.BOTO_SESSION_REGION_NAME
                else:
                    raise NoRegionFound("AWS Region cannot be found")

        # check if the service is available in region
        partition = ArnGenerator.get_partition_name(region)
        available_regions = session.get_available_regions(service, partition_name=partition)
        return region in available_regions
