import os

from parameterized import parameterized
from tests_integ.helpers.base_test import BaseTest

class TestBasicFunction(BaseTest):
    @parameterized.expand([
        ("basic_function"),
        ("basic_function_event_destinations")
    ])
    def test_basic_function(self, file_name):
        self.create_and_verify_stack(file_name)
