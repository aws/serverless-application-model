from integration.helpers.base_test import BaseTest


class TestFunctionWithLayers(BaseTest):
    def test_function_with_layer(self):
        self.create_and_verify_stack("combination/function_with_layer")

        lambda_function_name = self.get_physical_id_by_type("AWS::Lambda::Function")
        lambda_client = self.client_provider.lambda_client

        function_configuration_result = lambda_client.get_function_configuration(FunctionName=lambda_function_name)

        # Get the layer ARN from the stack and from the lambda function and verify they're the same
        lambda_layer_version_arn = self.get_physical_id_by_type("AWS::Lambda::LayerVersion")

        lambda_function_layer_reference_arn = function_configuration_result["Layers"][0]["Arn"]
        self.assertEqual(lambda_function_layer_reference_arn, lambda_layer_version_arn)
