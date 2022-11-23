import json
import pytest
import os
import itertools

from pathlib import Path
from typing import Iterator
from unittest import TestCase
from cfn_flip import to_json  # type: ignore
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from parameterized import parameterized


SCHEMA = json.loads(Path("samtranslator/schema/schema.json").read_bytes())

# TODO: Enable (most likely) everything but 'error_*' and 'basic_schema_validation_failure'
SKIPPED_TESTS = [
    "error_",
    "unsupported_resources",
    "resource_with_invalid_type",
    "state_machine_with_null_events",
    "state_machine_with_cwe",  # Doesn't match schema at all...
    "function_with_null_events",
    "function_with_event_bridge_rule_state",  # Doesn't match schema at all...
    "sns_existing_sqs",  # 8 is not of type string
    "eventbridgerule_with_dlq",  # Doesn't match schema at all...
    "sns_outside_sqs",  # 8 is not of type string
    "function_with_cwe_dlq_and_retry_policy",  # Doesn't match schema at all...
    "function_with_cwe_dlq_generated",  # Doesn't match schema at all...
    "function_with_request_parameters",  # RequestParameters don't match documentation. Documentation and its example don't match either
    "api_with_request_parameters_openapi",  # RequestParameters don't match documentation. Documentation and its example don't match either
    "api_with_aws_iam_auth_overrides",  # null for invokeRole
    "eventbridgerule",  # missing required field 'Patterns'
    "self_managed_kafka_with_intrinsics",  # 'EnableValue' is of type bool but defined as string
    "api_with_resource_policy_global",  # 'ResourcePolicy CustomStatements' output expects a List
    "api_with_resource_policy",  # 'ResourcePolicy CustomStatements' output expects a List
    "api_with_if_conditional_with_resource_policy",  # 'ResourcePolicy CustomStatements' output expects a List
    "api_rest_paths_with_if_condition_swagger",  # 'EnableSimpleResponses' and 'AuthorizerPayloadFormatVersion' not defined in documentation
    "api_rest_paths_with_if_condition_openapi",  # 'EnableSimpleResponses' and 'AuthorizerPayloadFormatVersion' not defined in documentation
    "state_machine_with_api_authorizer_maximum",  # 'UserPoolArn' expects to be a string, but received list
    "api_with_auth_all_maximum",  # 'UserPoolArn' expects to be a string, but received list
    "api_with_auth_and_conditions_all_max",  # 'UserPoolArn' expects to be a string, but received list
    "api_with_auth_all_maximum_openapi_3",  # 'UserPoolArn' expects to be a string, but received list
    "api_with_authorizers_max_openapi",  # 'UserPoolArn' expects to be a string, but received list
    "api_with_authorizers_max",  # 'UserPoolArn' expects to be a string, but received list
    "api_with_any_method_in_swagger",  # Missing required field 'FunctionArn'
    "api_with_cors_and_only_headers",  # 'AllowOrigins' is required field
    "api_with_cors_and_only_methods",  # 'AllowOrigins' is required field
    "implicit_api_with_auth_and_conditions_max",  # 'UserPoolArn' expects to be a string, but received list
    "success_complete_api",  # 'DefinitionBody` expects JSON, but string inputted
]


def should_skip_test(s: str) -> bool:
    for test in SKIPPED_TESTS:
        if test in s:
            return True
    return False


def get_all_test_templates():
    return (
        list(Path("tests/translator/input").glob("**/*.yaml"))
        + list(Path("tests/translator/input").glob("**/*.yml"))
        + list(Path("tests/validator/input").glob("**/*.yaml"))
        + list(Path("tests/validator/input").glob("**/*.yml"))
        + list(Path("integration/resources/templates").glob("**/*.yaml"))
        + list(Path("integration/resources/templates").glob("**/*.yml"))
    )


SCHEMA_VALIDATION_TESTS = [str(f) for f in get_all_test_templates() if not should_skip_test(str(f))]


class TestValidateSchema(TestCase):
    @parameterized.expand(itertools.product(SCHEMA_VALIDATION_TESTS))
    def test_validate_schema(self, testcase):
        obj = json.loads(to_json(Path(testcase).read_bytes()))
        validate(obj, schema=SCHEMA)

    @parameterized.expand(
        [
            "tests/translator/input/error_schema_validation_wrong_property.yaml",
            "tests/translator/input/error_schema_validation_wrong_type.yaml",
        ]
    )
    def test_validate_schema_error(self, testcase):
        obj = json.loads(to_json(Path(testcase).read_bytes()))
        with pytest.raises(ValidationError):
            validate(obj, schema=SCHEMA)
