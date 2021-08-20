from unittest.case import skipIf

from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


class TestFunctionWithApplication(BaseTest):
    @skipIf(
        current_region_does_not_support(["ServerlessRepo"]), "ServerlessRepo is not supported in this testing region"
    )
    def test_function_referencing_outputs_from_application(self):
        self.create_and_verify_stack("combination/function_with_application")

        lambda_function_name = self.get_physical_id_by_type("AWS::Lambda::Function")
        nested_stack_name = self.get_physical_id_by_type("AWS::CloudFormation::Stack")
        lambda_client = self.client_provider.lambda_client
        cfn_client = self.client_provider.cfn_client

        function_config = lambda_client.get_function_configuration(FunctionName=lambda_function_name)
        stack_result = cfn_client.describe_stacks(StackName=nested_stack_name)
        expected = stack_result["Stacks"][0]["Outputs"][0]["OutputValue"]

        self.assertEqual(function_config["Environment"]["Variables"]["TABLE_NAME"], expected)
