from parameterized import parameterized

from integration.helpers.base_test import BaseTest


class TestHttpApiWithDisableExecuteApiEndpoint(BaseTest):
    @parameterized.expand(
        [
            ("combination/http_api_with_disable_execute_api_endpoint_true", True),
            ("combination/http_api_with_disable_execute_api_endpoint_false", False),
        ]
    )
    def test_disable_execute_api_endpoint_true(self, file_name, is_disable):
        self.create_and_verify_stack(file_name)
        api_2_client = self.client_provider.api_v2_client
        api_id = self.get_stack_outputs()["ApiId"]
        api_result = api_2_client.get_api(ApiId=api_id)
        self.assertEqual(api_result["DisableExecuteApiEndpoint"], is_disable)
