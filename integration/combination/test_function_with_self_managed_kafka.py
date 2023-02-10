from unittest.case import skipIf

import pytest
from parameterized import parameterized

from integration.config.service_names import SELF_MANAGED_KAFKA
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_not_included


@skipIf(
    current_region_not_included([SELF_MANAGED_KAFKA]),
    "SelfManagedKafka testing is not performed in this testing region",
)
class TestFunctionWithSelfManagedKafka(BaseTest):
    @pytest.mark.flaky(reruns=5)
    @parameterized.expand(
        [
            "combination/function_with_self_managed_kafka",
            "combination/function_with_self_managed_kafka_intrinsics",
        ]
    )
    def test_function_with_self_managed_kafka(self, file_name):
        self.create_and_verify_stack(file_name)
        # Get the notification configuration and make sure Lambda Function connection is added
        lambda_client = self.client_provider.lambda_client
        function_name = self.get_physical_id_by_type("AWS::Lambda::Function")
        lambda_function_arn = lambda_client.get_function_configuration(FunctionName=function_name)["FunctionArn"]
        event_source_mapping_id = self.get_physical_id_by_type("AWS::Lambda::EventSourceMapping")
        event_source_mapping_result = lambda_client.get_event_source_mapping(UUID=event_source_mapping_id)
        event_source_mapping_function_arn = event_source_mapping_result["FunctionArn"]
        self.assertEqual(event_source_mapping_function_arn, lambda_function_arn)
