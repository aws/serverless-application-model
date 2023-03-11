from unittest.case import skipIf

from integration.config.service_names import API_KEY, REST_API
from integration.helpers.base_test import BaseTest
from integration.helpers.deployer.utils.retry import retry
from integration.helpers.exception import StatusCodeError
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([REST_API, API_KEY]), "RestApi/ApiKey is not supported in this testing region")
class TestApiWithAuthorizerApiKey(BaseTest):
    def test_authorizer_apikey(self):
        self.create_and_verify_stack("combination/api_with_authorizer_apikey")
        stack_outputs = self.get_stack_outputs()

        rest_api_id = self.get_physical_id_by_type("AWS::ApiGateway::RestApi")
        apigw_client = self.client_provider.api_client

        authorizers = apigw_client.get_authorizers(restApiId=rest_api_id)["items"]

        lambda_authorizer_uri = "arn:{}:apigateway:{}:lambda:path/2015-03-31/functions/{}/invocations".format(
            self.partition, self.my_region, stack_outputs["AuthorizerFunctionArn"]
        )

        lambda_token_authorizer = get_authorizer_by_name(authorizers, "MyLambdaTokenAuth")
        self.assertEqual(lambda_token_authorizer["type"], "TOKEN", "lambdaTokenAuthorizer: Type must be TOKEN")
        self.assertEqual(
            lambda_token_authorizer["identitySource"],
            "method.request.header.Authorization",
            "lambdaTokenAuthorizer: identity source must be method.request.header.Authorization",
        )
        self.assertIsNone(
            lambda_token_authorizer.get("authorizerCredentials"),
            "lambdaTokenAuthorizer: authorizer credentials must not be set",
        )
        self.assertIsNone(
            lambda_token_authorizer.get("identityValidationExpression"),
            "lambdaTokenAuthorizer: validation expression must not be set",
        )
        self.assertEqual(
            lambda_token_authorizer["authorizerUri"],
            lambda_authorizer_uri,
            "lambdaTokenAuthorizer: authorizer URI must be the Lambda Function Authorizer's URI",
        )
        self.assertIsNone(
            lambda_token_authorizer.get("authorizerResultTtlInSeconds"), "lambdaTokenAuthorizer: TTL must not be set"
        )

        resources = apigw_client.get_resources(restApiId=rest_api_id)["items"]

        lambda_token_get_method_result = get_method(resources, "/lambda-token-api-key", rest_api_id, apigw_client)
        self.assertEqual(
            lambda_token_get_method_result["authorizerId"],
            lambda_token_authorizer["id"],
            "lambdaTokenAuthorizer: GET method must be configured to use the Lambda Token Authorizer",
        )

        base_url = stack_outputs["ApiUrl"]

        self.verify_authorized_request(base_url + "none", 200)
        self.verify_authorized_request(base_url + "lambda-token-api-key", 401)
        # ApiKeySourceType is AUTHORIZER. This will trigger the Lambda Authorizer and in turn returns the api key
        self.verify_authorized_request(base_url + "lambda-token-api-key", 200, "Authorization", "allow")

        api_key_id = stack_outputs["ApiKeyId"]
        key = apigw_client.get_api_key(apiKey=api_key_id, includeValue=True)

        self.verify_authorized_request(base_url + "lambda-token-api-key", 401)
        # ApiKeySourceType is AUTHORIZER. Passing api key via x-api-key will not get authorized
        self.verify_authorized_request(base_url + "lambda-token-api-key", 401, "x-api-key", key["value"])

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
