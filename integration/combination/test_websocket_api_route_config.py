from unittest.case import skipIf

from integration.config.service_names import WEBSOCKET_API
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([WEBSOCKET_API]), "WebSocketApi is not supported in this region")
class TestWebSocketApiRouteConfig(BaseTest):

    def test_websocket_api_route_config(self):
        """
        Checks API config parameters that are strings
        """
        self.create_and_verify_stack("combination/websocket_api_route_config")
        websocket_route_list = self.get_stack_resources("AWS::ApiGatewayV2::Route")
        self.assertEqual(len(websocket_route_list), 1)
        websocket_route_integ_list = self.get_stack_resources("AWS::ApiGatewayV2::Integration")
        self.assertEqual(len(websocket_route_integ_list), 1)
        websocket_route_perm_list = self.get_stack_resources("AWS::Lambda::Permission")
        self.assertEqual(len(websocket_route_perm_list), 1)
        api_id = self.get_stack_outputs()["ApiId"]
        api_2_client = self.client_provider.api_v2_client
        routes = api_2_client.get_routes(ApiId=api_id)["Items"]
        self.assertEqual(len(routes), 1)
        route = routes[0]
        self.assertEqual(route["RouteKey"], "$connect")
        self.assertEqual(route["ModelSelectionExpression"], "$request.body.modelType")
        self.assertEqual(route["OperationName"], "connect")
        self.assertIsNotNone(route["RequestParameters"].get("route.request.querystring.p1"))
        self.assertEqual(route["RouteResponseSelectionExpression"], "$default")
        integrations = api_2_client.get_integrations(ApiId=api_id)
        self.assertEqual(len(integrations["Items"]), 1)
        integration = integrations["Items"][0]
        self.assertEqual(integration["TimeoutInMillis"], 15000)
