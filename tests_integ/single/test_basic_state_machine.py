from parameterized import parameterized
from tests_integ.helpers.base_test import BaseTest


class TestBasicLayerVersion(BaseTest):
    @parameterized.expand(
        [
            "basic_state_machine_inline_definition",
            # ("basic_state_machine_with_tags"), # cannot be translated by sam-tran
        ]
    )
    def test_basic_state_machine(self, file_name):
        self.create_and_verify_stack(file_name)
