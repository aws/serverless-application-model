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
from typing import Dict, Iterator, Tuple


def parse(s: str) -> Iterator[Tuple[str, str]]:
    """Parse an AWS docs page in Markdown format, yielding each property."""
    # Prevent from parsing return values accidentally
    s = stringbetween(s, "#\s+Properties", "#\s+Return values")
    if not s:
        return
    parts = s.split("\n\n")
    for part in parts:
        match = re.match(r"^\s*`(\w+)`\s+<a", part)
        if match:
            yield match.group(1), part


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
    """
    Return string between regexes. Case-insensitive. If sep2 doesn't match,
    returns to end of string.
    """
    start = re.search(sep1, s, re.IGNORECASE)
    if not start:
        return ""
    s = s[start.end() :]
    end = re.search(sep2, s, re.IGNORECASE)
    if not end:
        return s
    return s[: end.start()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dir", type=Path)
    parser.add_argument("--cfn", action="store_true")
    args = parser.parse_args()

    props: Dict[str, Dict[str, str]] = {}
    for path in args.dir.glob("*.md"):
        text = path.read_text()
        title = stringbetween(text, r"#\s+", r"<a")
        if not title:
            raise Exception(f"{path} has no title")
        # In CFN docs, always expect either `AWS::Foo::Bar`, or `AWS::Foo::Bar SomeProperty`,
        # which maps to the definition names in GoFormation schema
        # Tangentially related: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-resource-specification-format.html
        if args.cfn and not re.match(r"^\w+::\w+::\w+( \w+)?$", title):
            continue
        page = title if args.cfn else path.stem
        for name, description in parse(text):
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
            # Assume properties (what we care about) at top, so skip if already exists
            if name in props[page]:
                continue
            props[page][name] = description.strip()

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
