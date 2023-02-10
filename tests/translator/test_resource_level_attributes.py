import itertools
from unittest.mock import patch

from parameterized import parameterized

from tests.translator.test_translator import AbstractTestTranslator, mock_sar_service_call


class TestResourceLevelAttributes(AbstractTestTranslator):
    @parameterized.expand(
        itertools.product(
            [
                "cognito_userpool_with_event",
                "s3_with_condition",
                "function_with_condition",
                "basic_function",
                "basic_application",
                "application_with_intrinsics",
                "cloudwatchevent",
                "eventbridgerule",
                "cloudwatchlog",
                "streams",
                "sqs",
                "function_with_amq",
                "simpletable",
                "implicit_api",
                "explicit_api",
                "api_description",
                "s3",
                "sns",
                "alexa_skill",
                "iot_rule",
                "layers_all_properties",
                "unsupported_resources",
                "intrinsic_functions",
                "basic_function_with_tags",
                "depends_on",
                "function_event_conditions",
                "function_with_alias",
                "function_with_layers",
                "global_handle_path_level_parameter",
                "all_policy_templates",
                "simple_table_ref_parameter_intrinsic",
                "implicit_api_with_serverless_rest_api_resource",
                "api_with_cors_and_conditions_no_definitionbody",
                "api_with_auth_and_conditions_all_max",
                "api_with_apikey_required",
                "api_with_path_parameters",
                "function_with_event_source_mapping",
                "api_with_usageplans",
                "state_machine_with_inline_definition",
                "function_with_file_system_config",
                "state_machine_with_permissions_boundary",
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
    def test_transform_with_additional_resource_level_attributes(
        self, testcase, partition_with_region, mock_get_region_from_session
    ):
        partition = partition_with_region[0]
        region = partition_with_region[1]
        mock_get_region_from_session.return_value = region

        # add resource level attributes to input resources
        manifest = self._read_input(testcase)
        resources = manifest.get("Resources", [])
        for _, resource in resources.items():
            resource["DeletionPolicy"] = "Delete"
            resource["UpdateReplacePolicy"] = "Retain"

        # add resource level attributes to expected output resources
        expected = self._read_expected_output(testcase, partition)
        expected_resources = expected.get("Resources", [])
        for _, expected_resource in expected_resources.items():
            expected_resource["DeletionPolicy"] = "Delete"
            expected_resource["UpdateReplacePolicy"] = "Retain"

        self._compare_transform(manifest, expected, partition, region)
