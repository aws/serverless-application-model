from unittest.case import skipIf

import pytest

from integration.config.service_names import MSK
from integration.helpers.base_test import BaseTest, nonblocking
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([MSK]), "MSK is not supported in this testing region")
@nonblocking
class TestFunctionWithMsk(BaseTest):
    @pytest.fixture(autouse=True)
    def companion_stack_outputs(self, get_companion_stack_outputs):
        self.companion_stack_outputs = get_companion_stack_outputs

    def test_function_with_msk_trigger(self):
        parameters = self.get_parameters()
        self._common_validations_for_MSK("combination/function_with_msk", parameters)

    def test_function_with_msk_trigger_using_manage_policy(self):
        parameters = self.get_parameters()
        self._common_validations_for_MSK("combination/function_with_msk_using_managed_policy", parameters)

    def test_function_with_msk_trigger_and_s3_onfailure_events_destinations(self):
        parameters = self.get_parameters()
        self._common_validations_for_MSK(
            "combination/function_with_msk_trigger_and_s3_onfailure_events_destinations", parameters
        )

    def test_function_with_msk_trigger_and_premium_features(self):
        parameters = self.get_parameters()
        self._common_validations_for_MSK("combination/function_with_msk_trigger_and_premium_features", parameters)
        event_source_mapping_result = self._common_validations_for_MSK(
            "combination/function_with_msk_trigger_and_confluent_schema_registry", parameters
        )
        self.assertTrue(event_source_mapping_result.get("BisectBatchOnFunctionError"))
        self.assertEqual(event_source_mapping_result.get("MaximumRecordAgeInSeconds"), 3600)
        self.assertEqual(event_source_mapping_result.get("MaximumRetryAttempts"), 3)
        self.assertEqual(event_source_mapping_result.get("FunctionResponseTypes"), ["ReportBatchItemFailures"])

    def _common_validations_for_MSK(self, file_name, parameters):
        self.create_and_verify_stack(file_name, parameters)

        msk_cluster_arn = self.companion_stack_outputs["PreCreatedMskClusterArn"]

        lambda_client = self.client_provider.lambda_client
        function_name = self.get_physical_id_by_type("AWS::Lambda::Function")
        lambda_function_arn = lambda_client.get_function_configuration(FunctionName=function_name)["FunctionArn"]

        event_source_mapping_id = self.get_physical_id_by_type("AWS::Lambda::EventSourceMapping")
        event_source_mapping_result = lambda_client.get_event_source_mapping(UUID=event_source_mapping_id)

        event_source_mapping_function_arn = event_source_mapping_result["FunctionArn"]
        event_source_mapping_kafka_cluster_arn = event_source_mapping_result["EventSourceArn"]

        self.assertEqual(event_source_mapping_function_arn, lambda_function_arn)
        self.assertEqual(event_source_mapping_kafka_cluster_arn, msk_cluster_arn)
        return event_source_mapping_result

    def get_parameters(self):
        return [
            self.generate_parameter("PreCreatedMskClusterArn", self.companion_stack_outputs["PreCreatedMskClusterArn"]),
        ]
