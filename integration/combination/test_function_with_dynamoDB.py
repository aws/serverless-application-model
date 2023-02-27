from unittest.case import skipIf

from integration.config.service_names import DYNAMO_DB
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([DYNAMO_DB]), "DynamoDB is not supported in this testing region")
class TestFunctionWithDynamoDB(BaseTest):
    def test_function_with_dynamoDB_trigger(self):
        self.create_and_verify_stack("combination/function_with_dynamodb")

        ddb_id = self.get_physical_id_by_type("AWS::DynamoDB::Table")
        dynamodb_streams_client = self.client_provider.dynamodb_streams_client
        ddb_stream = dynamodb_streams_client.list_streams(TableName=ddb_id)["Streams"][0]

        lambda_client = self.client_provider.lambda_client
        function_name = self.get_physical_id_by_type("AWS::Lambda::Function")
        lambda_function_arn = lambda_client.get_function_configuration(FunctionName=function_name)["FunctionArn"]

        event_source_mapping_arn = self.get_physical_id_by_type("AWS::Lambda::EventSourceMapping")
        event_source_mapping_result = lambda_client.get_event_source_mapping(UUID=event_source_mapping_arn)
        event_source_mapping_batch_size = event_source_mapping_result["BatchSize"]
        event_source_mapping_function_arn = event_source_mapping_result["FunctionArn"]
        event_source_mapping_dynamodb_stream_arn = event_source_mapping_result["EventSourceArn"]

        self.assertEqual(event_source_mapping_batch_size, 10)
        self.assertEqual(event_source_mapping_function_arn, lambda_function_arn)
        self.assertEqual(event_source_mapping_dynamodb_stream_arn, ddb_stream["StreamArn"])
