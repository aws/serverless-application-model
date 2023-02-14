import time
from unittest.case import skipIf

import pytest

from integration.config.service_names import HTTP_API
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([HTTP_API]), "HttpApi is not supported in this testing region")
class TestFunctionWithHttpApiAndAuth(BaseTest):
    """
    AWS::Lambda::Function tests with http api events and auth
    """

    @pytest.mark.flaky(reruns=5)
    def test_function_with_http_api_and_auth(self):
        # If the request is not signed, which none of the below are, IAM will respond with a "Forbidden" message.
        # We are not testing that IAM auth works here, we are simply testing if it was applied.
        IAM_AUTH_OUTPUT = '{"message":"Forbidden"}'

        self.create_and_verify_stack("single/function_with_http_api_events_and_auth")

        # This will be changed according to APIGW suggested wait time
        time.sleep(10)

        implicitEndpoint = self.get_api_v2_endpoint("ServerlessHttpApi")
        self.assertEqual(
            self.do_get_request_with_logging(implicitEndpoint + "/default-auth").text, self.FUNCTION_OUTPUT
        )
        self.assertEqual(self.do_get_request_with_logging(implicitEndpoint + "/iam-auth").text, IAM_AUTH_OUTPUT)

        defaultIamEndpoint = self.get_api_v2_endpoint("MyDefaultIamAuthHttpApi")
        self.assertEqual(self.do_get_request_with_logging(defaultIamEndpoint + "/no-auth").text, self.FUNCTION_OUTPUT)
        self.assertEqual(self.do_get_request_with_logging(defaultIamEndpoint + "/default-auth").text, IAM_AUTH_OUTPUT)
        self.assertEqual(self.do_get_request_with_logging(defaultIamEndpoint + "/iam-auth").text, IAM_AUTH_OUTPUT)

        iamEnabledEndpoint = self.get_api_v2_endpoint("MyIamAuthEnabledHttpApi")
        self.assertEqual(
            self.do_get_request_with_logging(iamEnabledEndpoint + "/default-auth").text, self.FUNCTION_OUTPUT
        )
        self.assertEqual(self.do_get_request_with_logging(iamEnabledEndpoint + "/iam-auth").text, IAM_AUTH_OUTPUT)
