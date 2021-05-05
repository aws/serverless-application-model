import json


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
