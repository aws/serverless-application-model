#!/usr/bin/env python
"""
Converts docs JSON from this format:
  https://github.com/aws/aws-cdk/blob/ad89f0182e218eee01b0aef84b055a96556dda59/packages/%40aws-cdk/cfnspec/spec-source/cfn-docs/cfn-docs.json
To this format:
  https://github.com/aws/serverless-application-model/blob/237c7394c6e7ab61c1fad27f439a7b52bcd1b5af/schema_source/cloudformation-docs.json
Originally used https://github.com/awsdocs/aws-cloudformation-user-guide, but switched since retired.
See https://aws.amazon.com/blogs/aws/retiring-the-aws-documentation-on-github/
Expects input from stdin; outputs to stdout.
"""

import json
import sys
from typing import Any, Dict


def main() -> None:
    obj = json.load(sys.stdin)

    out: Dict[str, Any] = {"properties": {}}
    for k, v in obj["Types"].items():
        kk = k.replace(".", " ")
        vv = v["properties"]
        out["properties"][kk] = vv

    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
