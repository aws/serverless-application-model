from unittest.case import skipIf

from integration.config.service_names import WEBSOCKET_API
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([WEBSOCKET_API]), "WebSocketApi is not supported in this region")
class TestWebSocketApiBasic(BaseTest):

    def test_websocket_api_basic(self):
        """
        Creates a Basic WebSocket API
        """
        # Validates list of generated resources is same as expected
        self.create_and_verify_stack("combination/websocket_api_basic")

        stages = self.get_api_v2_stack_stages()

        self.assertEqual(len(stages), 1)
        self.assertEqual(stages[0]["StageName"], "default")

        api_id = self.get_stack_outputs()["ApiId"]
        api_2_client = self.client_provider.api_v2_client

        routes = api_2_client.get_routes(ApiId=api_id)["Items"]
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0]["RouteKey"], "$default")

        integrations = api_2_client.get_integrations(ApiId=api_id)["Items"]
        self.assertEqual(len(integrations), 1)

    def test_websocket_api_basic_config(self):
        """
        Checks API config parameters that are strings
        """
        self.create_and_verify_stack("combination/websocket_api_basic_config")
        websocket_api_list = self.get_stack_resources("AWS::ApiGatewayV2::Api")
        self.assertEqual(len(websocket_api_list), 1)

        websocket_resource = websocket_api_list[0]
        websocket_api_id = websocket_resource["PhysicalResourceId"]
        api_v2_client = self.client_provider.api_v2_client
        api_configuration = api_v2_client.get_api(ApiId=websocket_api_id)
        properties_to_check = {
            "ApiKeySelectionExpression": "$request.header.x-api-key",
            "Description": "Toy API",
            "DisableExecuteApiEndpoint": False,
            "Name": "MyApiName",
            "ProtocolType": "WEBSOCKET",
            "RouteSelectionExpression": "$request.body.action",
        }
        for key, value in properties_to_check.items():
            self.assertEqual(api_configuration[key], value)
        # assert custom tags are present
        # CFN and SAM tags also exist, so we can't check equality of the full list
        self.assertEqual(api_configuration["Tags"].get("t1"), "v1")
        self.assertEqual(api_configuration["Tags"].get("t2"), "v2")
