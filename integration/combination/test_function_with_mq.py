from parameterized import parameterized

from integration.helpers.base_test import BaseTest


class TestFunctionWithMq(BaseTest):
    @parameterized.expand(
        [
            "combination/function_with_mq",
            "combination/function_with_mq_using_autogen_role",
        ]
    )
    def test_function_with_mq(self, file_name):
        self.create_and_verify_stack(file_name)

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


def get_broker_summary(mq_broker_id, mq_client):
    broker_summaries = mq_client.list_brokers()["BrokerSummaries"]
    return [broker_summary for broker_summary in broker_summaries if broker_summary["BrokerId"] == mq_broker_id]
