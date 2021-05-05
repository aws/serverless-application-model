from integration.helpers.base_test import BaseTest


class TestFunctionWithMsk(BaseTest):
    def test_function_with_msk_trigger(self):
        self._common_validations_for_MSK("combination/function_with_msk")

    def test_function_with_msk_trigger_using_manage_policy(self):
        self._common_validations_for_MSK("combination/function_with_msk_using_managed_policy")

    def _common_validations_for_MSK(self, file_name):
        self.create_and_verify_stack(file_name)

        kafka_client = self.client_provider.kafka_client

        msk_cluster_id = self.get_physical_id_by_type("AWS::MSK::Cluster")
        cluster_info_list = kafka_client.list_clusters()["ClusterInfoList"]
        cluster_info = [x for x in cluster_info_list if x["ClusterArn"] == msk_cluster_id]

        self.assertEqual(len(cluster_info), 1, "One MSK cluster should be present")

        msk_cluster_arn = cluster_info[0]["ClusterArn"]
        lambda_client = self.client_provider.lambda_client
        function_name = self.get_physical_id_by_type("AWS::Lambda::Function")
        lambda_function_arn = lambda_client.get_function_configuration(FunctionName=function_name)["FunctionArn"]

        event_source_mapping_id = self.get_physical_id_by_type("AWS::Lambda::EventSourceMapping")
        event_source_mapping_result = lambda_client.get_event_source_mapping(UUID=event_source_mapping_id)

        event_source_mapping_function_arn = event_source_mapping_result["FunctionArn"]
        event_source_mapping_kafka_cluster_arn = event_source_mapping_result["EventSourceArn"]

        self.assertEqual(event_source_mapping_function_arn, lambda_function_arn)
        self.assertEqual(event_source_mapping_kafka_cluster_arn, msk_cluster_arn)
