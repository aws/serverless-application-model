from unittest.case import skipIf

import pytest
from parameterized import parameterized

from integration.config.service_names import MQ
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support, generate_suffix


@skipIf(current_region_does_not_support([MQ]), "MQ is not supported in this testing region")
class TestFunctionWithMq(BaseTest):
    @pytest.fixture(autouse=True)
    def companion_stack_outputs(self, get_companion_stack_outputs):
        self.companion_stack_outputs = get_companion_stack_outputs

    @parameterized.expand(
        [
            ("combination/function_with_mq", "MQBrokerName", "MQBrokerUserSecretName", "PreCreatedSubnetOne"),
            (
                "combination/function_with_mq_using_autogen_role",
                "MQBrokerName2",
                "MQBrokerUserSecretName2",
                "PreCreatedSubnetTwo",
            ),
        ]
    )
    def test_function_with_mq(self, file_name, mq_broker, mq_secret, subnet_key):
        # Temporarily skip this test and we should either re-enable this once the AZ issue is fixed
        # or once we figure out a way to trigger integ test only when transform output changes.
        if subnet_key == "PreCreatedSubnetOne":
            pytest.skip("Skipping this test to temporarily bypass AvailabilityZone issue.")
        companion_stack_outputs = self.companion_stack_outputs
        parameters = self.get_parameters(companion_stack_outputs, subnet_key)
        secret_name = mq_secret + "-" + generate_suffix()
        parameters.append(self.generate_parameter(mq_secret, secret_name))
        secret_name = mq_broker + "-" + generate_suffix()
        parameters.append(self.generate_parameter(mq_broker, secret_name))

        self.create_and_verify_stack(file_name, parameters)

        mq_client = self.client_provider.mq_client
        mq_broker_id = self.get_physical_id_by_type("AWS::AmazonMQ::Broker")
        broker_summary = get_broker_summary(mq_broker_id, mq_client)

        self.assertEqual(len(broker_summary), 1, "One MQ cluster should be present")
        mq_broker_arn = broker_summary[0]["BrokerArn"]

        lambda_client = self.client_provider.lambda_client
        function_name = self.get_physical_id_by_type("AWS::Lambda::Function")
        lambda_function_arn = lambda_client.get_function_configuration(FunctionName=function_name)["FunctionArn"]

        event_source_mapping_id = self.get_physical_id_by_type("AWS::Lambda::EventSourceMapping")
        event_source_mapping_result = lambda_client.get_event_source_mapping(UUID=event_source_mapping_id)
        event_source_mapping_function_arn = event_source_mapping_result["FunctionArn"]
        event_source_mapping_mq_broker_arn = event_source_mapping_result["EventSourceArn"]

        self.assertEqual(event_source_mapping_function_arn, lambda_function_arn)
        self.assertEqual(event_source_mapping_mq_broker_arn, mq_broker_arn)

    def get_parameters(self, dictionary, subnet_key):
        parameters = []
        parameters.append(self.generate_parameter("PreCreatedVpc", dictionary["PreCreatedVpc"]))
        parameters.append(self.generate_parameter(subnet_key, dictionary[subnet_key]))
        parameters.append(self.generate_parameter("PreCreatedInternetGateway", dictionary["PreCreatedInternetGateway"]))
        return parameters


def get_broker_summary(mq_broker_id, mq_client):
    broker_summaries = mq_client.list_brokers()["BrokerSummaries"]
    return [broker_summary for broker_summary in broker_summaries if broker_summary["BrokerId"] == mq_broker_id]
