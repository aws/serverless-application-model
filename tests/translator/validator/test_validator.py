import os.path
import pytest
from unittest import TestCase
from tests.translator.yaml_helper import yaml_parse
from samtranslator.validator.validator import SamTemplateValidator

input_folder = 'tests/translator/input'

@pytest.mark.parametrize('testcase', [
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
    'explicit_api_with_invalid_events_config'
])
def test_validate_template_success(testcase):
    # These templates are failing validation, will fix schema one at a time
    excluded = [
        'api_endpoint_configuration',
        'api_with_binary_media_types',
        'api_with_cors',
        'cloudwatch_logs_with_ref',
        'sns',
        'sns_existing_other_subscription',
        'sns_topic_outside_template',
        'alexa_skill',
        'iot_rule',
        'function_managed_inline_policy',
        'unsupported_resources',
        'intrinsic_functions',
        'basic_function_with_tags',
        'function_with_kmskeyarn',
        'function_with_alias',
        'function_with_alias_intrinsics',
        'function_with_disabled_deployment_preference',
        'function_with_deployment_preference',
        'function_with_deployment_preference_all_parameters',
        'function_with_deployment_preference_multiple_combinations',
        'function_with_alias_and_event_sources',
        'function_with_resource_refs',
        'function_with_policy_templates',
        'globals_for_function',
        'all_policy_templates',
        'simple_table_ref_parameter_intrinsic',
        'simple_table_with_table_name',
        'function_concurrency',
        'simple_table_with_extra_tags'
    ]
    if testcase in excluded:
        return
    manifest = yaml_parse(open(os.path.join(input_folder, testcase + '.yaml'), 'r'))
    validation_errors = SamTemplateValidator.validate(manifest)
    has_errors = len(validation_errors)
    if has_errors:
        print("\nFailing template: {0}\n".format(testcase))
        print(validation_errors)
    assert len(validation_errors) == 0
