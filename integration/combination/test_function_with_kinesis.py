from integration.helpers.base_test import BaseTest


class TestFunctionWithKinesis(BaseTest):
    def test_function_with_kinesis_trigger(self):
        self.create_and_verify_stack("combination/function_with_kinesis")

        kinesis_client = self.client_provider.kinesis_client
        kinesis_id = self.get_physical_id_by_type("AWS::Kinesis::Stream")
        kinesis_stream = kinesis_client.describe_stream(StreamName=kinesis_id)["StreamDescription"]

        lambda_client = self.client_provider.lambda_client
        function_name = self.get_physical_id_by_type("AWS::Lambda::Function")
        lambda_function_arn = lambda_client.get_function_configuration(FunctionName=function_name)["FunctionArn"]

        event_source_mapping_arn = self.get_physical_id_by_type("AWS::Lambda::EventSourceMapping")
        event_source_mapping_result = lambda_client.get_event_source_mapping(UUID=event_source_mapping_arn)
        event_source_mapping_batch_size = event_source_mapping_result["BatchSize"]
        event_source_mapping_function_arn = event_source_mapping_result["FunctionArn"]
        event_source_mapping_kinesis_stream_arn = event_source_mapping_result["EventSourceArn"]

        self.assertEqual(event_source_mapping_batch_size, 100)
        self.assertEqual(event_source_mapping_function_arn, lambda_function_arn)
        self.assertEqual(event_source_mapping_kinesis_stream_arn, kinesis_stream["StreamARN"])


class TestFunctionWithKinesisIntrinsics(BaseTest):
    def test_function_with_kinesis_trigger(self):
        self.create_and_verify_stack("combination/function_with_kinesis_intrinsics")

        kinesis_client = self.client_provider.kinesis_client
        kinesis_id = self.get_physical_id_by_type("AWS::Kinesis::Stream")
        kinesis_stream = kinesis_client.describe_stream(StreamName=kinesis_id)["StreamDescription"]

        lambda_client = self.client_provider.lambda_client
        function_name = self.get_physical_id_by_type("AWS::Lambda::Function")
        lambda_function_arn = lambda_client.get_function_configuration(FunctionName=function_name)["FunctionArn"]

        event_source_mapping_arn = self.get_physical_id_by_type("AWS::Lambda::EventSourceMapping")
        event_source_mapping_result = lambda_client.get_event_source_mapping(UUID=event_source_mapping_arn)
        event_source_mapping_batch_size = event_source_mapping_result["BatchSize"]
        event_source_mapping_function_arn = event_source_mapping_result["FunctionArn"]
        event_source_mapping_kinesis_stream_arn = event_source_mapping_result["EventSourceArn"]

        self.assertEqual(event_source_mapping_batch_size, 100)
        self.assertEqual(event_source_mapping_function_arn, lambda_function_arn)
        self.assertEqual(event_source_mapping_kinesis_stream_arn, kinesis_stream["StreamARN"])
