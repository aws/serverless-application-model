import logging
from unittest.case import skipIf

import pytest

from integration.config.service_names import HTTP_API
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support

LOG = logging.getLogger(__name__)


@skipIf(current_region_does_not_support([HTTP_API]), "HttpApi is not supported in this testing region")
class TestFunctionWithHttpApi(BaseTest):
    @pytest.mark.flaky(reruns=5)
    def test_function_with_http_api(self):
        self.create_and_verify_stack("combination/function_with_http_api")

        stack_outputs = self.get_stack_outputs()
        base_url = stack_outputs["ApiUrl"]
        self.verify_get_request_response(base_url + "some/path", 200)
        self.verify_get_request_response(base_url + "something", 404)
        self.verify_get_request_response(base_url + "another/endpoint", 404)

    def test_function_with_http_api_default_path(self):
        self.create_and_verify_stack("combination/function_with_http_api_default_path")

        stack_outputs = self.get_stack_outputs()
        base_url = stack_outputs["ApiUrl"]
        # The $default route catches requests that don't explicitly match other routes
        self.verify_get_request_response(base_url, 200)
        self.verify_get_request_response(base_url + "something", 200)
