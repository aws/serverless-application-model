import json

import boto3

from samtranslator.public.translator import ManagedPolicyLoader


def foo(s: str) -> str:
    return s.replace("arn:aws:", "arn:<partition>:")


def main() -> None:
    iam = boto3.client("iam", region_name="us-west-2")
    policies = ManagedPolicyLoader(iam).load()  # type: ignore
    print(json.dumps({k: foo(v) for k, v in policies.items()}, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
