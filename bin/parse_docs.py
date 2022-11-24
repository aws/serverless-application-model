#!/usr/bin/env python

import argparse
import json
from pathlib import Path


def parse(s: str):
    parts = s.split("\n\n")
    for part in parts:
        if part.startswith(" `"):
            name = part.split("`")[1]
            yield name, part


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dir", type=Path)
    args = parser.parse_args()

    props = {}
    for path in args.dir.glob("*.md"):
        for name, description in parse(path.read_text()):
            field = f"{path.stem}.{name}"
            props[field] = description

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
