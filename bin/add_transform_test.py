#!/usr/bin/env python
"""Automatically create transform tests input and output files given an input template.

Usage:
    add_transform_test.py --template-file=sam-template.yaml [--disable-api-configuration]
    add_transform_test.py --template-file=sam-template.yaml

Options:
    --template-file=<i>             Location of SAM template to transform [default: template.yaml].
    --disable-api-configuration     Disable adding REGIONAL configuration to AWS::ApiGateway::RestApi
"""
import json
import subprocess
import os
import shutil
import sys
import tempfile
from docopt import docopt  # type: ignore
from pathlib import Path
from typing import Any, Dict

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
TRANSFORM_TEST_DIR = os.path.join(SCRIPT_DIR, "..", "tests", "translator")
CLI_OPTIONS = docopt(__doc__)


def read_json_file(file_path: str) -> Dict[str, Any]:
    template: Dict[str, Any] = json.loads(Path(file_path).read_text(encoding="utf-8"))
    return template


def write_json_file(obj: Dict[str, Any], file_path: str) -> None:
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


def add_regional_endpoint_configuration_if_needed(template: Dict[str, Any]) -> Dict[str, Any]:
    for _, resource in template["Resources"].items():
        if resource["Type"] == "AWS::ApiGateway::RestApi":
            properties = resource["Properties"]
            if "EndpointConfiguration" not in properties:
                properties["EndpointConfiguration"] = {"Types": ["REGIONAL"]}
            if "Parameters" not in properties:
                properties["Parameters"] = {"endpointConfigurationTypes": "REGIONAL"}

    return template


def generate_transform_test_output_files(input_file_path: str, file_basename: str) -> None:
    output_file_option = file_basename + ".json"

    # run sam-translate.py and get the temporary output file
    with tempfile.NamedTemporaryFile() as temp_output_file:
        subprocess.run(
            [
                sys.executable,
                os.path.join(SCRIPT_DIR, "sam-translate.py"),
                "--template-file",
                input_file_path,
                "--output-template",
                temp_output_file.name,
            ],
            check=True,
        )

        # copy the output files into correct directories
        transform_test_output_path = os.path.join(TRANSFORM_TEST_DIR, "output", output_file_option)
        shutil.copyfile(temp_output_file.name, transform_test_output_path)

        regional_transform_test_output_paths = [
            os.path.join(TRANSFORM_TEST_DIR, path, output_file_option)
            for path in [
                "output/aws-cn/",
                "output/aws-us-gov/",
            ]
        ]

        if not CLI_OPTIONS.get("--disable-api-configuration"):
            template = read_json_file(temp_output_file.name)
            template = add_regional_endpoint_configuration_if_needed(template)
            write_json_file(template, temp_output_file.name)

        for output_path in regional_transform_test_output_paths:
            shutil.copyfile(temp_output_file.name, output_path)
            print(f"Transform Test output files generated {output_path}")


def get_input_file_path() -> str:
    input_file_option = CLI_OPTIONS.get("--template-file")
    return os.path.join(os.getcwd(), input_file_option)


def copy_input_file_to_transform_test_dir(input_file_path: str, transform_test_input_path: str) -> None:
    shutil.copyfile(input_file_path, transform_test_input_path)
    print(f"Transform Test input file generated {transform_test_input_path}")


def verify_input_template(input_file_path: str):  # type: ignore[no-untyped-def]
    if "arn:aws:" in Path(input_file_path).read_text(encoding="utf-8"):
        print("ERROR: hardcoded partition name detected. Consider replace it with pseudo parameter {AWS::Partition}")
        sys.exit(1)


def main() -> None:
    input_file_path = get_input_file_path()
    file_basename = Path(input_file_path).stem

    verify_input_template(input_file_path)

    transform_test_input_path = os.path.join(TRANSFORM_TEST_DIR, "input", file_basename + ".yaml")
    copy_input_file_to_transform_test_dir(input_file_path, transform_test_input_path)

    generate_transform_test_output_files(transform_test_input_path, file_basename)

    print(
        "Generating transform test input and output files complete. \n\nPlease check the generated output is as expected. This tool does not guarantee correct output."
    )


if __name__ == "__main__":
    main()
