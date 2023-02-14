from unittest.case import skipIf

from integration.config.service_names import SQS
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([SQS]), "SQS is not supported in this testing region")
class TestFunctionWithSQS(BaseTest):
    def test_function_with_sqs_bucket_trigger(self):
        self.create_and_verify_stack("combination/function_with_sqs")

        sqs_client = self.client_provider.sqs_client
        sqs_queue_url = self.get_physical_id_by_type("AWS::SQS::Queue")
        queue_attributes = sqs_client.get_queue_attributes(QueueUrl=sqs_queue_url, AttributeNames=["QueueArn"])[
            "Attributes"
        ]
        sqs_queue_arn = queue_attributes["QueueArn"]

        lambda_client = self.client_provider.lambda_client
        function_name = self.get_physical_id_by_type("AWS::Lambda::Function")
        lambda_function_arn = lambda_client.get_function_configuration(FunctionName=function_name)["FunctionArn"]

        event_source_mapping_arn = self.get_physical_id_by_type("AWS::Lambda::EventSourceMapping")
        event_source_mapping_result = lambda_client.get_event_source_mapping(UUID=event_source_mapping_arn)

        self.assertEqual(event_source_mapping_result["BatchSize"], 2)
        self.assertEqual(event_source_mapping_result["FunctionArn"], lambda_function_arn)
        self.assertEqual(event_source_mapping_result["EventSourceArn"], sqs_queue_arn)
