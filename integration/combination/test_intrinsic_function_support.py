from parameterized import parameterized

from integration.helpers.base_test import BaseTest


class TestIntrinsicFunctionsSupport(BaseTest):

    # test code definition uri object and serverless function properties support
    @parameterized.expand(
        [
            "combination/intrinsics_code_definition_uri",
            "combination/intrinsics_serverless_function",
        ]
    )
    def test_common_support(self, file_name):
        # Just a simple deployment will validate that Code & Swagger files were accessible
        # Just a simple deployment will validate that all properties were resolved expected
        self.create_and_verify_stack(file_name, self.get_default_test_template_parameters())

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
            "{} should be present in policy {}".format(get_api_policy_expectation, policy),
        )
        self.assertTrue(
            post_api_policy_expectation in policy,
            "{} should be present in policy {}".format(post_api_policy_expectation, policy),
        )

        # Test for tags
        function_result = lambda_client.get_function(FunctionName=lambda_function_name)
        tags = function_result["Tags"]

        self.assertIsNotNone(tags, "Expecting tags on function.")
        self.assertTrue("lambda:createdBy" in tags, "Expected 'lambda:CreatedBy' tag key, but not found.")
        self.assertEqual(tags["lambda:createdBy"], "SAM", "Expected 'SAM' tag value, but not found.")
        self.assertTrue("TagKey1" in tags)
        self.assertEqual(tags["TagKey1"], api_stage_name)
