from functools import lru_cache
from typing import Optional

import boto3


class NoRegionFound(Exception):
    pass


@lru_cache(maxsize=1)  # Only need to cache one as once deployed, it is not gonna deal with another region.
def _get_region_from_session() -> str:
    return boto3.session.Session().region_name


@lru_cache(maxsize=1)  # Only need to cache one as once deployed, it is not gonna deal with another region.
def _region_to_partition(region: str) -> str:
    # setting default partition to aws, this will be overwritten by checking the region below
    region_string = region.lower()
    region_to_partition_map = {
        "cn-": "aws-cn",
        "us-iso-": "aws-iso",
        "us-isob": "aws-iso-b",
        "us-gov": "aws-us-gov",
        "eu-isoe": "aws-iso-e",
        "us-isof": "aws-iso-f",
    }
    for key, value in region_to_partition_map.items():
        if region_string.startswith(key):
            return value

    return "aws"


class ArnGenerator:
    BOTO_SESSION_REGION_NAME: Optional[str] = None

    @classmethod
    def generate_arn(
        cls,
        partition: str,
        service: str,
        resource: str,
        include_account_id: bool = True,
        region: Optional[str] = None,
    ) -> str:
        """Generate AWS ARN.

        Parameters
        ----------
        partition
            AWS partition, ie "aws" or "aws-cn"
        service
            AWS service name
        resource
            Resource name, it must include service specific prefixes is "table/" for DynamoDB table
        include_account_id, optional
            include account ID in the ARN or not, by default True
        region, optional
            resource region, by default None.
            To omit region in ARN (ie for a S3 bucket) pass "" (empty string).
            Don't set it to any other default value because None can be passed by a caller and
            must be handled in the function itself.

        Returns
        -------
            Generated ARN

        Raises
        ------
        RuntimeError
            if service or resource are not provided
        """
        if not service or not resource:
            raise RuntimeError("Could not construct ARN for resource.")

        if region is None:
            region = "${AWS::Region}"

        arn = "arn:{0}:{1}:{region}:"

        if include_account_id:
            arn += "${{AWS::AccountId}}:"

        arn += "{2}"

        return arn.format(partition, service, resource, region=region)

    @classmethod
    def generate_aws_managed_policy_arn(cls, policy_name: str) -> str:
        """
        Method to create an ARN of AWS Owned Managed Policy. This uses the right partition name to construct
        the ARN

        :param policy_name: Name of the policy
        :return: ARN Of the managed policy
        """
        return f"arn:{ArnGenerator.get_partition_name()}:iam::aws:policy/{policy_name}"

    @classmethod
    def get_partition_name(cls, region: Optional[str] = None) -> str:
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

            region = (
                _get_region_from_session()
                if ArnGenerator.BOTO_SESSION_REGION_NAME is None
                else ArnGenerator.BOTO_SESSION_REGION_NAME
            )

        # If region is still None, then we could not find the region. This will only happen
        # in the local context. When this is deployed, we will be able to find the region like
        # we did before.
        if region is None:
            raise NoRegionFound("AWS Region cannot be found")

        return _region_to_partition(region)

    @classmethod
    def generate_dynamodb_table_arn(cls, partition: str, region: str, table_name: str) -> str:
        """Generate DynamoDB table ARN.

        Parameters
        ----------
        partition
            _description_
        region
            DynamoDB table region
        table_name
            DynamoDB table name

        Returns
        -------
            DynamoDB table ARN.
        """
        return ArnGenerator.generate_arn(
            partition=partition, service="dynamodb", resource=f"table/{table_name}", region=region
        )
