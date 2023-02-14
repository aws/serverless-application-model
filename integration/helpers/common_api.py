import json
import logging

from tenacity import (
    after_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_random,
)

LOG = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10) + wait_random(0, 1),
    retry=retry_if_exception_type(KeyError),
    after=after_log(LOG, logging.WARNING),
    reraise=True,
)
def get_queue_policy(queue_url, sqs_client):
    result = sqs_client.get_queue_attributes(QueueUrl=queue_url, AttributeNames=["Policy"])
    policy_document = result["Attributes"]["Policy"]
    policy = json.loads(policy_document)
    return policy["Statement"]


def get_function_versions(function_name, lambda_client):
    versions = lambda_client.list_versions_by_function(FunctionName=function_name)["Versions"]

    # Exclude $LATEST from the list and simply return all the version numbers.
    return [version["Version"] for version in versions if version["Version"] != "$LATEST"]


def get_policy_statements(role_name, policy_name, iam_client):
    role_policy_result = iam_client.get_role_policy(RoleName=role_name, PolicyName=policy_name)
    policy = role_policy_result["PolicyDocument"]
    return policy["Statement"]
