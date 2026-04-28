from unittest.case import skipIf

from integration.config.service_names import WEBSOCKET_API
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([WEBSOCKET_API]), "WebSocketApi is not supported in this region")
class TestWebSocketApiRouteSettings(BaseTest):
    def test_websocket_api_route_settings(self):
        """
        Verifies that RouteSettings with specific route keys deploys successfully.
        This test ensures Stage has DependsOn for routes.
        """
        self.create_and_verify_stack("combination/websocket_api_route_settings")

        stages = self.get_api_v2_stack_stages()
        self.assertEqual(len(stages), 1)
        stage = stages[0]
        self.assertIsNotNone(stage.get("RouteSettings"))
