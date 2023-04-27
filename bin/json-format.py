#!/usr/bin/env python
"""JSON file formatter (without prettier)."""
import sys
from pathlib import Path

# To allow this script to be executed from other directories
sys.path.insert(0, str(Path(__file__).absolute().parent.parent))

import json
from typing import Type

from bin._file_formatter import FileFormatter


class JSONFormatter(FileFormatter):
    @staticmethod
    def description() -> str:
        return "JSON file formatter"

    def format_str(self, input_str: str) -> str:
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
