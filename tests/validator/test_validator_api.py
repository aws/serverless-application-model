import os.path
import sys

from parameterized import parameterized

from tests.validator.test_validator import TestValidatorBase

if sys.version_info.major == 3 and sys.version_info.minor < 8:
    from importlib_metadata import version
else:
    from importlib.metadata import version

BASE_PATH = os.path.dirname(__file__)
INPUT_FOLDER = os.path.join(BASE_PATH, "input", "api")
OUTPUT_FOLDER = os.path.join(BASE_PATH, "output", "api")


class TestValidatorApi(TestValidatorBase):
    # jsonschema 4.* is more restrictive than 3, so we need a separate check
    # See https://github.com/aws/serverless-application-model/issues/2426
    jsonschemaVersion = version("jsonschema")
    jsonschemaMajorVersion = int(jsonschemaVersion.split(".")[0])
    _error_definitionuri = "error_definitionuri" if jsonschemaMajorVersion > 3 else "error_definitionuri_jsonschema3"

    @parameterized.expand(
        [
            "error_accesslogsetting",
            "error_auth",
            "error_auth_cognito",
            "error_auth_lambda",
            "error_auth_lambdarequest_identity",
            "error_auth_lambdatoken_identity",
            "error_auth_resourcepolicy",
            "error_auth_usageplan",
            "error_binarymediatypes",
            "error_cachecluster",
            "error_canarysetting",
            "error_cors",
            "error_definitionbody",
            _error_definitionuri,
            "error_description",
            "error_domain",
            "error_endpointconfiguration",
            "error_gatewayresponses",
            "error_methodsettings",
            "error_minimumcompressionsize",
            "error_models",
            "error_name",
            "error_openapiversion",
            "error_properties",
            "error_resource_attributes",
            "error_stagename",
            "error_tags",
            "error_tracingenabled",
            "error_variables",
        ],
    )
    def test_errors(self, template):
        self._test_validator_error(os.path.join(INPUT_FOLDER, template), os.path.join(OUTPUT_FOLDER, template))

    @parameterized.expand(
        [
            "success_auth_cognito",
            "success_auth_lambdarequest",
            "success_complete_api",
            "success_minimal_api",
            "success_resource_attributes",
        ],
    )
    def test_success(self, template):
        self._test_validator_success(os.path.join(INPUT_FOLDER, template))
