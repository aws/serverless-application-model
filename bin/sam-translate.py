#!/usr/bin/env python2

"""Convert SAM templates to CloudFormation templates.

Known limitations: cannot transform CodeUri pointing at local directory.

Usage:
  sam-translate.py --input-file=sam-template.yaml [--output-file=<o>]

Options:
  --input-file=<i>     Location of SAM template to transform.
  --output-file=<o>    Location to store resulting CloudFormation template [default: cfn-template.json].

"""
import json
import os

import boto3
from docopt import docopt

from samtranslator.public.translator import ManagedPolicyLoader
from samtranslator.translator.transform import transform
from samtranslator.yaml_helper import yaml_parse
from samtranslator.model.exceptions import InvalidDocumentException


cli_options = docopt(__doc__)
iam_client = boto3.client('iam')
cwd = os.getcwd()


def get_input_output_file_paths():
    input_file_option = cli_options.get('--input-file')
    output_file_option = cli_options.get('--output-file')
    input_file_path = os.path.join(cwd, input_file_option)
    output_file_path = os.path.join(cwd, output_file_option)

    return input_file_path, output_file_path


def main():
    input_file_path, output_file_path = get_input_output_file_paths()

    with open(input_file_path, 'r') as f:
        sam_template = yaml_parse(f)

    try:
        cloud_formation_template = transform(
            sam_template, {}, ManagedPolicyLoader(iam_client))
        cloud_formation_template_prettified = json.dumps(
            cloud_formation_template, indent=2)

        with open(output_file_path, 'w') as f:
            f.write(cloud_formation_template_prettified)

        print('Wrote transformed CloudFormation template to: ' + output_file_path)
    except InvalidDocumentException as e:
        errorMessage = reduce(lambda message, error: message + ' ' + error.message, e.causes, e.message)
        print(errorMessage)
        errors = map(lambda cause: cause.message, e.causes)
        print(errors)


if __name__ == '__main__':
    main()
