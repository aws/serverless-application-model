#!/usr/bin/env python
"""Print the templates selected by .cfnlintrc.yaml, relative to the project root, one per line."""

import glob
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).absolute().parent.parent


def expand(patterns: list[str]) -> set[str]:
    # glob.glob, like cfn-lint, rather than Path.glob, which differs for hidden files and symlinks
    paths: set[str] = set()
    for pattern in patterns:
        paths.update(glob.glob(pattern, root_dir=PROJECT_ROOT, recursive=True))  # noqa: PTH207
    return paths


def main() -> None:
    config = yaml.safe_load(PROJECT_ROOT.joinpath(".cfnlintrc.yaml").read_text())
    templates = expand(config["templates"]) - expand(config.get("ignore_templates", []))
    print("\n".join(sorted(templates)))


if __name__ == "__main__":
    main()
