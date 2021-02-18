import os.path
from parameterized import parameterized
import pytest
from unittest import TestCase
from samtranslator.yaml_helper import yaml_parse
from samtranslator.validator.validator import SamTemplateValidator
from tests.validator.test_validator import TestValidatorBase

BASE_PATH = os.path.dirname(__file__)
INPUT_FOLDER = os.path.join(BASE_PATH, "input", "api")
OUTPUT_FOLDER = os.path.join(BASE_PATH, "output", "api")


class TestValidatorApi(TestValidatorBase):
    @parameterized.expand(
        [
            "error_properties_empty",
            "error_properties_missing",
            "error_accesslogsetting_destinationarn_not_string",
            "error_accesslogsetting_empty",
            "error_accesslogsetting_format_not_string",
            "error_accesslogsetting_unknown_property",
            "error_auth_adddefaultauthorizertocorspreflight_empty",
            "error_auth_adddefaultauthorizertocorspreflight_not_boolean",
            "error_auth_apikeyrequired_empty",
            "error_auth_apikeyrequired_not_boolean",
            "error_auth_authorizers_empty",
            "error_auth_authorizers_item_empty",
            "error_auth_authorizers_not_object",
            "error_auth_cognito_authorizationscopes_empty",
            "error_auth_cognito_authorizationscopes_item_not_string",
            "error_auth_cognito_authorizationscopes_not_list",
            "error_auth_cognito_identity_empty",
            "error_auth_cognito_identity_header_empty",
            "error_auth_cognito_identity_header_not_string",
            "error_auth_cognito_identity_reauthaurizeevery_empty",
            "error_auth_cognito_identity_reauthaurizeevery_not_int",
            "error_auth_cognito_identity_reauthaurizeevery_too_high",
            "error_auth_cognito_identity_reauthaurizeevery_too_low",
            "error_auth_cognito_identity_validationexpression_empty",
            "error_auth_cognito_identity_validationexpression_not_string",
            "error_auth_cognito_userpoolarn_empty",
            "error_auth_cognito_userpoolarn_missing",
            "error_auth_cognito_userpoolarn_not_string",
            "error_auth_empty",
            "error_auth_lambda_authorizationscopes_empty",
            "error_auth_lambda_authorizationscopes_item_not_string",
            "error_auth_lambda_authorizationscopes_not_list",
            "error_auth_lambda_functionarn_empty",
            "error_auth_lambda_functionarn_missing",
            "error_auth_lambda_functionarn_not_string",
            "error_auth_lambda_functioninvokerole_empty",
            "error_auth_lambda_functioninvokerole_not_string",
            "error_auth_lambda_functionpayloadtype_not_string",
            "error_auth_lambda_functionpayloadtype_unknown_value",
            # Auth LambdaRequest Identity
            # Auth LambdaToken Identity
            "error_binarymediatypes_empty",
            "error_binarymediatypes_item_not_string",
            "error_binarymediatypes_not_list",
            "error_cacheclusterenabled_empty",
            "error_cacheclusterenabled_not_boolean",
            "error_cacheclustersize_empty",
            "error_cacheclustersize_not_string",
            "error_canarysetting_deploymentid_empty",
            "error_canarysetting_deploymentid_not_string",
            "error_canarysetting_empty",
            "error_canarysetting_not_object",
            "error_canarysetting_percenttraffic_empty",
            "error_canarysetting_percenttraffic_not_number",
            "error_canarysetting_percenttraffic_too_high",
            "error_canarysetting_percenttraffic_too_low",
            "error_canarysetting_stagevariableoverrides_empty",
            "error_canarysetting_stagevariableoverrides_item_empty",
            "error_canarysetting_stagevariableoverrides_item_not_string",
            "error_canarysetting_stagevariableoverrides_not_object",
            "error_canarysetting_usestagecache_empty",
            "error_canarysetting_usestagecache_not_boolean",
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
            "error_stagename_empty",
            "error_stagename_missing",
            "error_stagename_not_string",
            # Tags
            # TracingEnabled
            # Variables
        ],
    )
    def test_validator_api_errors(self, template):
        self._test_validator_error(os.path.join(INPUT_FOLDER, template), os.path.join(OUTPUT_FOLDER, template))

    @parameterized.expand(
        [
            "success_auth_cognito_complete",
            "success_auth_cognito_minimal",
            "success_auth_lambdarequest_complete",
            "success_auth_lambdarequest_identity_only_context",
            "success_auth_lambdarequest_identity_only_headers",
            "success_auth_lambdarequest_identity_only_querystrings",
            "success_auth_lambdarequest_identity_only_variables",
            "success_complete_api",
            "success_minimum_api",
        ],
    )
    def test_validator_api_success(self, template):
        self._test_validator_success(os.path.join(INPUT_FOLDER, template))
