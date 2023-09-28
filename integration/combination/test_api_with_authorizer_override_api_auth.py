from unittest.case import skipIf

from integration.config.service_names import API_KEY, COGNITO, REST_API
from integration.helpers.base_test import BaseTest
from integration.helpers.deployer.utils.retry import retry
from integration.helpers.exception import StatusCodeError
from integration.helpers.resource import current_region_does_not_support


@skipIf(
    current_region_does_not_support([COGNITO, API_KEY, REST_API]), "Cognito is not supported in this testing region"
)
class TestApiWithAuthorizerOverrideApiAuth(BaseTest):
    def test_authorizer_override_api_auth(self):
        self.create_and_verify_stack("combination/api_with_authorizer_override_api_auth")

        stack_outputs = self.get_stack_outputs()

        base_url = stack_outputs["ApiUrl"]

        # Default case with no Auth override
        self.verify_authorized_request(base_url + "lambda-request?authorization=allow", 200)
        self.verify_authorized_request(base_url + "lambda-request", 401)

        # Override Auth to NONE, lambda request should pass without authorization
        self.verify_authorized_request(base_url + "lambda-request-override-none", 200)

        # Override Auth to CognitoUserPool, lambda request should fail with authorization for lambda request
        self.verify_authorized_request(base_url + "lambda-request-override-cognito?authorization=allow", 401)

    @retry(StatusCodeError, 10, 0.25)
    def verify_authorized_request(
        self,
        url,
        expected_status_code,
        header_key=None,
        header_value=None,
    ):
        if not header_key or not header_value:
            response = self.do_get_request_with_logging(url)
        else:
            headers = {header_key: header_value}
            response = self.do_get_request_with_logging(url, headers)
        status = response.status_code

        if status != expected_status_code:
            raise StatusCodeError(
                f"Request to {url} failed with status: {status}, expected status: {expected_status_code}"
            )

        if not header_key or not header_value:
            self.assertEqual(
                status, expected_status_code, "Request to " + url + "  must return HTTP " + str(expected_status_code)
            )
        else:
            self.assertEqual(
                status,
                expected_status_code,
                "Request to "
                + url
                + " ("
                + header_key
                + ": "
                + header_value
                + ") must return HTTP "
                + str(expected_status_code),
            )


def get_authorizer_by_name(authorizers, name):
    for authorizer in authorizers:
        if authorizer["name"] == name:
            return authorizer
    return None


def get_resource_by_path(resources, path):
    for resource in resources:
        if resource["path"] == path:
            return resource
    return None


def get_method(resources, path, rest_api_id, apigw_client):
    resource = get_resource_by_path(resources, path)
    return apigw_client.get_method(restApiId=rest_api_id, resourceId=resource["id"], httpMethod="GET")
