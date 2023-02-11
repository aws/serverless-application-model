from unittest.case import skipIf

from integration.config.service_names import REST_API
from integration.helpers.base_test import BaseTest
from integration.helpers.common_api import get_function_versions
from integration.helpers.resource import current_region_does_not_support


# Tests resource references support of SAM Function resource
class TestResourceReferences(BaseTest):
    def test_function_alias_references(self):
        self.create_and_verify_stack("combination/function_with_resource_refs")

        lambda_client = self.client_provider.lambda_client
        functions = self.get_stack_resources("AWS::Lambda::Function")
        function_names = [x["PhysicalResourceId"] for x in functions]

        main_function_name = next((x for x in function_names if "MyLambdaFunction" in x), None)
        other_function_name = next((x for x in function_names if "MyOtherFunction" in x), None)

        alias_result = lambda_client.get_alias(FunctionName=main_function_name, Name="Live")
        alias_arn = alias_result["AliasArn"]
        version_number = get_function_versions(main_function_name, lambda_client)[0]
        version_arn = lambda_client.get_function_configuration(
            FunctionName=main_function_name, Qualifier=version_number
        )["FunctionArn"]

        # Make sure the AliasArn is injected properly in all places where it is referenced
        other_function_env_var_result = lambda_client.get_function_configuration(FunctionName=other_function_name)
        other_function_env_var = other_function_env_var_result["Environment"]["Variables"]["AliasArn"]
        self.assertEqual(other_function_env_var, alias_arn)

        # Grab outputs from the stack
        stack_outputs = self.get_stack_outputs()
        self.assertEqual(stack_outputs["AliasArn"], alias_arn)
        self.assertEqual(stack_outputs["AliasInSub"], alias_arn + " Alias")
        self.assertEqual(stack_outputs["VersionNumber"], version_number)
        self.assertEqual(stack_outputs["VersionArn"], version_arn)

    @skipIf(current_region_does_not_support([REST_API]), "Rest API is not supported in this testing region")
    def test_api_with_resource_references(self):
        self.create_and_verify_stack("combination/api_with_resource_refs")

        rest_api_id = self.get_physical_id_by_type("AWS::ApiGateway::RestApi")

        apigw_client = self.client_provider.api_client
        stage_result = apigw_client.get_stage(restApiId=rest_api_id, stageName="Prod")

        stack_outputs = self.get_stack_outputs()
        self.assertEqual(stack_outputs["StageName"], "Prod")
        self.assertEqual(stack_outputs["ApiId"], rest_api_id)
        self.assertEqual(stack_outputs["DeploymentId"], stage_result["deploymentId"])
