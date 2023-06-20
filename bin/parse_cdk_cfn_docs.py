#!/usr/bin/env python
"""
Converts docs JSON from this format:
  https://github.com/aws/aws-cdk/blob/ad89f0182e218eee01b0aef84b055a96556dda59/packages/%40aws-cdk/cfnspec/spec-source/cfn-docs/cfn-docs.json
To this format:
  https://github.com/aws/serverless-application-model/blob/237c7394c6e7ab61c1fad27f439a7b52bcd1b5af/schema_source/cloudformation-docs.json

Originally used https://github.com/awsdocs/aws-cloudformation-user-guide, but switched since retired.
See https://aws.amazon.com/blogs/aws/retiring-the-aws-documentation-on-github/
"""

import argparse
import json
from pathlib import Path
from typing import Dict, Any


def convert(obj: Dict[str, Any]) -> Dict[str, Any]:
    out = {
        "properties": {},
    }

    for k, v in obj["Types"].items():
        kk = k.replace(".", " ")
        vv = v["properties"]
        out["properties"][kk] = vv

    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs", type=Path, required=True)
    args = parser.parse_args()

    obj = json.loads(args.docs.read_text())
    print(
        json.dumps(
            convert(obj),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
