from integration.helpers.base_test import BaseTest


class TestFunctionWithHttpApiAndAuth(BaseTest):
    """
    AWS::Lambda::Function tests with http api events and auth
    """

    def test_function_with_http_api_and_auth(self):
        # If the request is not signed, which none of the below are, IAM will respond with a "Forbidden" message.
        # We are not testing that IAM auth works here, we are simply testing if it was applied.
        IAM_AUTH_OUTPUT = '{"message":"Forbidden"}'

        self.create_and_verify_stack("function_with_http_api_events_and_auth")

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
