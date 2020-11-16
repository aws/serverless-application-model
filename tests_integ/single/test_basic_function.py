import os

from parameterized import parameterized
from tests_integ.helpers.base_test import BaseTest


class TestBasicFunction(BaseTest):
    @parameterized.expand(
        [
            "basic_function",
            "basic_function_event_destinations",
            "basic_function_no_envvar",
            "basic_function_openapi",
            "basic_function_with_kmskeyarn",
            "basic_function_with_sns_dlq",
            "basic_function_with_sqs_dlq",
            "basic_function_with_tags",
            # ("basic_function_with_tracing"), # need different set up to create changeset
            # ("basic_table_no_param"), # no test case in java code base
            # ("basic_table_with_param") # no test case in java code base
        ]
    )
    def test_basic_function(self, file_name):
        self.create_and_verify_stack(file_name)
