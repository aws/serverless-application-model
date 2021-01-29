import os.path
from parameterized import parameterized
import pytest
from unittest import TestCase
from samtranslator.yaml_helper import yaml_parse
from samtranslator.validator.validator import SamTemplateValidator
from tests.translator.validator.test_validator import TestValidatorBase

BASE_PATH = os.path.dirname(__file__)
INPUT_FOLDER = os.path.join(BASE_PATH, os.pardir, "input", "api")


class TestValidatorApi(TestValidatorBase):
    @parameterized.expand(
        [
            (
                "error_accesslogsetting_empty",
                [
                    "[/Resources/MyApi] {'Type': 'AWS::Serverless::Api', 'Properties': {'StageName': 'Stage name', 'AccessLogSetting': None}} is not valid. Context: None is not of type 'object'"
                ],
            ),
            (
                "error_accesslogsetting_destinationarn_not_string",
                [
                    "[/Resources/MyApi] {'Type': 'AWS::Serverless::Api', 'Properties': {'AccessLogSetting': {'DestinationArn': 3, 'Format': 'format'}, 'StageName': 'Stage name'}} is not valid. Context: 3 is not of type 'string'"
                ],
            ),
            (
                "error_accesslogsetting_format_not_string",
                [
                    "[/Resources/MyApi] {'Type': 'AWS::Serverless::Api', 'Properties': {'AccessLogSetting': {'DestinationArn': 'destination arn', 'Format': 3}, 'StageName': 'Stage name'}} is not valid. Context: 3 is not of type 'string'"
                ],
            ),
            (
                "error_accesslogsetting_unknown_property",
                [
                    "[/Resources/MyApi] {'Type': 'AWS::Serverless::Api', 'Properties': {'AccessLogSetting': {'DestinationArn': 'destination arn', 'Format': 'format', 'Unknown': 'Value'}, 'StageName': 'Stage name'}} is not valid. Context: Additional properties are not allowed ('Unknown' was unexpected)"
                ],
            ),
            (
                "error_empty_properties",
                [
                    "[/Resources/MyApi] {'Type': 'AWS::Serverless::Api', 'Properties': None} is not valid. Context: None is not of type 'object'"
                ],
            ),
            (
                "error_missing_properties_element",
                [
                    "[/Resources/MyApi] {'Type': 'AWS::Serverless::Api'} is not valid. Context: 'Properties' is a required property"
                ],
            ),
            (
                "error_missing_stagename",
                [
                    "[/Resources/MyApi] {'Type': 'AWS::Serverless::Api', 'Properties': {'CacheClusterSize': '32'}} is not valid. Context: 'StageName' is a required property"
                ],
            ),
            (
                "success_minimum_api",
                [],
            ),
        ],
    )
    def test_validator_api(self, template, errors):
        self._test_validator(os.path.join(INPUT_FOLDER, template), errors)
