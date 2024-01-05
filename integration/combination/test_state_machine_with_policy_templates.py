from unittest.case import skipIf

from integration.config.service_names import SQS
from integration.helpers.base_test import BaseTest
from integration.helpers.common_api import get_policy_statements
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([SQS]), "SQS is not supported in this testing region")
class TestStateMachineWithPolicyTemplates(BaseTest):
    def test_with_policy_templates(self):
        self.create_and_verify_stack("combination/state_machine_with_policy_templates")

        state_machine_role_name = self.get_stack_outputs()["MyStateMachineRole"]

        # There should be two policies created. Each policy has the name <resource-logicalid>Policy<index>

        # Verify the contents of first policy
        sqs_poller_policy = get_policy_statements(
            state_machine_role_name, "MyStateMachineRolePolicy0", self.client_provider.iam_client
        )
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
            state_machine_role_name, "MyStateMachineRolePolicy1", self.client_provider.iam_client
        )
        self.assertEqual(len(lambda_invoke_policy), 1, "One policies statements should be present")

        lambda_policy_statement = lambda_invoke_policy[0]
        self.assertFalse(isinstance(lambda_policy_statement["Resource"], list))

        function_name = self.get_physical_id_by_type("AWS::Lambda::Function")
        #  NOTE: The resource ARN has "*" suffix to allow for any Lambda function version as well
        expected_function_suffix = "function:" + function_name + "*"
        actual_function_arn = lambda_policy_statement["Resource"]
        self.assertTrue(
            actual_function_arn.endswith(expected_function_suffix),
            "Function ARN " + actual_function_arn + " must end with suffix " + expected_function_suffix,
        )
