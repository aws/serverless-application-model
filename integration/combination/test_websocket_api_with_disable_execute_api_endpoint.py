from unittest.case import skipIf

from parameterized import parameterized

from integration.config.service_names import WEBSOCKET_API
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([WEBSOCKET_API]), "WebSocketApi is not supported in this region")
class TestWebSocketApiWithDisableExecuteApiEndpoint(BaseTest):
    @parameterized.expand([True, False])
    def test_disable_execute_api_endpoint_true(self, is_disable):
        parameters = [
            {
                "ParameterKey": "DisableExecuteApiEndpointValue",
                "ParameterValue": "true" if is_disable else "false",
                "UsePreviousValue": False,
                "ResolvedValue": "string",
            }
        ]

        self.create_and_verify_stack("combination/websocket_api_with_disable_execute_api_endpoint", parameters)
        api_2_client = self.client_provider.api_v2_client
        api_id = self.get_stack_outputs()["ApiId"]
        api_result = api_2_client.get_api(ApiId=api_id)
        self.assertEqual(api_result["DisableExecuteApiEndpoint"], is_disable)
