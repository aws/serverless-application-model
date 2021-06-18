import boto3


class NoRegionFound(Exception):
    pass


class ArnGenerator(object):
    BOTO_SESSION_REGION_NAME = None

    @classmethod
    def generate_arn(cls, partition, service, resource, include_account_id=True):
        if not service or not resource:
            raise RuntimeError("Could not construct ARN for resource.")

        arn = "arn:{0}:{1}:${{AWS::Region}}:"

        if include_account_id:
            arn += "${{AWS::AccountId}}:"

        arn += "{2}"

        return arn.format(partition, service, resource)

    @classmethod
    def generate_aws_managed_policy_arn(cls, policy_name):
        """
        Method to create an ARN of AWS Owned Managed Policy. This uses the right partition name to construct
        the ARN

        :param policy_name: Name of the policy
        :return: ARN Of the managed policy
        """
        return "arn:{}:iam::aws:policy/{}".format(ArnGenerator.get_partition_name(), policy_name)

    @classmethod
    def get_partition_name(cls, region=None):
        """
        Gets the name of the partition given the region name. If region name is not provided, this method will
        use Boto3 to get name of the region where this code is running.

        This implementation is borrowed from AWS CLI
        https://github.com/aws/aws-cli/blob/1.11.139/awscli/customizations/emr/createdefaultroles.py#L59

        :param region: Optional name of the region
        :return: Partition name
        """

        if region is None:
            # Use Boto3 to get the region where code is running. This uses Boto's regular region resolution
            # mechanism, starting from AWS_DEFAULT_REGION environment variable.

            if ArnGenerator.BOTO_SESSION_REGION_NAME is None:
                region = boto3.session.Session().region_name
            else:
                region = ArnGenerator.BOTO_SESSION_REGION_NAME

        # If region is still None, then we could not find the region. This will only happen
        # in the local context. When this is deployed, we will be able to find the region like
        # we did before.
        if region is None:
            raise NoRegionFound("AWS Region cannot be found")

        # setting default partition to aws, this will be overwritten by checking the region below
        partition = "aws"

        region_string = region.lower()
        if region_string.startswith("cn-"):
            partition = "aws-cn"
        elif region_string.startswith("us-iso-"):
            partition = "aws-iso"
        elif region_string.startswith("us-isob"):
            partition = "aws-iso-b"
        elif region_string.startswith("us-gov"):
            partition = "aws-us-gov"

        return partition
