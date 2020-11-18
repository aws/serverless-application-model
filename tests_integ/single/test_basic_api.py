from parameterized import parameterized
from tests_integ.helpers.base_test import BaseTest


class TestBasicApi(BaseTest):
    @parameterized.expand(
        [
            "basic_api_inline_openapi",
            "basic_api_inline_swagger",
            "basic_api_with_tags",
            "basic_api",
        ]
    )
    def test_basic_api(self, file_name):
        self.create_and_verify_stack(file_name)
