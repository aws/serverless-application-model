import json
import itertools
import os.path
from functools import reduce

from samtranslator.translator.translator import Translator, prepare_plugins, make_policy_template_for_function_plugin
from samtranslator.parser.parser import Parser
from samtranslator.model.exceptions import InvalidDocumentException
from samtranslator.model import Resource
from samtranslator.model.sam_resources import SamSimpleTable
from samtranslator.public.plugins import BasePlugin

from tests.translator.helpers import get_template_parameter_values
from tests.translator.yaml_helper import yaml_parse
from parameterized import parameterized, param

import pytest
import yaml
from unittest import TestCase
from samtranslator.translator.transform import transform
from mock import Mock, MagicMock, patch


input_folder = 'tests/translator/input'
output_folder = 'tests/translator/output'


def deep_sorted(value):
    if isinstance(value, dict):
        return {k: deep_sorted(v) for k, v in value.items()}
    if isinstance(value, list):
        return sorted(deep_sorted(x) for x in value)
    else:
        return value

# implicit_api, explicit_api, explicit_api_ref, api_cache tests currently have deployment IDs hardcoded in output file.
# These ids are generated using sha1 hash of the swagger body for implicit
# api and s3 location for explicit api.

class TestTranslatorEndToEnd(TestCase):

    @parameterized.expand(
      itertools.product([
        'basic_function',
        'cloudwatchevent',
        'cloudwatch_logs_with_ref',
        'cloudwatchlog',
        'streams',
        'simpletable',
        'implicit_api',
        'explicit_api',
        'api_endpoint_configuration',
        'api_with_method_settings',
        'api_with_binary_media_types',
        'api_with_resource_refs',
        'api_with_cors',
        'api_with_cors_and_only_methods',
        'api_with_cors_and_only_headers',
        'api_with_cors_and_only_origins',
        'api_with_cors_and_only_maxage',
        'api_cache',
        's3',
        's3_create_remove',
        's3_existing_lambda_notification_configuration',
        's3_existing_other_notification_configuration',
        's3_filter',
        's3_multiple_events_same_bucket',
        's3_multiple_functions',
        'sns',
        'sns_existing_other_subscription',
        'sns_topic_outside_template',
        'alexa_skill',
        'iot_rule',
        'function_managed_inline_policy',
        'unsupported_resources',
        'intrinsic_functions',
        'basic_function_with_tags',
        'depends_on',
        'function_with_dlq',
        'function_with_kmskeyarn',
        'function_with_alias',
        'function_with_alias_intrinsics',
        'function_with_disabled_deployment_preference',
        'function_with_deployment_preference',
        'function_with_deployment_preference_all_parameters',
        'function_with_deployment_preference_multiple_combinations',
        'function_with_alias_and_event_sources',
        'function_with_resource_refs',
        'function_with_deployment_and_custom_role',
        'function_with_deployment_no_service_role',
        'function_with_policy_templates',
        'globals_for_function',
        'globals_for_api',
        'all_policy_templates',
        'simple_table_ref_parameter_intrinsic',
        'simple_table_with_table_name',
        'function_concurrency',
        'simple_table_with_extra_tags',
        'explicit_api_with_invalid_events_config',
        'no_implicit_api_with_serverless_rest_api_resource',
        'implicit_api_with_serverless_rest_api_resource'
      ],
      [
       ("aws", "ap-southeast-1"),
       ("aws-cn", "cn-north-1"),
       ("aws-us-gov", "us-gov-west-1")
      ] # Run all the above tests against each of the list of partitions to test against
      )
    )
    def test_transform_success(self, testcase, partition_with_region):
        partition = partition_with_region[0]
        region = partition_with_region[1]

        manifest = yaml_parse(open(os.path.join(input_folder, testcase + '.yaml'), 'r'))
        # To uncover unicode-related bugs, convert dict to JSON string and parse JSON back to dict
        manifest = json.loads(json.dumps(manifest))
        partition_folder = partition if partition != "aws" else ""
        expected = json.load(open(os.path.join(output_folder,partition_folder, testcase + '.json'), 'r'))

        old_region = os.environ.get("AWS_DEFAULT_REGION", "")
        os.environ["AWS_DEFAULT_REGION"] = region

        try:
            parameter_values = get_template_parameter_values()
            mock_policy_loader = MagicMock()
            mock_policy_loader.load.return_value = {
                'AWSLambdaBasicExecutionRole': 'arn:{}:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'.format(partition),
                'AmazonDynamoDBFullAccess': 'arn:{}:iam::aws:policy/AmazonDynamoDBFullAccess'.format(partition),
                'AmazonDynamoDBReadOnlyAccess': 'arn:{}:iam::aws:policy/AmazonDynamoDBReadOnlyAccess'.format(partition),
                'AWSLambdaRole': 'arn:{}:iam::aws:policy/service-role/AWSLambdaRole'.format(partition),
            }

            output_fragment = transform(
                manifest, parameter_values, mock_policy_loader)
        finally:
            os.environ["AWS_DEFAULT_REGION"] = old_region

        print(json.dumps(output_fragment, indent=2))

        assert deep_sorted(output_fragment) == deep_sorted(expected)


@pytest.mark.parametrize('testcase', [
    'error_api_duplicate_methods_same_path',
    'error_api_invalid_definitionuri',
    'error_api_invalid_definitionbody',
    'error_api_invalid_restapiid',
    'error_cors_on_external_swagger',
    'error_invalid_cors_dict',
    'error_function_invalid_codeuri',
    'error_function_no_codeuri',
    'error_function_no_handler',
    'error_function_no_runtime',
    'error_function_with_deployment_preference_missing_alias',
    'error_function_with_invalid_deployment_preference_hook_property',
    'error_invalid_logical_id',
    'error_multiple_resource_errors',
    'error_s3_not_in_template',
    'error_table_invalid_attributetype',
    'error_invalid_resource_parameters',
    'error_reserved_sam_tag',
    'existing_event_logical_id',
    'existing_permission_logical_id',
    'existing_role_logical_id',
    'error_invalid_template',
    'error_globals_is_not_dict',
    'error_globals_unsupported_type',
    'error_globals_unsupported_property',
    'error_globals_api_with_stage_name',
    'error_function_policy_template_with_missing_parameter',
    'error_function_policy_template_invalid_value',
    'error_function_with_unknown_policy_template',
    'error_function_with_invalid_policy_statement'
])
def test_transform_invalid_document(testcase):
    manifest = yaml.load(open(os.path.join(input_folder, testcase + '.yaml'), 'r'))
    expected = json.load(open(os.path.join(output_folder, testcase + '.json'), 'r'))

    mock_policy_loader = MagicMock()
    parameter_values = get_template_parameter_values()

    with pytest.raises(InvalidDocumentException) as e:
        transform(manifest, parameter_values, mock_policy_loader)

    error_message = get_exception_error_message(e)

    assert error_message == expected.get('errorMessage')

def test_transform_unhandled_failure_empty_managed_policy_map():
    document = {
        'Transform': 'AWS::Serverless-2016-10-31',
        'Resources': {
            'Resource': {
                'Type': 'AWS::Serverless::Function',
                'Properties': {
                    'CodeUri': 's3://bucket/key',
                    'Handler': 'index.handler',
                    'Runtime': 'nodejs4.3',
                    'Policies': 'AmazonS3FullAccess'
                }
            }
        }
    }

    parameter_values = get_template_parameter_values()
    mock_policy_loader = MagicMock()
    mock_policy_loader.load.return_value = {}

    with pytest.raises(Exception) as e:
        transform(document, parameter_values, mock_policy_loader)

    error_message = e.value.message

    assert error_message == 'Managed policy map is empty, but should not be.'


def assert_metric_call(mock, transform, transform_failure=0, invalid_document=0):
    metric_dimensions = [
        {
            'Name': 'Transform',
            'Value': transform
        }
    ]

    mock.put_metric_data.assert_called_once_with(
        Namespace='ServerlessTransform',
        MetricData=[
            {
                'MetricName': 'TransformFailure',
                'Value': transform_failure,
                'Unit': 'Count',
                'Dimensions': metric_dimensions
            },
            {
                'MetricName': 'InvalidDocument',
                'Value': invalid_document,
                'Unit': 'Count',
                'Dimensions': metric_dimensions
            }
        ]
    )


def test_swagger_body_sha_gets_recomputed():

    document = {
        'Transform': 'AWS::Serverless-2016-10-31',
        'Resources': {
            'Resource': {
                'Type': 'AWS::Serverless::Api',
                'Properties': {
                    "StageName": "Prod",
                    "DefinitionBody": {
                        # Some body property will do
                        "a": "b"
                    }
                }
            }
        }

    }

    mock_policy_loader = get_policy_mock()
    parameter_values = get_template_parameter_values()

    output_fragment = transform(document, parameter_values, mock_policy_loader)

    print(json.dumps(output_fragment, indent=2))
    deployment_key = get_deployment_key(output_fragment)
    assert deployment_key

    # Now let's change the Body property and transform again
    document["Resources"]["Resource"]["Properties"]["DefinitionBody"]["a"] = "foo"
    output_fragment = transform(document, parameter_values, mock_policy_loader)
    deployment_key_changed = get_deployment_key(output_fragment)
    assert deployment_key_changed

    assert deployment_key != deployment_key_changed

    # Now let's re-deploy the document without any changes. Deployment Key must NOT change
    output_fragment = transform(document, parameter_values, mock_policy_loader)
    assert get_deployment_key(output_fragment) == deployment_key_changed


def test_swagger_definitionuri_sha_gets_recomputed():

    document = {
        'Transform': 'AWS::Serverless-2016-10-31',
        'Resources': {
            'Resource': {
                'Type': 'AWS::Serverless::Api',
                'Properties': {
                    "StageName": "Prod",
                    "DefinitionUri": "s3://bucket/key"
                }
            }
        }

    }

    mock_policy_loader = get_policy_mock()
    parameter_values = get_template_parameter_values()

    output_fragment = transform(document, parameter_values, mock_policy_loader)

    print(json.dumps(output_fragment, indent=2))
    deployment_key = get_deployment_key(output_fragment)
    assert deployment_key

    # Now let's change the Body property and transform again
    document["Resources"]["Resource"]["Properties"]["DefinitionUri"] = "s3://bucket/key1/key2"
    output_fragment = transform(document, parameter_values, mock_policy_loader)
    deployment_key_changed = get_deployment_key(output_fragment)
    assert deployment_key_changed

    assert deployment_key != deployment_key_changed

    # Now let's re-deploy the document without any changes. Deployment Key must NOT change
    output_fragment = transform(document, parameter_values, mock_policy_loader)
    assert get_deployment_key(output_fragment) == deployment_key_changed

class TestFunctionVersionWithParameterReferences(TestCase):
    """
    Test how Lambda Function Version gets created when intrinsic functions
    """

    def setUp(self):
        self.document = {
            'Transform': 'AWS::Serverless-2016-10-31',
            'Resources': {
                'MyFunction': {
                    'Type': 'AWS::Serverless::Function',
                    'Properties': {
                        "Runtime": "nodejs4.3",
                        "Handler": "index.handler",
                        "CodeUri": {
                            "Bucket": {"Ref": "SomeBucket"},
                            "Key": {"Ref": "CodeKeyParam"}
                        },
                        "AutoPublishAlias": "live"
                    }
                }
            }
        }

    def test_logical_id_change_with_parameters(self):
        parameter_values = {
            'CodeKeyParam': 'value1'
        }
        first_transformed_template = self._do_transform(self.document, parameter_values)

        parameter_values["CodeKeyParam"] = "value2"
        second_transformed_template = self._do_transform(self.document, parameter_values)

        first_version_id, _ = get_resource_by_type(first_transformed_template, "AWS::Lambda::Version")
        second_version_id, _ = get_resource_by_type(second_transformed_template, "AWS::Lambda::Version")

        assert first_version_id != second_version_id

    def test_logical_id_remains_same_without_parameter_change(self):
        parameter_values = {
            'CodeKeyParam': 'value1'
        }

        first_transformed_template = self._do_transform(self.document, parameter_values)
        second_transformed_template = self._do_transform(self.document, parameter_values)

        first_version_id, _ = get_resource_by_type(first_transformed_template, "AWS::Lambda::Version")
        second_version_id, _ = get_resource_by_type(second_transformed_template, "AWS::Lambda::Version")

        assert first_version_id == second_version_id

    def test_logical_id_without_resolving_reference(self):
        # Now value of `CodeKeyParam` is not present in document

        first_transformed_template = self._do_transform(self.document)
        second_transformed_template = self._do_transform(self.document)

        first_version_id, _ = get_resource_by_type(first_transformed_template, "AWS::Lambda::Version")
        second_version_id, _ = get_resource_by_type(second_transformed_template, "AWS::Lambda::Version")

        assert first_version_id == second_version_id

    def _do_transform(self, document, parameter_values=get_template_parameter_values()):
        mock_policy_loader = get_policy_mock()
        output_fragment = transform(document, parameter_values, mock_policy_loader)

        print(json.dumps(output_fragment, indent=2))

        return output_fragment


class TestParameterValuesHandling(TestCase):
    """
    Test how user-supplied parameters & default template parameter values from template get merged
    """

    def test_add_default_parameter_values_must_merge(self):
        parameter_values = {
            "Param1": "value1"
        }

        sam_template = {
            "Parameters": {
                "Param2": {
                    "Type": "String",
                    "Default": "template default"
                }
            }
        }

        expected = {
            "Param1": "value1",
            "Param2": "template default"
        }

        sam_parser = Parser()
        translator = Translator({}, sam_parser)
        result = translator._add_default_parameter_values(sam_template,
            parameter_values)
        self.assertEquals(expected, result)

    def test_add_default_parameter_values_must_override_user_specified_values(self):
        parameter_values = {
            "Param1": "value1"
        }

        sam_template = {
            "Parameters": {
                "Param1": {
                    "Type": "String",
                    "Default": "template default"
                }
            }
        }

        expected = {
            "Param1": "value1"
        }


        sam_parser = Parser()
        translator = Translator({}, sam_parser)
        result = translator._add_default_parameter_values(sam_template, parameter_values)
        self.assertEquals(expected, result)

    def test_add_default_parameter_values_must_skip_params_without_defaults(self):
        parameter_values = {
            "Param1": "value1"
        }

        sam_template = {
            "Parameters": {
                "Param1": {
                    "Type": "String"
                },
                "Param2": {
                    "Type": "String"
                }
            }
        }

        expected = {
            "Param1": "value1"
        }

        sam_parser = Parser()
        translator = Translator({}, sam_parser)
        result = translator._add_default_parameter_values(sam_template, parameter_values)
        self.assertEquals(expected, result)


    @parameterized.expand([
        # Array
        param(["1", "2"]),

        # String
        param("something"),

        # Some other non-parameter looking dictionary
        param({"Param1": {"Foo": "Bar"}}),

        param(None)
    ])
    def test_add_default_parameter_values_must_ignore_invalid_template_parameters(self, template_parameters):
        parameter_values = {
            "Param1": "value1"
        }

        expected = {
            "Param1": "value1"
        }

        sam_template = {
            "Parameters": template_parameters
        }


        sam_parser = Parser()
        translator = Translator({}, sam_parser)
        result = translator._add_default_parameter_values(
            sam_template, parameter_values)
        self.assertEquals(expected, result)


class TestTemplateValidation(TestCase):

    def test_throws_when_resource_not_found(self):
        template = {
            "foo": "bar"
        }

        with self.assertRaises(InvalidDocumentException):
            sam_parser = Parser()
            translator = Translator({}, sam_parser)
            translator.translate(template, {})

    def test_throws_when_resource_is_empty(self):
        template = {
            "Resources": {}
        }

        with self.assertRaises(InvalidDocumentException):
            sam_parser = Parser()
            translator = Translator({}, sam_parser)
            translator.translate(template, {})


    def test_throws_when_resource_is_not_dict(self):
        template = {
            "Resources": [1,2,3]
        }

        with self.assertRaises(InvalidDocumentException):
            sam_parser = Parser()
            translator = Translator({}, sam_parser)
            translator.translate(template, {})

class TestPluginsUsage(TestCase):
    # Tests if plugins are properly injected into the translator

    @patch("samtranslator.translator.translator.make_policy_template_for_function_plugin")
    def test_prepare_plugins_must_add_required_plugins(self, make_policy_template_for_function_plugin_mock):

        # This is currently the only required plugin
        plugin_instance = BasePlugin("something")
        make_policy_template_for_function_plugin_mock.return_value = plugin_instance

        sam_plugins = prepare_plugins([])
        self.assertEquals(3, len(sam_plugins))

    @patch("samtranslator.translator.translator.make_policy_template_for_function_plugin")
    def test_prepare_plugins_must_merge_input_plugins(self, make_policy_template_for_function_plugin_mock):

        required_plugin = BasePlugin("something")
        make_policy_template_for_function_plugin_mock.return_value = required_plugin

        custom_plugin = BasePlugin("someplugin")
        sam_plugins = prepare_plugins([custom_plugin])
        self.assertEquals(4, len(sam_plugins))

    def test_prepare_plugins_must_handle_empty_input(self):

        sam_plugins = prepare_plugins(None)
        self.assertEquals(3, len(sam_plugins)) # one required plugin

    @patch("samtranslator.translator.translator.PolicyTemplatesProcessor")
    @patch("samtranslator.translator.translator.PolicyTemplatesForFunctionPlugin")
    def test_make_policy_template_for_function_plugin_must_work(self,
                                                                policy_templates_for_function_plugin_mock,
                                                                policy_templates_processor_mock):

        default_templates = {"some": "value"}
        policy_templates_processor_mock.get_default_policy_templates_json.return_value = default_templates

        # mock to return instance of the processor
        processor_instance = Mock()
        policy_templates_processor_mock.return_value = processor_instance

        # mock for plugin instance
        plugin_instance = Mock()
        policy_templates_for_function_plugin_mock.return_value = plugin_instance

        result = make_policy_template_for_function_plugin()

        self.assertEquals(plugin_instance, result)

        policy_templates_processor_mock.get_default_policy_templates_json.assert_called_once_with()
        policy_templates_processor_mock.assert_called_once_with(default_templates)
        policy_templates_for_function_plugin_mock.assert_called_once_with(processor_instance)

    @patch.object(Resource, "from_dict")
    @patch("samtranslator.translator.translator.SamPlugins")
    @patch("samtranslator.translator.translator.prepare_plugins")
    def test_transform_method_must_inject_plugins_when_creating_resources(self,
                                                                          prepare_plugins_mock,
                                                                          sam_plugins_class_mock,
                                                                          resource_from_dict_mock):
        manifest = {
            'Resources': {
                'MyTable': {
                    'Type': 'AWS::Serverless::SimpleTable',
                    'Properties': {
                    }
                }
            }
        }

        sam_plugins_object_mock = Mock()
        sam_plugins_class_mock.return_value = sam_plugins_object_mock
        prepare_plugins_mock.return_value = sam_plugins_object_mock
        resource_from_dict_mock.return_value = SamSimpleTable("MyFunction")

        initial_plugins = [1,2,3]
        sam_parser = Parser()
        translator = Translator({}, sam_parser, plugins=initial_plugins)
        translator.translate(manifest, {})

        resource_from_dict_mock.assert_called_with("MyTable",
                                                        manifest["Resources"]["MyTable"],
                                                        sam_plugins=sam_plugins_object_mock)
        prepare_plugins_mock.assert_called_once_with(initial_plugins)

def get_policy_mock():
    mock_policy_loader = MagicMock()
    mock_policy_loader.load.return_value = {
        'AmazonDynamoDBFullAccess': 'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess',
        'AmazonDynamoDBReadOnlyAccess': 'arn:aws:iam::aws:policy/AmazonDynamoDBReadOnlyAccess',
        'AWSLambdaRole': 'arn:aws:iam::aws:policy/service-role/AWSLambdaRole',
    }

    return mock_policy_loader

def get_deployment_key(fragment):
    logical_id, value = get_resource_by_type(fragment, "AWS::ApiGateway::Deployment")
    return logical_id

def get_resource_by_type(template, type):
    resources = template["Resources"]
    for key in resources:
        value = resources[key]
        if "Type" in value and value.get("Type") == type:
            return key, value

def get_exception_error_message(e):
    return reduce(lambda message, error: message + ' ' + error.message, e.value.causes, e.value.message)
