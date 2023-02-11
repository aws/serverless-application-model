from unittest.case import skipIf

from integration.config.service_names import HTTP_API
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([HTTP_API]), "HttpApi is not supported in this testing region")
class TestFunctionWithUserPoolEvent(BaseTest):
    def test_function_with_user_pool_event(self):
        self.create_and_verify_stack("combination/http_api_with_auth")

        http_api_list = self.get_stack_resources("AWS::ApiGatewayV2::Api")
        self.assertEqual(len(http_api_list), 1)

        http_resource = http_api_list[0]
        http_api_id = http_resource["PhysicalResourceId"]
        api_v2_client = self.client_provider.api_v2_client
        authorizer_list = api_v2_client.get_authorizers(ApiId=http_api_id)["Items"]

        self.assertEqual(len(authorizer_list), 2)

        lambda_auth = next(x for x in authorizer_list if x["Name"] == "MyLambdaAuth")
        self.assertEqual(lambda_auth["AuthorizerType"], "REQUEST")
        self.assertEqual(lambda_auth["AuthorizerPayloadFormatVersion"], "2.0")
        self.assertTrue(lambda_auth["EnableSimpleResponses"])
        lambda_identity_source_list = lambda_auth["IdentitySource"]
        self.assertEqual(len(lambda_identity_source_list), 4)
        self.assertTrue("$request.header.Authorization" in lambda_identity_source_list)
        self.assertTrue("$request.querystring.petId" in lambda_identity_source_list)
        self.assertTrue("$stageVariables.stageVar" in lambda_identity_source_list)
        self.assertTrue("$context.contextVar" in lambda_identity_source_list)

        role_resources = self.get_stack_resources("AWS::IAM::Role")
        self.assertEqual(len(role_resources), 2)
        auth_role = next((x for x in role_resources if x["LogicalResourceId"] == "MyAuthFnRole"), None)
        auth_role_arn = auth_role["PhysicalResourceId"]
        self.assertTrue(auth_role_arn in lambda_auth["AuthorizerCredentialsArn"])

        # Format of AuthorizerUri is in format of /2015-03-31/functions/[FunctionARN]/invocations
        function_resources = self.get_stack_resources("AWS::Lambda::Function")
        self.assertEqual(len(function_resources), 2)
        auth_function = next((x for x in function_resources if x["LogicalResourceId"] == "MyAuthFn"), None)
        auth_function_arn = auth_function["PhysicalResourceId"]
        self.assertTrue(auth_function_arn in lambda_auth["AuthorizerUri"])
        self.assertEqual(lambda_auth["AuthorizerResultTtlInSeconds"], 23)

        oauth_2_auth = next((x for x in authorizer_list if x["Name"] == "MyOAuth2Auth"), None)
        self.assertEqual(oauth_2_auth["AuthorizerType"], "JWT")
        jwt_configuration = oauth_2_auth["JwtConfiguration"]
        self.assertEqual(jwt_configuration["Issuer"], "https://openid-connect.onelogin.com/oidc")
        self.assertEqual(len(jwt_configuration["Audience"]), 1)
        self.assertEqual(jwt_configuration["Audience"][0], "MyApi")
        self.assertEqual(len(oauth_2_auth["IdentitySource"]), 1)
        self.assertEqual(oauth_2_auth["IdentitySource"][0], "$request.querystring.param")

        # Test updating stack
        self.update_stack(file_path="combination/http_api_with_auth_updated")

        http_api_list_updated = self.get_stack_resources("AWS::ApiGatewayV2::Api")
        self.assertEqual(len(http_api_list_updated), 1)

        http_resource_updated = http_api_list_updated[0]
        http_api_id_updated = http_resource_updated["PhysicalResourceId"]
        authorizer_list_updated = api_v2_client.get_authorizers(ApiId=http_api_id_updated)["Items"]
        self.assertEqual(len(authorizer_list_updated), 1)

        lambda_auth_updated = next(x for x in authorizer_list_updated if x["Name"] == "MyLambdaAuthUpdated")
        self.assertEqual(lambda_auth_updated["AuthorizerType"], "REQUEST")
        self.assertEqual(lambda_auth_updated["AuthorizerPayloadFormatVersion"], "1.0")
        self.assertEqual(lambda_auth_updated["AuthorizerResultTtlInSeconds"], 37)
        lambda_identity_source_list_updated = lambda_auth_updated["IdentitySource"]
        self.assertEqual(len(lambda_identity_source_list_updated), 1)
        self.assertTrue("$request.header.Authorization" in lambda_identity_source_list_updated)

        role_resources_updated = self.get_stack_resources("AWS::IAM::Role")
        self.assertEqual(len(role_resources_updated), 2)
        auth_role_updated = next((x for x in role_resources_updated if x["LogicalResourceId"] == "MyAuthFnRole"), None)
        auth_role_arn_updated = auth_role_updated["PhysicalResourceId"]
        self.assertTrue(auth_role_arn_updated in lambda_auth_updated["AuthorizerCredentialsArn"])

        function_resources_updated = self.get_stack_resources("AWS::Lambda::Function")
        self.assertEqual(len(function_resources_updated), 2)
        auth_function_updated = next(
            (x for x in function_resources_updated if x["LogicalResourceId"] == "MyAuthFn"), None
        )
        auth_function_arn_updated = auth_function_updated["PhysicalResourceId"]
        self.assertTrue(auth_function_arn_updated in lambda_auth_updated["AuthorizerUri"])
