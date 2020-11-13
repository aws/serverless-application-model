import os

from parameterized import parameterized
from tests_integ.helpers.base_test import BaseTest

class TestBasicApplication(BaseTest):
    @parameterized.expand([
        ("basic_application_sar_location"),
        ("basic_application_sar_location_with_intrinsics"),
    ])
    def test_basic_application(self, file_name):
        self.create_and_verify_stack(file_name)
