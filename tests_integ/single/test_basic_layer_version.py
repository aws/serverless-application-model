from parameterized import parameterized

from tests_integ.helpers.base_test import BaseTest


class TestBasicLayerVersion(BaseTest):
    @parameterized.expand(
        [
            "basic_layer",
            "basic_layer_with_parameters",
        ]
    )
    def test_basic_layer_version(self, file_name):
        self.create_and_verify_stack(file_name)
