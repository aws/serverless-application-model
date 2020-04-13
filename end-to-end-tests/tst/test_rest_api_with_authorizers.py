import boto3
import os
from helpers.base_test import BaseTest
from helpers.resources import Resources
from helpers.resource_types import ResourceTypes
import urllib2


class RestApiWithAuthorizersTest(BaseTest):
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

    def test_authorizeres_min(self):
        input_template = os.path.join(
            os.getcwd(), "end-to-end-tests/input", "rest_api_with_authorizers", "template.yaml"
        )
        capabilities = ["CAPABILITY_IAM"]
        stack_name = self.make_and_verify_stack(input_template, capabilities, self.rest_api_with_authorizers_resources)
        stack_resources_list = self.get_stack_resources()
        stack_outputs = self.get_outputs()

        rest_api_id = self.get_stack_resource_with_resource_type(ResourceTypes.APIGW_RESTAPI).get("PhysicalResourceId")
        api_gateway_client = boto3.client("apigateway")
        authorizers = api_gateway_client.get_authorizers(restApiId=rest_api_id).get("items")
        lambda_authorizer_uri = "arn:aws:apigateway:" + boto3.session.Session().region_name + \
                                ":lambda:path/2015-03-31/functions/" + stack_outputs.get("AuthorizerFunctionArn")\
                                + "/invocations"
        lambda_token_authorizer = self.get_authorizer_by_name(authorizers, "MyLambdaTokenAuth")
        self.assertEquals(lambda_token_authorizer.get("type"), "TOKEN", "lambdaTokenAuthorizer: Type must be TOKEN")
        self.assertEquals(lambda_token_authorizer.get("identitySource"), "method.request.header.Authorization", "lambdaTokenAuthorizer: identity source must be method.request.header.Authorization")
        self.assertEquals(lambda_token_authorizer.get("authorizerCredentials"), None, "lambdaTokenAuthorizer: authorizer credentials must not be set")
        self.assertEquals(lambda_token_authorizer.get("identityValidationExpression"), None, "lambdaTokenAuthorizer: validation expression must not be set")
        self.assertEquals(lambda_token_authorizer.get("authorizerUri"), lambda_authorizer_uri, "lambdaTokenAuthorizer: authorizer URI must be the Lambda Function Authorizer's URI")
        self.assertEquals(lambda_token_authorizer.get("authorizerResultTtlInSeconds"), None, "lambdaTokenAuthorizer: TTL must be None")

        resources = api_gateway_client.get_resources(restApiId=rest_api_id).get("items")
        lambda_token_method_result = self.get_method(resources, "/lambda-token", rest_api_id, api_gateway_client)

        self.assertEquals(lambda_token_method_result.get("authorizerId"), lambda_token_authorizer.get("id"), "lambdaTokenAuthorizer: GET method must be configured to use the Lambda Token Authorizer");
        base_url = stack_outputs.get("ApiUrl")

        self.assertTrue(RestApiWithAuthorizersTest.verify_authorized_request(base_url + "none", 200, "", ""))
        self.assertTrue(RestApiWithAuthorizersTest.verify_authorized_request(base_url + "lambda-token", 401, "", ""))
        self.assertTrue(RestApiWithAuthorizersTest.verify_authorized_request(base_url + "lambda-token", 200, "Authorization", "allow"))

    @staticmethod
    def get_authorizer_by_name(authorizers, authorizer_name):
        authorizer = list(filter(lambda d: d['name'] == authorizer_name, authorizers))
        if len(authorizer) == 1:
            return authorizer[0]
        else:
            raise ValueError("No authorizers found with name: {}".format(authorizer_name))

    @staticmethod
    def get_method(resources, path, rest_api_id, api_gateway_client):
        resource = RestApiWithAuthorizersTest.get_resource_by_path(resources, path)[0]
        return api_gateway_client.get_method(restApiId=rest_api_id, resourceId=resource.get("id"), httpMethod="GET")

    @staticmethod
    def get_resource_by_path(resources, path):
        return list(filter(lambda d: d['path'] == path, resources))

    @staticmethod
    def verify_authorized_request(url, expected_status_code, auth_header_key, auth_header_value):
        status = RestApiWithAuthorizersTest.make_authorized_request(url, auth_header_key, auth_header_value)
        return status == expected_status_code

    @staticmethod
    def make_authorized_request(url, auth_header_key, auth_header_value):
        print("Making request to " + url)
        try:
            if auth_header_key is None or len(auth_header_key) == 0:
                req = urllib2.Request(url)
            else:
                headers = {auth_header_key: auth_header_value}
                req = urllib2.Request(url, headers=headers)

            response = urllib2.urlopen(req)
            return response.getcode()
        except urllib2.HTTPError, e:
            return e.code
