import logging
from unittest.case import skipIf

from tenacity import stop_after_attempt, retry_if_exception_type, after_log, wait_exponential, retry, wait_random

from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support

LOG = logging.getLogger(__name__)


@skipIf(current_region_does_not_support(["HttpApi"]), "HttpApi is not supported in this testing region")
class TestFunctionWithHttpApiAndAuth(BaseTest):
    """
    AWS::Lambda::Function tests with http api events and auth
    """

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=10) + wait_random(0, 1),
        retry=retry_if_exception_type(AssertionError),
        after=after_log(LOG, logging.WARNING),
        reraise=True,
    )
    def test_function_with_http_api_and_auth(self):
        # If the request is not signed, which none of the below are, IAM will respond with a "Forbidden" message.
        # We are not testing that IAM auth works here, we are simply testing if it was applied.
        IAM_AUTH_OUTPUT = '{"message":"Forbidden"}'

        self.create_and_verify_stack("single/function_with_http_api_events_and_auth")

        implicitEndpoint = self.get_api_v2_endpoint("ServerlessHttpApi")
        self.assertEqual(
            BaseTest.do_get_request_with_logging(implicitEndpoint + "/default-auth").text, self.FUNCTION_OUTPUT
        )
        self.assertEqual(BaseTest.do_get_request_with_logging(implicitEndpoint + "/iam-auth").text, IAM_AUTH_OUTPUT)

        defaultIamEndpoint = self.get_api_v2_endpoint("MyDefaultIamAuthHttpApi")
        self.assertEqual(
            BaseTest.do_get_request_with_logging(defaultIamEndpoint + "/no-auth").text, self.FUNCTION_OUTPUT
        )
        self.assertEqual(
            BaseTest.do_get_request_with_logging(defaultIamEndpoint + "/default-auth").text, IAM_AUTH_OUTPUT
        )
        self.assertEqual(BaseTest.do_get_request_with_logging(defaultIamEndpoint + "/iam-auth").text, IAM_AUTH_OUTPUT)

        iamEnabledEndpoint = self.get_api_v2_endpoint("MyIamAuthEnabledHttpApi")
        self.assertEqual(
            BaseTest.do_get_request_with_logging(iamEnabledEndpoint + "/default-auth").text, self.FUNCTION_OUTPUT
        )
        self.assertEqual(BaseTest.do_get_request_with_logging(iamEnabledEndpoint + "/iam-auth").text, IAM_AUTH_OUTPUT)
