from unittest.case import skipIf

from integration.config.service_names import REST_API
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([REST_API]), "Rest API is not supported in this testing region")
class TestFunctionWithApi(BaseTest):
    def test_function_with_api(self):
        self.create_and_verify_stack("combination/function_with_api")

        # Examine each resource policy and confirm that ARN contains correct APIGW stage
        physical_api_id = self.get_physical_id_by_type("AWS::ApiGateway::RestApi")
        lambda_function_name = self.get_physical_id_by_type("AWS::Lambda::Function")

        lambda_client = self.client_provider.lambda_client
        policy_response = lambda_client.get_policy(FunctionName=lambda_function_name)
        # This is a JSON string of resource policy
        policy = policy_response["Policy"]

        # Instead of parsing the policy, we will verify that the policy contains certain strings
        # that we would expect based on the resource policy

        # Paths are specified in the YAML template
        get_api_policy_expectation = "{}/{}/{}/{}".format(physical_api_id, "*", "GET", "pathget")
        post_api_policy_expectation = "{}/{}/{}/{}".format(physical_api_id, "*", "POST", "pathpost")

        self.assertTrue(
            get_api_policy_expectation in policy,
            f"{get_api_policy_expectation} should be present in policy {policy}",
        )
        self.assertTrue(
            post_api_policy_expectation in policy,
            f"{post_api_policy_expectation} should be present in policy {policy}",
        )
