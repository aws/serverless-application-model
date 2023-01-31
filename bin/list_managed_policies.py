import json

import boto3

from samtranslator.public.translator import ManagedPolicyLoader


# TODO: generic replace?
def foo(arn: str, partition) -> str:
    return arn.replace("arn:aws:", "arn:" + partition + ":")


def main() -> None:
    # Any region from `aws` partition; IAM is global
    iam = boto3.client("iam", region_name="us-west-2")

    policies_aws = ManagedPolicyLoader(iam).load()  # type: ignore
    policies_aws_cn = {k: foo(v, "aws-cn") for k, v in policies_aws.items()}
    policies_aws_us_gov = {k: foo(v, "aws-us-gov") for k, v in policies_aws.items()}

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
