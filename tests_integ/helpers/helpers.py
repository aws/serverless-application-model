import json
import logging
import re
import random
import string  # not deprecated, a bug from pylint https://www.logilab.org/ticket/2481
from functools import reduce

import boto3
from botocore.exceptions import ClientError, NoRegionError

from samtranslator.model.exceptions import InvalidDocumentException
from samtranslator.translator.managed_policy_translator import ManagedPolicyLoader
from samtranslator.translator.transform import transform
from samtranslator.yaml_helper import yaml_parse

RANDOM_SUFFIX_LENGTH = 12


def transform_template(input_file_path, output_file_path):
    LOG = logging.getLogger(__name__)
    iam_client = boto3.client("iam")

    with open(input_file_path) as f:
        sam_template = yaml_parse(f)

    try:
        cloud_formation_template = transform(sam_template, {}, ManagedPolicyLoader(iam_client))
        cloud_formation_template_prettified = json.dumps(cloud_formation_template, indent=2)

        with open(output_file_path, "w") as f:
            f.write(cloud_formation_template_prettified)

        print("Wrote transformed CloudFormation template to: " + output_file_path)
    except InvalidDocumentException as e:
        error_message = reduce(lambda message, error: message + " " + error.message, e.causes, e.message)
        LOG.error(error_message)
        errors = map(lambda cause: cause.message, e.causes)
        LOG.error(errors)


def verify_stack_resources(expected_file_path, stack_resources):
    with open(expected_file_path) as expected_data:
        expected_resources = _sort_resources(json.load(expected_data))
    parsed_resources = _sort_resources(stack_resources["StackResourceSummaries"])

    if len(expected_resources) != len(parsed_resources):
        return False

    for i in range(len(expected_resources)):
        exp = expected_resources[i]
        parsed = parsed_resources[i]
        if not re.fullmatch(exp["LogicalResourceId"] + "([0-9a-f]{10})?", parsed["LogicalResourceId"]):
            return False
        if exp["ResourceType"] != parsed["ResourceType"]:
            return False
    return True


def generate_suffix():
    # Very basic random letters generator
    return "".join(random.choice(string.ascii_lowercase) for i in range(RANDOM_SUFFIX_LENGTH))


def _sort_resources(resources):
    return sorted(resources, key=lambda d: d["LogicalResourceId"])


def create_bucket(bucket_name, region=None):
    """Create an S3 bucket in a specified region

    copy code from boto3 doc example
    MG: removed the try so that the exception bubbles up and interrupts the test

    If a region is not specified, the bucket is created in the S3 default
    region (us-east-1).

    :param bucket_name: Bucket to create
    :param region: String region to create bucket in, e.g., 'us-west-2'
    :return: True if bucket created, else False
    """

    # Create bucket
    if region is None:
        raise NoRegionError()
    elif region == "us-east-1":
        s3_client = boto3.client("s3")
        s3_client.create_bucket(Bucket=bucket_name)
    else:
        s3_client = boto3.client("s3", region_name=region)
        location = {"LocationConstraint": region}
        s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=location)
