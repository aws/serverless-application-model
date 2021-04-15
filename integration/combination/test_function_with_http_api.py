from integration.helpers.base_test import BaseTest


class TestFunctionWithHttpApi(BaseTest):
    def test_function_with_http_api(self):
        self.create_and_verify_stack("combination/function_with_http_api")

        stack_outputs = self.get_stack_outputs()
        base_url = stack_outputs["ApiUrl"]
        self.verify_get_request_response(base_url + "some/path", 200)
        self.verify_get_request_response(base_url + "something", 404)
        self.verify_get_request_response(base_url + "another/endpoint", 404)
