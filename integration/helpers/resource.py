import json
import re
import random
import string  # pylint: disable=deprecated-module

import yaml

try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path

import boto3
from botocore.exceptions import ClientError, NoRegionError

from samtranslator.translator.logical_id_generator import LogicalIdGenerator

# Length of the random suffix added at the end of the resources we create
# to avoid collisions between tests
RANDOM_SUFFIX_LENGTH = 12


def verify_stack_resources(expected_file_path, stack_resources):
    """
    Verifies that the stack resources match the expected ones

    Parameters
    ----------
    expected_file_path : Path
        Path to the file containing the expected resources
    stack_resources : List
        Stack resources

    Returns
    -------
    bool
        True if the stack resources exactly match the expected ones, False otherwise
    """
    with open(expected_file_path) as expected_data:
        expected_resources = _sort_resources(json.load(expected_data))
    parsed_resources = _sort_resources(stack_resources["StackResourceSummaries"])

    if len(expected_resources) != len(parsed_resources):
        return False

    for i in range(len(expected_resources)):
        exp = expected_resources[i]
        parsed = parsed_resources[i]
        if not re.match(
            "^" + exp["LogicalResourceId"] + "([0-9a-f]{" + str(LogicalIdGenerator.HASH_LENGTH) + "})?$",
            parsed["LogicalResourceId"],
        ):
            return False
        if exp["ResourceType"] != parsed["ResourceType"]:
            return False
    return True


def generate_suffix():
    """
    Generates a basic random string of length RANDOM_SUFFIX_LENGTH
    to append to objects names used in the tests to avoid collisions
    between tests runs

    Returns
    -------
    string
        Random lowercase alphanumeric string of length RANDOM_SUFFIX_LENGTH
    """
    return "".join(random.choice(string.ascii_lowercase) for i in range(RANDOM_SUFFIX_LENGTH))


def _sort_resources(resources):
    """
    Sorts a stack's resources by LogicalResourceId

    Parameters
    ----------
    resources : list
        Resources to sort

    Returns
    -------
    list
        List of resources, sorted
    """
    if resources is None:
        return []
    return sorted(resources, key=lambda d: d["LogicalResourceId"])


def create_bucket(bucket_name, region):
    """
    Creates a S3 bucket in a specific region

    Parameters
    ----------
    bucket_name : string
        Bucket name
    region : string
        Region name

    Raises
    ------
    NoRegionError
        If region is not specified
    """
    if region is None:
        raise NoRegionError()
    if region == "us-east-1":
        s3_client = boto3.client("s3")
        s3_client.create_bucket(Bucket=bucket_name)
    else:
        s3_client = boto3.client("s3", region_name=region)
        location = {"LocationConstraint": region}
        s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=location)


def load_yaml(file_path):
    """
    Loads a yaml file

    Parameters
    ----------
    file_path : Path
        File path

    Returns
    -------
    Object
        Yaml object
    """
    with open(file_path) as f:
        data = f.read()
    return yaml.load(data, Loader=yaml.FullLoader)


def should_exclude_test_in_region(exclude_resource):
    """
    Decide if a test should be skipped in the current testing region with the specific resource

    Parameters
    ----------
    exclude_resource : String
        the resource to be tested in the current testing region

    Returns
    -------
    Boolean
        If skip return true otherwise false
    """

    session = boto3.session.Session()
    my_region = session.region_name

    tests_integ_dir = Path(__file__).resolve().parents[1]
    config_dir = Path(tests_integ_dir, "config")
    region_exclude_resources_file = str(Path(config_dir, "region_exclude_resources.yml"))
    region_exclude_resources = load_yaml(region_exclude_resources_file)

    if my_region not in region_exclude_resources["regions"]:
        return False
    return exclude_resource in region_exclude_resources["regions"][my_region]["exclude_resources"]
