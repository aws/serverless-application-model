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
            "error_properties",
            "error_accesslogsetting",
            "error_auth",
            "error_auth_cognito",
            "error_auth_lambda",
            "error_auth_lambdarequest_identity",
            "error_auth_lambdatoken_identity",
            "error_binarymediatypes",
            "error_cachecluster",
            "error_canarysetting",
            "error_cors",
            "error_definitionbody",
            "error_definitionuri",
            "error_description",
            "error_domain",
            "error_endpointconfiguration",
            "error_gatewayresponses",
            "error_methodsettings",
            "error_minimumcompressionsize",
            "error_models",
            "error_name",
            "error_openapiversion",
            "error_stagename",
            # "error_tags",
            "error_tracingenabled",
            "error_variables",
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
