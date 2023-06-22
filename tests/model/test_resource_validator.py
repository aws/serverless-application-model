from unittest import TestCase

from samtranslator.internal.schema_source.aws_serverless_connector import Properties as ConnectorProperties
from samtranslator.internal.schema_source.aws_serverless_function import Properties as FunctionProperties
from samtranslator.model.exceptions import InvalidResourceException
from samtranslator.model.sam_resources import (
    SamConnector,
    SamFunction,
)


class TestResourceValidator(TestCase):
    def setUp(self) -> None:
        self.connector = SamConnector("foo")
        self.connector.Source = {
            "Arn": "random-arn",
            "Type": "random-type",
        }
        self.connector.Destination = {"Id": "MyTable"}
        self.connector.Permissions = ["Read"]

        self.function = SamFunction("function")
        self.function.CodeUri = "s3://foobar/foo.zip"
        self.function.Runtime = "foo"
        self.function.Handler = "bar"
        self.function.FunctionUrlConfig = {"Cors": {"AllowOrigins": ["example1.com"]}, "AuthType": "123"}
        self.function.Events = {
            "MyMqEvent": {
                "Type": "MQ",
                "Properties": {
                    "Broker": {"Fn::GetAtt": "MyMqBroker.Arn"},
                    "Queues": ["TestQueue"],
                    "SourceAccessConfigurations": [{"Type": "BASIC_AUTH"}],
                },
            }
        }

    def test_connector_model(self):
        connector_model = self.connector.validate_properties_and_return_model(
            ConnectorProperties,
        )
        self.assertEqual(connector_model.Source.Arn, "random-arn")
        self.assertEqual(connector_model.Source.Type, "random-type")
        self.assertEqual(connector_model.Source.Id, None)
        self.assertEqual(connector_model.Destination.Id, "MyTable")
        self.assertEqual(connector_model.Permissions, ["Read"])

    def test_lambda_model(self):
        model = self.function.validate_properties_and_return_model(FunctionProperties)
        self.assertEqual(model.CodeUri, "s3://foobar/foo.zip")
        self.assertEqual(model.Runtime, "foo")
        self.assertEqual(model.Handler, "bar")
        self.assertEqual(model.FunctionUrlConfig.Cors, {"AllowOrigins": ["example1.com"]})
        self.assertEqual(model.FunctionUrlConfig.AuthType, "123")
        self.assertEqual(model.Events["MyMqEvent"].Type, "MQ")
        self.assertEqual(model.Events["MyMqEvent"].Properties.Broker, {"Fn::GetAtt": "MyMqBroker.Arn"})
        self.assertEqual(model.Events["MyMqEvent"].Properties.Queues, ["TestQueue"])
        self.assertEqual(model.Events["MyMqEvent"].Properties.SourceAccessConfigurations, [{"Type": "BASIC_AUTH"}])


class TestResourceValidatorFailure(TestCase):
    def test_connector_with_empty_properties(self):
        invalid_connector = SamConnector("foo")
        with self.assertRaises(
            InvalidResourceException,
        ):
            invalid_connector.validate_properties_and_return_model(ConnectorProperties)
            self.assertRegex(".+Given resource property '(Source|Destination|Permissions)'.+ is invalid.")

    def test_connector_without_source(self):
        invalid_connector = SamConnector("foo")
        invalid_connector.Destination = {"Id": "MyTable"}
        invalid_connector.Permissions = ["Read"]
        with self.assertRaises(
            InvalidResourceException,
        ):
            invalid_connector.validate_properties_and_return_model(ConnectorProperties)
            self.assertRegex(".+Property 'Source'.+ is invalid.")

    def test_connector_with_invalid_permission(self):
        invalid_connector = SamConnector("foo")
        invalid_connector.Source = {"Id": "MyTable"}
        invalid_connector.Destination = {"Id": "MyTable"}
        invalid_connector.Permissions = ["Invoke"]
        with self.assertRaises(
            InvalidResourceException,
        ):
            invalid_connector.validate_properties_and_return_model(ConnectorProperties)
            self.assertRegex(".+Property 'Permissions'.+ is invalid.")

    def test_connector_with_invalid_permission_type(self):
        invalid_connector = SamConnector("foo")
        invalid_connector.Source = {"Id": "MyTable"}
        invalid_connector.Destination = {"Id": "MyTable"}
        invalid_connector.Permissions = {"Hello": "World"}
        with self.assertRaises(
            InvalidResourceException,
        ):
            invalid_connector.validate_properties_and_return_model(ConnectorProperties)
            self.assertRegex(".+Property 'Permissions'.+ is invalid.")
