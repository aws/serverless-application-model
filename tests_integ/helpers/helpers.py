import json
import logging
import re
from functools import reduce

import boto3

from samtranslator.model.exceptions import InvalidDocumentException
from samtranslator.translator.managed_policy_translator import ManagedPolicyLoader
from samtranslator.translator.transform import transform
from samtranslator.yaml_helper import yaml_parse


def transform_template(input_file_path, output_file_path):
    LOG = logging.getLogger(__name__)
    iam_client = boto3.client("iam")

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


def verify_stack_resources(expected_file_path, stack_resources):
    with open(expected_file_path, 'r') as expected_data:
        expected_resources = _sort_resources(json.load(expected_data))
    parsed_resources = _sort_resources(stack_resources['StackResourceSummaries'])

    if len(expected_resources) != len(parsed_resources):
        return False

    for i in range(len(expected_resources)):
        exp = expected_resources[i]
        parsed = parsed_resources[i]
        if parsed["ResourceStatus"] != "CREATE_COMPLETE":
            return False
        if not re.fullmatch(exp["LogicalResourceId"]+"([0-9a-f]{10})?", parsed["LogicalResourceId"]):
            return False
        if exp["ResourceType"] != parsed["ResourceType"]:
            return False
    return True


def _sort_resources(resources):
    return sorted(resources, key=lambda d: d["LogicalResourceId"])
