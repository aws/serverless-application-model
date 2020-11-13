from parameterized import parameterized

from tests_integ.helpers.base_test import BaseTest


class TestBasicHttpApi(BaseTest):
    @parameterized.expand([
        "basic_http_api",
    ])
    def test_basic_http_api(self, file_name):
        self.create_and_verify_stack(file_name)
