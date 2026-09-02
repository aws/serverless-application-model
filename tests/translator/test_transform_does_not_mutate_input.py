import copy
from unittest import TestCase
from unittest.mock import MagicMock, patch

from samtranslator.translator.transform import transform


def _managed_policy_loader():
    loader = MagicMock()
    loader.load.return_value = {
        "AWSLambdaBasicExecutionRole": "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
    }
    return loader


def _transform(template, parameter_values=None):
    if parameter_values is None:
        parameter_values = {}
    with patch("boto3.session.Session.region_name", "us-east-1"):
        return transform(template, parameter_values, _managed_policy_loader())


FUNCTION_PROPERTIES = {
    "CodeUri": "s3://bucket/key",
    "Handler": "index.handler",
    "Runtime": "python3.11",
}

TEMPLATE_WITH_GLOBALS = {
    "Transform": "AWS::Serverless-2016-10-31",
    "Globals": {"Function": {"Timeout": 30}},
    "Resources": {"Fn": {"Type": "AWS::Serverless::Function", "Properties": dict(FUNCTION_PROPERTIES)}},
}

TEMPLATE_WITH_API_EVENT = {
    "Transform": "AWS::Serverless-2016-10-31",
    "Resources": {
        "Fn": {
            "Type": "AWS::Serverless::Function",
            "Properties": {
                **FUNCTION_PROPERTIES,
                "Events": {"Api": {"Type": "Api", "Properties": {"Path": "/x", "Method": "get"}}},
            },
        }
    },
}


TEMPLATE_WITH_EXPLICIT_API = {
    "Transform": "AWS::Serverless-2016-10-31",
    "Resources": {
        "Fn": {
            "Type": "AWS::Serverless::Function",
            "Properties": {
                **FUNCTION_PROPERTIES,
                "Events": {
                    "Api": {
                        "Type": "Api",
                        "Properties": {"Path": "/x", "Method": "get", "RestApiId": {"Ref": "Api"}},
                    }
                },
            },
        },
        "Api": {"Type": "AWS::Serverless::Api", "Properties": {"StageName": "prod"}},
    },
}

TEMPLATE_WITH_EXPLICIT_HTTP_API = {
    "Transform": "AWS::Serverless-2016-10-31",
    "Resources": {
        "Fn": {
            "Type": "AWS::Serverless::Function",
            "Properties": {
                **FUNCTION_PROPERTIES,
                "Events": {
                    "Http": {
                        "Type": "HttpApi",
                        "Properties": {"Path": "/x", "Method": "get", "ApiId": {"Ref": "Api"}},
                    }
                },
            },
        },
        "Api": {"Type": "AWS::Serverless::HttpApi", "Properties": {"StageName": "prod"}},
    },
}


class TestTransformDoesNotMutateInput(TestCase):
    def test_globals_template_is_not_modified(self):
        template = copy.deepcopy(TEMPLATE_WITH_GLOBALS)
        expected = copy.deepcopy(template)

        _transform(template)

        # The Globals section used to be deleted from the caller's template, and the
        # merged Timeout written into the caller's resource properties.
        self.assertEqual(template, expected)

    def test_api_event_template_is_not_modified(self):
        template = copy.deepcopy(TEMPLATE_WITH_API_EVENT)
        expected = copy.deepcopy(template)

        _transform(template)

        self.assertEqual(template, expected)

    def test_explicit_api_template_is_not_modified(self):
        template = copy.deepcopy(TEMPLATE_WITH_EXPLICIT_API)
        expected = copy.deepcopy(template)

        _transform(template)

        # The generated DefinitionBody used to be written into the caller's
        # AWS::Serverless::Api resource.
        self.assertEqual(template, expected)

    def test_parameter_values_are_not_modified(self):
        # to_py27_compatible_template() used to replace parameter_values' entries
        # in place with Py27UniStr/Py27Dict/Py27LongInt wrappers -- caller-visible
        # via a different __repr__ and, for dicts, Python 2 hash-order iteration --
        # even though it only runs for templates with an API resource.
        template = copy.deepcopy(TEMPLATE_WITH_EXPLICIT_API)
        parameter_values = {"StageName": "prod", "Count": 3, "Tags": {"a": 1, "b": 2}}
        expected = copy.deepcopy(parameter_values)

        _transform(template, parameter_values)

        self.assertEqual(parameter_values, expected)
        self.assertIs(type(parameter_values["StageName"]), str)
        self.assertIs(type(parameter_values["Count"]), int)
        self.assertIs(type(parameter_values["Tags"]), dict)

    def test_transforming_the_same_template_twice_gives_the_same_result(self):
        # Transforming the same object twice used to raise InvalidDocumentException:
        # 'API method "get" defined multiple times for path "/x"', because the first
        # transform left its own generated DefinitionBody in the caller's template.
        for name, template in [
            ("rest api", TEMPLATE_WITH_EXPLICIT_API),
            ("http api", TEMPLATE_WITH_EXPLICIT_HTTP_API),
        ]:
            with self.subTest(name):
                reused = copy.deepcopy(template)

                first = _transform(reused)
                second = _transform(reused)

                self.assertEqual(first, second)
