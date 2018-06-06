#!/usr/bin/env python2

"""Convert SAM templates to CloudFormation templates.
Known limitations: cannot transform CodeUri pointing at local directory.

Usage:
  sam-translate.py --input-file=sam-template.yaml [--output-file=<o>]

Options:
  --input-file=<i>     Location of SAM template to transform.
  --output-file=<o>    Location to store resulting CloudFormation template [default: cfn-template.json].

"""
import os
import sys
import json
import yaml
import boto3
from docopt import docopt
from samtranslator.public.translator import ManagedPolicyLoader
from samtranslator.translator.transform import transform
from samtranslator.yaml_helper import yaml_parse

cli_options = docopt(__doc__, sys.argv[1:])
iam_client = boto3.client('iam')

if __name__ == '__main__':
    cwd = os.getcwd()
    input_file_option = cli_options.get('--input-file')
    output_file_option = cli_options.get('--output-file')
    input_file_path = os.path.join(cwd, input_file_option)
    output_file_path = os.path.join(cwd, output_file_option)
    samTemplate = yaml_parse(open(input_file_path, 'r'))
    cloud_formation_template = transform(samTemplate, {}, ManagedPolicyLoader(iam_client))
    cloud_formation_template_prettified = json.dumps(cloud_formation_template, indent=2)
    print(cloud_formation_template_prettified)
    cloud_formation_template_file = open(output_file_path, 'w')
    cloud_formation_template_file.write(cloud_formation_template_prettified)
