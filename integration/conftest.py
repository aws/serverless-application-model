import logging
from pathlib import Path

import boto3
import botocore
import pytest
from botocore.exceptions import ClientError

from integration.helpers.base_test import S3_BUCKET_PREFIX
from integration.helpers.client_provider import ClientProvider
from integration.helpers.deployer.exceptions.exceptions import S3DoesNotExistException, ThrottlingError
from integration.helpers.deployer.utils.retry import retry_with_exponential_backoff_and_jitter
from integration.helpers.resource import (
    current_region_does_not_support,
    read_test_config_file,
    write_test_config_file_to_json,
)
from integration.helpers.stack import Stack
from integration.helpers.yaml_utils import load_yaml

LOG = logging.getLogger(__name__)

COMPANION_STACK_NAME = "sam-integ-stack-companion"
COMPANION_STACK_TEMPLATE = "companion-stack.yaml"
SAR_APP_TEMPLATE = "example-sar-app.yaml"
SAR_APP_NAME = "sam-integration-test-sar-app"
SAR_APP_VERSION = "1.0.3"


def _get_all_buckets():
    s3 = boto3.resource("s3")
    return s3.buckets.all()


def clean_bucket(s3_bucket_name, s3_client):
    """
    Empties and deletes the bucket used for the tests
    """
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(s3_bucket_name)
    object_summary_iterator = bucket.objects.all()

    for object_summary in object_summary_iterator:
        try:
            s3_client.delete_object(Key=object_summary.key, Bucket=s3_bucket_name)
        except ClientError as e:
            LOG.error("Unable to delete object %s from bucket %s", object_summary.key, s3_bucket_name, exc_info=e)
    try:
        s3_client.delete_bucket(Bucket=s3_bucket_name)
    except ClientError as e:
        LOG.error("Unable to delete bucket %s", s3_bucket_name, exc_info=e)


@pytest.fixture(scope="session")
def clean_all_integ_buckets():
    buckets = _get_all_buckets()
    s3_client = ClientProvider().s3_client
    for bucket in buckets:
        if bucket.name.startswith(S3_BUCKET_PREFIX):
            clean_bucket(bucket.name, s3_client)


@pytest.fixture()
def setup_companion_stack_once(tmpdir_factory, get_prefix):
    tests_integ_dir = Path(__file__).resolve().parents[1]
    template_foler = Path(tests_integ_dir, "integration", "setup")
    companion_stack_tempalte_path = Path(template_foler, COMPANION_STACK_TEMPLATE)
    cfn_client = ClientProvider().cfn_client
    output_dir = tmpdir_factory.mktemp("data")
    stack_name = get_prefix + COMPANION_STACK_NAME
    companion_stack = Stack(stack_name, companion_stack_tempalte_path, cfn_client, output_dir)
    companion_stack.create_or_update(_stack_exists(stack_name))


@pytest.fixture()
def get_serverless_application_repository_app():
    """Create or re-use a simple SAR app"""
    if current_region_does_not_support(["ServerlessRepo"]):
        LOG.info("Creating SAR application is skipped since SAR tests are not supported in this region.")
        return None

    sar_client = ClientProvider().sar_client
    sar_apps = sar_client.list_applications().get("Applications", [])
    for sar_app in sar_apps:
        if sar_app.get("Name") == SAR_APP_NAME:
            LOG.info("SAR Application was already created, skipping SAR application publish")
            return sar_app.get("ApplicationId")

    LOG.info("SAR application not found, publishing new one...")

    tests_integ_dir = Path(__file__).resolve().parents[1]
    template_foler = Path(tests_integ_dir, "integration", "setup")
    sar_app_template_path = Path(template_foler, SAR_APP_TEMPLATE)
    with open(sar_app_template_path) as f:
        sar_template_contents = f.read()
    create_app_result = sar_client.create_application(
        Author="SAM Team",
        Description="SAR Application for Integration Tests",
        Name=SAR_APP_NAME,
        SemanticVersion=SAR_APP_VERSION,
        TemplateBody=sar_template_contents,
    )
    LOG.info("SAR application creation result: %s", create_app_result)
    return create_app_result.get("ApplicationId")


@pytest.fixture()
def upload_resources(get_s3):
    """
    Creates the bucket and uploads the files used by the tests to it
    """
    s3_bucket = get_s3
    if not _s3_exists(s3_bucket):
        raise S3DoesNotExistException(get_s3, "Check companion stack status")
    code_dir = Path(__file__).resolve().parents[0].joinpath("resources").joinpath("code")
    file_to_s3_uri_map = read_test_config_file("file_to_s3_map.json")

    if not file_to_s3_uri_map or not file_to_s3_uri_map.items():
        LOG.debug("No resources to upload")
        return

    current_file_name = ""

    try:
        s3_client = ClientProvider().s3_client
        session = boto3.session.Session()
        region = session.region_name
        for file_name, file_info in file_to_s3_uri_map.items():
            current_file_name = file_name
            code_path = str(Path(code_dir, file_name))
            LOG.debug("Uploading file %s to bucket %s", file_name, s3_bucket)
            s3_client.upload_file(code_path, s3_bucket, file_name)
            LOG.debug("File %s uploaded successfully to bucket %s", file_name, s3_bucket)
            file_info["uri"] = get_s3_uri(file_name, file_info["type"], s3_bucket, region)
    except ClientError as error:
        LOG.error("Upload of file %s to bucket %s failed", current_file_name, s3_bucket, exc_info=error)
        raise error

    write_test_config_file_to_json("file_to_s3_map_modified.json", file_to_s3_uri_map)


def get_s3_uri(file_name, uri_type, bucket, region):
    if uri_type == "s3":
        return f"s3://{bucket}/{file_name}"

    if region == "us-east-1":
        return f"https://s3.amazonaws.com/{bucket}/{file_name}"
    if region == "us-iso-east-1":
        return f"https://s3.us-iso-east-1.c2s.ic.gov/{bucket}/{file_name}"
    if region == "us-isob-east-1":
        return f"https://s3.us-isob-east-1.sc2s.sgov.gov/{bucket}/{file_name}"

    return f"https://s3-{region}.amazonaws.com/{bucket}/{file_name}"


@pytest.fixture()
def delete_companion_stack_once(get_prefix):
    if not get_prefix:
        ClientProvider().cfn_client.delete_stack(StackName=COMPANION_STACK_NAME)


@retry_with_exponential_backoff_and_jitter(ThrottlingError, 5, 360)
def get_stack_description(stack_name):
    try:
        stack_description = ClientProvider().cfn_client.describe_stacks(StackName=stack_name)
        return stack_description
    except botocore.exceptions.ClientError as ex:
        if "Throttling" in str(ex):
            raise ThrottlingError(stack_name=stack_name, msg=str(ex))
        raise ex


def get_stack_outputs(stack_description):
    if not stack_description:
        return {}
    output_list = stack_description["Stacks"][0]["Outputs"]
    return {output["OutputKey"]: output["OutputValue"] for output in output_list}


@pytest.fixture()
def get_companion_stack_outputs(get_prefix):
    companion_stack_description = get_stack_description(get_prefix + COMPANION_STACK_NAME)
    return get_stack_outputs(companion_stack_description)


@pytest.fixture()
def get_s3(get_companion_stack_outputs):
    s3_bucket = get_companion_stack_outputs.get("PreCreatedS3Bucket")
    return str(s3_bucket)


@pytest.fixture()
def get_prefix(request):
    prefix = ""
    if request.config.getoption("--prefix"):
        prefix = request.config.getoption("--prefix") + "-"
    return prefix


@pytest.fixture()
def get_stage(request):
    stage = ""
    if request.config.getoption("--stage"):
        stage = request.config.getoption("--stage")
    return stage


@pytest.fixture()
def check_internal(request):
    internal = False
    if request.config.getoption("--internal"):
        internal = True
    return internal


@pytest.fixture()
def parameter_values(request):
    parameter_values = {}
    parameter_values_option = request.config.getoption("--parameter-values")
    if parameter_values_option:
        parameter_values = load_yaml(parameter_values_option)
    return parameter_values


def pytest_addoption(parser):
    parser.addoption(
        "--prefix",
        default=None,
        action="store",
        help="the prefix of the stack",
    )
    parser.addoption(
        "--stage",
        default=None,
        action="store",
        help="the stage of the stack",
    )
    parser.addoption(
        "--internal",
        action="store_true",
        help="run internal tests",
    )
    parser.addoption(
        "--parameter-values",
        default=None,
        help="YAML file path which will contain parameter values that could be passed during deployment of the stack",
    )


@retry_with_exponential_backoff_and_jitter(ThrottlingError, 5, 360)
def _stack_exists(stack_name):
    cloudformation = boto3.resource("cloudformation")
    stack = cloudformation.Stack(stack_name)
    try:
        status = stack.stack_status
        if status == "REVIEW_IN_PROGRESS":
            return False
    except ClientError as ex:
        if "does not exist" in str(ex):
            return False
        if "Throttling" in str(ex):
            raise ThrottlingError(stack_name=stack_name, msg=str(ex))
        raise ex

    return True


@retry_with_exponential_backoff_and_jitter(ThrottlingError, 5, 360)
def _s3_exists(s3_bucket):
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(s3_bucket)
    try:
        s3.meta.client.head_bucket(Bucket=bucket.name)
    except ClientError:
        return False

    return True
