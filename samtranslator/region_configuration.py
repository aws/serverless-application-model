from .translator.arn_generator import ArnGenerator


class RegionConfiguration(object):
    """
    There are times when certain services, or certain configurations of a service are not supported in a region. This
    class abstracts all region/partition specific configuration.
    """

    partitions = {
        "govcloud": "aws-us-gov",
        "china": "aws-cn"
    }

    @classmethod
    def is_apigw_edge_configuration_supported(cls):
        """
        # API Gateway defaults to EDGE endpoint configuration in all regions in AWS partition. But for other partitions,
        # such as GovCloud, they don't support Edge.

        :return: True, if API Gateway does not support Edge configuration
        """

        return ArnGenerator.get_partition_name() not in [
            cls.partitions["govcloud"],
            cls.partitions["china"]
        ]
