from unittest.case import skipIf

import pytest

from integration.config.service_names import MSK
from integration.helpers.base_test import BaseTest, nonblocking
from integration.helpers.resource import current_region_does_not_support, generate_suffix


@skipIf(current_region_does_not_support([MSK]), "MSK is not supported in this testing region")
@nonblocking
class TestFunctionWithMsk(BaseTest):
    @pytest.fixture(autouse=True)
    def companion_stack_outputs(self, get_companion_stack_outputs):
        self.companion_stack_outputs = get_companion_stack_outputs

    def test_function_with_msk_trigger(self):
        companion_stack_outputs = self.companion_stack_outputs
        parameters = self.get_parameters(companion_stack_outputs)
        cluster_name = "MskCluster-" + generate_suffix()
        parameters.append(self.generate_parameter("MskClusterName", cluster_name))
        self._common_validations_for_MSK("combination/function_with_msk", parameters)

    def test_function_with_msk_trigger_using_manage_policy(self):
        companion_stack_outputs = self.companion_stack_outputs
        parameters = self.get_parameters(companion_stack_outputs)
        cluster_name = "MskCluster2-" + generate_suffix()
        parameters.append(self.generate_parameter("MskClusterName2", cluster_name))
        self._common_validations_for_MSK("combination/function_with_msk_using_managed_policy", parameters)

    def _common_validations_for_MSK(self, file_name, parameters):
        self.create_and_verify_stack(file_name, parameters)

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

    def get_parameters(self, dictionary):
        parameters = []
        parameters.append(self.generate_parameter("PreCreatedSubnetOne", dictionary["PreCreatedSubnetOne"]))
        parameters.append(self.generate_parameter("PreCreatedSubnetTwo", dictionary["PreCreatedSubnetTwo"]))
        return parameters
