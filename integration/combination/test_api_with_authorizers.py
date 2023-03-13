from unittest.case import skipIf

from integration.config.service_names import API_KEY, COGNITO, REST_API
from integration.helpers.base_test import BaseTest
from integration.helpers.deployer.utils.retry import retry
from integration.helpers.exception import StatusCodeError
from integration.helpers.resource import current_region_does_not_support


@skipIf(
    current_region_does_not_support([COGNITO, API_KEY, REST_API]), "Cognito is not supported in this testing region"
)
class TestApiWithAuthorizers(BaseTest):
    def test_authorizers_min(self):
        self.create_and_verify_stack("combination/api_with_authorizers_min")
        stack_outputs = self.get_stack_outputs()

        rest_api_id = self.get_physical_id_by_type("AWS::ApiGateway::RestApi")
        apigw_client = self.client_provider.api_client

        authorizers = apigw_client.get_authorizers(restApiId=rest_api_id)["items"]
        lambda_authorizer_uri = (
            "arn:aws:apigateway:"
            + self.my_region
            + ":lambda:path/2015-03-31/functions/"
            + stack_outputs["AuthorizerFunctionArn"]
            + "/invocations"
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

        lambda_request_authorizer = get_authorizer_by_name(authorizers, "MyLambdaRequestAuth")
        self.assertEqual(lambda_request_authorizer["type"], "REQUEST", "lambdaRequestAuthorizer: Type must be REQUEST")
        self.assertEqual(
            lambda_request_authorizer["identitySource"],
            "method.request.querystring.authorization",
            "lambdaRequestAuthorizer: identity source must be method.request.querystring.authorization",
        )
        self.assertIsNone(
            lambda_request_authorizer.get("authorizerCredentials"),
            "lambdaRequestAuthorizer: authorizer credentials must not be set",
        )
        self.assertEqual(
            lambda_request_authorizer["authorizerUri"],
            lambda_authorizer_uri,
            "lambdaRequestAuthorizer: authorizer URI must be the Lambda Function Authorizer's URI",
        )
        self.assertIsNone(
            lambda_request_authorizer.get("authorizerResultTtlInSeconds"),
            "lambdaRequestAuthorizer: TTL must not be set",
        )

        cognito_authorizer = get_authorizer_by_name(authorizers, "MyCognitoAuthorizer")
        cognito_user_pool_arn = stack_outputs["CognitoUserPoolArn"]
        self.assertEqual(
            cognito_authorizer["type"], "COGNITO_USER_POOLS", "cognitoAuthorizer: Type must be COGNITO_USER_POOLS"
        )
        self.assertEqual(
            cognito_authorizer["providerARNs"],
            [cognito_user_pool_arn],
            "cognitoAuthorizer: provider ARN must be the Cognito User Pool ARNs",
        )
        self.assertIsNone(
            cognito_authorizer.get("identityValidationExpression"),
            "cognitoAuthorizer: validation expression must not be set",
        )
        self.assertEqual(
            cognito_authorizer["identitySource"],
            "method.request.header.Authorization",
            "cognitoAuthorizer: identity source must be method.request.header.Authorization",
        )

        resources = apigw_client.get_resources(restApiId=rest_api_id)["items"]

        lambda_token_get_method_result = get_method(resources, "/lambda-token", rest_api_id, apigw_client)
        self.assertEqual(
            lambda_token_get_method_result["authorizerId"],
            lambda_token_authorizer["id"],
            "lambdaTokenAuthorizer: GET method must be configured to use the Lambda Token Authorizer",
        )

        lambda_request_get_method_result = get_method(resources, "/lambda-request", rest_api_id, apigw_client)
        self.assertEqual(
            lambda_request_get_method_result["authorizerId"],
            lambda_request_authorizer["id"],
            "lambdaRequestAuthorizer: GET method must be configured to use the Lambda Request Authorizer",
        )

        cognito_get_method_result = get_method(resources, "/cognito", rest_api_id, apigw_client)
        self.assertEqual(
            cognito_get_method_result["authorizerId"],
            cognito_authorizer["id"],
            "cognitoAuthorizer: GET method must be configured to use the Cognito Authorizer",
        )

        iam_get_method_result = get_method(resources, "/iam", rest_api_id, apigw_client)
        self.assertEqual(
            iam_get_method_result["authorizationType"],
            "AWS_IAM",
            "iamAuthorizer: GET method must be configured to use AWS_IAM",
        )

        base_url = stack_outputs["ApiUrl"]

        self.verify_authorized_request(base_url + "none", 200)
        self.verify_authorized_request(base_url + "lambda-token", 401)
        self.verify_authorized_request(base_url + "lambda-token", 200, "Authorization", "allow")

        self.verify_authorized_request(base_url + "lambda-request", 401)
        self.verify_authorized_request(base_url + "lambda-request?authorization=allow", 200)

        self.verify_authorized_request(base_url + "cognito", 401)

        self.verify_authorized_request(base_url + "iam", 403)

    def test_authorizers_max(self):
        self.create_and_verify_stack("combination/api_with_authorizers_max")
        stack_outputs = self.get_stack_outputs()

        rest_api_id = self.get_physical_id_by_type("AWS::ApiGateway::RestApi")
        apigw_client = self.client_provider.api_client

        authorizers = apigw_client.get_authorizers(restApiId=rest_api_id)["items"]
        lambda_authorizer_uri = (
            "arn:aws:apigateway:"
            + self.my_region
            + ":lambda:path/2015-03-31/functions/"
            + stack_outputs["AuthorizerFunctionArn"]
            + "/invocations"
        )

        lambda_token_authorizer = get_authorizer_by_name(authorizers, "MyLambdaTokenAuth")
        self.assertEqual(lambda_token_authorizer["type"], "TOKEN", "lambdaTokenAuthorizer: Type must be TOKEN")
        self.assertEqual(
            lambda_token_authorizer["identitySource"],
            "method.request.header.MyCustomAuthHeader",
            "lambdaTokenAuthorizer: identity source must be method.request.header.MyCustomAuthHeader",
        )
        self.assertEqual(
            lambda_token_authorizer["authorizerCredentials"],
            stack_outputs["LambdaAuthInvokeRoleArn"],
            "lambdaTokenAuthorizer: authorizer credentials must be set",
        )
        self.assertEqual(
            lambda_token_authorizer["identityValidationExpression"],
            "allow",
            "lambdaTokenAuthorizer: validation expression must be set to allow",
        )
        self.assertEqual(
            lambda_token_authorizer["authorizerUri"],
            lambda_authorizer_uri,
            "lambdaTokenAuthorizer: authorizer URI must be the Lambda Function Authorizer's URI",
        )
        self.assertEqual(
            lambda_token_authorizer["authorizerResultTtlInSeconds"], 20, "lambdaTokenAuthorizer: TTL must be 20"
        )

        lambda_request_authorizer = get_authorizer_by_name(authorizers, "MyLambdaRequestAuth")
        self.assertEqual(lambda_request_authorizer["type"], "REQUEST", "lambdaRequestAuthorizer: Type must be REQUEST")
        self.assertEqual(
            lambda_request_authorizer["identitySource"],
            "method.request.header.authorizationHeader, method.request.querystring.authorization, method.request.querystring.authorizationQueryString1",
            "lambdaRequestAuthorizer: identity source must be method.request.header.authorizationHeader, method.request.querystring.authorization, method.request.querystring.authorizationQueryString1",
        )
        self.assertEqual(
            lambda_request_authorizer["authorizerCredentials"],
            stack_outputs["LambdaAuthInvokeRoleArn"],
            "lambdaRequestAuthorizer: authorizer credentials must be set",
        )
        self.assertEqual(
            lambda_request_authorizer["authorizerUri"],
            lambda_authorizer_uri,
            "lambdaRequestAuthorizer: authorizer URI must be the Lambda Function Authorizer's URI",
        )
        self.assertEqual(
            lambda_request_authorizer["authorizerResultTtlInSeconds"], 0, "lambdaRequestAuthorizer: TTL must be 0"
        )

        cognito_authorizer = get_authorizer_by_name(authorizers, "MyCognitoAuthorizer")
        cognito_user_pool_arn = stack_outputs["CognitoUserPoolArn"]
        cognito_user_pool2_arn = stack_outputs["CognitoUserPoolTwoArn"]
        self.assertEqual(
            cognito_authorizer["type"], "COGNITO_USER_POOLS", "cognitoAuthorizer: Type must be COGNITO_USER_POOLS"
        )
        self.assertEqual(
            cognito_authorizer["providerARNs"],
            [cognito_user_pool_arn, cognito_user_pool2_arn],
            "cognitoAuthorizer: provider ARN must be the Cognito User Pool ARNs",
        )
        self.assertEqual(
            cognito_authorizer["identityValidationExpression"],
            "myauthvalidationexpression",
            "cognitoAuthorizer: validation expression must be set to myauthvalidationexpression",
        )
        self.assertEqual(
            cognito_authorizer["identitySource"],
            "method.request.header.MyAuthorizationHeader",
            "cognitoAuthorizer: identity source must be method.request.header.MyAuthorizationHeader",
        )

        resources = apigw_client.get_resources(restApiId=rest_api_id)["items"]

        lambda_token_get_method_result = get_method(resources, "/lambda-token", rest_api_id, apigw_client)
        self.assertEqual(
            lambda_token_get_method_result["authorizerId"],
            lambda_token_authorizer["id"],
            "lambdaTokenAuthorizer: GET method must be configured to use the Lambda Token Authorizer",
        )

        lambda_request_get_method_result = get_method(resources, "/lambda-request", rest_api_id, apigw_client)
        self.assertEqual(
            lambda_request_get_method_result["authorizerId"],
            lambda_request_authorizer["id"],
            "lambdaRequestAuthorizer: GET method must be configured to use the Lambda Request Authorizer",
        )

        cognito_get_method_result = get_method(resources, "/cognito", rest_api_id, apigw_client)
        self.assertEqual(
            cognito_get_method_result["authorizerId"],
            cognito_authorizer["id"],
            "cognitoAuthorizer: GET method must be configured to use the Cognito Authorizer",
        )

        iam_get_method_result = get_method(resources, "/iam", rest_api_id, apigw_client)
        self.assertEqual(
            iam_get_method_result["authorizationType"],
            "AWS_IAM",
            "iamAuthorizer: GET method must be configured to use AWS_IAM",
        )

        base_url = stack_outputs["ApiUrl"]

        self.verify_authorized_request(base_url + "none", 200)
        self.verify_authorized_request(base_url + "lambda-token", 401)
        self.verify_authorized_request(base_url + "lambda-token", 200, "MyCustomAuthHeader", "allow")

        self.verify_authorized_request(base_url + "lambda-request", 401)
        self.verify_authorized_request(
            base_url + "lambda-request?authorization=allow&authorizationQueryString1=x", 200, "authorizationHeader", "y"
        )

        self.verify_authorized_request(base_url + "cognito", 401)

        self.verify_authorized_request(base_url + "iam", 403)

    def test_authorizers_max_openapi(self):
        self.create_and_verify_stack("combination/api_with_authorizers_max_openapi")
        stack_outputs = self.get_stack_outputs()

        rest_api_id = self.get_physical_id_by_type("AWS::ApiGateway::RestApi")
        apigw_client = self.client_provider.api_client

        authorizers = apigw_client.get_authorizers(restApiId=rest_api_id)["items"]
        lambda_authorizer_uri = (
            "arn:aws:apigateway:"
            + self.my_region
            + ":lambda:path/2015-03-31/functions/"
            + stack_outputs["AuthorizerFunctionArn"]
            + "/invocations"
        )

        lambda_token_authorizer = get_authorizer_by_name(authorizers, "MyLambdaTokenAuth")
        self.assertEqual(lambda_token_authorizer["type"], "TOKEN", "lambdaTokenAuthorizer: Type must be TOKEN")
        self.assertEqual(
            lambda_token_authorizer["identitySource"],
            "method.request.header.MyCustomAuthHeader",
            "lambdaTokenAuthorizer: identity source must be method.request.header.MyCustomAuthHeader",
        )
        self.assertEqual(
            lambda_token_authorizer["authorizerCredentials"],
            stack_outputs["LambdaAuthInvokeRoleArn"],
            "lambdaTokenAuthorizer: authorizer credentials must be set",
        )
        self.assertEqual(
            lambda_token_authorizer["identityValidationExpression"],
            "allow",
            "lambdaTokenAuthorizer: validation expression must be set to allow",
        )
        self.assertEqual(
            lambda_token_authorizer["authorizerUri"],
            lambda_authorizer_uri,
            "lambdaTokenAuthorizer: authorizer URI must be the Lambda Function Authorizer's URI",
        )
        self.assertEqual(
            lambda_token_authorizer["authorizerResultTtlInSeconds"], 20, "lambdaTokenAuthorizer: TTL must be 20"
        )

        lambda_request_authorizer = get_authorizer_by_name(authorizers, "MyLambdaRequestAuth")
        self.assertEqual(lambda_request_authorizer["type"], "REQUEST", "lambdaRequestAuthorizer: Type must be REQUEST")
        self.assertEqual(
            lambda_request_authorizer["identitySource"],
            "method.request.header.authorizationHeader, method.request.querystring.authorization, method.request.querystring.authorizationQueryString1",
            "lambdaRequestAuthorizer: identity source must be method.request.header.authorizationHeader, method.request.querystring.authorization, method.request.querystring.authorizationQueryString1",
        )
        self.assertEqual(
            lambda_request_authorizer["authorizerCredentials"],
            stack_outputs["LambdaAuthInvokeRoleArn"],
            "lambdaRequestAuthorizer: authorizer credentials must be set",
        )
        self.assertEqual(
            lambda_request_authorizer["authorizerUri"],
            lambda_authorizer_uri,
            "lambdaRequestAuthorizer: authorizer URI must be the Lambda Function Authorizer's URI",
        )
        self.assertEqual(
            lambda_request_authorizer["authorizerResultTtlInSeconds"], 0, "lambdaRequestAuthorizer: TTL must be 0"
        )

        cognito_authorizer = get_authorizer_by_name(authorizers, "MyCognitoAuthorizer")
        cognito_user_pool_arn = stack_outputs["CognitoUserPoolArn"]
        cognito_user_pool2_arn = stack_outputs["CognitoUserPoolTwoArn"]
        self.assertEqual(
            cognito_authorizer["type"], "COGNITO_USER_POOLS", "cognitoAuthorizer: Type must be COGNITO_USER_POOLS"
        )
        self.assertEqual(
            cognito_authorizer["providerARNs"],
            [cognito_user_pool_arn, cognito_user_pool2_arn],
            "cognitoAuthorizer: provider ARN must be the Cognito User Pool ARNs",
        )
        self.assertEqual(
            cognito_authorizer["identityValidationExpression"],
            "myauthvalidationexpression",
            "cognitoAuthorizer: validation expression must be set to myauthvalidationexpression",
        )
        self.assertEqual(
            cognito_authorizer["identitySource"],
            "method.request.header.MyAuthorizationHeader",
            "cognitoAuthorizer: identity source must be method.request.header.MyAuthorizationHeader",
        )

        resources = apigw_client.get_resources(restApiId=rest_api_id)["items"]

        lambda_token_get_method_result = get_method(resources, "/lambda-token", rest_api_id, apigw_client)
        self.assertEqual(
            lambda_token_get_method_result["authorizerId"],
            lambda_token_authorizer["id"],
            "lambdaTokenAuthorizer: GET method must be configured to use the Lambda Token Authorizer",
        )

        lambda_request_get_method_result = get_method(resources, "/lambda-request", rest_api_id, apigw_client)
        self.assertEqual(
            lambda_request_get_method_result["authorizerId"],
            lambda_request_authorizer["id"],
            "lambdaRequestAuthorizer: GET method must be configured to use the Lambda Request Authorizer",
        )

        cognito_get_method_result = get_method(resources, "/cognito", rest_api_id, apigw_client)
        self.assertEqual(
            cognito_get_method_result["authorizerId"],
            cognito_authorizer["id"],
            "cognitoAuthorizer: GET method must be configured to use the Cognito Authorizer",
        )

        iam_get_method_result = get_method(resources, "/iam", rest_api_id, apigw_client)
        self.assertEqual(
            iam_get_method_result["authorizationType"],
            "AWS_IAM",
            "iamAuthorizer: GET method must be configured to use AWS_IAM",
        )

        base_url = stack_outputs["ApiUrl"]

        self.verify_authorized_request(base_url + "none", 200)
        self.verify_authorized_request(base_url + "lambda-token", 401)
        self.verify_authorized_request(base_url + "lambda-token", 200, "MyCustomAuthHeader", "allow")

        self.verify_authorized_request(base_url + "lambda-request", 401)
        self.verify_authorized_request(
            base_url + "lambda-request?authorization=allow&authorizationQueryString1=x", 200, "authorizationHeader", "y"
        )

        self.verify_authorized_request(base_url + "cognito", 401)

        self.verify_authorized_request(base_url + "iam", 403)

        api_key_id = stack_outputs["ApiKeyId"]
        key = apigw_client.get_api_key(apiKey=api_key_id, includeValue=True)

        self.verify_authorized_request(base_url + "apikey", 200, "x-api-key", key["value"])
        self.verify_authorized_request(base_url + "apikey", 403)

    def test_authorizers_with_invoke_function_set_none(self):
        self.create_and_verify_stack("combination/api_with_authorizers_invokefunction_set_none")

        rest_api_id = self.get_physical_id_by_type("AWS::ApiGateway::RestApi")
        apigw_client = self.client_provider.api_client

        resources = apigw_client.get_resources(restApiId=rest_api_id)["items"]

        function_with_invoke_role_default = get_method(
            resources, "/MyFunctionDefaultInvokeRole", rest_api_id, apigw_client
        )
        credentials_for_invoke_role_default = function_with_invoke_role_default["methodIntegration"]["credentials"]
        self.assertEqual(credentials_for_invoke_role_default, "arn:aws:iam::*:user/*")
        function_with_invoke_role_none = get_method(resources, "/MyFunctionNONEInvokeRole", rest_api_id, apigw_client)
        credentials_for_invoke_role_none = function_with_invoke_role_none.get("methodIntegration").get(
            "methodIntegration"
        )
        self.assertIsNone(credentials_for_invoke_role_none)

        api_event_with_auth = get_method(resources, "/api/with-auth", rest_api_id, apigw_client)
        auth_type_for_api_event_with_auth = api_event_with_auth["authorizationType"]
        self.assertEqual(auth_type_for_api_event_with_auth, "AWS_IAM")
        api_event_with_out_auth = get_method(resources, "/api/without-auth", rest_api_id, apigw_client)
        auth_type_for_api_event_without_auth = api_event_with_out_auth["authorizationType"]
        self.assertEqual(auth_type_for_api_event_without_auth, "NONE")

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
