from unittest.case import skipIf

from integration.config.service_names import CWE_CWS_DLQ
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([CWE_CWS_DLQ]), "CweCwsDlq is not supported in this testing region")
class TestFunctionWithCweDlqAndRetryPolicy(BaseTest):
    def test_function_with_cwe(self):
        # Verifying that following resources were created is correct
        self.create_and_verify_stack("combination/function_with_cwe_dlq_and_retry_policy")
        outputs = self.get_stack_outputs()
        lambda_target_arn = outputs["MyLambdaArn"]
        rule_name = outputs["MyEventName"]
        lambda_target_dlq_arn = outputs["MyDLQArn"]

        cloud_watch_event_client = self.client_provider.cloudwatch_event_client
        # checking if the target's DLQ and RetryPolicy properties are correct
        targets = cloud_watch_event_client.list_targets_by_rule(Rule=rule_name)["Targets"]

        self.assertEqual(len(targets), 1, "Rule should contain a single target")

        target = targets[0]
        self.assertEqual(target["Arn"], lambda_target_arn)
        self.assertEqual(target["DeadLetterConfig"]["Arn"], lambda_target_dlq_arn)

        self.assertEqual(target["RetryPolicy"]["MaximumEventAgeInSeconds"], 900)
        self.assertEqual(target["RetryPolicy"]["MaximumRetryAttempts"], 6)
