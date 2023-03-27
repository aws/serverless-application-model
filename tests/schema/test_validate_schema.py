import itertools
import json
from pathlib import Path
from unittest import TestCase

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from jsonschema.validators import Draft4Validator
from parameterized import parameterized
from samtranslator.yaml_helper import yaml_parse

PROJECT_ROOT = Path(__file__).parent.parent.parent

SCHEMA = json.loads(PROJECT_ROOT.joinpath("schema_source/sam.schema.json").read_bytes())
UNIFIED_SCHEMA = json.loads(PROJECT_ROOT.joinpath("samtranslator/schema/schema.json").read_bytes())

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
    "documentdb_with_intrinsics",  # 'EnableValue' is of type bool but defined as string
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
    "function_with_event_source_mapping",  # Has empty DestinationConfig
    # Has partial Domain in Globals... but Domain model doesn't know about partial models
    # This is valid SAM, not entirely sure how to tell Pydantic "the type is Domain but all
    # fields are optional"
    # TODO: Support globals (e.g. somehow make all fields of a model optional only for Globals)
    "api_with_custom_base_path",
]


def should_skip_test(s: str) -> bool:
    return any(test in s for test in SKIPPED_TESTS)


def get_all_test_templates():
    return (
        list(Path(PROJECT_ROOT, "tests/translator/input").glob("**/*.yaml"))
        + list(Path(PROJECT_ROOT, "tests/translator/input").glob("**/*.yml"))
        + list(Path(PROJECT_ROOT, "tests/validator/input").glob("**/*.yaml"))
        + list(Path(PROJECT_ROOT, "tests/validator/input").glob("**/*.yml"))
        + list(Path(PROJECT_ROOT, "integration/resources/templates").glob("**/*.yaml"))
        + list(Path(PROJECT_ROOT, "integration/resources/templates").glob("**/*.yml"))
    )


SCHEMA_VALIDATION_TESTS = [str(f) for f in get_all_test_templates() if not should_skip_test(str(f))]


class TestValidateSchema(TestCase):
    @parameterized.expand(itertools.product(SCHEMA_VALIDATION_TESTS))
    def test_validate_schema(self, testcase):
        obj = yaml_parse(Path(testcase).read_bytes())
        validate(obj, schema=SCHEMA)

    @parameterized.expand(
        [
            (PROJECT_ROOT.joinpath("tests/translator/input/error_schema_validation_wrong_property.yaml"),),
            (PROJECT_ROOT.joinpath("tests/translator/input/error_schema_validation_wrong_type.yaml"),),
        ]
    )
    def test_validate_schema_error(self, testcase):
        obj = yaml_parse(Path(testcase).read_bytes())
        with pytest.raises(ValidationError):
            validate(obj, schema=SCHEMA)


class TestValidateUnifiedSchema(TestCase):
    """
    The unified schema includes SAM and CloudFormation schema. It's a lot larger, a lot
    slower to validate, and doesn't support intrinsic functions.
    """

    @parameterized.expand(
        [
            (PROJECT_ROOT.joinpath("tests/translator/input/schema_validation_4.yaml"),),
            (PROJECT_ROOT.joinpath("tests/translator/input/schema_validation_5.yaml"),),
        ]
    )
    def test_validate_unified_schema(self, testcase):
        obj = yaml_parse(Path(testcase).read_bytes())
        validate(obj, schema=UNIFIED_SCHEMA)

    @parameterized.expand(
        [
            (PROJECT_ROOT.joinpath("tests/translator/input/error_api_invalid_auth.yaml"),),
            (PROJECT_ROOT.joinpath("tests/translator/input/error_function_invalid_event_type.yaml"),),
            (PROJECT_ROOT.joinpath("tests/translator/input/schema_validation_ec2_not_valid.yaml"),),
        ]
    )
    def test_validate_unified_schema_error(self, testcase):
        obj = yaml_parse(Path(testcase).read_bytes())
        with pytest.raises(ValidationError):
            validate(obj, schema=UNIFIED_SCHEMA)

    def test_structure(self):
        assert UNIFIED_SCHEMA["$schema"] == "http://json-schema.org/draft-04/schema#"
        assert {
            "AWSTemplateFormatVersion",
            "Conditions",
            "Description",
            "Globals",
            "Mappings",
            "Metadata",
            "Outputs",
            "Parameters",
            "Resources",
            "Transform",
        } == set(UNIFIED_SCHEMA["properties"].keys())
        assert len(UNIFIED_SCHEMA["properties"]["Resources"]["additionalProperties"]["anyOf"]) > 1000
        assert (
            "The set of properties must conform to the defined `Type`"
            in UNIFIED_SCHEMA["definitions"][
                "samtranslator__internal__schema_source__aws_serverless_statemachine__ApiEvent"
            ]["properties"]["Properties"]["markdownDescription"]
        )

        # Contains all definitions from SAM-only schema (except rule that ignores non-SAM)
        # Pass-through properties are replaced in the SAM schema, so can't do a deep check
        sam_defs = {
            k
            for k in SCHEMA["definitions"]
            if k != "samtranslator__internal__schema_source__any_cfn_resource__Resource"
        }
        unified_defs = set(UNIFIED_SCHEMA["definitions"])
        assert sam_defs < unified_defs

        # Contains all resources from SAM-only schema (except rule that ignores non-SAM)
        unified_resources = UNIFIED_SCHEMA["properties"]["Resources"]["additionalProperties"]["anyOf"]
        for v in SCHEMA["properties"]["Resources"]["additionalProperties"]["anyOf"]:
            if v["$ref"] != "#/definitions/samtranslator__internal__schema_source__any_cfn_resource__Resource":
                assert v in unified_resources

    @parameterized.expand(
        [
            [
                # Valid (SAM)
                {
                    "Transform": "AWS::Serverless-2016-10-31",
                    "Resources": {
                        "Foo": {
                            "Type": "AWS::Serverless::SimpleTable",
                        },
                    },
                }
            ],
            [
                # Valid (CFN)
                {
                    "Resources": {
                        "Foo": {
                            "Type": "AWS::S3::Bucket",
                        },
                    },
                },
            ],
        ],
    )
    def test_sanity_valid(self, template):
        Draft4Validator(UNIFIED_SCHEMA).validate(template)
        validate(template, schema=UNIFIED_SCHEMA)

    @parameterized.expand(
        [
            [
                # Unknown property (SAM)
                {
                    "Transform": "AWS::Serverless-2016-10-31",
                    "Resources": {
                        "Foo": {
                            "Type": "AWS::Serverless::SimpleTable",
                            "Properties": {
                                "UnknownProperty": True,
                            },
                        },
                    },
                },
            ],
            [
                # Missing property (SAM)
                {
                    "Transform": "AWS::Serverless-2016-10-31",
                    "Resources": {
                        "Foo": {
                            "Type": "AWS::Serverless::SimpleTable",
                            "Properties": {
                                "PrimaryKey": {
                                    "Name": "Foo",
                                },
                            },
                        },
                    },
                },
            ],
            [
                # Wrong value type (SAM)
                {
                    "Transform": "AWS::Serverless-2016-10-31",
                    "Resources": {
                        "Foo": {
                            "Type": "AWS::Serverless::Function",
                            "Properties": {
                                "InlineCode": "foo",
                                "Handler": "bar",
                                "Runtime": "node16.x",
                                "Events": 1337,
                            },
                        },
                    },
                },
            ],
            [
                # Unknown property (CFN)
                {
                    "Resources": {
                        "Foo": {
                            "Type": "AWS::S3::Bucket",
                            "Properties": {
                                "UnknownProperty": True,
                            },
                        },
                    },
                },
            ],
            [
                # Missing property (CFN)
                {
                    "Resources": {
                        "Foo": {
                            "Type": "AWS::ResourceGroups::Group",
                        }
                    }
                }
            ],
            [
                # Wrong value type (CFN)
                {
                    "Resources": {
                        "Foo": {
                            "Type": "AWS::ResourceGroups::Group",
                            "Properties": {
                                "Name": 1337,
                            },
                        }
                    }
                }
            ],
        ],
    )
    def test_sanity_invalid(self, template):
        with pytest.raises(ValidationError):
            validate(template, schema=UNIFIED_SCHEMA)
