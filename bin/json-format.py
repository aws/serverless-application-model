#!/usr/bin/env python
"""JSON file formatter (without prettier)."""
import os
import sys

my_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, my_path + "/..")

import json
from typing import Type

from bin._file_formatter import FileFormatter


class JSONFormatter(FileFormatter):
    @staticmethod
    def description() -> str:
        return "JSON file formatter"

    @staticmethod
    def format(input_str: str) -> str:
        """Opinionated format JSON file."""
        obj = json.loads(input_str)
        return json.dumps(obj, indent=2, sort_keys=True) + "\n"

    @staticmethod
    def decode_exception() -> Type[Exception]:
        return json.JSONDecodeError

    @staticmethod
    def file_extension() -> str:
        return ".json"


if __name__ == "__main__":
    JSONFormatter.main()
