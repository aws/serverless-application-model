import hashlib
import itertools
import json
import os.path
import re
import time
from functools import cmp_to_key, reduce
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, Mock, patch

import pytest
from parameterized import parameterized
from samtranslator.model import Resource
from samtranslator.model.exceptions import InvalidDocumentException, InvalidResourceException
from samtranslator.model.sam_resources import SamSimpleTable
from samtranslator.parser.parser import Parser
from samtranslator.public.plugins import BasePlugin
from samtranslator.translator.transform import transform
from samtranslator.translator.translator import Translator, make_policy_template_for_function_plugin, prepare_plugins
from samtranslator.yaml_helper import yaml_parse

from tests.plugins.application.test_serverless_app_plugin import mock_get_region
from tests.translator.helpers import get_template_parameter_values

PROJECT_ROOT = Path(__file__).parent.parent.parent
BASE_PATH = os.path.dirname(__file__)
INPUT_FOLDER = BASE_PATH + "/input"
OUTPUT_FOLDER = BASE_PATH + "/output"
# Do not sort AWS::Serverless::Function Layers Property.
# Order of Layers is an important attribute and shouldn't be changed.
DO_NOT_SORT = ["Layers"]

BASE_PATH = os.path.dirname(__file__)
INPUT_FOLDER = os.path.join(BASE_PATH, "input")
SUCCESS_FILES_NAMES_FOR_TESTING = [
    os.path.splitext(f)[0] for f in os.listdir(INPUT_FOLDER) if not (f.startswith(("error_", "translate_")))
]
ERROR_FILES_NAMES_FOR_TESTING = [os.path.splitext(f)[0] for f in os.listdir(INPUT_FOLDER) if f.startswith("error_")]
OUTPUT_FOLDER = os.path.join(BASE_PATH, "output")


def _parse_yaml(path):
    return yaml_parse(PROJECT_ROOT.joinpath(path).read_text())


def deep_sort_lists(value):
    """
    Custom sorting implemented as a wrapper on top of Python's built-in ``sorted`` method. This is necessary because
    the previous behavior assumed lists were unordered. As part of migration to Py3, we are trying to
    retain the same behavior. But in Py3, lists with complex data types like dict cannot be sorted. Hence
    we provide a custom sort function that tries best sort the lists in a stable order. The actual order
    does not matter as long as it is stable between runs.

    This implementation assumes that the input was parsed from a JSON data. So it can have one of the
    following types: a primitive type, list or other dictionaries.
    We traverse the dictionary like how we would traverse a tree. If a value is a list, we recursively sort the members
    of the list, and then sort the list itself.

    This assumption that lists are unordered is a problem at the first place. As part of dropping support for Python2,
    we should remove this assumption. We have to update SAM Translator to output lists in a predictable ordering so we
    can assume lists are ordered and compare them.
    """
    if isinstance(value, dict):
        return {k: deep_sort_lists(v) for k, v in value.items()}
    if isinstance(value, list):
        # Py3 cannot sort lists with complex types. Hence a custom comparator function
        return sorted((deep_sort_lists(x) for x in value), key=cmp_to_key(custom_list_data_comparator))
    else:
        return value


def custom_list_data_comparator(obj1, obj2):
    """
    Comparator function used to sort lists with complex data types in them. This is meant to be used only within the
    context of sorting lists for use with unit tests.

    Given any two objects, this function will return the "difference" between the two objects. This difference obviously
    does not make sense for complex data types like dictionaries & list. This function implements a custom logic that
    is partially borrowed from Python2's implementation of such a comparison:

    * Both objects are dict: Convert them JSON strings and compare
    * Both objects are comparable data types (ie. ones that have > and < operators): Compare them directly
    * Objects are non-comparable (ie. one is a dict other is a list): Compare the names of the data types.
      ie. dict < list because of alphabetical order. This is Python2's behavior.

    """

    if isinstance(obj1, dict) and isinstance(obj2, dict):
        obj1 = json.dumps(obj1, sort_keys=True)
        obj2 = json.dumps(obj2, sort_keys=True)

    try:
        return (obj1 > obj2) - (obj1 < obj2)
    # In Py3 a TypeError will be raised if obj1 and obj2 are different types or uncomparable
    except TypeError:
        s1, s2 = type(obj1).__name__, type(obj2).__name__
        return (s1 > s2) - (s1 < s2)


def mock_sar_service_call(self, service_call_function, logical_id, *args):
    """
    Current implementation: args[0] is always the application_id
    """
    application_id = args[0]
    status = "ACTIVE"
    if application_id == "no-access":
        raise InvalidResourceException(logical_id, f"Cannot access application: {application_id}.")
    elif application_id == "non-existent":
        raise InvalidResourceException(logical_id, f"Cannot access application: {application_id}.")
    elif application_id == "invalid-semver":
        raise InvalidResourceException(logical_id, f"Cannot access application: {application_id}.")
    elif application_id == 1:
        raise InvalidResourceException(logical_id, "Type of property 'ApplicationId' is invalid.")
    elif application_id == "preparing" and self._wait_for_template_active_status < 2:
        self._wait_for_template_active_status += 1
        self.SLEEP_TIME_SECONDS = 0
        self.TEMPLATE_WAIT_TIMEOUT_SECONDS = 2
        status = "PREPARING"
    elif application_id == "preparing-never-ready":
        self._wait_for_template_active_status = True
        self.SLEEP_TIME_SECONDS = 0
        self.TEMPLATE_WAIT_TIMEOUT_SECONDS = 0
        status = "PREPARING"
    elif application_id == "expired":
        status = "EXPIRED"
    message = {
        "ApplicationId": args[0],
        "CreationTime": "x",
        "ExpirationTime": "x",
        "SemanticVersion": "1.1.1",
        "Status": status,
        "TemplateId": "id-xx-xx",
        "TemplateUrl": "https://awsserverlessrepo-changesets-xxx.s3.amazonaws.com/signed-url",
    }
    return message


# implicit_api, explicit_api, explicit_api_ref, api_cache tests currently have deployment IDs hardcoded in output file.
# These ids are generated using sha1 hash of the swagger body for implicit
# api and s3 location for explicit api.


class AbstractTestTranslator(TestCase):
    maxDiff = None

    def _read_input(self, testcase):
        manifest = yaml_parse(open(os.path.join(INPUT_FOLDER, testcase + ".yaml")))
        # To uncover unicode-related bugs, convert dict to JSON string and parse JSON back to dict
        return json.loads(json.dumps(manifest))

    def _read_expected_output(self, testcase, partition):
        partition_folder = partition if partition != "aws" else ""
        expected_filepath = os.path.join(OUTPUT_FOLDER, partition_folder, testcase + ".json")
        return json.load(open(expected_filepath))

    def _compare_transform(self, manifest, expected, partition, region):
        with patch("boto3.session.Session.region_name", region):
            parameter_values = get_template_parameter_values()
            mock_policy_loader = MagicMock()
            mock_policy_loader.load.return_value = {
                "AWSLambdaBasicExecutionRole": "arn:{}:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole".format(
                    partition
                ),
                "AmazonDynamoDBFullAccess": f"arn:{partition}:iam::aws:policy/AmazonDynamoDBFullAccess",
                "AmazonDynamoDBReadOnlyAccess": f"arn:{partition}:iam::aws:policy/AmazonDynamoDBReadOnlyAccess",
                "AWSLambdaRole": f"arn:{partition}:iam::aws:policy/service-role/AWSLambdaRole",
            }
            if partition == "aws":
                mock_policy_loader.load.return_value[
                    "AWSXrayWriteOnlyAccess"
                ] = "arn:aws:iam::aws:policy/AWSXrayWriteOnlyAccess"
            else:
                mock_policy_loader.load.return_value[
                    "AWSXRayDaemonWriteAccess"
                ] = f"arn:{partition}:iam::aws:policy/AWSXRayDaemonWriteAccess"

            # For the managed_policies_minimal.yaml transform test.
            # For aws and aws-cn, these policies are cached (see https://github.com/aws/serverless-application-model/pull/2839),
            # however we don't bundle managed policies in aws-us-gov, so instead we simulate passing the
            # fallback policy loader
            if partition == "aws-us-gov":
                mock_policy_loader.load.return_value[
                    "AmazonS3FullAccess"
                ] = "arn:aws-us-gov:iam::aws:policy/AmazonS3FullAccess-mock-from-fallback-policy-loader"
                mock_policy_loader.load.return_value[
                    "AWSXrayWriteOnlyAccess"
                ] = "arn:aws-us-gov:iam::aws:policy/AWSXrayWriteOnlyAccess-mock-from-fallback-policy-loader"
                mock_policy_loader.load.return_value[
                    "AmazonAPIGatewayPushToCloudWatchLogs"
                ] = "arn:aws-us-gov:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs-mock-from-fallback-policy-loader"

            output_fragment = transform(manifest, parameter_values, mock_policy_loader)

        print(json.dumps(output_fragment, indent=2))

        self.assertEqual(deep_sort_lists(output_fragment), deep_sort_lists(expected))

    def _update_logical_id_hash(self, resources):
        """
        Brute force method for updating all APIGW Deployment LogicalIds and references to a consistent hash
        """
        output_resources = resources.get("Resources", {})
        deployment_logical_id_dict = {}
        rest_api_to_swagger_hash = {}
        dict_of_things_to_delete = {}

        # Find all RestApis in the template
        for logical_id, resource_dict in output_resources.items():
            if resource_dict.get("Type") == "AWS::ApiGateway::RestApi":
                resource_properties = resource_dict.get("Properties", {})
                if "Body" in resource_properties:
                    self._generate_new_deployment_hash(
                        logical_id, resource_properties.get("Body"), rest_api_to_swagger_hash
                    )

                elif "BodyS3Location" in resource_dict.get("Properties"):
                    self._generate_new_deployment_hash(
                        logical_id, resource_properties.get("BodyS3Location"), rest_api_to_swagger_hash
                    )

        # Collect all APIGW Deployments LogicalIds and generate the new ones
        for logical_id, resource_dict in output_resources.items():
            if resource_dict.get("Type") == "AWS::ApiGateway::Deployment":
                resource_properties = resource_dict.get("Properties", {})

                rest_id = resource_properties.get("RestApiId").get("Ref")

                data_hash = rest_api_to_swagger_hash.get(rest_id)

                description = resource_properties.get("Description")[: -len(data_hash)]

                resource_properties["Description"] = description + data_hash

                new_logical_id = logical_id[:-10] + data_hash[:10]

                deployment_logical_id_dict[logical_id] = new_logical_id
                dict_of_things_to_delete[logical_id] = (new_logical_id, resource_dict)

        # Update References to APIGW Deployments
        for logical_id, resource_dict in output_resources.items():
            if resource_dict.get("Type") == "AWS::ApiGateway::Stage":
                resource_properties = resource_dict.get("Properties", {})

                rest_id = resource_properties.get("RestApiId", {}).get("Ref", "")

                data_hash = rest_api_to_swagger_hash.get(rest_id)

                deployment_id = resource_properties.get("DeploymentId", {}).get("Ref")
                new_logical_id = deployment_logical_id_dict.get(deployment_id, "")[:-10]
                new_logical_id = new_logical_id + data_hash[:10]

                resource_properties.get("DeploymentId", {})["Ref"] = new_logical_id

        # To avoid mutating the template while iterating, delete only after find everything to update
        for logical_id_to_remove, tuple_to_add in dict_of_things_to_delete.items():
            output_resources[tuple_to_add[0]] = tuple_to_add[1]
            del output_resources[logical_id_to_remove]

        # Update any Output References in the template
        for _output_key, output_value in resources.get("Outputs", {}).items():
            if output_value.get("Value").get("Ref") in deployment_logical_id_dict:
                output_value["Value"]["Ref"] = deployment_logical_id_dict[output_value.get("Value").get("Ref")]

    def _generate_new_deployment_hash(self, logical_id, dict_to_hash, rest_api_to_swagger_hash):
        data_bytes = json.dumps(dict_to_hash, separators=(",", ":"), sort_keys=True).encode("utf8")
        data_hash = hashlib.sha1(data_bytes).hexdigest()
        rest_api_to_swagger_hash[logical_id] = data_hash


class TestTranslatorEndToEnd(AbstractTestTranslator):
    @parameterized.expand(
        itertools.product(
            SUCCESS_FILES_NAMES_FOR_TESTING,
            [
                ("aws", "ap-southeast-1"),
                ("aws-cn", "cn-north-1"),
                ("aws-us-gov", "us-gov-west-1"),
            ],  # Run all the above tests against each of the list of partitions to test against
        )
    )
    @patch(
        "samtranslator.plugins.application.serverless_app_plugin.ServerlessAppPlugin._sar_service_call",
        mock_sar_service_call,
    )
    @patch("samtranslator.translator.arn_generator._get_region_from_session")
    def test_transform_success(self, testcase, partition_with_region, mock_get_region_from_session):
        partition = partition_with_region[0]
        region = partition_with_region[1]
        mock_get_region_from_session.return_value = region

        manifest = self._read_input(testcase)
        expected = self._read_expected_output(testcase, partition)

        self._compare_transform(manifest, expected, partition, region)

    @parameterized.expand(
        itertools.product(
            [
                "explicit_api_openapi_3",
                "api_with_auth_all_maximum_openapi_3",
                "api_with_cors_openapi_3",
                "api_with_gateway_responses_all_openapi_3",
                "api_with_open_api_version",
                "api_with_open_api_version_2",
                "api_with_auth_all_minimum_openapi",
                "api_with_swagger_and_openapi_with_auth",
                "api_with_openapi_definition_body_no_flag",
                "api_request_model_with_validator_openapi_3",
                "api_request_model_openapi_3",
                "api_with_apikey_required_openapi_3",
                "api_with_basic_custom_domain",
                "api_with_basic_custom_domain_intrinsics",
                "api_with_custom_domain_route53",
                "api_with_custom_domain_route53_hosted_zone_name",
                "api_with_custom_domain_route53_multiple",
                "api_with_custom_domain_route53_multiple_intrinsic_hostedzoneid",
                "api_with_basic_custom_domain_http",
                "api_with_basic_custom_domain_intrinsics_http",
                "api_with_custom_domain_route53_http",
                "api_with_custom_domain_route53_hosted_zone_name_http",
                "implicit_http_api",
                "explicit_http_api_minimum",
                "implicit_http_api_auth_and_simple_case",
                "http_api_existing_openapi",
                "http_api_existing_openapi_conditions",
                "implicit_http_api_with_many_conditions",
                "http_api_explicit_stage",
                "http_api_def_uri",
                "explicit_http_api",
                "explicit_http_api_with_name",
                "http_api_custom_iam_auth",
                "http_api_with_cors",
                "http_api_description",
                "http_api_global_iam_auth_enabled_with_existing_conflicting_authorizer",
                "http_api_global_iam_auth_enabled",
                "http_api_lambda_auth",
                "http_api_lambda_auth_full",
                "http_api_local_iam_auth_enabled_with_existing_conflicting_authorizer",
                "http_api_local_iam_auth_enabled",
                "http_api_multiple_authorizers",
                "http_api_with_custom_domain_route53_multiple",
                "mixed_api_with_custom_domain_route53_multiple",
            ],
            [
                ("aws", "ap-southeast-1"),
                ("aws-cn", "cn-north-1"),
                ("aws-us-gov", "us-gov-west-1"),
            ],  # Run all the above tests against each of the list of partitions to test against
        )
    )
    @pytest.mark.slow
    @patch(
        "samtranslator.plugins.application.serverless_app_plugin.ServerlessAppPlugin._sar_service_call",
        mock_sar_service_call,
    )
    @patch("samtranslator.translator.arn_generator._get_region_from_session")
    def test_transform_success_openapi3(self, testcase, partition_with_region, mock_get_region_from_session):
        partition = partition_with_region[0]
        region = partition_with_region[1]
        mock_get_region_from_session.return_value = region

        manifest = yaml_parse(open(os.path.join(INPUT_FOLDER, testcase + ".yaml")))
        # To uncover unicode-related bugs, convert dict to JSON string and parse JSON back to dict
        manifest = json.loads(json.dumps(manifest))
        partition_folder = partition if partition != "aws" else ""
        expected_filepath = os.path.join(OUTPUT_FOLDER, partition_folder, testcase + ".json")
        expected = json.load(open(expected_filepath))

        with patch("boto3.session.Session.region_name", region):
            parameter_values = get_template_parameter_values()
            mock_policy_loader = MagicMock()
            mock_policy_loader.load.return_value = {
                "AWSLambdaBasicExecutionRole": "arn:{}:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole".format(
                    partition
                ),
                "AmazonDynamoDBFullAccess": f"arn:{partition}:iam::aws:policy/AmazonDynamoDBFullAccess",
                "AmazonDynamoDBReadOnlyAccess": f"arn:{partition}:iam::aws:policy/AmazonDynamoDBReadOnlyAccess",
                "AWSLambdaRole": f"arn:{partition}:iam::aws:policy/service-role/AWSLambdaRole",
            }

            output_fragment = transform(manifest, parameter_values, mock_policy_loader)

        print(json.dumps(output_fragment, indent=2))

        self.assertEqual(deep_sort_lists(output_fragment), deep_sort_lists(expected))

    @parameterized.expand(
        itertools.product(
            [
                "api_with_aws_account_whitelist",
                "api_with_aws_account_blacklist",
                "api_with_ip_range_whitelist",
                "api_with_ip_range_blacklist",
                "api_with_source_vpc_whitelist",
                "api_with_source_vpc_blacklist",
                "api_with_resource_policy",
                "api_with_resource_policy_global",
                "api_with_resource_policy_global_implicit",
                "api_with_if_conditional_with_resource_policy",
            ],
            [
                ("aws", "ap-southeast-1"),
                ("aws-cn", "cn-north-1"),
                ("aws-us-gov", "us-gov-west-1"),
            ],  # Run all the above tests against each of the list of partitions to test against
        )
    )
    @patch(
        "samtranslator.plugins.application.serverless_app_plugin.ServerlessAppPlugin._sar_service_call",
        mock_sar_service_call,
    )
    @patch("samtranslator.translator.arn_generator._get_region_from_session")
    def test_transform_success_resource_policy(self, testcase, partition_with_region, mock_get_region_from_session):
        partition = partition_with_region[0]
        region = partition_with_region[1]
        mock_get_region_from_session.return_value = region

        manifest = yaml_parse(open(os.path.join(INPUT_FOLDER, testcase + ".yaml")))
        # To uncover unicode-related bugs, convert dict to JSON string and parse JSON back to dict
        manifest = json.loads(json.dumps(manifest))
        partition_folder = partition if partition != "aws" else ""
        expected_filepath = os.path.join(OUTPUT_FOLDER, partition_folder, testcase + ".json")
        expected = json.load(open(expected_filepath))

        with patch("boto3.session.Session.region_name", region):
            parameter_values = get_template_parameter_values()
            mock_policy_loader = MagicMock()
            mock_policy_loader.load.return_value = {
                "AWSLambdaBasicExecutionRole": "arn:{}:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole".format(
                    partition
                ),
                "AmazonDynamoDBFullAccess": f"arn:{partition}:iam::aws:policy/AmazonDynamoDBFullAccess",
                "AmazonDynamoDBReadOnlyAccess": f"arn:{partition}:iam::aws:policy/AmazonDynamoDBReadOnlyAccess",
                "AWSLambdaRole": f"arn:{partition}:iam::aws:policy/service-role/AWSLambdaRole",
            }

            output_fragment = transform(manifest, parameter_values, mock_policy_loader)
        print(json.dumps(output_fragment, indent=2))

        self.assertEqual(deep_sort_lists(output_fragment), deep_sort_lists(expected))

    @parameterized.expand(
        itertools.product(
            [
                (
                    "usage_plans",
                    ("api_with_usageplans_shared_no_side_effect_1", "api_with_usageplans_shared_no_side_effect_2"),
                ),
            ],
            [
                ("aws", "ap-southeast-1"),
                ("aws-cn", "cn-north-1"),
                ("aws-us-gov", "us-gov-west-1"),
            ],
        )
    )
    @patch(
        "samtranslator.plugins.application.serverless_app_plugin.ServerlessAppPlugin._sar_service_call",
        mock_sar_service_call,
    )
    @patch("samtranslator.translator.arn_generator._get_region_from_session")
    def test_transform_success_no_side_effect(self, testcase, partition_with_region, mock_get_region_from_session):
        """
        Tests that the transform does not leak/leave data in shared caches/lists between executions
        Performs the transform of the templates in a row without reinitialization
        Data from template X should not leak in template X+1

        Parameters
        ----------
        testcase : Tuple
            Test name (unused) and Templates
        templates : List
            List of templates to transform
        """
        partition = partition_with_region[0]
        region = partition_with_region[1]
        mock_get_region_from_session.return_value = region

        for template in testcase[1]:
            print(template, partition, region)
            manifest = self._read_input(template)
            expected = self._read_expected_output(template, partition)

            self._compare_transform(manifest, expected, partition, region)


@pytest.mark.parametrize(
    "testcase",
    ERROR_FILES_NAMES_FOR_TESTING,
)
@patch("boto3.session.Session.region_name", "ap-southeast-1")
@patch(
    "samtranslator.plugins.application.serverless_app_plugin.ServerlessAppPlugin._sar_service_call",
    mock_sar_service_call,
)
@patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
def test_transform_invalid_document(testcase):
    manifest = yaml_parse(open(os.path.join(INPUT_FOLDER, testcase + ".yaml")))
    expected = json.load(open(os.path.join(OUTPUT_FOLDER, testcase + ".json")))

    mock_policy_loader = MagicMock()
    mock_policy_loader.load.return_value = None
    parameter_values = get_template_parameter_values()

    with pytest.raises(InvalidDocumentException) as e:
        transform(manifest, parameter_values, mock_policy_loader)

    error_message = get_exception_error_message(e)
    error_message = re.sub(r"u'([A-Za-z0-9]*)'", r"'\1'", error_message)

    assert error_message == expected.get("errorMessage")


def assert_metric_call(mock, transform, transform_failure=0, invalid_document=0):
    metric_dimensions = [{"Name": "Transform", "Value": transform}]

    mock.put_metric_data.assert_called_once_with(
        Namespace="ServerlessTransform",
        MetricData=[
            {
                "MetricName": "TransformFailure",
                "Value": transform_failure,
                "Unit": "Count",
                "Dimensions": metric_dimensions,
            },
            {
                "MetricName": "InvalidDocument",
                "Value": invalid_document,
                "Unit": "Count",
                "Dimensions": metric_dimensions,
            },
        ],
    )


@patch("boto3.session.Session.region_name", "ap-southeast-1")
@patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
def test_swagger_body_sha_gets_recomputed():
    document = {
        "Transform": "AWS::Serverless-2016-10-31",
        "Resources": {
            "Resource": {
                "Type": "AWS::Serverless::Api",
                "Properties": {
                    "StageName": "Prod",
                    "DefinitionBody": {
                        # Some body property will do
                        "a": "b"
                    },
                },
            }
        },
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


@patch("boto3.session.Session.region_name", "ap-southeast-1")
@patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
def test_swagger_definitionuri_sha_gets_recomputed():
    document = {
        "Transform": "AWS::Serverless-2016-10-31",
        "Resources": {
            "Resource": {
                "Type": "AWS::Serverless::Api",
                "Properties": {"StageName": "Prod", "DefinitionUri": "s3://bucket/key"},
            }
        },
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
            "Transform": "AWS::Serverless-2016-10-31",
            "Resources": {
                "MyFunction": {
                    "Type": "AWS::Serverless::Function",
                    "Properties": {
                        "Runtime": "nodejs12.x",
                        "Handler": "index.handler",
                        "CodeUri": {"Bucket": {"Ref": "SomeBucket"}, "Key": {"Ref": "CodeKeyParam"}},
                        "AutoPublishAlias": "live",
                    },
                }
            },
        }

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_logical_id_change_with_parameters(self):
        parameter_values = {"CodeKeyParam": "value1"}
        first_transformed_template = self._do_transform(self.document, parameter_values)

        parameter_values["CodeKeyParam"] = "value2"
        second_transformed_template = self._do_transform(self.document, parameter_values)

        first_version_id, _ = get_resource_by_type(first_transformed_template, "AWS::Lambda::Version")
        second_version_id, _ = get_resource_by_type(second_transformed_template, "AWS::Lambda::Version")

        assert first_version_id != second_version_id

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_logical_id_remains_same_without_parameter_change(self):
        parameter_values = {"CodeKeyParam": "value1"}

        first_transformed_template = self._do_transform(self.document, parameter_values)
        second_transformed_template = self._do_transform(self.document, parameter_values)

        first_version_id, _ = get_resource_by_type(first_transformed_template, "AWS::Lambda::Version")
        second_version_id, _ = get_resource_by_type(second_transformed_template, "AWS::Lambda::Version")

        assert first_version_id == second_version_id

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
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


class TestApiAlwaysDeploy(TestCase):
    """
    AlwaysDeploy is used to force API Gateway to redeploy at every deployment.
    See https://github.com/aws/serverless-application-model/issues/660

    Since it relies on the system time to generate the template, need to patch
    time.time() for deterministic tests.
    """

    @staticmethod
    def get_deployment_ids(template):
        cfn_template = Translator({}, Parser()).translate(template, {})
        deployment_ids = set()
        for k, v in cfn_template["Resources"].items():
            if v["Type"] == "AWS::ApiGateway::Deployment":
                deployment_ids.add(k)
        return deployment_ids

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_always_deploy(self):
        with patch("time.time", lambda: 13.37):
            obj = _parse_yaml("tests/translator/input/translate_always_deploy.yaml")
            deployment_ids = TestApiAlwaysDeploy.get_deployment_ids(obj)
            self.assertEqual(deployment_ids, {"MyApiDeploymentbd307a3ec3"})

        with patch("time.time", lambda: 42.123):
            obj = _parse_yaml("tests/translator/input/translate_always_deploy.yaml")
            deployment_ids = TestApiAlwaysDeploy.get_deployment_ids(obj)
            self.assertEqual(deployment_ids, {"MyApiDeployment92cfceb39d"})

        with patch("time.time", lambda: 42.1337):
            obj = _parse_yaml("tests/translator/input/translate_always_deploy.yaml")
            deployment_ids = TestApiAlwaysDeploy.get_deployment_ids(obj)
            self.assertEqual(deployment_ids, {"MyApiDeployment92cfceb39d"})

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_without_alwaysdeploy_never_changes(self):
        sam_template = {
            "Resources": {
                "MyApi": {
                    "Type": "AWS::Serverless::Api",
                    "Properties": {
                        "StageName": "prod",
                    },
                }
            },
        }

        deployment_ids = set()
        deployment_ids.update(TestApiAlwaysDeploy.get_deployment_ids(sam_template))
        time.sleep(2)
        deployment_ids.update(TestApiAlwaysDeploy.get_deployment_ids(sam_template))
        time.sleep(2)
        deployment_ids.update(TestApiAlwaysDeploy.get_deployment_ids(sam_template))

        self.assertEqual(len(deployment_ids), 1)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_with_alwaysdeploy_always_changes(self):
        sam_template = {
            "Resources": {
                "MyApi": {
                    "Type": "AWS::Serverless::Api",
                    "Properties": {
                        "StageName": "prod",
                        "AlwaysDeploy": True,
                    },
                }
            },
        }

        deployment_ids = set()
        deployment_ids.update(TestApiAlwaysDeploy.get_deployment_ids(sam_template))
        time.sleep(2)
        deployment_ids.update(TestApiAlwaysDeploy.get_deployment_ids(sam_template))
        time.sleep(2)
        deployment_ids.update(TestApiAlwaysDeploy.get_deployment_ids(sam_template))

        self.assertEqual(len(deployment_ids), 3)


class TestTemplateValidation(TestCase):
    _MANAGED_POLICIES_TEMPLATE = {
        "Resources": {
            "MyFunction": {
                "Type": "AWS::Serverless::Function",
                "Properties": {
                    "Runtime": "python3.8",
                    "Handler": "foo",
                    "InlineCode": "bar",
                    "Policies": [
                        "foo",
                    ],
                },
            },
            "MyStateMachine": {
                "Type": "AWS::Serverless::StateMachine",
                "Properties": {
                    "DefinitionUri": "s3://foo/bar",
                    "Policies": [
                        "foo",
                    ],
                },
            },
        }
    }

    @parameterized.expand(
        [
            # All combinations, should use first that matches from left
            ({"foo": "a1"}, {"foo": "a2"}, {"foo": "a3"}, "a1"),
            (None, None, {"foo": "a3"}, "a3"),
            (None, {"foo": "a2"}, None, "a2"),
            ({"foo": "a1"}, {"foo": "a2"}, None, "a1"),
            (None, None, {"foo": "a3"}, "a3"),
            (None, {"foo": "a2"}, None, "a2"),
            ({"foo": "a1"}, None, None, "a1"),
        ]
    )
    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_managed_policies_translator_translate(
        self,
        managed_policy_map,
        bundled_managed_policy_map,
        get_managed_policy_map_value,
        expected_arn,
    ):
        """
        Ensure expectd ARN is derived from managed policy name when transforming
        with Translator.translate() (used in actual transform).

        This tests the fallback logic, but in practice managed_policy_map and
        get_managed_policy_map() are expected to be the same. They must both be
        currently supported managed policies for the Policies property to work.
        """

        def get_managed_policy_map():
            return get_managed_policy_map_value

        with patch(
            "samtranslator.internal.managed_policies._BUNDLED_MANAGED_POLICIES",
            {"aws": bundled_managed_policy_map},
        ):
            parameters = {}
            cfn_template = Translator(managed_policy_map, Parser()).translate(
                self._MANAGED_POLICIES_TEMPLATE,
                parameters,
                get_managed_policy_map=get_managed_policy_map,
            )

        function_arn = cfn_template["Resources"]["MyFunctionRole"]["Properties"]["ManagedPolicyArns"][1]
        sfn_arn = cfn_template["Resources"]["MyStateMachineRole"]["Properties"]["ManagedPolicyArns"][0]

        self.assertEqual(function_arn, expected_arn)
        self.assertEqual(sfn_arn, expected_arn)

    @parameterized.expand(
        [
            (None, None, None, "foo"),
        ]
    )
    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_managed_policies_translator_translate_no_match(
        self,
        managed_policy_map,
        bundled_managed_policy_map,
        get_managed_policy_map_value,
        expected_arn,
    ):
        def get_managed_policy_map():
            return get_managed_policy_map_value

        with patch(
            "samtranslator.internal.managed_policies._BUNDLED_MANAGED_POLICIES",
            {"aws": bundled_managed_policy_map},
        ):
            parameters = {}
            with self.assertRaises(InvalidDocumentException):
                Translator(managed_policy_map, Parser()).translate(
                    self._MANAGED_POLICIES_TEMPLATE,
                    parameters,
                    get_managed_policy_map=get_managed_policy_map,
                )

    # test to make sure with arn it doesnt load, with non-arn it does
    @parameterized.expand(
        [
            ([""], 1),
            (["SomeNonArnThing"], 1),
            (["SomeNonArnThing", "AnotherNonArnThing"], 1),
            (["aws:looks:like:an:ARN:but-not-really"], 1),
            (["arn:looks:like:an:ARN:foo", "Mixing_things_v2"], 1),
            (["arn:looks:like:an:ARN:foo"], 0),
            ([{"Ref": "Foo"}], 0),
            ([{"SQSPollerPolicy": {"QueueName": "Bar"}}], 0),
            (["arn:looks:like:an:ARN", "arn:aws:ec2:us-east-1:123456789012:vpc/vpc-0e9801d129EXAMPLE"], 0),
        ]
    )
    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_managed_policies_arn_not_loaded(self, policies, load_policy_count):
        class ManagedPolicyLoader:
            def __init__(self):
                self.call_count = 0

            def load(self):
                self.call_count += 1
                return {
                    "": "arn:",
                    "SomeNonArnThing": "arn:SomeNonArnThing",
                    "AnotherNonArnThing": "arn:AnotherNonArnThing",
                    "aws:looks:like:an:ARN:but-not-really": "arn:aws:looks:like:an:ARN:but-not-really",
                    "Mixing_things_v2": "arn:Mixing_things_v2",
                }

        managed_policy_loader = ManagedPolicyLoader()

        with patch("samtranslator.internal.managed_policies._BUNDLED_MANAGED_POLICIES", {}):
            transform(
                {
                    "Resources": {
                        "MyFunction": {
                            "Type": "AWS::Serverless::Function",
                            "Properties": {
                                "Handler": "foo",
                                "InlineCode": "bar",
                                "Runtime": "nodejs14.x",
                                "Policies": policies,
                            },
                        },
                        "MyStateMachine": {
                            "Type": "AWS::Serverless::StateMachine",
                            "Properties": {
                                "DefinitionUri": "s3://egg/baz",
                                "Policies": policies,
                            },
                        },
                    }
                },
                {},
                managed_policy_loader,
            )

        self.assertEqual(load_policy_count, managed_policy_loader.call_count)

    @parameterized.expand(
        [
            # All combinations, bundled map takes precedence
            ({"foo": "a1"}, {"foo": "a2"}, "a2"),
            ({"foo": "a1"}, None, "a1"),
            (None, {"foo": "a2"}, "a2"),
        ]
    )
    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_managed_policies_transform(
        self,
        managed_policy_map,
        bundled_managed_policy_map,
        expected_arn,
    ):
        """
        Ensure expectd ARN is derived from managed policy name when transforming
        with transform(). It calls Translator.translate() under the hood.
        """

        class ManagedPolicyLoader:
            def load(self):
                return managed_policy_map

        with patch(
            "samtranslator.internal.managed_policies._BUNDLED_MANAGED_POLICIES",
            {"aws": bundled_managed_policy_map},
        ):
            parameters = {}
            cfn_template = transform(
                self._MANAGED_POLICIES_TEMPLATE,
                parameters,
                ManagedPolicyLoader(),
            )

        function_arn = cfn_template["Resources"]["MyFunctionRole"]["Properties"]["ManagedPolicyArns"][1]
        sfn_arn = cfn_template["Resources"]["MyStateMachineRole"]["Properties"]["ManagedPolicyArns"][0]

        self.assertEqual(function_arn, expected_arn)
        self.assertEqual(sfn_arn, expected_arn)

    @parameterized.expand(
        [
            (None, None, "foo"),
        ]
    )
    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_managed_policies_transform_no_match(
        self,
        managed_policy_map,
        bundled_managed_policy_map,
        expected_arn,
    ):
        class ManagedPolicyLoader:
            def load(self):
                return managed_policy_map

        with patch(
            "samtranslator.internal.managed_policies._BUNDLED_MANAGED_POLICIES",
            {"aws": bundled_managed_policy_map},
        ):
            parameters = {}
            with self.assertRaises(InvalidDocumentException):
                transform(
                    self._MANAGED_POLICIES_TEMPLATE,
                    parameters,
                    ManagedPolicyLoader(),
                )

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_managed_policies_transform_policies_loaded_once(self):
        """
        Ensure transform() calls the policy loader load() (i.e. IAM call) only once.
        """

        class ManagedPolicyLoader:
            def __init__(self):
                self.call_count = 0

            def load(self):
                self.call_count += 1
                return {
                    "foo": "arn:foo",
                    "bar": "arn:bar",
                    "egg": "arn:egg",
                    "baz": "arn:baz",
                }

        managed_policy_loader = ManagedPolicyLoader()

        with patch("samtranslator.internal.managed_policies._BUNDLED_MANAGED_POLICIES", {}):
            transform(
                {
                    "Resources": {
                        "MyStateMachine1": {
                            "Type": "AWS::Serverless::StateMachine",
                            "Properties": {
                                "DefinitionUri": "s3://foo/bar",
                                "Policies": [
                                    "foo",
                                    "bar",
                                ],
                            },
                        },
                        "MyStateMachine2": {
                            "Type": "AWS::Serverless::StateMachine",
                            "Properties": {
                                "DefinitionUri": "s3://egg/baz",
                                "Policies": [
                                    "egg",
                                    "baz",
                                ],
                            },
                        },
                    }
                },
                {},
                managed_policy_loader,
            )

        self.assertEqual(1, managed_policy_loader.call_count)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_throws_when_resource_not_found(self):
        template = {"foo": "bar"}

        with self.assertRaises(InvalidDocumentException):
            sam_parser = Parser()
            translator = Translator({}, sam_parser)
            translator.translate(template, {})

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_throws_when_resource_is_empty(self):
        template = {"Resources": {}}

        with self.assertRaises(InvalidDocumentException):
            sam_parser = Parser()
            translator = Translator({}, sam_parser)
            translator.translate(template, {})

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_throws_when_resource_is_not_dict(self):
        template = {"Resources": [1, 2, 3]}

        with self.assertRaises(InvalidDocumentException):
            sam_parser = Parser()
            translator = Translator({}, sam_parser)
            translator.translate(template, {})

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_throws_when_resources_not_all_dicts(self):
        template = {"Resources": {"notadict": None, "MyResource": {}}}

        with self.assertRaises(InvalidDocumentException):
            sam_parser = Parser()
            translator = Translator({}, sam_parser)
            translator.translate(template, {})

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_validate_translated_no_metadata(self):
        with open(os.path.join(INPUT_FOLDER, "translate_convert_metadata.yaml")) as f:
            template = yaml_parse(f.read())
        with open(os.path.join(OUTPUT_FOLDER, "translate_convert_no_metadata.json")) as f:
            expected = json.loads(f.read())

        sam_parser = Parser()
        translator = Translator(None, sam_parser)
        actual = translator.translate(template, {})
        self.assertEqual(expected, actual)

    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_validate_translated_metadata(self):
        self.maxDiff = None
        with open(os.path.join(INPUT_FOLDER, "translate_convert_metadata.yaml")) as f:
            template = yaml_parse(f.read())
        with open(os.path.join(OUTPUT_FOLDER, "translate_convert_metadata.json")) as f:
            expected = json.loads(f.read())

        sam_parser = Parser()
        translator = Translator(None, sam_parser)
        actual = translator.translate(template, {}, passthrough_metadata=True)
        self.assertEqual(expected, actual)


class _SomethingPlugin(BasePlugin):
    pass


class _CustomPlugin(BasePlugin):
    pass


class TestPluginsUsage(TestCase):
    # Tests if plugins are properly injected into the translator

    @patch("samtranslator.translator.translator.make_policy_template_for_function_plugin")
    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_prepare_plugins_must_add_required_plugins(self, make_policy_template_for_function_plugin_mock):
        # This is currently the only required plugin
        plugin_instance = _SomethingPlugin()
        make_policy_template_for_function_plugin_mock.return_value = plugin_instance

        sam_plugins = prepare_plugins([])
        self.assertEqual(6, len(sam_plugins))

    @patch("samtranslator.translator.translator.make_policy_template_for_function_plugin")
    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_prepare_plugins_must_merge_input_plugins(self, make_policy_template_for_function_plugin_mock):
        required_plugin = _SomethingPlugin()
        make_policy_template_for_function_plugin_mock.return_value = required_plugin

        custom_plugin = _CustomPlugin()
        sam_plugins = prepare_plugins([custom_plugin])
        self.assertEqual(7, len(sam_plugins))

    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_prepare_plugins_must_handle_empty_input(self):
        sam_plugins = prepare_plugins(None)
        self.assertEqual(6, len(sam_plugins))

    @patch("samtranslator.translator.translator.PolicyTemplatesProcessor")
    @patch("samtranslator.translator.translator.PolicyTemplatesForResourcePlugin")
    def test_make_policy_template_for_function_plugin_must_work(
        self, policy_templates_for_function_plugin_mock, policy_templates_processor_mock
    ):
        default_templates = {"some": "value"}
        policy_templates_processor_mock.get_default_policy_templates_json.return_value = default_templates

        # mock to return instance of the processor
        processor_instance = Mock()
        policy_templates_processor_mock.return_value = processor_instance

        # mock for plugin instance
        plugin_instance = Mock()
        policy_templates_for_function_plugin_mock.return_value = plugin_instance

        result = make_policy_template_for_function_plugin()

        self.assertEqual(plugin_instance, result)

        policy_templates_processor_mock.get_default_policy_templates_json.assert_called_once_with()
        policy_templates_processor_mock.assert_called_once_with(default_templates)
        policy_templates_for_function_plugin_mock.assert_called_once_with(processor_instance)

    @patch.object(Resource, "from_dict")
    @patch("samtranslator.translator.translator.SamPlugins")
    @patch("samtranslator.translator.translator.prepare_plugins")
    @patch("boto3.session.Session.region_name", "ap-southeast-1")
    def test_transform_method_must_inject_plugins_when_creating_resources(
        self, prepare_plugins_mock, sam_plugins_class_mock, resource_from_dict_mock
    ):
        manifest = {"Resources": {"MyTable": {"Type": "AWS::Serverless::SimpleTable", "Properties": {}}}}

        sam_plugins_object_mock = Mock()
        sam_plugins_class_mock.return_value = sam_plugins_object_mock
        prepare_plugins_mock.return_value = sam_plugins_object_mock
        resource_from_dict_mock.return_value = SamSimpleTable("MyFunction")

        initial_plugins = [1, 2, 3]
        sam_parser = Parser()
        translator = Translator({}, sam_parser, plugins=initial_plugins)
        translator.translate(manifest, {})

        resource_from_dict_mock.assert_called_with(
            "MyTable", manifest["Resources"]["MyTable"], sam_plugins=sam_plugins_object_mock
        )
        prepare_plugins_mock.assert_called_once_with(
            initial_plugins, {"AWS::Region": "ap-southeast-1", "AWS::Partition": "aws"}
        )


def get_policy_mock():
    mock_policy_loader = MagicMock()
    mock_policy_loader.load.return_value = {
        "AmazonDynamoDBFullAccess": "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess",
        "AmazonDynamoDBReadOnlyAccess": "arn:aws:iam::aws:policy/AmazonDynamoDBReadOnlyAccess",
        "AWSLambdaRole": "arn:aws:iam::aws:policy/service-role/AWSLambdaRole",
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
    return None


def get_exception_error_message(e):
    return reduce(
        lambda message, error: message + " " + error.message,
        sorted(e.value.causes, key=_exception_sort_key),
        e.value.message,
    )


def _exception_sort_key(cause):
    """
    Returns the key to be used for sorting among other exceptions
    """
    if hasattr(cause, "_logical_id"):
        return cause._logical_id
    if hasattr(cause, "_event_id"):
        return cause._event_id
    if hasattr(cause, "message"):
        return cause.message
    return str(cause)
