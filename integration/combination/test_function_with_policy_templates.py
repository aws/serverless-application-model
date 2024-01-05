from integration.helpers.base_test import BaseTest
from integration.helpers.common_api import get_policy_statements


class TestFunctionWithPolicyTemplates(BaseTest):
    def test_with_policy_templates(self):
        self.create_and_verify_stack("combination/function_with_policy_templates")
        role_name = self.get_physical_id_by_type("AWS::IAM::Role")

        # There should be three policies created. Each policy has the name <resource-logicalid>Policy<index>

        # Verify the contents of first policy
        sqs_poller_policy = get_policy_statements(role_name, "MyFunctionRolePolicy0", self.client_provider.iam_client)
        self.assertEqual(len(sqs_poller_policy), 1, "Only one statement must be in SQS Poller policy")

        sqs_policy_statement = sqs_poller_policy[0]
        self.assertFalse(isinstance(sqs_policy_statement["Resource"], list))

        queue_url = self.get_physical_id_by_type("AWS::SQS::Queue")
        parts = queue_url.split("/")
        expected_queue_name = parts[-1]
        actual_queue_arn = sqs_policy_statement["Resource"]
        self.assertTrue(
            actual_queue_arn.endswith(expected_queue_name),
            "Queue Arn " + actual_queue_arn + " must end with suffix " + expected_queue_name,
        )

        # Verify the contents of second policy
        lambda_invoke_policy = get_policy_statements(
            role_name, "MyFunctionRolePolicy1", self.client_provider.iam_client
        )
        self.assertEqual(len(lambda_invoke_policy), 1, "One policies statements should be present")

        lambda_policy_statement = lambda_invoke_policy[0]
        self.assertFalse(isinstance(lambda_policy_statement["Resource"], list))

        #  NOTE: The resource ARN has "*" suffix to allow for any Lambda function version as well
        expected_function_suffix = "function:somename*"
        actual_function_arn = lambda_policy_statement["Resource"]
        self.assertTrue(
            actual_function_arn.endswith(expected_function_suffix),
            "Function ARN " + actual_function_arn + " must end with suffix " + expected_function_suffix,
        )

        # Verify the contents of third policy
        cloud_watch_put_metric_policy = get_policy_statements(
            role_name, "MyFunctionRolePolicy2", self.client_provider.iam_client
        )
        self.assertEqual(
            len(cloud_watch_put_metric_policy), 1, "Only one statement must be in CloudWatchPutMetricPolicy"
        )

        cloud_watch_put_metric_statement = cloud_watch_put_metric_policy[0]
        self.assertEqual(cloud_watch_put_metric_statement.get("Resource"), "*")

    def test_all_policy_templates(self):
        # template too large, upload it to s3
        self.create_and_verify_stack("combination/all_policy_templates", s3_uploader=self.s3_uploader)

        iam_roles = self.get_stack_resources("AWS::IAM::Role")
        actual_num_polices = 0

        for iam_role in iam_roles:
            role_name = iam_role.get("PhysicalResourceId")
            result = self.client_provider.iam_client.list_role_policies(RoleName=role_name)
            policy_names = result.get("PolicyNames")
            actual_num_polices += len(policy_names)

        expected_num_polices = 69
        self.assertEqual(actual_num_polices, expected_num_polices)
