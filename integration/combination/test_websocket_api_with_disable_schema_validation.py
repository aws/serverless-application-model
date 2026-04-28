from unittest.case import skipIf

from parameterized import parameterized

from integration.config.service_names import WEBSOCKET_API
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([WEBSOCKET_API]), "WebSocketApi is not supported in this region")
class TestWebSocketApiDisableSchemaValidation(BaseTest):
    @parameterized.expand([True, False])
    def test_disable_schema_validation(self, is_disable):
        parameters = [
            {
                "ParameterKey": "DisableSchemaValidationValue",
                "ParameterValue": "true" if is_disable else "false",
                "UsePreviousValue": False,
                "ResolvedValue": "string",
            }
        ]
        self.create_and_verify_stack("combination/websocket_api_with_disable_schema_validation", parameters)
        websocket_api_list = self.get_stack_resources("AWS::ApiGatewayV2::Api")
        self.assertEqual(len(websocket_api_list), 1)
        # API Gateway SDK for some reason doesn't return the disableSchemaValidation
        # property when getting the API, so we just check that there were no errors
        # during the creation, but we can't check that it was properly applied
