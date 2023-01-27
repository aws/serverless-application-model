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
import re
from pathlib import Path
from typing import Iterator, Tuple, Dict


def parse(s: str, cfn_docs: bool) -> Iterator[Tuple[str, str]]:
    """Parse an AWS docs page in Markdown format, yielding each property."""
    parts = s.split("\n\n")
    for part in parts:
        # TODO: More robust matching against properties? This might skip or include wrong sections
        sam_prop = not cfn_docs and part.startswith(" `")
        cfn_prop = cfn_docs and re.match(r"`\w+`  <a .+", part)
        if sam_prop or cfn_prop:
            name = part.split("`")[1]
            yield name, part.strip()


# TODO: Change in the docs instead?
def fix_markdown_code_link(s: str) -> str:
    """Turns `[foo](bar)` into [`foo`](bar); the former doesn't display as a link."""
    return re.sub(r"`\[(\w+)\]\(([^ ]+)\)`", r"[`\1`](\2)", s)


def remove_first_line(s: str) -> str:
    try:
        return s.split("\n", 1)[1]
    except IndexError:
        return ""


def convert_to_full_path(description: str, prefix: str) -> str:
    pattern = re.compile("\(([#\.a-zA-Z0-9_-]+)\)")
    matched_content = pattern.findall(description)

    for path in matched_content:
        if "https://docs.aws.amazon.com/" not in path:
            url = path.split(".")[0] + ".html"
            if "#" in path:
                url += "#" + path.split("#")[1]
            description = description.replace(path, prefix + url)
    return description


def stringbetween(s: str, sep1: str, sep2: str) -> str:
    return s.split(sep1, 1)[1].split(sep2, 1)[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dir", type=Path)
    parser.add_argument("--cfn", action="store_true")
    parser.add_argument("--with-title", help="use doc title instead of filename as key", action="store_true")
    args = parser.parse_args()

    props: Dict[str, Dict[str, str]] = {}
    for path in args.dir.glob("*.md"):
        text = path.read_text()
        title = stringbetween(text, "# ", "<a")
        page = title if args.with_title else path.stem
        for name, description in parse(text, args.cfn):
            if page not in props:
                props[page] = {}
            description = remove_first_line(description)  # Remove property name; already in the schema title
            description = fix_markdown_code_link(description)
            prefix = (
                "https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/"
                if args.cfn
                else "https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/"
            )
            description = convert_to_full_path(description, prefix)
            props[page][name] = description

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
