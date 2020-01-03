#!/usr/bin/env python2

"""Convert SAM templates to CloudFormation templates.

Known limitations: cannot transform CodeUri pointing at local directory.

Usage:
  sam-translate.py --template-file=sam-template.yaml [--verbose] [--output-template=<o>]
  sam-translate.py package --template-file=sam-template.yaml --s3-bucket=my-bucket [--verbose] [--output-template=<o>]
  sam-translate.py deploy --template-file=sam-template.yaml --s3-bucket=my-bucket --capabilities=CAPABILITY_NAMED_IAM --stack-name=my-stack [--verbose] [--output-template=<o>]

Options:
  --template-file=<i>       Location of SAM template to transform [default: template.yaml].
  --output-template=<o>     Location to store resulting CloudFormation template [default: transformed-template.json].
  --s3-bucket=<s>           S3 bucket to use for SAM artifacts when using the `package` command
  --capabilities=<c>        Capabilities
  --stack-name=<n>          Unique name for your CloudFormation Stack
  --verbose                 Enables verbose logging

"""
import json
import logging
import os
import platform
import subprocess
import sys

import boto3
from docopt import docopt

my_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, my_path + "/..")

from samtranslator.public.translator import ManagedPolicyLoader
from samtranslator.translator.transform import transform
from samtranslator.yaml_helper import yaml_parse
from samtranslator.model.exceptions import InvalidDocumentException

LOG = logging.getLogger(__name__)
cli_options = docopt(__doc__)
iam_client = boto3.client("iam")
cwd = os.getcwd()

if cli_options.get("--verbose"):
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig()


def execute_command(command, args):
    try:
        aws_cmd = "aws" if platform.system().lower() != "windows" else "aws.cmd"
        command_with_args = [aws_cmd, "cloudformation", command] + list(args)

        LOG.debug("Executing command: %s", command_with_args)

        subprocess.check_call(command_with_args)

        LOG.debug("Command successful")
    except subprocess.CalledProcessError as e:
        # Underlying aws command will print the exception to the user
        LOG.debug("Exception: %s", e)
        sys.exit(e.returncode)


def get_input_output_file_paths():
    input_file_option = cli_options.get("--template-file")
    output_file_option = cli_options.get("--output-template")
    input_file_path = os.path.join(cwd, input_file_option)
    output_file_path = os.path.join(cwd, output_file_option)

    return input_file_path, output_file_path


def package(input_file_path, output_file_path):
    template_file = input_file_path
    package_output_template_file = input_file_path + "._sam_packaged_.yaml"
    s3_bucket = cli_options.get("--s3-bucket")
    args = [
        "--template-file",
        template_file,
        "--output-template-file",
        package_output_template_file,
        "--s3-bucket",
        s3_bucket,
    ]

    execute_command("package", args)

    return package_output_template_file


def transform_template(input_file_path, output_file_path):
    with open(input_file_path, "r") as f:
        sam_template = yaml_parse(f)

    try:
        cloud_formation_template = transform(sam_template, {}, ManagedPolicyLoader(iam_client))
        cloud_formation_template_prettified = json.dumps(cloud_formation_template, indent=2)

        with open(output_file_path, "w") as f:
            f.write(cloud_formation_template_prettified)

        print("Wrote transformed CloudFormation template to: " + output_file_path)
    except InvalidDocumentException as e:
        errorMessage = reduce(lambda message, error: message + " " + error.message, e.causes, e.message)
        LOG.error(errorMessage)
        errors = map(lambda cause: cause.message, e.causes)
        LOG.error(errors)


def deploy(template_file):
    capabilities = cli_options.get("--capabilities")
    stack_name = cli_options.get("--stack-name")
    args = ["--template-file", template_file, "--capabilities", capabilities, "--stack-name", stack_name]

    execute_command("deploy", args)

    return package_output_template_file


if __name__ == "__main__":
    input_file_path, output_file_path = get_input_output_file_paths()

    if cli_options.get("package"):
        package_output_template_file = package(input_file_path, output_file_path)
        transform_template(package_output_template_file, output_file_path)
    elif cli_options.get("deploy"):
        package_output_template_file = package(input_file_path, output_file_path)
        transform_template(package_output_template_file, output_file_path)
        deploy(output_file_path)
    else:
        transform_template(input_file_path, output_file_path)
