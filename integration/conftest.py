import boto3
import botocore
import pytest
from botocore.exceptions import ClientError
import logging

from integration.helpers.base_test import S3_BUCKET_PREFIX
from integration.helpers.client_provider import ClientProvider
from integration.helpers.deployer.exceptions.exceptions import ThrottlingError
from integration.helpers.deployer.utils.retry import retry_with_exponential_backoff_and_jitter
from integration.helpers.stack import Stack

try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path

LOG = logging.getLogger(__name__)

COMPANION_STACK_NAME_ONCE = "sam-integ-stack-companion"
COMPANION_STACK_Template = "companion-stack.yaml"


def _get_all_buckets():
    s3 = boto3.resource("s3")
    return s3.buckets.all()


def _clean_bucket(s3_bucket_name, s3_client):
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
            _clean_bucket(bucket.name, s3_client)


@pytest.fixture()
def setup_companion_stack_once(tmpdir_factory, get_prefix):
    tests_integ_dir = Path(__file__).resolve().parents[1]
    template_foler = Path(tests_integ_dir, "integration", "setup")
    companion_stack_tempalte_path = Path(template_foler, COMPANION_STACK_Template)
    cfn_client = ClientProvider().cfn_client
    output_dir = tmpdir_factory.mktemp("data")
    stack_name = get_prefix + COMPANION_STACK_NAME_ONCE
    if _stack_exists(stack_name):
        return
    companion_stack = Stack(stack_name, companion_stack_tempalte_path, cfn_client, output_dir)
    companion_stack.create()


@pytest.fixture()
def delete_companion_stack_once(request, get_prefix):
    if request.config.getoption("--pipeline"):
        return
    ClientProvider().cfn_client.delete_stack(StackName=(get_prefix + COMPANION_STACK_NAME_ONCE))


@retry_with_exponential_backoff_and_jitter(ThrottlingError, 5, 360)
def get_stack_description(stack_name):
    try:
        stack_description = ClientProvider().cfn_client.describe_stacks(StackName=stack_name)
        return stack_description
    except botocore.exceptions.ClientError as ex:
        if "Throttling" in str(ex):
            raise ThrottlingError(stack_name=stack_name, msg=str(ex))
        raise


def get_stack_outputs(stack_description):
    if not stack_description:
        return {}
    output_list = stack_description["Stacks"][0]["Outputs"]
    return {output["OutputKey"]: output["OutputValue"] for output in output_list}


@pytest.fixture()
def get_companion_stack_outputs(get_prefix):
    companion_stack_description = get_stack_description(get_prefix + COMPANION_STACK_NAME_ONCE)
    return get_stack_outputs(companion_stack_description)


@pytest.fixture()
def get_prefix(request):
    prefix = ""
    if request.config.getoption("--pipeline"):
        prefix = request.config.getoption("--pipeline") + "-"
    return prefix


def pytest_addoption(parser):
    parser.addoption(
        "--pipeline",
        default=None,
        help="the name of the testing pipeline",
    )


def _stack_exists(stack_name):
    cloudformation = boto3.resource('cloudformation')
    stack = cloudformation.Stack(stack_name)
    try:
        stack.stack_status
    except ClientError as ex:
        if "does not exist" in str(ex):
            return False
        raise ex

    return True
