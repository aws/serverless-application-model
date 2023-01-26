import argparse
import json
import sys
from pathlib import Path
from typing import Iterator


def slugify(s: str) -> str:
    return s.lower().replace(".", "-").replace("::", "-")


def stringafter(s: str, sep: str) -> str:
    return s.split(sep, 1)[1]


# e.g. for AWS::S3::Bucket it's prefixed with aws-properties-s3-bucket: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-s3-bucket.html
def prop_slugs(s: str) -> Iterator[str]:
    slug = slugify(stringafter(s, "::"))
    yield "aws-properties-" + slug
    yield "aws-resource-" + slug


def log(s: str) -> None:
    print(s, file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--docs", type=Path, required=True)
    args = parser.parse_args()

    schema = json.loads(args.schema.read_text())
    docs = json.loads(args.docs.read_text())["properties"]

    # Assumes schema is from GoFormation and has consistent structure
    # TODO: Check whether this shallow walk is enough
    for k, v in schema["definitions"].items():
        if "AWS::" not in k:
            log(f"Skipping {k}: does not start with AWS::")
            continue
        # Property
        if "." in k:
            for slug in prop_slugs(k):
                if slug not in docs:
                    log(f"Skipping {k}: {slug} not in docs")
                    continue
                for kk, vv in v["properties"].items():
                    if kk not in docs[slug]:
                        log(f"Skipping {k}: {kk} not in {slug} docs")
                        continue
                    vv["markdownDescription"] = docs[slug][kk]
        # Resource
        else:
            for slug in prop_slugs(k):
                if slug not in docs:
                    log(f"Skipping {k}: {slug} not in docs")
                    continue
                for kk, vv in v["properties"]["Properties"]["properties"].items():
                    if kk not in docs[slug]:
                        log(f"Skipping {k}: {kk} not in {slug} docs")
                        continue
                    vv["markdownDescription"] = docs[slug][kk]

    print(json.dumps(schema, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
