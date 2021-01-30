import os.path
from parameterized import parameterized
import pytest
from unittest import TestCase
from samtranslator.yaml_helper import yaml_parse
from samtranslator.validator.validator import SamTemplateValidator
from tests.translator.validator.test_validator import TestValidatorBase

BASE_PATH = os.path.dirname(__file__)
INPUT_FOLDER = os.path.join(BASE_PATH, os.pardir, "input", "api")


class TestValidatorApi(TestValidatorBase):
    @parameterized.expand(
        [
            # AccessLogSetting
            (
                "error_accesslogsetting_destinationarn_not_string",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/AccessLogSetting/DestinationArn] 3 is not of type 'string'",
                ],
            ),
            (
                "error_accesslogsetting_empty",
                ["[/Resources/MyApi] Is not valid", "[/__/Properties/AccessLogSetting] Must not be empty"],
            ),
            (
                "error_accesslogsetting_format_not_string",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/AccessLogSetting/Format] 3 is not of type 'string'",
                ],
            ),
            (
                "error_accesslogsetting_unknown_property",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/AccessLogSetting] Additional properties are not allowed ('Unknown' was unexpected)",
                ],
            ),
            # Auth
            (
                "error_auth_adddefaultauthorizertocorspreflight_empty",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/Auth/AddDefaultAuthorizerToCorsPreflight] None is not of type 'boolean'",
                ],
            ),
            (
                "error_auth_adddefaultauthorizertocorspreflight_not_boolean",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/Auth/AddDefaultAuthorizerToCorsPreflight] 'true' is not of type 'boolean'",
                ],
            ),
            (
                "error_auth_apikeyrequired_empty",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/Auth/ApiKeyRequired] None is not of type 'boolean'",
                ],
            ),
            (
                "error_auth_apikeyrequired_not_boolean",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/Auth/ApiKeyRequired] 'true' is not of type 'boolean'",
                ],
            ),
            # Auth Authorizers
            (
                "error_auth_authorizers_empty",
                ["[/Resources/MyApi] Is not valid", "[/__/Properties/Auth/Authorizers] Must not be empty"],
            ),
            (
                "error_auth_authorizers_item_empty",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/Auth/Authorizers/MyCognitoAuth] Is not valid",
                    "[/__/__/] Must not be empty",
                    "[/__/__/] Must not be empty",
                    "[/__/__/] Must not be empty",
                ],
            ),
            (
                "error_auth_authorizers_not_object",
                ["[/Resources/MyApi] Is not valid", "[/__/Properties/Auth/Authorizers] 3 is not of type 'object'"],
            ),
            # Auth Cognito
            (
                "error_auth_cognito_authorizationscopes_not_list",
                ["[/Resources/MyApi] Is not valid", "[/__/] Is not valid", ""],
            ),
            (
                "error_auth_cognito_userpoolarn_missing",
                ["[/Resources/MyApi] Is not valid", "{'AuthorizationScopes': ['Scope1', 'Scope2']} is not valid", ""],
            ),
            (
                "error_auth_cognito_identity_empty",
                ["[/Resources/MyApi] Is not valid", "{'Identity': None} is not valid", ""],
            ),
            (
                "error_auth_cognito_identity_header_empty",
                ["[/Resources/MyApi] Is not valid", "{'Identity': {'Header': None}} is not valid", ""],
            ),
            (
                "error_auth_cognito_identity_header_not_string",
                ["[/Resources/MyApi] Is not valid", ""],
            ),
            (
                "error_auth_cognito_identity_reauthaurizeevery_empty",
                ["[/Resources/MyApi] Is not valid", ""],
            ),
            (
                "error_auth_cognito_identity_reauthaurizeevery_not_int",
                ["[/Resources/MyApi] Is not valid", "{'Identity': {'ReauthorizeEvery': '3'}} is not valid", ""],
            ),
            (
                "error_auth_cognito_identity_reauthaurizeevery_too_high",
                ["[/Resources/MyApi] Is not valid", "{'Identity': {'ReauthorizeEvery': 3601}} is not valid", ""],
            ),
            (
                "error_auth_cognito_identity_reauthaurizeevery_too_low",
                [
                    "[/Resources/MyApi] {'Type': 'AWS::Serverless::Api', 'Properties': {'StageName': 'Stage name', 'Auth': {'Authorizers': {'MyCognitoAuth': {'Identity': {'ReauthorizeEvery': 0}}}}}} is not valid. Context: {'Identity': {'ReauthorizeEvery': 0}} is not valid"
                ],
            ),
            (
                "error_auth_cognito_identity_validationexpression_empty",
                [
                    "[/Resources/MyApi] {'Type': 'AWS::Serverless::Api', 'Properties': {'StageName': 'Stage name', 'Auth': {'Authorizers': {'MyCognitoAuth': {'Identity': {'ValidationExpression': None}}}}}} is not valid. Context: {'Identity': {'ValidationExpression': None}} is not valid"
                ],
            ),
            (
                "error_auth_cognito_identity_validationexpression_not_string",
                [
                    "[/Resources/MyApi] {'Type': 'AWS::Serverless::Api', 'Properties': {'StageName': 'Stage name', 'Auth': {'Authorizers': {'MyCognitoAuth': {'Identity': {'ValidationExpression': 3}}}}}} is not valid. Context: {'Identity': {'ValidationExpression': 3}} is not valid"
                ],
            ),
            # Auth LambdaRequest
            (
                "error_auth_lambdarequest_functionpayloadtype_not_string",
                [
                    "[/Resources/MyApi] {'Type': 'AWS::Serverless::Api', 'Properties': {'StageName': 'Stage name', 'Auth': {'Authorizers': {'MyLambdaRequestAuth': {'FunctionArn': 'Function.arn', 'FunctionPayloadType': 3}}}}} is not valid. Context: {'FunctionArn': 'Function.arn', 'FunctionPayloadType': 3} is not valid"
                ],
            ),
            (
                "error_auth_lambdarequest_functionpayloadtype_unknown_value",
                [
                    "[/Resources/MyApi] Is not valid",
                    "  [/Properties/Auth/Authorizers/MyLambdaRequestAuth] Is not valid",
                    "    [/] Additional properties are not allowed ('FunctionArn', 'FunctionPayloadType' were unexpected)",
                    "    [/] 'UserPoolArn' is a required property",
                    "",
                ],
            ),
            # Auth empty
            (
                "error_auth_empty",
                ["[/Resources/MyApi] Is not valid", "[/__/Properties/Auth] Must not be empty"],
            ),
            # Api root element
            (
                "error_empty_properties",
                ["[/Resources/MyApi] Is not valid", "[/__/Properties] Must not be empty"],
            ),
            (
                "error_missing_properties_element",
                ["[/Resources/MyApi] Is not valid", "[/__/] 'Properties' is a required property"],
            ),
            (
                "error_missing_stagename",
                ["[/Resources/MyApi] Is not valid", "[/__/Properties] 'StageName' is a required property"],
            ),
            # Success
            ("success_auth_cognito_complete", []),
            ("success_auth_cognito_minimal", []),
            ("success_complete_api", []),
            ("success_minimum_api", []),
        ],
    )
    def test_validator_api(self, template, errors):
        self._test_validator(os.path.join(INPUT_FOLDER, template), errors)
