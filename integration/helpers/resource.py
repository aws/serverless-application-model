import json
import re
import random
import string  # pylint: disable=deprecated-module

from integration.helpers.yaml_utils import load_yaml

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
        return "'{}' resources expected, '{}' found: \n{}".format(
            len(expected_resources), len(parsed_resources), json.dumps(parsed_resources, default=str)
        )

    for i in range(len(expected_resources)):
        exp = expected_resources[i]
        parsed = parsed_resources[i]
        if not re.match(
            "^" + exp["LogicalResourceId"] + "([0-9a-f]{" + str(LogicalIdGenerator.HASH_LENGTH) + "})?$",
            parsed["LogicalResourceId"],
        ):
            parsed_trimed_down = {
                "LogicalResourceId": parsed["LogicalResourceId"],
                "ResourceType": parsed["ResourceType"],
            }

            return "'{}' expected, '{}' found (Don't include the LogicalId random suffix)".format(
                exp, parsed_trimed_down
            )
        if exp["ResourceType"] != parsed["ResourceType"]:
            return "'{}' expected, '{}' found".format(exp["ResourceType"], parsed["ResourceType"])
    return None


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
    Filters and sorts a stack's resources by LogicalResourceId.
    Keeps only the LogicalResourceId and ResourceType properties

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

    filtered_resources = map(
        lambda x: {"LogicalResourceId": x["LogicalResourceId"], "ResourceType": x["ResourceType"]}, resources
    )

    return sorted(filtered_resources, key=lambda d: d["LogicalResourceId"])


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
    s3 = boto3.resource("s3")
    if region is None:
        raise NoRegionError()

    if region == "us-east-1":
        bucket = s3.create_bucket(Bucket=bucket_name)
    else:
        location = {"LocationConstraint": region}
        bucket = s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=location)

    bucket.wait_until_exists()


def _get_region():
    """Returns current region from boto3 session object"""
    session = boto3.session.Session()
    region = session.region_name
    return region


def read_test_config_file(filename):
    """Reads test config file and returns the contents"""
    tests_integ_dir = Path(__file__).resolve().parents[1]
    test_config_file_path = Path(tests_integ_dir, "config", filename)
    if not test_config_file_path.is_file():
        return {}
    test_config = load_yaml(str(test_config_file_path))
    return test_config


def write_test_config_file_to_json(filename, input):
    """Reads test config file and returns the contents"""
    tests_integ_dir = Path(__file__).resolve().parents[1]
    test_config_file_path = Path(tests_integ_dir, "config", filename)
    with open(test_config_file_path, "w") as f:
        json.dump(input, f)


def current_region_does_not_support(services):
    """
    Decide if a test should be skipped in the current testing region with the specific resources

    Parameters
    ----------
    services : List
        the services to be tested in the current testing region

    Returns
    -------
    Boolean
        If skip return true otherwise false
    """

    region = _get_region()
    region_exclude_services = read_test_config_file("region_service_exclusion.yaml")

    if region not in region_exclude_services.get("regions", {}):
        return False

    # check if any one of the services is in the excluded services for current testing region
    return bool(set(services).intersection(set(region_exclude_services["regions"][region])))


def current_region_not_included(services):
    """
    Opposite of current_region_does_not_support.
    Decides which tests should only be run in certain regions
    """
    region = _get_region()
    region_include_services = read_test_config_file("region_service_inclusion.yaml")

    if region not in region_include_services.get("regions", {}):
        return True

    # check if any one of the services is in the excluded services for current testing region
    return not bool(set(services).intersection(set(region_include_services["regions"][region])))


def first_item_in_dict(dictionary):
    """
    return the first key-value pair in dictionary

    Parameters
    ----------
    dictionary : Dictionary
        the dictionary used to grab the first tiem

    Returns
    -------
    Tuple
        the first key-value pair in the dictionary
    """
    if not dictionary:
        return None
    first_key = list(dictionary.keys())[0]
    return first_key, dictionary[first_key]
