import os.path
from typing import Dict, List
from unittest import TestCase

from pydantic import BaseModel
from pydantic.error_wrappers import ValidationError
from samtranslator.internal.schema_source.aws_serverless_connector import Properties as ConnectorProperties
from samtranslator.validator.resource_validator import to_model
from samtranslator.yaml_helper import yaml_parse

BASE_PATH = os.path.dirname(__file__)
CONNECTOR_INPUT_FOLDER = os.path.join(BASE_PATH, "input", "connector")


class Random(BaseModel):
    value: int


class Tag(BaseModel):
    A: str
    B: int


class Content(BaseModel):
    Tags: Tag


class Contents(BaseModel):
    Content: Content


class Properties(BaseModel):
    Key: Dict[str, Random]
    Hello: List[str]
    Random: Random


class ValidatiorBaseModel(BaseModel):
    Properties: Properties
    Contents: List[Contents]


class TestModel(TestCase):
    def setUp(self) -> None:
        self.connector_template = {
            "Source": {
                "Arn": "random-arn",
                "Type": "random-type",
            },
            "Destination": {"Id": "MyTable"},
            "Permissions": ["Read"],
        }

        self.model_template = {
            "Properties": {"Key": {"A": {"value": 10}}, "Hello": ["1", "2", "3"], "Random": {"value": 5}},
            "Contents": [
                {"Content": {"Tags": {"A": "hello", "B": 5}}},
                {"Content": {"Tags": {"A": "wow", "B": 10}}},
                {"Content": {"Tags": {"A": "no", "B": -5}}},
            ],
        }

    def test_connector_model_get_operation(self):
        connector_model = to_model(
            self.connector_template,
            ConnectorProperties,
        )
        self.assertEqual(connector_model.Source.Arn, "random-arn")
        self.assertEqual(connector_model.Source.Type, "random-type")
        self.assertEqual(connector_model.Source.Id, None)
        self.assertEqual(connector_model.Destination.Id, "MyTable")
        self.assertEqual(connector_model.Permissions, ["Read"])

    def test_model_get_operation(self):
        model = to_model(self.model_template, ValidatiorBaseModel)
        self.assertEqual(model.Properties.Key, {"A": {"value": 10}})
        self.assertEqual(model.Properties.Key["A"], {"value": 10})
        self.assertEqual(model.Properties.Hello, ["1", "2", "3"])
        self.assertEqual(model.Properties.Random.value, 5)

        self.assertEqual(len(model.Contents), 3)
        self.assertEqual(model.Contents[0].Content.Tags.A, "hello")
        self.assertEqual(model.Contents[0].Content.Tags.B, 5)
        self.assertEqual(model.Contents[1].Content.Tags.A, "wow")
        self.assertEqual(model.Contents[2].Content.Tags.B, -5)


class TestModelValidatorFailure(TestCase):
    def test_to_model_error_connector_template(self):
        manifest = yaml_parse(open(os.path.join(CONNECTOR_INPUT_FOLDER, "error_connector.yaml")))
        for _, resource in manifest["Resources"].items():
            properties = resource["Properties"]

            with self.assertRaisesRegex(
                ValidationError,
                "[1-9] validation error for Properties(.|\n)+(Source|Destination|Permissions)(.|\n)*(field required)|(unexpected value)|(str type expected)|(value is not a valid list).+",
            ):
                to_model(properties, ConnectorProperties)

    def test_to_model_test_base_model(self):
        invalid_model_template = {
            "Properties": {"Key": "123", "Hello": 5, "Random": {}},
            "Contents": [{"Content": {"Tags": {"A": "hello", "B": 5}}}, {"Content": {"Tags": {"A": "wow"}}}],
        }

        with self.assertRaisesRegex(
            ValidationError,
            "[1-9] validation error for TestBaseModel(.|\n)+(Contents)(.|\n)*(field required)|(unexpected value)|(str type expected)|(value is not a valid list).+",
        ):
            to_model(invalid_model_template, ValidatiorBaseModel)
