import os

from parameterized import parameterized
from tests_integ.helpers.base_test import BaseTest

class TestBasicApi(BaseTest):
    @parameterized.expand([
        ("basic_api_inline_openapi"),
        ("basic_api_inline_swagger"),
        # These three require a template replacement of ${definitionuri}
        # ("basic_api_with_cache"),
        # ("basic_api_with_tags"),
        # ("basic_api.yaml"),
    ])
    def test_basic_api(self, file_name):
        self.create_and_verify_stack(file_name)
