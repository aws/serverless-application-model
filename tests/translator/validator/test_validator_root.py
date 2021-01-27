import os.path
from parameterized import parameterized
import pytest
from unittest import TestCase
from samtranslator.yaml_helper import yaml_parse
from samtranslator.validator.validator import SamTemplateValidator
from tests.translator.validator.test_validator import TestValidatorBase

BASE_PATH = os.path.dirname(__file__)
INPUT_FOLDER = os.path.join(BASE_PATH, os.pardir, "input", "root")


class TestValidatorRoot(TestValidatorBase):
    @parameterized.expand(
        [
            "minimum_valid_api_template",
        ],
    )
    def test_validator_root_success(self, template):
        self._test_validator_success(os.path.join(INPUT_FOLDER, template))

    @parameterized.expand(
        [
            ("error_empty_template", ["Must not be empty (/)"]),
            (
                "error_resources_missing",
                ["'Resources' is a required property (/)"],
            ),
            ("error_resources_empty", ["Must not be empty (/Resources)"]),
            ("error_resources_not_object", ["3 is not of type 'object' (/Resources)"]),
            (
                "error_transform_missing",
                ["'Transform' is a required property (/)"],
            ),
            (
                "error_transform_unknown",
                ["'AWS::Serverless-2021-01-26' is not one of ['AWS::Serverless-2016-10-31'] (/Transform)"],
            ),
            (
                "error_awstemplateformatversion_unknown",
                ["'2021-01-26' is not one of ['2010-09-09'] (/AWSTemplateFormatVersion)"],
            ),
        ],
    )
    def test_validator_root_error(self, template, errors):
        self._test_validator_error(os.path.join(INPUT_FOLDER, template), errors)
