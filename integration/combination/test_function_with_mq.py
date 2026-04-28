from unittest.case import skipIf

import pytest
from parameterized import parameterized

from integration.config.service_names import MQ
from integration.helpers.base_test import BaseTest, nonblocking
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([MQ]), "MQ is not supported in this testing region")
class TestFunctionWithMq(BaseTest):
    @pytest.fixture(autouse=True)
    def companion_stack_outputs(self, get_companion_stack_outputs):
        self.companion_stack_outputs = get_companion_stack_outputs

    @parameterized.expand(
        [
            ("combination/function_with_mq",),
            ("combination/function_with_mq_using_autogen_role",),
        ]
    )
    @nonblocking
    def test_function_with_mq(self, file_name):
        companion_stack_outputs = self.companion_stack_outputs
        parameters = [
            self.generate_parameter("PreCreatedMqBrokerArn", companion_stack_outputs["PreCreatedMqBrokerArn"]),
            self.generate_parameter(
                "PreCreatedMqBrokerSecretArn", companion_stack_outputs["PreCreatedMqBrokerSecretArn"]
            ),
        ]

        self.create_and_verify_stack(file_name, parameters)

        mq_broker_arn = companion_stack_outputs["PreCreatedMqBrokerArn"]

        lambda_client = self.client_provider.lambda_client
        function_name = self.get_physical_id_by_type("AWS::Lambda::Function")
        lambda_function_arn = lambda_client.get_function_configuration(FunctionName=function_name)["FunctionArn"]

        event_source_mapping_id = self.get_physical_id_by_type("AWS::Lambda::EventSourceMapping")
        event_source_mapping_result = lambda_client.get_event_source_mapping(UUID=event_source_mapping_id)
        event_source_mapping_function_arn = event_source_mapping_result["FunctionArn"]
        event_source_mapping_mq_broker_arn = event_source_mapping_result["EventSourceArn"]

        self.assertEqual(event_source_mapping_function_arn, lambda_function_arn)
        self.assertEqual(event_source_mapping_mq_broker_arn, mq_broker_arn)
