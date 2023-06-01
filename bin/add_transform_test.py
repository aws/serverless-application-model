#!/usr/bin/env python
"""Automatically create transform tests input and output files given an input template."""
import argparse
import json
import shutil
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import boto3

from samtranslator.translator.managed_policy_translator import ManagedPolicyLoader
from samtranslator.translator.transform import transform
from samtranslator.yaml_helper import yaml_parse

SCRIPT_DIR = Path(__file__).parent
TRANSFORM_TEST_DIR = SCRIPT_DIR.parent / "tests" / "translator"

iam_client = boto3.client("iam")

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--template-file",
    help="Location of SAM template to transform [default: template.yaml].",
    type=Path,
    default=Path("template.yaml"),
)
CLI_OPTIONS = parser.parse_args()


def read_json_file(file_path: Path) -> Dict[str, Any]:
    template: Dict[str, Any] = json.loads(file_path.read_text(encoding="utf-8"))
    return template


def write_json_file(obj: Dict[str, Any], file_path: Path) -> None:
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True)


def generate_transform_test_output_files(input_file_path: Path, file_basename: str) -> None:
    output_file_option = file_basename + ".json"

    with input_file_path.open(encoding="utf-8") as f:
        manifest = yaml_parse(f)  # type: ignore[no-untyped-call]

    transform_test_output_paths = {
        "aws": ("us-west-2", TRANSFORM_TEST_DIR / "output" / output_file_option),
        "aws-cn": ("cn-north-1 ", TRANSFORM_TEST_DIR / "output" / "aws-cn" / output_file_option),
        "aws-us-gov": ("us-gov-west-1", TRANSFORM_TEST_DIR / "output" / "aws-us-gov" / output_file_option),
    }

    for _, (region, output_path) in transform_test_output_paths.items():
        with patch("samtranslator.translator.arn_generator._get_region_from_session", return_value=region), patch(
            "boto3.session.Session.region_name", region
        ):
            # Implicit API Plugin may alter input template file, thus passing a copy here.
            output_fragment = transform(deepcopy(manifest), {}, ManagedPolicyLoader(iam_client))
            write_json_file(output_fragment, output_path)


def get_input_file_path() -> Path:
    input_file_option = str(CLI_OPTIONS.template_file)
    return Path.cwd() / input_file_option


def copy_input_file_to_transform_test_dir(input_file_path: Path, transform_test_input_path: Path) -> None:
    shutil.copyfile(input_file_path, transform_test_input_path)
    print(f"Transform Test input file generated {transform_test_input_path}")


def verify_input_template(input_file_path: Path) -> None:
    if "arn:aws:" in input_file_path.read_text(encoding="utf-8"):
        print(
            "WARNING: hardcoded partition name detected. Consider replace it with pseudo parameter {AWS::Partition}",
            file=sys.stderr,
        )


def format_test_files() -> None:
    subprocess.run(
        [sys.executable, SCRIPT_DIR / "json-format.py", "--write", "tests"],
        check=True,
    )

    subprocess.run(
        [sys.executable, SCRIPT_DIR / "yaml-format.py", "--write", "tests"],
        check=True,
    )


def main() -> None:
    input_file_path = get_input_file_path()
    file_basename = input_file_path.stem

    verify_input_template(input_file_path)

    transform_test_input_path = TRANSFORM_TEST_DIR / "input" / (file_basename + ".yaml")
    copy_input_file_to_transform_test_dir(input_file_path, transform_test_input_path)

    generate_transform_test_output_files(transform_test_input_path, file_basename)

    print(
        "Generating transform test input and output files complete. \n\nPlease check the generated output is as expected. This tool does not guarantee correct output."
    )

    format_test_files()


if __name__ == "__main__":
    main()
