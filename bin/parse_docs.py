#!/usr/bin/env python
"""
Script to parse a directory containing the AWS SAM documentation in Markdown
format (e.g. https://github.com/awsdocs/aws-sam-developer-guide/tree/main/doc_source).
Outputs in the docs.json format expected by the SAM JSON schema code (see
samtranslator/schema/schema.py).

Usage:
  git clone https://github.com/awsdocs/aws-sam-developer-guide.git
  bin/parse_docs.py aws-sam-developer-guide/doc_source > samtranslator/schema/docs.json
"""

import argparse
import json
from pathlib import Path
from typing import Iterator, Tuple, Dict


def parse(s: str) -> Iterator[Tuple[str, str]]:
    """Parse an AWS SAM docs page in Markdown format, yielding each property."""
    parts = s.split("\n\n")
    for part in parts:
        if part.startswith(" `"):
            name = part.split("`")[1]
            yield name, part.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dir", type=Path)
    args = parser.parse_args()

    props: Dict[str, Dict[str, str]] = {}
    for path in args.dir.glob("*.md"):
        props[path.stem] = {}
        for name, description in parse(path.read_text()):
            props[path.stem][name] = description

    print(
        json.dumps(
            {
                "properties": props,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
