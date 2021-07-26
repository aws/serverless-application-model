from integration.helpers.base_test import BaseTest


class TestFunctionWithImplicitHttpApi(BaseTest):
    def test_function_with_implicit_api(self):
        self.create_and_verify_stack("combination/function_with_implicit_http_api")

        stack_outputs = self.get_stack_outputs()
        base_url = stack_outputs["ApiUrl"]
        self.verify_get_request_response(base_url, 200)
        self.verify_get_request_response(base_url + "something", 200)
        self.verify_get_request_response(base_url + "another/endpoint", 200)
