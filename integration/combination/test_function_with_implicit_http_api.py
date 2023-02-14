from unittest.case import skipIf

from integration.config.service_names import HTTP_API
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([HTTP_API]), "HttpApi is not supported in this testing region")
class TestFunctionWithImplicitHttpApi(BaseTest):
    def test_function_with_implicit_api(self):
        self.create_and_verify_stack("combination/function_with_implicit_http_api")

        stack_outputs = self.get_stack_outputs()
        base_url = stack_outputs["ApiUrl"]
        self.verify_get_request_response(base_url, 200)
        self.verify_get_request_response(base_url + "something", 200)
        self.verify_get_request_response(base_url + "another/endpoint", 200)
