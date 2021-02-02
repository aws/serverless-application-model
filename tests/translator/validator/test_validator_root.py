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
            ("error_empty_template", ["[/] Must not be empty"]),
            ("error_resources_missing", ["[/] 'Resources' is a required property"]),
            ("error_resources_empty", ["[/Resources] Must not be empty"]),
            ("error_resources_not_object", ["[/Resources] 3 is not of type 'object'"]),
            ("error_transform_missing", ["[/] 'Transform' is a required property"]),
            (
                "error_resources_one_empty",
                ["[/Resources/MyApi] Is not valid", "[/__/] Must not be empty"],
            ),
            (
                "error_resources_one_missing_type_element",
                [
                    "[/Resources/MyApi] Is not valid",
                    "[/__/] 'Type' is a required property",
                ],
            ),
            (
                "error_transform_unknown",
                ["[/Transform] 'AWS::Serverless-2021-01-26' is not one of ['AWS::Serverless-2016-10-31']"],
            ),
            (
                "error_awstemplateformatversion_unknown",
                ["[/AWSTemplateFormatVersion] '2021-01-26' is not one of ['2010-09-09']"],
            ),
            ("success_minimum_template", []),
        ],
    )
    def test_validator_root(self, template, errors):
        self._test_validator(os.path.join(INPUT_FOLDER, template), errors)
