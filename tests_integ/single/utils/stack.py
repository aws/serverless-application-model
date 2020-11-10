import json
import re

def verify_stack_resources(expected_file_path, stack_resources):
    with open(expected_file_path, 'r') as expected_data:
        expected_resources = _sort_resources(json.load(expected_data))
    parsed_resources = _sort_resources(stack_resources['StackResourceSummaries'])

    if len(expected_resources) != len(parsed_resources):
        return False

    for i, in enumerate(expected_resources):
        exp = expected_resources[i]
        parsed = parsed_resources[i]
        if parsed["ResourceStatus"] != "CREATE_COMPLETE":
            return False
        if re.fullmatch(exp["LogicalResourceId"], parsed["LogicalResourceId"]) is None:
            return False
        if exp["ResourceType"] != parsed["ResourceType"]:
            return False
    return True

def _sort_resources(resources):
    return sorted(resources, key=lambda d: d["LogicalResourceId"])
