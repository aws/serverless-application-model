import json
import itertools
import os.path
import hashlib
import sys
from functools import reduce, cmp_to_key

from samtranslator.translator.translator import Translator, prepare_plugins, make_policy_template_for_function_plugin
from samtranslator.parser.parser import Parser
from samtranslator.model.exceptions import InvalidDocumentException, InvalidResourceException
from samtranslator.model import Resource
from samtranslator.model.sam_resources import SamSimpleTable
from samtranslator.public.plugins import BasePlugin

from tests.translator.helpers import get_template_parameter_values
from tests.plugins.application.test_serverless_app_plugin import mock_get_region
from samtranslator.yaml_helper import yaml_parse
from parameterized import parameterized, param

import pytest
import yaml
from unittest import TestCase
from samtranslator.translator.transform import transform
from mock import Mock, MagicMock, patch

BASE_PATH = os.path.dirname(__file__)
INPUT_FOLDER = BASE_PATH + "/input"
OUTPUT_FOLDER = BASE_PATH + "/output"
# Do not sort AWS::Serverless::Function Layers Property.
# Order of Layers is an important attribute and shouldn't be changed.
DO_NOT_SORT = ["Layers"]

BASE_PATH = os.path.dirname(__file__)
INPUT_FOLDER = os.path.join(BASE_PATH, "input")
OUTPUT_FOLDER = os.path.join(BASE_PATH, "output")


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
        if sys.version_info.major < 3:
            # Py2 can sort lists with complex types like dictionaries
            return sorted((deep_sort_lists(x) for x in value))
        else:
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
        raise InvalidResourceException(logical_id, "Cannot access application: {}.".format(application_id))
    elif application_id == "non-existent":
        raise InvalidResourceException(logical_id, "Cannot access application: {}.".format(application_id))
    elif application_id == "invalid-semver":
        raise InvalidResourceException(logical_id, "Cannot access application: {}.".format(application_id))
    elif application_id == 1:
        raise InvalidResourceException(
            logical_id, "Type of property 'ApplicationId' is invalid.".format(application_id)
        )
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
    def _read_input(self, testcase):
        manifest = yaml_parse(open(os.path.join(INPUT_FOLDER, testcase + ".yaml"), "r"))
        # To uncover unicode-related bugs, convert dict to JSON string and parse JSON back to dict
        return json.loads(json.dumps(manifest))

    def _read_expected_output(self, testcase, partition):
        partition_folder = partition if partition != "aws" else ""
        expected_filepath = os.path.join(OUTPUT_FOLDER, partition_folder, testcase + ".json")
        return json.load(open(expected_filepath, "r"))

    def _compare_transform(self, manifest, expected, partition, region):
        with patch("boto3.session.Session.region_name", region):
            parameter_values = get_template_parameter_values()
            mock_policy_loader = MagicMock()
            mock_policy_loader.load.return_value = {
                "AWSLambdaBasicExecutionRole": "arn:{}:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole".format(
                    partition
                ),
                "AmazonDynamoDBFullAccess": "arn:{}:iam::aws:policy/AmazonDynamoDBFullAccess".format(partition),
                "AmazonDynamoDBReadOnlyAccess": "arn:{}:iam::aws:policy/AmazonDynamoDBReadOnlyAccess".format(partition),
                "AWSLambdaRole": "arn:{}:iam::aws:policy/service-role/AWSLambdaRole".format(partition),
            }
            if partition == "aws":
                mock_policy_loader.load.return_value[
                    "AWSXrayWriteOnlyAccess"
                ] = "arn:aws:iam::aws:policy/AWSXrayWriteOnlyAccess"
            else:
                mock_policy_loader.load.return_value[
                    "AWSXRayDaemonWriteAccess"
                ] = "arn:{}:iam::aws:policy/AWSXRayDaemonWriteAccess".format(partition)

            output_fragment = transform(manifest, parameter_values, mock_policy_loader)

        print(json.dumps(output_fragment, indent=2))

        # Only update the deployment Logical Id hash in Py3.
        if sys.version_info.major >= 3:
            self._update_logical_id_hash(expected)
            self._update_logical_id_hash(output_fragment)

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
            if "AWS::ApiGateway::RestApi" == resource_dict.get("Type"):
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
            if "AWS::ApiGateway::Deployment" == resource_dict.get("Type"):
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
            if "AWS::ApiGateway::Stage" == resource_dict.get("Type"):
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
        for output_key, output_value in resources.get("Outputs", {}).items():
            if output_value.get("Value").get("Ref") in deployment_logical_id_dict:
                output_value["Value"]["Ref"] = deployment_logical_id_dict[output_value.get("Value").get("Ref")]

    def _generate_new_deployment_hash(self, logical_id, dict_to_hash, rest_api_to_swagger_hash):
        data_bytes = json.dumps(dict_to_hash, separators=(",", ":"), sort_keys=True).encode("utf8")
        data_hash = hashlib.sha1(data_bytes).hexdigest()
        rest_api_to_swagger_hash[logical_id] = data_hash


class TestTranslatorEndToEnd(AbstractTestTranslator):
    @parameterized.expand(
        itertools.product(
            [
                "cognito_userpool_with_event",
                "s3_with_condition",
                "function_with_condition",
                "basic_function",
                "basic_function_withimageuri",
                "basic_application",
                "application_preparing_state",
                "application_with_intrinsics",
                "basic_layer",
                "basic_canary",
                "canary_with_policies",
                "canary_with_role",
                "canary_with_no_role",
                "canary_with_assume_role_policy",
                "canary_with_code",
                "canary_with_no_artifact_location",
                "canary_with_defined_artifact_location",
                "canary_with_alarms",
                "canaries_with_no_artifact_location_and_no_role",
                "cloudwatchevent",
                "eventbridgerule",
                "eventbridgerule_with_dlq",
                "eventbridgerule_with_retry_policy",
                "eventbridgerule_schedule_properties",
                "cloudwatch_logs_with_ref",
                "cloudwatchlog",
                "streams",
                "sqs",
                "function_with_amq",
                "function_with_amq_kms",
                "simpletable",
                "simpletable_with_sse",
                "implicit_api",
                "explicit_api",
                "api_description",
                "api_endpoint_configuration",
                "api_endpoint_configuration_with_vpcendpoint",
                "api_with_auth_all_maximum",
                "api_with_auth_all_minimum",
                "api_with_auth_no_default",
                "api_with_auth_with_default_scopes",
                "api_with_auth_with_default_scopes_openapi",
                "api_with_default_aws_iam_auth",
                "api_with_default_aws_iam_auth_and_no_auth_route",
                "api_with_method_aws_iam_auth",
                "api_with_aws_iam_auth_overrides",
                "api_with_swagger_authorizer_none",
                "api_with_method_settings",
                "api_with_binary_media_types",
                "api_with_binary_media_types_definition_body",
                "api_with_minimum_compression_size",
                "api_with_resource_refs",
                "api_with_cors",
                "api_with_cors_and_auth_no_preflight_auth",
                "api_with_cors_and_auth_preflight_auth",
                "api_with_cors_and_only_methods",
                "api_with_cors_and_only_headers",
                "api_with_cors_and_only_origins",
                "api_with_cors_and_only_maxage",
                "api_with_cors_and_only_credentials_false",
                "api_with_cors_no_definitionbody",
                "api_with_incompatible_stage_name",
                "api_with_gateway_responses",
                "api_with_gateway_responses_all",
                "api_with_gateway_responses_minimal",
                "api_with_gateway_responses_implicit",
                "api_with_gateway_responses_string_status_code",
                "api_cache",
                "api_with_access_log_setting",
                "api_with_canary_setting",
                "api_with_xray_tracing",
                "api_request_model",
                "api_with_stage_tags",
                "api_with_mode",
                "s3",
                "s3_create_remove",
                "s3_existing_lambda_notification_configuration",
                "s3_existing_other_notification_configuration",
                "s3_filter",
                "s3_multiple_events_same_bucket",
                "s3_multiple_functions",
                "s3_with_dependsOn",
                "sns",
                "sns_sqs",
                "sns_existing_sqs",
                "sns_outside_sqs",
                "sns_existing_other_subscription",
                "sns_topic_outside_template",
                "alexa_skill",
                "alexa_skill_with_skill_id",
                "iot_rule",
                "layers_with_intrinsics",
                "layers_all_properties",
                "layer_deletion_policy_precedence",
                "function_managed_inline_policy",
                "unsupported_resources",
                "intrinsic_functions",
                "basic_function_with_tags",
                "depends_on",
                "function_event_conditions",
                "function_with_dlq",
                "function_with_kmskeyarn",
                "function_with_alias",
                "function_with_alias_intrinsics",
                "function_with_custom_codedeploy_deployment_preference",
                "function_with_custom_conditional_codedeploy_deployment_preference",
                "function_with_disabled_deployment_preference",
                "function_with_deployment_preference",
                "function_with_deployment_preference_all_parameters",
                "function_with_deployment_preference_from_parameters",
                "function_with_deployment_preference_multiple_combinations",
                "function_with_deployment_preference_alarms_intrinsic_if",
                "function_with_alias_and_event_sources",
                "function_with_resource_refs",
                "function_with_deployment_and_custom_role",
                "function_with_deployment_no_service_role",
                "function_with_global_layers",
                "function_with_layers",
                "function_with_many_layers",
                "function_with_permissions_boundary",
                "function_with_policy_templates",
                "function_with_sns_event_source_all_parameters",
                "function_with_conditional_managed_policy",
                "function_with_conditional_managed_policy_and_ref_no_value",
                "function_with_conditional_policy_template",
                "function_with_conditional_policy_template_and_ref_no_value",
                "function_with_request_parameters",
                "function_with_signing_profile",
                "global_handle_path_level_parameter",
                "globals_for_function",
                "globals_for_api",
                "globals_for_simpletable",
                "all_policy_templates",
                "simple_table_ref_parameter_intrinsic",
                "simple_table_with_table_name",
                "function_concurrency",
                "simple_table_with_extra_tags",
                "explicit_api_with_invalid_events_config",
                "no_implicit_api_with_serverless_rest_api_resource",
                "implicit_api_deletion_policy_precedence",
                "implicit_api_with_serverless_rest_api_resource",
                "implicit_api_with_auth_and_conditions_max",
                "implicit_api_with_many_conditions",
                "implicit_and_explicit_api_with_conditions",
                "inline_precedence",
                "api_with_cors_and_conditions_no_definitionbody",
                "api_with_auth_and_conditions_all_max",
                "api_with_apikey_default_override",
                "api_with_apikey_required",
                "api_with_path_parameters",
                "function_with_event_source_mapping",
                "function_with_event_dest",
                "function_with_event_dest_basic",
                "function_with_event_dest_conditional",
                "api_with_usageplans",
                "api_with_usageplans_shared_attributes_two",
                "api_with_usageplans_shared_attributes_three",
                "api_with_usageplans_intrinsics",
                "state_machine_with_inline_definition",
                "state_machine_with_tags",
                "state_machine_with_inline_definition_intrinsics",
                "state_machine_with_role",
                "state_machine_with_inline_policies",
                "state_machine_with_sam_policy_templates",
                "state_machine_with_definition_S3_string",
                "state_machine_with_definition_S3_object",
                "state_machine_with_definition_substitutions",
                "state_machine_with_standard_logging",
                "state_machine_with_express_logging",
                "state_machine_with_managed_policy",
                "state_machine_with_condition",
                "state_machine_with_schedule",
                "state_machine_with_schedule_dlq_retry_policy",
                "state_machine_with_cwe",
                "state_machine_with_eb_retry_policy",
                "state_machine_with_eb_dlq",
                "state_machine_with_eb_dlq_generated",
                "state_machine_with_explicit_api",
                "state_machine_with_implicit_api",
                "state_machine_with_implicit_api_globals",
                "state_machine_with_api_authorizer",
                "state_machine_with_api_authorizer_maximum",
                "state_machine_with_api_resource_policy",
                "state_machine_with_api_auth_default_scopes",
                "state_machine_with_condition_and_events",
                "state_machine_with_xray_policies",
                "state_machine_with_xray_role",
                "function_with_file_system_config",
                "state_machine_with_permissions_boundary",
                "version_deletion_policy_precedence",
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
    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_transform_success(self, testcase, partition_with_region):
        partition = partition_with_region[0]
        region = partition_with_region[1]

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
                "api_request_model_openapi_3",
                "api_with_apikey_required_openapi_3",
                "api_with_basic_custom_domain",
                "api_with_basic_custom_domain_intrinsics",
                "api_with_custom_domain_route53",
                "api_with_custom_domain_route53_hosted_zone_name",
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
                "http_api_with_cors",
                "http_api_description",
                "http_api_lambda_auth",
                "http_api_lambda_auth_full",
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
    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_transform_success_openapi3(self, testcase, partition_with_region):
        partition = partition_with_region[0]
        region = partition_with_region[1]

        manifest = yaml_parse(open(os.path.join(INPUT_FOLDER, testcase + ".yaml"), "r"))
        # To uncover unicode-related bugs, convert dict to JSON string and parse JSON back to dict
        manifest = json.loads(json.dumps(manifest))
        partition_folder = partition if partition != "aws" else ""
        expected_filepath = os.path.join(OUTPUT_FOLDER, partition_folder, testcase + ".json")
        expected = json.load(open(expected_filepath, "r"))

        with patch("boto3.session.Session.region_name", region):
            parameter_values = get_template_parameter_values()
            mock_policy_loader = MagicMock()
            mock_policy_loader.load.return_value = {
                "AWSLambdaBasicExecutionRole": "arn:{}:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole".format(
                    partition
                ),
                "AmazonDynamoDBFullAccess": "arn:{}:iam::aws:policy/AmazonDynamoDBFullAccess".format(partition),
                "AmazonDynamoDBReadOnlyAccess": "arn:{}:iam::aws:policy/AmazonDynamoDBReadOnlyAccess".format(partition),
                "AWSLambdaRole": "arn:{}:iam::aws:policy/service-role/AWSLambdaRole".format(partition),
            }

            output_fragment = transform(manifest, parameter_values, mock_policy_loader)

        print(json.dumps(output_fragment, indent=2))

        # Only update the deployment Logical Id hash in Py3.
        if sys.version_info.major >= 3:
            self._update_logical_id_hash(expected)
            self._update_logical_id_hash(output_fragment)

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
    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_transform_success_resource_policy(self, testcase, partition_with_region):
        partition = partition_with_region[0]
        region = partition_with_region[1]

        manifest = yaml_parse(open(os.path.join(INPUT_FOLDER, testcase + ".yaml"), "r"))
        # To uncover unicode-related bugs, convert dict to JSON string and parse JSON back to dict
        manifest = json.loads(json.dumps(manifest))
        partition_folder = partition if partition != "aws" else ""
        expected_filepath = os.path.join(OUTPUT_FOLDER, partition_folder, testcase + ".json")
        expected = json.load(open(expected_filepath, "r"))

        with patch("boto3.session.Session.region_name", region):
            parameter_values = get_template_parameter_values()
            mock_policy_loader = MagicMock()
            mock_policy_loader.load.return_value = {
                "AWSLambdaBasicExecutionRole": "arn:{}:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole".format(
                    partition
                ),
                "AmazonDynamoDBFullAccess": "arn:{}:iam::aws:policy/AmazonDynamoDBFullAccess".format(partition),
                "AmazonDynamoDBReadOnlyAccess": "arn:{}:iam::aws:policy/AmazonDynamoDBReadOnlyAccess".format(partition),
                "AWSLambdaRole": "arn:{}:iam::aws:policy/service-role/AWSLambdaRole".format(partition),
            }

            output_fragment = transform(manifest, parameter_values, mock_policy_loader)
        print(json.dumps(output_fragment, indent=2))

        # Only update the deployment Logical Id hash in Py3.
        if sys.version_info.major >= 3:
            self._update_logical_id_hash(expected)
            self._update_logical_id_hash(output_fragment)

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
    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_transform_success_no_side_effect(self, testcase, partition_with_region):
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

        for template in testcase[1]:
            print(template, partition, region)
            manifest = self._read_input(template)
            expected = self._read_expected_output(template, partition)

            self._compare_transform(manifest, expected, partition, region)


@pytest.mark.parametrize(
    "testcase",
    [
        "error_canary_alarm_duplicate_alarm_names",
        "error_canary_alarm_invalid_format",
        "error_canary_alarm_with_no_metric_name",
        "error_canary_alarm_invalid_metric_name",
        "error_canary_no_handler",
        "error_canary_invalid_codeuri",
        "error_canary_no_code",
        "error_canary_no_schedule",
        "error_canary_no_start_canary",
        "error_existing_alarm_logical_id",
        "error_canary_existing_role_logical_id",
        "error_state_machine_definition_string",
        "error_state_machine_invalid_s3_object",
        "error_state_machine_invalid_s3_string",
        "error_state_machine_with_api_auth_none",
        "error_state_machine_with_no_api_authorizers",
        "error_state_machine_with_undefined_api_authorizer",
        "error_state_machine_with_invalid_default_authorizer",
        "error_state_machine_with_schedule_invalid_dlq_type",
        "error_state_machine_with_schedule_both_dlq_property_provided",
        "error_state_machine_with_schedule_missing_dlq_property",
        "error_state_machine_with_cwe_invalid_dlq_type",
        "error_state_machine_with_cwe_both_dlq_property_provided",
        "error_state_machine_with_cwe_missing_dlq_property",
        "error_cognito_userpool_duplicate_trigger",
        "error_cognito_userpool_not_string",
        "error_api_duplicate_methods_same_path",
        "error_api_gateway_responses_nonnumeric_status_code",
        "error_api_gateway_responses_unknown_responseparameter",
        "error_api_gateway_responses_unknown_responseparameter_property",
        "error_api_invalid_auth",
        "error_api_invalid_path",
        "error_api_invalid_definitionuri",
        "error_api_invalid_definitionbody",
        "error_api_invalid_stagename",
        "error_api_with_invalid_open_api_version",
        "error_api_invalid_restapiid",
        "error_api_invalid_request_model",
        "error_application_properties",
        "error_application_does_not_exist",
        "error_application_no_access",
        "error_application_preparing_timeout",
        "error_cors_on_external_swagger",
        "error_invalid_cors_dict",
        "error_invalid_findinmap",
        "error_invalid_getatt",
        "error_cors_credentials_true_with_wildcard_origin",
        "error_cors_credentials_true_without_explicit_origin",
        "error_function_invalid_codeuri",
        "error_function_invalid_api_event",
        "error_function_invalid_autopublishalias",
        "error_function_invalid_event_type",
        "error_function_invalid_layer",
        "error_function_no_codeuri",
        "error_function_no_handler",
        "error_function_no_runtime",
        "error_function_with_deployment_preference_invalid_alarms",
        "error_function_with_deployment_preference_missing_alias",
        "error_function_with_invalid_deployment_preference_hook_property",
        "error_function_invalid_request_parameters",
        "error_function_with_schedule_invalid_dlq_type",
        "error_function_with_schedule_both_dlq_property_provided",
        "error_function_with_schedule_missing_dlq_property",
        "error_function_with_cwe_invalid_dlq_type",
        "error_function_with_cwe_both_dlq_property_provided",
        "error_function_with_cwe_missing_dlq_property",
        "error_invalid_logical_id",
        "error_layer_invalid_properties",
        "error_missing_broker",
        "error_missing_queue",
        "error_missing_startingposition",
        "error_missing_stream",
        "error_multiple_resource_errors",
        "error_null_application_id",
        "error_s3_not_in_template",
        "error_table_invalid_attributetype",
        "error_table_primary_key_missing_name",
        "error_table_primary_key_missing_type",
        "error_invalid_resource_parameters",
        "error_reserved_sam_tag",
        "error_existing_event_logical_id",
        "error_existing_permission_logical_id",
        "error_existing_role_logical_id",
        "error_invalid_template",
        "error_resource_not_dict",
        "error_resource_properties_not_dict",
        "error_globals_is_not_dict",
        "error_globals_unsupported_type",
        "error_globals_unsupported_property",
        "error_globals_api_with_stage_name",
        "error_function_policy_template_with_missing_parameter",
        "error_function_policy_template_invalid_value",
        "error_function_with_unknown_policy_template",
        "error_function_with_invalid_policy_statement",
        "error_function_with_invalid_condition_name",
        "error_invalid_document_empty_semantic_version",
        "error_api_with_invalid_open_api_version_type",
        "error_api_with_invalid_auth_scopes_openapi",
        "error_api_with_custom_domains_invalid",
        "error_api_with_custom_domains_route53_invalid",
        "error_api_event_import_vaule_reference",
        "error_function_with_method_auth_and_no_api_auth",
        "error_function_with_no_alias_provisioned_concurrency",
        "error_http_api_def_body_uri",
        "error_http_api_event_invalid_api",
        "error_http_api_invalid_auth",
        "error_http_api_invalid_openapi",
        "error_http_api_tags",
        "error_http_api_tags_def_uri",
        "error_implicit_http_api_properties",
        "error_implicit_http_api_method",
        "error_implicit_http_api_path",
        "error_http_api_event_multiple_same_path",
        "error_function_with_event_dest_invalid",
        "error_function_with_event_dest_type",
        "error_function_with_api_key_false",
        "error_api_with_usage_plan_invalid_parameter",
        "error_http_api_with_cors_def_uri",
        "error_http_api_invalid_lambda_auth",
        "error_api_mtls_configuration_invalid_field",
        "error_api_mtls_configuration_invalid_type",
        "error_httpapi_mtls_configuration_invalid_field",
        "error_httpapi_mtls_configuration_invalid_type",
        "error_resource_policy_not_dict",
        "error_implicit_http_api_auth_any_method",
        "error_invalid_method_definition",
        "error_mappings_is_null",
        "error_swagger_security_not_dict",
    ],
)
@patch("boto3.session.Session.region_name", "ap-southeast-1")
@patch(
    "samtranslator.plugins.application.serverless_app_plugin.ServerlessAppPlugin._sar_service_call",
    mock_sar_service_call,
)
@patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
def test_transform_invalid_document(testcase):
    manifest = yaml_parse(open(os.path.join(INPUT_FOLDER, testcase + ".yaml"), "r"))
    expected = json.load(open(os.path.join(OUTPUT_FOLDER, testcase + ".json"), "r"))

    mock_policy_loader = MagicMock()
    parameter_values = get_template_parameter_values()

    with pytest.raises(InvalidDocumentException) as e:
        transform(manifest, parameter_values, mock_policy_loader)

    error_message = get_exception_error_message(e)

    assert error_message == expected.get("errorMessage")


@patch("boto3.session.Session.region_name", "ap-southeast-1")
@patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
def test_transform_unhandled_failure_empty_managed_policy_map():
    document = {
        "Transform": "AWS::Serverless-2016-10-31",
        "Resources": {
            "Resource": {
                "Type": "AWS::Serverless::Function",
                "Properties": {
                    "CodeUri": "s3://bucket/key",
                    "Handler": "index.handler",
                    "Runtime": "nodejs12.x",
                    "Policies": "AmazonS3FullAccess",
                },
            }
        },
    }

    parameter_values = get_template_parameter_values()
    mock_policy_loader = MagicMock()
    mock_policy_loader.load.return_value = {}

    with pytest.raises(Exception) as e:
        transform(document, parameter_values, mock_policy_loader)

    error_message = str(e.value)

    assert error_message == "Managed policy map is empty, but should not be."


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


class TestTemplateValidation(TestCase):
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


class TestPluginsUsage(TestCase):
    # Tests if plugins are properly injected into the translator

    @patch("samtranslator.translator.translator.make_policy_template_for_function_plugin")
    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_prepare_plugins_must_add_required_plugins(self, make_policy_template_for_function_plugin_mock):

        # This is currently the only required plugin
        plugin_instance = BasePlugin("something")
        make_policy_template_for_function_plugin_mock.return_value = plugin_instance

        sam_plugins = prepare_plugins([])
        self.assertEqual(6, len(sam_plugins))

    @patch("samtranslator.translator.translator.make_policy_template_for_function_plugin")
    @patch("botocore.client.ClientEndpointBridge._check_default_region", mock_get_region)
    def test_prepare_plugins_must_merge_input_plugins(self, make_policy_template_for_function_plugin_mock):

        required_plugin = BasePlugin("something")
        make_policy_template_for_function_plugin_mock.return_value = required_plugin

        custom_plugin = BasePlugin("someplugin")
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


def get_exception_error_message(e):
    return reduce(lambda message, error: message + " " + error.message, e.value.causes, e.value.message)
