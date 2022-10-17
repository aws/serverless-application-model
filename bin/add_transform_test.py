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
import re
import os
import shutil
import yaml
import tempfile
from docopt import docopt
from pathlib import Path
from typing import Any

from samtranslator.yaml_helper import yaml_parse

cwd = os.getcwd()
CLI_OPTIONS = docopt(__doc__)


def get_input_file_path() -> str:
    input_file_option = CLI_OPTIONS.get("--template-file")
    return os.path.join(cwd, input_file_option)


def copy_input_file_to_transform_test_dir(input_file_path: str, transform_test_input_path: str) -> None:
    shutil.copyfile(input_file_path, transform_test_input_path)

    replace_arn_partitions(transform_test_input_path)
    print(f"Transform Test input file generated {transform_test_input_path}")


def add_regional_endpoint_configuration_if_needed(temp_output_file_path: str) -> None:
    with open(temp_output_file_path, "r") as f:
        sam_template = json.load(f)

    for logical_id, resource in sam_template["Resources"].items():
        if resource["Type"] == "AWS::ApiGateway::RestApi":
            if "EndpointConfiguration" not in resource["Properties"]:
                sam_template["Resources"][logical_id]["Properties"]["EndpointConfiguration"] = {"Types": ["REGIONAL"]}
            if "Parameters" not in resource["Properties"]:
                sam_template["Resources"][logical_id]["Properties"]["Parameters"] = {
                    "endpointConfigurationTypes": "REGIONAL"
                }

    with open(temp_output_file_path, "w") as f:
        json.dump(sam_template, f, indent=2)


def generate_transform_test_output_files(input_file_path: str, file_basename: str) -> None:
    output_file_option = file_basename + ".json"

    # run sam-translate.py and get the temporary output file
    with tempfile.NamedTemporaryFile() as temp_output_file:
        subprocess.run(
            [
                "python",
                os.path.dirname(os.path.realpath(__file__)) + "/sam-translate.py",
                "--template-file",
                input_file_path,
                "--output-template",
                temp_output_file.name,
            ],
            check=True,
        )

        # copy the output files into correct directories
        transform_test_output_path = cwd + "/tests/translator/output/" + output_file_option
        shutil.copyfile(temp_output_file.name, transform_test_output_path)

        regional_transform_test_output_paths = [
            cwd + path + output_file_option
            for path in [
                "/tests/translator/output/aws-cn/",
                "/tests/translator/output/aws-us-gov/",
            ]
        ]

        if not CLI_OPTIONS.get("--disable-api-configuration"):
            add_regional_endpoint_configuration_if_needed(temp_output_file.name)

        for output_path in regional_transform_test_output_paths:
            shutil.copyfile(temp_output_file.name, output_path)
            print(f"Transform Test output files generated {output_path}")


def map_nested(obj: Any, fn) -> Any:
    if isinstance(obj, dict):
        return {k: map_nested(v, fn) for k, v in obj.items()}
    if isinstance(obj, list):
        return [map_nested(v, fn) for v in obj]
    return fn(obj)


def replace_arn(s: Any) -> Any:
    if not isinstance(s, str):
        return s

    pattern = "arn:aws:"
    replaced_pattern = "arn:${AWS::Partition}"
    if pattern in s:
        # pattern is substring of s, use Fn::Sub to replace part of s
        s = s.replace(pattern, replaced_pattern)
    if re.search(r"\${.+}", s):
        return {"Fn::Sub": s}
    return s


def replace_arn_partitions(input_file_path: str) -> None:
    with open(input_file_path, "r") as f:
        sam_template = yaml_parse(f)

    replaced_template = map_nested(sam_template, lambda v: replace_arn(v))

    with open(input_file_path, "w") as f:
        yaml.dump(replaced_template, f, default_flow_style=False)


def main() -> None:
    input_file_path = get_input_file_path()
    file_basename = Path(input_file_path).stem

    transform_test_input_path = cwd + "/tests/translator/input/" + file_basename + ".yaml"
    copy_input_file_to_transform_test_dir(input_file_path, transform_test_input_path)

    generate_transform_test_output_files(transform_test_input_path, file_basename)


if __name__ == "__main__":
    main()
