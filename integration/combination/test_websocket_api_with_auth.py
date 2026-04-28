from unittest.case import skipIf

from integration.config.service_names import WEBSOCKET_API
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([WEBSOCKET_API]), "WebSocketApi is not supported in this region")
class TestWebSocketApiWithAuth(BaseTest):

    def test_websocket_api_with_iam_auth(self):
        """
        Creates a WebSocket API with an IAM authorizer
        """
        self.create_and_verify_stack("combination/websocket_api_with_iam_auth")

        websocket_api_list = self.get_stack_resources("AWS::ApiGatewayV2::Api")
        self.assertEqual(len(websocket_api_list), 1)

        stages = self.get_api_v2_stack_stages()

        self.assertEqual(len(stages), 1)
        self.assertEqual(stages[0]["StageName"], "default")

        websocket_resource = websocket_api_list[0]
        websocket_api_id = websocket_resource["PhysicalResourceId"]
        api_v2_client = self.client_provider.api_v2_client
        routes_list = api_v2_client.get_routes(ApiId=websocket_api_id)["Items"]
        route = routes_list[0]
        self.assertEqual(route["AuthorizationType"], "AWS_IAM")

    def test_none_auth(self):
        self.create_and_verify_stack("combination/websocket_api_with_none_auth")

        websocket_api_list = self.get_stack_resources("AWS::ApiGatewayV2::Api")
        self.assertEqual(len(websocket_api_list), 1)

        websocket_resource = websocket_api_list[0]
        websocket_api_id = websocket_resource["PhysicalResourceId"]
        api_v2_client = self.client_provider.api_v2_client
        routes_list = api_v2_client.get_routes(ApiId=websocket_api_id)["Items"]
        route = routes_list[0]
        self.assertEqual(route["AuthorizationType"], "NONE")

    def test_websocket_api_with_lambda_auth_config(self):
        """
        Creates a WebSocket API with a Lambda authorizer
        """
        self.create_and_verify_stack("combination/websocket_api_with_lambda_auth")

        websocket_api_list = self.get_stack_resources("AWS::ApiGatewayV2::Api")
        self.assertEqual(len(websocket_api_list), 1)

        websocket_resource = websocket_api_list[0]
        websocket_api_id = websocket_resource["PhysicalResourceId"]
        api_v2_client = self.client_provider.api_v2_client

        route_list = api_v2_client.get_routes(ApiId=websocket_api_id)["Items"]
        self.assertEqual(len(route_list), 1)
        route = route_list[0]
        self.assertEqual(route["AuthorizationType"], "CUSTOM")
        self.assertIsNotNone(route["AuthorizerId"])

        authorizer_list = api_v2_client.get_authorizers(ApiId=websocket_api_id)["Items"]
        self.assertEqual(len(authorizer_list), 1)
        lambda_auth = authorizer_list[0]
        # Not sure this is returning properly either
        self.assertEqual(lambda_auth["AuthorizerType"], "REQUEST")
        # Verify authorizer URI contains expected components
        authorizer_uri = lambda_auth["AuthorizerUri"]
        self.assertIn("lambda:path/2015-03-31/functions", authorizer_uri)
        self.assertIn("MyAuthFn", authorizer_uri)
        self.assertIn("/invocations", authorizer_uri)

        # Same authorizer coming from the route and from the authorizers
        self.assertEqual(route["AuthorizerId"], lambda_auth["AuthorizerId"])
