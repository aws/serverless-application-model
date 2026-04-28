from unittest.case import skipIf

from integration.config.service_names import WEBSOCKET_API
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([WEBSOCKET_API]), "WebSocketApi is not supported in this region")
class TestWebSocketApiMultiple(BaseTest):

    def test_websocket_multi_api(self):
        self.create_and_verify_stack("combination/websocket_api_multiple_api")

    def test_websocket_multi_route(self):
        self.create_and_verify_stack("combination/websocket_api_multiple_routes")
