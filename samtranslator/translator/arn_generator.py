import boto3


class ArnGenerator(object):

    @classmethod
    def generate_arn(cls, partition, service, resource, include_account_id=True):
        if not service or not resource:
            raise RuntimeError("Could not construct ARN for resource.")

        arn = 'arn:{0}:{1}:${{AWS::Region}}:'

        if include_account_id:
            arn += '${{AWS::AccountId}}:'

        arn += '{2}'

        return arn.format(partition, service, resource)

    @classmethod
    def generate_aws_managed_policy_arn(cls, policy_name):
        """
        Method to create an ARN of AWS Owned Managed Policy. This uses the right partition name to construct
        the ARN

        :param policy_name: Name of the policy
        :return: ARN Of the managed policy
        """
        return 'arn:{}:iam::aws:policy/{}'.format(ArnGenerator.get_partition_name(),
                                                  policy_name)

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
            region = boto3.session.Session().region_name

        region_string = region.lower()
        if region_string.startswith("cn-"):
            return "aws-cn"
        elif region_string.startswith("us-gov"):
            return "aws-us-gov"
        else:
            return "aws"
