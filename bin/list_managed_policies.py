import json
import re

import boto3

from samtranslator.translator.managed_policy_translator import ManagedPolicyLoader


def replace_partition(arn: str, partition: str) -> str:
    return re.sub(r"^arn:\w+:", f"arn:{partition}:", arn)


def main() -> None:
    # Any region from `aws` partition; IAM is global
    iam = boto3.client("iam", region_name="us-west-2")

    policies_aws = ManagedPolicyLoader(iam).load()  # type: ignore
    policies_aws_cn = {k: replace_partition(v, "aws-cn") for k, v in policies_aws.items()}
    policies_aws_us_gov = {k: replace_partition(v, "aws-us-gov") for k, v in policies_aws.items()}

    print(
        json.dumps(
            {
                "aws": policies_aws,
                "aws-cn": policies_aws_cn,
                "aws-us-gov": policies_aws_us_gov,
            }
        )
    )


if __name__ == "__main__":
    main()
