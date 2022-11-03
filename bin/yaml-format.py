#!/usr/bin/env python
"""JSON file formatter (without prettier)."""
import os
import sys

my_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, my_path + "/..")

import re
from io import StringIO
from typing import Type

# We use ruamel.yaml for parsing yaml files because it can preserve comments
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from bin._file_formatter import FileFormatter

yaml = YAML()
# We have pyyaml (5.4) to parse our yamls in this repo,
# and pyyaml uses Yaml 1.1
yaml.version = (1, 1)  # type: ignore


class YAMLFormatter(FileFormatter):
    @staticmethod
    def description() -> str:
        return "YAML file formatter"

    @staticmethod
    def format(input_str: str) -> str:
        """Opinionated format YAML file."""
        obj = yaml.load(input_str)
        out_stream = StringIO()
        yaml.dump(
            obj,
            stream=out_stream,
        )
        # ruamel.yaml tends to add 2 empty lines at the bottom of the dump
        return re.sub(r"\n+$", "\n", out_stream.getvalue())

    @staticmethod
    def decode_exception() -> Type[Exception]:
        return YAMLError

    @staticmethod
    def file_extension() -> str:
        return ".yaml"


if __name__ == "__main__":
    YAMLFormatter.main()
