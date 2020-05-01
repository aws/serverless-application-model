import boto3
import os
from .helpers.base_test import BaseTest
from .helpers.resources import Resources
from .helpers.resource_types import ResourceTypes
import requests


class RestApiWithAuthorizersTest(BaseTest):
    """
    contains methods to test authorizer for AWS::Serverless::RestApi

    Methods
    -------
    :method test_authorizers(self)
        test lambdaTokenAuthorizer for AWS::Serverless::RestApi
    :method get_authorizer_by_name(authorizers, authorizer_name)
        returns the authorizer by name
    :method get_method(resources, path, rest_api_id, api_gateway_client)
        returns the method containing methodIntegrations, AuthorizationScopes
    :method get_resource_by_path(resources, path)
        returns the resource for given path
    :method verify_authorized_request(url, expected_status_code, auth_header_key, auth_header_value)
        verifies if the request is valid
    :method make_authorized_request(url, auth_header_key, auth_header_value)
        returns the status of the api call
    """

    rest_api_with_authorizers_resources = (
        Resources()
        .created("MyApi", ResourceTypes.APIGW_RESTAPI)
        .created("MyApiDeployment", ResourceTypes.APIGW_DEPLOYMENT)
        .created("MyApiMyLambdaRequestAuthAuthorizerPermission", ResourceTypes.LAMBDA_PERMISSION)
        .created("MyApiMyLambdaTokenAuthAuthorizerPermission", ResourceTypes.LAMBDA_PERMISSION)
        .created("MyApiProdStage", ResourceTypes.APIGW_STAGE)
        .created("MyCognitoUserPool", ResourceTypes.COGNITO_USER_POOL)
        .created("MyCognitoUserPoolClient", ResourceTypes.COGNITO_USER_POOL_CLIENT)
        .created("MyFunction", ResourceTypes.LAMBDA_FUNCTION)
        .created("MyFunctionCognitoPermissionProd", ResourceTypes.LAMBDA_PERMISSION)
        .created("MyFunctionNonePermissionProd", ResourceTypes.LAMBDA_PERMISSION)
        .created("MyFunctionLambdaRequestPermissionProd", ResourceTypes.LAMBDA_PERMISSION)
        .created("MyFunctionLambdaTokenPermissionProd", ResourceTypes.LAMBDA_PERMISSION)
        .created("MyFunctionIamPermissionProd", ResourceTypes.LAMBDA_PERMISSION)
        .created("MyFunctionRole", ResourceTypes.IAM_ROLE)
        .created("MyLambdaAuthFunction", ResourceTypes.LAMBDA_FUNCTION)
        .created("MyLambdaAuthFunctionRole", ResourceTypes.IAM_ROLE)
    )

    def tearDown(self):
        self.delete_stack()

    def test_authorizers(self):
        """
        test lambdaTokenAuthorizer for AWS::Serverless::RestApi
        """
        input_template = os.path.join(
            os.getcwd(), "end_to_end_tests/input", "rest_api_with_authorizers", "template.yaml"
        )
        capabilities = ["CAPABILITY_IAM"]
        self.make_and_verify_stack(input_template, capabilities, self.rest_api_with_authorizers_resources)
        stack_outputs = self.get_outputs()

        rest_api_id = self.get_stack_resource_with_resource_type(ResourceTypes.APIGW_RESTAPI).get("PhysicalResourceId")
        api_gateway_client = boto3.client("apigateway")
        # list of authorizers associated with the Api
        authorizers = api_gateway_client.get_authorizers(restApiId=rest_api_id).get("items")
        lambda_authorizer_uri = (
            "arn:aws:apigateway:"
            + boto3.session.Session().region_name
            + ":lambda:path/2015-03-31/functions/"
            + stack_outputs.get("AuthorizerFunctionArn")
            + "/invocations"
        )
        lambda_token_authorizer = self.get_authorizer_by_name(authorizers, "MyLambdaTokenAuth")
        self.assertEqual(lambda_token_authorizer.get("type"), "TOKEN", "lambdaTokenAuthorizer: Type must be TOKEN")
        self.assertEqual(
            lambda_token_authorizer.get("identitySource"),
            "method.request.header.Authorization",
            "lambdaTokenAuthorizer: identity source must be method.request.header.Authorization",
        )
        self.assertEqual(
            lambda_token_authorizer.get("authorizerCredentials"),
            None,
            "lambdaTokenAuthorizer: authorizer credentials must not be set",
        )
        self.assertEqual(
            lambda_token_authorizer.get("identityValidationExpression"),
            None,
            "lambdaTokenAuthorizer: validation expression must not be set",
        )
        self.assertEqual(
            lambda_token_authorizer.get("authorizerUri"),
            lambda_authorizer_uri,
            "lambdaTokenAuthorizer: authorizer URI must be the Lambda Function Authorizer's URI",
        )
        self.assertEqual(
            lambda_token_authorizer.get("authorizerResultTtlInSeconds"), None, "lambdaTokenAuthorizer: TTL must be None"
        )

        resources = api_gateway_client.get_resources(restApiId=rest_api_id).get("items")
        lambda_token_method_result = self.get_method(resources, "/lambda-token", rest_api_id, api_gateway_client)

        self.assertEqual(
            lambda_token_method_result.get("authorizerId"),
            lambda_token_authorizer.get("id"),
            "lambdaTokenAuthorizer: GET method must be configured to use the Lambda Token Authorizer",
        )
        base_url = stack_outputs.get("ApiUrl")

        self.assertTrue(RestApiWithAuthorizersTest.verify_authorized_request(base_url + "none", 200, "", ""))
        self.assertTrue(RestApiWithAuthorizersTest.verify_authorized_request(base_url + "lambda-token", 401, "", ""))
        self.assertTrue(
            RestApiWithAuthorizersTest.verify_authorized_request(
                base_url + "lambda-token", 200, "Authorization", "allow"
            )
        )

    @staticmethod
    def get_authorizer_by_name(authorizers, authorizer_name):
        """
        returns the authorizer by name
        :param list authorizers: list of authorizers of the api
        :param str authorizer_name: name of the authorizer
        :raise: ValueError if authorizer is not found with the given name
        :return: returns the authorizer object with the given authorizer name
        :rtype: dict
        """
        authorizer = list(filter(lambda d: d["name"] == authorizer_name, authorizers))
        if len(authorizer) == 1:
            return authorizer[0]
        else:
            raise ValueError("No authorizers found with name: {}".format(authorizer_name))

    @staticmethod
    def get_method(resources, path, rest_api_id, api_gateway_client):
        """
        returns the method containing methodIntegrations, AuthorizationScopes
        :param list resources: list of resources of the api
        :param str path: path of the rest api
        :param str rest_api_id: rest api id of the api resource
        :param str api_gateway_client: apigateway client
        :raise: ValueError if resource is not found for the given path
        :return: returns the method object for the given path
        :rtype: dict
        """
        resource = RestApiWithAuthorizersTest.get_resource_by_path(resources, path)[0]
        if len(resource) == 0:
            raise ValueError("No resource found for path: {}".format(path))
        else:
            return api_gateway_client.get_method(restApiId=rest_api_id, resourceId=resource.get("id"), httpMethod="GET")

    @staticmethod
    def get_resource_by_path(resources, path):
        """
        returns the resource for given path
        :param list resources: list of resources of the api
        :param str path: path of the rest api
        :return: returns the resource object for the given path
        :rtype: list
        """
        return list(filter(lambda d: d["path"] == path, resources))

    @staticmethod
    def verify_authorized_request(url, expected_status_code, auth_header_key, auth_header_value):
        """
        verifies if the request is valid
        :param str url: api url endpoint to call
        :param str expected_status_code: expected status code of api call
        :param str auth_header_key: authorization header key
        :param str auth_header_value: authorization header value
        :return: returns True if the status code of the api call is same as expected status code
        :rtype: bool
        """
        status = RestApiWithAuthorizersTest.make_authorized_request(url, auth_header_key, auth_header_value)
        return status == expected_status_code

    @staticmethod
    def make_authorized_request(url, auth_header_key, auth_header_value):
        """
        returns the status of the api call
        :param str url: api url endpoint to call
        :param str auth_header_key: authorization header key
        :param str auth_header_value: authorization header value
        :raise: HTTPError if the request was not successful
        :return: returns the status code of the request
        :rtype: dict
        """
        print("Making request to " + url)
        try:
            if auth_header_key is None or len(auth_header_key) == 0:
                request = requests.get(url)
            else:
                headers = {auth_header_key: auth_header_value}
                request = requests.get(url, headers=headers)
            return request.status_code
        except requests.exceptions.HTTPError as e:
            print("HTTP error, while executing request: {}".format(url))
            return e
