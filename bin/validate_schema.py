#!/usr/bin/env python

import json
from pathlib import Path
from typing import Iterator

from cfn_flip import to_json  # type: ignore
from jsonschema import validate

SCHEMA = json.loads(Path("samtranslator/schema/schema.json").read_bytes())


def get_templates() -> Iterator[Path]:
    paths = (
        list(Path("tests/translator/input").glob("**/*.yaml"))
        + list(Path("tests/translator/input").glob("**/*.yml"))
        + list(Path("integration/resources/templates").glob("**/*.yaml"))
        + list(Path("integration/resources/templates").glob("**/*.yml"))
    )
    # TODO: Enable (most likely) everything but error_
    skips = [
        "error_",
        "unsupported_resources",
        "resource_with_invalid_type",
    ]

    def should_skip(s: str) -> bool:
        for skip in skips:
            if skip in s:
                return True
        return False

    for path in paths:
        if not should_skip(str(path)):
            yield path


def main() -> None:
    for path in get_templates():
        print(f"Checking {path}")
        obj = json.loads(to_json(path.read_bytes()))
        validate(obj, schema=SCHEMA)


if __name__ == "__main__":
    main()
