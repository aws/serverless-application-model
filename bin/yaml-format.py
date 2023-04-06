#!/usr/bin/env python
"""JSON file formatter (without prettier)."""
import sys
from pathlib import Path
from textwrap import dedent

# To allow this script to be executed from other directories
sys.path.insert(0, str(Path(__file__).absolute().parent.parent))

import re
from io import StringIO
from typing import Any, Dict, Type

# We use ruamel.yaml for parsing yaml files because it can preserve comments
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from bin._file_formatter import FileFormatter

yaml = YAML()
# We have pyyaml (5.4) to parse our yamls in this repo,
# and pyyaml uses Yaml 1.1
yaml.version = (1, 1)  # type: ignore


YAML_VERSION_COMMENT_REGEX = r"^%YAML [0-9.]+\n-+\n"


class YAMLFormatter(FileFormatter):
    @staticmethod
    def description() -> str:
        return "YAML file formatter"

    def format_str(self, input_str: str) -> str:
        """Opinionated format YAML file."""
        obj = yaml.load(input_str)
        if self.args.add_test_metadata:
            self._add_test_metadata(obj)
        out_stream = StringIO()
        yaml.dump(
            obj,
            stream=out_stream,
        )
        # ruamel.yaml tends to add 2 empty lines at the bottom of the dump
        formatted = re.sub(r"\n+$", "\n", out_stream.getvalue())

        # ruamel adds yaml version at the beginning of the output file
        # and we don't really want those, so if no yaml version
        # is specified in the original file, remove it from the output file.
        if not re.match(YAML_VERSION_COMMENT_REGEX, input_str):
            return re.sub(YAML_VERSION_COMMENT_REGEX, "", formatted)

        return formatted

    @staticmethod
    def _add_test_metadata(obj: Dict[str, Any]) -> None:
        metadata = obj.get("Metadata", {})
        if not metadata:
            metadata = obj["Metadata"] = {}
        sam_transform_test_value = metadata.get("SamTransformTest")
        if sam_transform_test_value is not None and sam_transform_test_value is not True:
            raise ValueError(f"Unexpected Metadata.SamTransformTest value {sam_transform_test_value}")
        metadata["SamTransformTest"] = True

    @staticmethod
    def decode_exception() -> Type[Exception]:
        return YAMLError

    @staticmethod
    def file_extension() -> str:
        return ".yaml"

    @classmethod
    def config_additional_args(cls) -> None:
        cls.arg_parser.add_argument(
            "--add-test-metadata",
            action="store_true",
            help=dedent(
                """\
                Add the testing metadata to yaml file if it doesn't exist:
                "Metadata: SamTransformTest: true" """
            ),
        )


if __name__ == "__main__":
    YAMLFormatter.main()
