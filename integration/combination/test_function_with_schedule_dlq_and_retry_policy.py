from unittest.case import skipIf

from integration.config.service_names import CWE_CWS_DLQ
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([CWE_CWS_DLQ]), "CweCwsDlq is not supported in this testing region")
class TestFunctionWithScheduleDlqAndRetryPolicy(BaseTest):
    def test_function_with_schedule(self):
        self.create_and_verify_stack("combination/function_with_schedule_dlq_and_retry_policy")

        stack_outputs = self.get_stack_outputs()
        schedule_name = stack_outputs["ScheduleName"]
        lambda_target_dlq_arn = stack_outputs["MyDLQArn"]

        cloud_watch_events_client = self.client_provider.cloudwatch_event_client

        # get the cloudwatch schedule rule
        cw_rule_result = cloud_watch_events_client.describe_rule(Name=schedule_name)

        # checking if the name, description and state properties are correct
        self.assertEqual(cw_rule_result["Name"], schedule_name)
        self.assertEqual(cw_rule_result["Description"], "test schedule")
        self.assertEqual(cw_rule_result["State"], "ENABLED")
        self.assertEqual(cw_rule_result["ScheduleExpression"], "rate(5 minutes)")

        # checking if the target's DLQ and RetryPolicy properties are correct
        targets = cloud_watch_events_client.list_targets_by_rule(Rule=schedule_name)["Targets"]

        self.assertEqual(len(targets), 1, "Rule should contain a single target")
        target = targets[0]

        self.assertEqual(target["DeadLetterConfig"]["Arn"], lambda_target_dlq_arn)
        self.assertIsNone(target["RetryPolicy"].get("MaximumEventAgeInSeconds"))
        self.assertEqual(target["RetryPolicy"]["MaximumRetryAttempts"], 10)
