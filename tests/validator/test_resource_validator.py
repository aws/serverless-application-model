import os.path
from unittest import TestCase

from pydantic.error_wrappers import ValidationError
from samtranslator.validator.resource_validator import to_resource_model
from samtranslator.yaml_helper import yaml_parse
from schema_source.aws_serverless_connector import Properties as ConnectorProperties

BASE_PATH = os.path.dirname(__file__)
CONNECTOR_INPUT_FOLDER = os.path.join(BASE_PATH, "input", "connector")


class TestResourceModel(TestCase):
    def setUp(self) -> None:
        self.connector_template = {
            "Source": {
                "Arn": "random-arn",
                "Type": "random-type",
            },
            "Destination": {"Id": "MyTable"},
            "Permissions": ["Read"],
        }

    def test_resource_model_get(self):
        connector_model = to_resource_model(
            self.connector_template,
            ConnectorProperties,
        )
        self.assertEqual(connector_model.get("Source").get("Arn"), "random-arn")
        self.assertEqual(connector_model.get("Source").get("Type"), "random-type")
        self.assertEqual(connector_model.get("Source").get("Id"), None)
        self.assertEqual(connector_model.get("Destination").get("Id"), "MyTable")
        self.assertEqual(connector_model.get("Permissions"), ["Read"])
        self.assertEqual(connector_model.get("FakeProperty"), None)

        self.assertEqual(connector_model["Source"]["Arn"], "random-arn")
        self.assertEqual(connector_model["Source"]["Type"], "random-type")
        self.assertEqual(connector_model["Destination"]["Id"], "MyTable")
        self.assertEqual(connector_model["Permissions"], ["Read"])


class TestResourceValidatorFailure(TestCase):
    def test_to_resource_model_error_connector_template(self):
        manifest = yaml_parse(open(os.path.join(CONNECTOR_INPUT_FOLDER, "error_connector.yaml")))
        for _, resource in manifest["Resources"].items():
            properties = resource["Properties"]

            with self.assertRaisesRegex(
                ValidationError,
                "[1-9] validation error for Properties(.|\n)+(Source|Destination|Permissions)(.|\n)*(field required)|(unexpected value)|(str type expected)|(value is not a valid list).+",
            ):
                to_resource_model(properties, ConnectorProperties)
