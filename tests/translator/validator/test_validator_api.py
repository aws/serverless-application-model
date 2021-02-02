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
            # Api root element
            (
                "error_properties_empty",
                ["[/Resources/MyApi] Is not valid", "[/__/Properties] Must not be empty"],
            ),
            (
                "error_properties_missing",
                ["[/Resources/MyApi] Is not valid", "[/__/] 'Properties' is a required property"],
            ),
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
                    "[/__/Properties/Auth/AddDefaultAuthorizerToCorsPreflight] Must not be empty",
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
                    "[/__/Properties/Auth/ApiKeyRequired] Must not be empty",
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
                    "[/__/Properties/Auth/Authorizers/MyCognitoAuth] Must not be empty",
                ],
            ),
            (
                "error_auth_authorizers_not_object",
                ["[/Resources/MyApi] Is not valid", "[/__/Properties/Auth/Authorizers] 3 is not of type 'object'"],
            ),
            # Auth Cognito
            (
                "error_auth_cognito_authorizationscopes_empty",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/Auth/Authorizers/MyCognitoAuth/AuthorizationScopes] Must not be empty",
                ],
            ),
            (
                "error_auth_cognito_authorizationscopes_item_not_string",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/Auth/Authorizers/MyCognitoAuth/AuthorizationScopes/0] 3 is not of type 'string'",
                ],
            ),
            (
                "error_auth_cognito_authorizationscopes_not_list",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/Auth/Authorizers/MyCognitoAuth/AuthorizationScopes] 'scopes1' is not of type 'array'",
                ],
            ),
            (
                "error_auth_cognito_identity_empty",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/Auth/Authorizers/MyCognitoAuth/Identity] Must not be empty",
                ],
            ),
            (
                "error_auth_cognito_identity_header_empty",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/Auth/Authorizers/MyCognitoAuth/Identity/Header] Must not be empty",
                ],
            ),
            (
                "error_auth_cognito_identity_header_not_string",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/Auth/Authorizers/MyCognitoAuth/Identity/Header] 3 is not of type 'string'",
                ],
            ),
            (
                "error_auth_cognito_identity_reauthaurizeevery_empty",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/Auth/Authorizers/MyCognitoAuth/Identity/ReauthorizeEvery] Must not be empty",
                ],
            ),
            (
                "error_auth_cognito_identity_reauthaurizeevery_not_int",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/Auth/Authorizers/MyCognitoAuth/Identity/ReauthorizeEvery] '3' is not of type 'integer'",
                ],
            ),
            (
                "error_auth_cognito_identity_reauthaurizeevery_too_high",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/Auth/Authorizers/MyCognitoAuth/Identity/ReauthorizeEvery] 3601 is greater than the maximum of 3600",
                ],
            ),
            (
                "error_auth_cognito_identity_reauthaurizeevery_too_low",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/Auth/Authorizers/MyCognitoAuth/Identity/ReauthorizeEvery] 0 is less than the minimum of 1",
                ],
            ),
            (
                "error_auth_cognito_identity_validationexpression_empty",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/Auth/Authorizers/MyCognitoAuth/Identity/ValidationExpression] Must not be empty",
                ],
            ),
            (
                "error_auth_cognito_identity_validationexpression_not_string",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/Auth/Authorizers/MyCognitoAuth/Identity/ValidationExpression] 3 is not of type 'string'",
                ],
            ),
            (
                "error_auth_cognito_userpoolarn_empty",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/Auth/Authorizers/MyCognitoAuth/UserPoolArn] Must not be empty",
                ],
            ),
            (
                "error_auth_cognito_userpoolarn_missing",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/Auth/Authorizers/MyCognitoAuth] 'UserPoolArn' is a required property",
                    "[/__/Properties/Auth/Authorizers/MyCognitoAuth] 'FunctionArn' is a required property",
                ],
            ),
            (
                "error_auth_cognito_userpoolarn_not_string",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/Auth/Authorizers/MyCognitoAuth/UserPoolArn] 3 is not of type 'string'",
                ],
            ),
            # Auth Lambda (common)
            (
                "error_auth_lambda_authorizationscopes_empty",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/Auth/Authorizers/MyLambdaAuth/AuthorizationScopes] Must not be empty",
                ],
            ),
            (
                "error_auth_lambda_authorizationscopes_item_not_string",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/Auth/Authorizers/MyLambdaAuth/AuthorizationScopes/0] 3 is not of type 'string'",
                ],
            ),
            (
                "error_auth_lambda_authorizationscopes_not_list",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/Auth/Authorizers/MyLambdaAuth/AuthorizationScopes] 'scopes1' is not of type 'array'",
                ],
            ),
            (
                "error_auth_lambda_functionarn_empty",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/Auth/Authorizers/MyLambdaAuth/FunctionArn] Must not be empty",
                ],
            ),
            (
                "error_auth_lambda_functionarn_missing",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/Auth/Authorizers/MyLambdaAuth] 'UserPoolArn' is a required property",
                    "[/__/Properties/Auth/Authorizers/MyLambdaAuth] 'FunctionArn' is a required property",
                ],
            ),
            (
                "error_auth_lambda_functionarn_not_string",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/Auth/Authorizers/MyLambdaAuth/FunctionArn] 3 is not of type 'string'",
                ],
            ),
            (
                "error_auth_lambda_functioninvokerole_empty",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/Auth/Authorizers/MyLambdaAuth/FunctionInvokeRole] Must not be empty",
                ],
            ),
            (
                "error_auth_lambda_functioninvokerole_not_string",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/Auth/Authorizers/MyLambdaAuth/FunctionInvokeRole] 3 is not of type 'string'",
                ],
            ),
            (
                "error_auth_lambda_functionpayloadtype_not_string",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/Auth/Authorizers/MyLambdaAuth/FunctionPayloadType] 3 is not one of ['TOKEN', 'REQUEST']",
                    "[/__/Properties/Auth/Authorizers/MyLambdaAuth/FunctionPayloadType] 3 is not of type 'string'",
                ],
            ),
            (
                "error_auth_lambda_functionpayloadtype_unknown_value",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/Auth/Authorizers/MyLambdaAuth/FunctionPayloadType] 'MyPayloadType' is not one of ['TOKEN', 'REQUEST']",
                ],
            ),
            # Auth LambdaRequest Identity
            # Auth LambdaToken Identity
            # Auth empty
            (
                "error_auth_empty",
                ["[/Resources/MyApi] Is not valid", "[/__/Properties/Auth] Must not be empty"],
            ),
            # BinaryMediaTypes
            (
                "error_binarymediatypes_empty",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/BinaryMediaTypes] Must not be empty",
                ],
            ),
            (
                "error_binarymediatypes_item_not_string",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/BinaryMediaTypes/0] 3 is not of type 'string'",
                ],
            ),
            (
                "error_binarymediatypes_not_list",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/BinaryMediaTypes] 'My binary media type' is not of type 'array'",
                ],
            ),
            # CacheClusterEnabled
            (
                "error_cacheclusterenabled_empty",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/CacheClusterEnabled] Must not be empty",
                ],
            ),
            (
                "error_cacheclusterenabled_not_boolean",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/CacheClusterEnabled] 'true' is not of type 'boolean'",
                ],
            ),
            # CacheClusterSize
            (
                "error_cacheclustersize_empty",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/CacheClusterSize] Must not be empty",
                ],
            ),
            (
                "error_cacheclustersize_not_string",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/CacheClusterSize] 3 is not of type 'string'",
                ],
            ),
            # CanarySetting
            (
                "error_canarysetting_deploymentid_empty",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/CanarySetting/DeploymentId] Must not be empty",
                ],
            ),
            (
                "error_canarysetting_deploymentid_not_string",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/CanarySetting/DeploymentId] 3 is not of type 'string'",
                ],
            ),
            (
                "error_canarysetting_empty",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/CanarySetting] Must not be empty",
                ],
            ),
            (
                "error_canarysetting_not_object",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/CanarySetting] 3 is not of type 'object'",
                ],
            ),
            (
                "error_canarysetting_percenttraffic_empty",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/CanarySetting/PercentTraffic] Must not be empty",
                ],
            ),
            (
                "error_canarysetting_percenttraffic_not_number",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/CanarySetting/PercentTraffic] '3.5' is not of type 'number'",
                ],
            ),
            (
                "error_canarysetting_percenttraffic_too_low",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/CanarySetting/PercentTraffic] -1 is less than the minimum of 0",
                ],
            ),
            (
                "error_canarysetting_percenttraffic_too_high",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/CanarySetting/PercentTraffic] 101 is greater than the maximum of 100",
                ],
            ),
            (
                "error_canarysetting_stagevariableoverrides_empty",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/CanarySetting/StageVariableOverrides] Must not be empty",
                ],
            ),
            (
                "error_canarysetting_stagevariableoverrides_not_object",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/CanarySetting/StageVariableOverrides] 'My override' is not of type 'object'",
                ],
            ),
            (
                "error_canarysetting_stagevariableoverrides_item_empty",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/CanarySetting/StageVariableOverrides/MyOverride] Must not be empty",
                ],
            ),
            (
                "error_canarysetting_stagevariableoverrides_item_not_string",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/CanarySetting/StageVariableOverrides/MyOverride] 3 is not of type 'string'",
                ],
            ),
            (
                "error_canarysetting_usestagecache_empty",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/CanarySetting/UseStageCache] Must not be empty",
                ],
            ),
            (
                "error_canarysetting_usestagecache_not_boolean",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/Properties/CanarySetting/UseStageCache] 'true' is not of type 'boolean'",
                ],
            ),
            # Cors
            # DefinitionBody
            # DefinitionUri
            # Description
            # Domain
            # EndpointConfiguration
            # GatewayResponses
            # MethodSettings
            # MinimumCompressionSize
            # Models
            # Name
            # OpenApiVersion
            # StageName
            (
                "error_stagename_empty",
                ["[/Resources/MyApi] Is not valid", "[/__/Properties/StageName] Must not be empty"],
            ),
            (
                "error_stagename_missing",
                ["[/Resources/MyApi] Is not valid", "[/__/Properties] 'StageName' is a required property"],
            ),
            (
                "error_stagename_not_string",
                ["[/Resources/MyApi] Is not valid", "[/__/Properties/StageName] 3 is not of type 'string'"],
            ),
            # Tags
            # TracingEnabled
            # Variables
            # Success
            ("success_auth_cognito_complete", []),
            ("success_auth_cognito_minimal", []),
            ("success_auth_lambdarequest_complete.yaml", []),
            ("success_auth_lambdarequest_identity_only_context.yaml", []),
            ("success_auth_lambdarequest_identity_only_headers.yaml", []),
            ("success_auth_lambdarequest_identity_only_querystrings.yaml", []),
            ("success_auth_lambdarequest_identity_only_variables.yaml", []),
            ("success_complete_api", []),
            ("success_minimum_api", []),
        ],
    )
    def test_validator_api(self, template, errors):
        self._test_validator(os.path.join(INPUT_FOLDER, template), errors)
