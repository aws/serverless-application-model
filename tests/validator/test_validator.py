import os.path
import pytest
from parameterized import parameterized
from unittest import TestCase
from samtranslator.yaml_helper import yaml_parse
from samtranslator.validator.validator import SamTemplateValidator, sam_schema

BASE_PATH = os.path.dirname(__file__)
TRANSLATOR_INPUT_FOLDER = os.path.join(BASE_PATH, os.pardir, "translator", "input")
VALIDATOR_INPUT_FOLDER = os.path.join(BASE_PATH, "input")


class TestValidatorProvider:
    validator = None

    @staticmethod
    def get():
        if TestValidatorProvider.validator is None:
            TestValidatorProvider.validator = SamTemplateValidator()
        return TestValidatorProvider.validator


class TestValidatorBase(TestCase):
    """
    Base class for TestValidator test classes

    Parameters
    ----------
    TestCase : TestCase
        unittest base class
    """

    def _test_validator_error(self, template, output):
        manifest = self._get_template_content(template)

        validation_errors = TestValidatorProvider.get().validate(manifest)

        errors = self._get_output_content(output)

        if len(validation_errors) != len(errors):
            self.fail(
                "Expected {} errors, found {}:\n{}".format(
                    len(errors), len(validation_errors), "\n".join(validation_errors)
                )
            )

        for i, v in enumerate(validation_errors):
            self.assertEqual(v, errors[i])

    def _test_validator_success(self, template):
        manifest = self._get_template_content(template)

        validation_errors = TestValidatorProvider.get().validate(manifest)

        self.assertFalse(validation_errors)

    def _get_template_content(self, template):
        """
        Returns the content of a template

        Parameters
        ----------
        template : str
            template path and name from the input dir (without .yaml)

        Returns
        -------
        str
            Template content
        """
        with open(template + ".yaml") as t:
            return yaml_parse(t)

    def _get_output_content(self, output):
        """
        Returns the content of an output file

        Parameters
        ----------
        output : str
            Output file path and name from the output dir (without .json)

        Returns
        -------
        str
            Output file content
        """
        with open(output + ".json") as t:
            return yaml_parse(t)


class TestValidatorTranslatorTemplates(TestValidatorBase):
    @parameterized.expand(
        [
            "alexa_skill",
            "all_policy_templates",
            "api_cache",
            "api_endpoint_configuration",
            "api_endpoint_configuration_with_vpcendpoint",
            "api_with_binary_media_types",
            "api_with_cors",
            "api_with_cors_and_only_headers",
            "api_with_cors_and_only_maxage",
            "api_with_cors_and_only_methods",
            "api_with_cors_and_only_origins",
            "api_with_method_settings",
            "api_with_minimum_compression_size",
            "api_with_resource_refs",
            "basic_function",
            "basic_function_with_tags",
            "cloudwatch_logs_with_ref",
            "cloudwatchevent",
            "cloudwatchlog",
            "depends_on",
            "eventbridgerule",
            "explicit_api",
            "explicit_api_with_invalid_events_config",
            "function_concurrency",
            "function_managed_inline_policy",
            "function_with_alias",
            "function_with_alias_and_event_sources",
            "function_with_alias_intrinsics",
            "function_with_deployment_and_custom_role",
            "function_with_deployment_no_service_role",
            "function_with_deployment_preference",
            "function_with_deployment_preference_all_parameters",
            "function_with_deployment_preference_from_parameters",
            "function_with_deployment_preference_multiple_combinations",
            "function_with_disabled_deployment_preference",
            "function_with_dlq",
            "function_with_kmskeyarn",
            "function_with_permissions_boundary",
            "function_with_policy_templates",
            "function_with_resource_refs",
            "function_with_sns_event_source_all_parameters",
            "globals_for_api",
            "globals_for_function",
            "globals_for_simpletable",
            "implicit_api",
            "intrinsic_functions",
            "iot_rule",
            "s3",
            "s3_create_remove",
            "s3_existing_lambda_notification_configuration",
            "s3_existing_other_notification_configuration",
            "s3_filter",
            "s3_multiple_events_same_bucket",
            "s3_multiple_functions",
            "simple_table_ref_parameter_intrinsic",
            "simple_table_with_extra_tags",
            "simple_table_with_table_name",
            "simpletable",
            "simpletable_with_sse",
            "sns",
            "sns_existing_other_subscription",
            "sns_topic_outside_template",
            "sqs",
            "streams",
            "unsupported_resources",
        ],
    )
    def test_success(self, testcase):
        manifest = yaml_parse(open(os.path.join(TRANSLATOR_INPUT_FOLDER, testcase + ".yaml")))
        validation_errors = TestValidatorProvider.get().validate(manifest)
        has_errors = len(validation_errors)
        if has_errors:
            print("\nFailing template: {0}\n".format(testcase))
            print(validation_errors)
        assert len(validation_errors) == 0


class TestValidatorLegacy(TestValidatorBase):
    def test_validate_using_old_interface_with_same_result(self):
        """
        Validates that the old deprecated static method returns the same result as the new one
        """
        manifest = yaml_parse(open(os.path.join(VALIDATOR_INPUT_FOLDER, "api", "success_complete_api.yaml")))

        old_validation_errors = SamTemplateValidator.validate(manifest)
        new_validation_errors = TestValidatorProvider.get().validate(manifest)

        self.assertEqual(old_validation_errors, ", ".join(new_validation_errors))
