import os.path
from parameterized import parameterized
import pytest
from unittest import TestCase
from samtranslator.yaml_helper import yaml_parse
from samtranslator.validator.validator import SamTemplateValidator
from tests.validator.test_validator import TestValidatorBase

BASE_PATH = os.path.dirname(__file__)
INPUT_FOLDER = os.path.join(BASE_PATH, "input", "root")
OUTPUT_FOLDER = os.path.join(BASE_PATH, "output", "root")


class TestValidatorRoot(TestValidatorBase):
    @parameterized.expand(
        [
            "error_empty_template",
            "error_resources_empty",
            "error_resources_missing",
            "error_resources_not_object",
            "error_transform_missing",
            "error_resources_one_empty",
            "error_resources_one_missing_type_element",
            "error_transform_unknown",
            "error_awstemplateformatversion_unknown",
        ],
    )
    def test_validator_root_errors(self, template):
        self._test_validator_error(os.path.join(INPUT_FOLDER, template), os.path.join(OUTPUT_FOLDER, template))

    @parameterized.expand(
        [
            "success_minimum_template",
        ],
    )
    def test_validator_root_success(self, template):
        self._test_validator_success(os.path.join(INPUT_FOLDER, template))
