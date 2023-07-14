import os.path

from parameterized import parameterized

from tests.validator.test_validator import TestValidatorBase

BASE_PATH = os.path.dirname(__file__)
INPUT_FOLDER = os.path.join(BASE_PATH, "input", "root")
OUTPUT_FOLDER = os.path.join(BASE_PATH, "output", "root")


class TestValidatorRoot(TestValidatorBase):
    @parameterized.expand(
        [
            "error_awstemplateformatversion_unknown",
            "error_empty_template",
            "error_minimal_template_with_parameters",
            "error_resources_empty",
            "error_resources_missing",
            "error_resources_not_object",
            "error_resources",
            "error_transform_empty",
        ],
    )
    def test_errors(self, template):
        self._test_validator_error(os.path.join(INPUT_FOLDER, template), os.path.join(OUTPUT_FOLDER, template))

    @parameterized.expand(
        [
            "success_minimal_template_with_parameters",
            "success_minimal_template",
        ],
    )
    def test_success(self, template):
        self._test_validator_success(os.path.join(INPUT_FOLDER, template))
