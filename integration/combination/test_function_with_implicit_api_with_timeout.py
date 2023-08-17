from unittest.case import skipIf

from integration.config.service_names import REST_API
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([REST_API]), "REST API is not supported in this testing region")
class TestFunctionWithImplicitApiWithTimeout(BaseTest):
    def test_function_with_implicit_api_with_timeout(self):
        self.create_and_verify_stack("combination/function_with_implicit_api_with_timeout")
