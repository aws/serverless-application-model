#!/usr/bin/env python
"""Print the templates selected by .cfnlintrc.yaml, relative to the project root, one per line."""

from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).absolute().parent.parent


def expand(patterns: list[str]) -> set[str]:
    return {str(path.relative_to(PROJECT_ROOT)) for pattern in patterns for path in PROJECT_ROOT.glob(pattern)}


def main() -> None:
    config = yaml.safe_load(PROJECT_ROOT.joinpath(".cfnlintrc.yaml").read_text())
    templates = expand(config["templates"]) - expand(config.get("ignore_templates", []))
    print("\n".join(sorted(templates)))


if __name__ == "__main__":
    main()
