from unittest.case import skipIf

from integration.config.service_names import WEBSOCKET_API
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([WEBSOCKET_API]), "WebSocketApi is not supported in this region")
class TestWebSocketApiStageConfig(BaseTest):

    def test_websocket_api_stage_config(self):
        """
        Checks API config parameters that are strings
        """
        self.create_and_verify_stack("combination/websocket_api_stage_config")
        stages = self.get_api_v2_stack_stages()
        self.assertEqual(len(stages), 1)
        stage = stages[0]
        self.assertEqual(stage["StageName"], "Prod")
        self.assertEqual(stage["StageVariables"], {"var1": "val1", "var2": "val2"})
        self.assertIsNotNone(stage["Tags"].get("t1"))
        self.assertIsNotNone(stage["Tags"].get("t2"))
