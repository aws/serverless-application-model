import os.path
from parameterized import parameterized
from tests.validator.test_validator import TestValidatorBase

BASE_PATH = os.path.dirname(__file__)
INPUT_FOLDER = os.path.join(BASE_PATH, "input", "simpletable")
OUTPUT_FOLDER = os.path.join(BASE_PATH, "output", "simpletable")


class TestValidatorSimpleTable(TestValidatorBase):
    @parameterized.expand(
        [
            "error_primarykey",
            "error_provisionedthroughput",
            "error_ssespecification",
            "error_tablename",
        ],
    )
    def test_errors(self, template):
        self._test_validator_error(os.path.join(INPUT_FOLDER, template), os.path.join(OUTPUT_FOLDER, template))

    @parameterized.expand(
        ["success_complete_simpletable", "success_minimal_simpletable", "success_resource_attributes"],
    )
    def test_success(self, template):
        self._test_validator_success(os.path.join(INPUT_FOLDER, template))
