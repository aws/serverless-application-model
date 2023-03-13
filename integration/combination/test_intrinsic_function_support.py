from unittest.case import skipIf

import pytest

from integration.config.service_names import REST_API
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([REST_API]), "Rest API is not supported in this testing region")
class TestIntrinsicFunctionsSupport(BaseTest):
    @pytest.fixture(autouse=True)
    def companion_stack_outputs(self, get_companion_stack_outputs):
        self.companion_stack_outputs = get_companion_stack_outputs

    # test serverless function properties support
    def test_serverless_function_property_support(self):
        # Just a simple deployment will validate that Code & Swagger files were accessible
        # Just a simple deployment will validate that all properties were resolved expected
        parameters = self.get_parameters(self.companion_stack_outputs)
        parameters.extend(self.get_default_test_template_parameters())
        self.create_and_verify_stack("combination/intrinsics_serverless_function", parameters)

    # test code definition uri object support
    def test_definition_uri_support(self):
        # Just a simple deployment will validate that Code & Swagger files were accessible
        # Just a simple deployment will validate that all properties were resolved expected
        parameters = self.get_default_test_template_parameters()
        self.create_and_verify_stack("combination/intrinsics_code_definition_uri", parameters)

    def test_severless_api_properties_support(self):
        self.create_and_verify_stack(
            "combination/intrinsics_serverless_api", self.get_default_test_template_parameters()
        )

        # Examine each resource policy and confirm that ARN contains correct APIGW stage
        lambda_function_name = self.get_physical_id_by_type("AWS::Lambda::Function")

        lambda_client = self.client_provider.lambda_client

        # This is a JSON string of resource policy
        policy = lambda_client.get_policy(FunctionName=lambda_function_name)["Policy"]

        # Instead of parsing the policy, we will verify that the policy contains certain strings
        # that we would expect based on the resource policy

        # This is the stage name specified in YAML template
        api_stage_name = "devstage"

        # Paths are specififed in the YAML template
        get_api_policy_expectation = "*/GET/pathget"
        post_api_policy_expectation = "*/POST/pathpost"

        self.assertTrue(
            get_api_policy_expectation in policy,
            f"{get_api_policy_expectation} should be present in policy {policy}",
        )
        self.assertTrue(
            post_api_policy_expectation in policy,
            f"{post_api_policy_expectation} should be present in policy {policy}",
        )

        # Test for tags
        function_result = lambda_client.get_function(FunctionName=lambda_function_name)
        tags = function_result["Tags"]

        self.assertIsNotNone(tags, "Expecting tags on function.")
        self.assertTrue("lambda:createdBy" in tags, "Expected 'lambda:CreatedBy' tag key, but not found.")
        self.assertEqual(tags["lambda:createdBy"], "SAM", "Expected 'SAM' tag value, but not found.")
        self.assertTrue("TagKey1" in tags)
        self.assertEqual(tags["TagKey1"], api_stage_name)

    def get_parameters(self, dictionary):
        parameters = []
        parameters.append(self.generate_parameter("PreCreatedSubnetOne", dictionary["PreCreatedSubnetOne"]))
        parameters.append(self.generate_parameter("PreCreatedVpc", dictionary["PreCreatedVpc"]))
        return parameters
