from unittest.case import skipIf

from integration.config.service_names import CWE_CWS_DLQ
from integration.helpers.base_test import BaseTest
from integration.helpers.common_api import get_policy_statements
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([CWE_CWS_DLQ]), "CweCwsDlq is not supported in this testing region")
class TestStateMachineWithScheduleDlqAndRetryPolicy(BaseTest):
    def test_state_machine_with_schedule(self):
        self.create_and_verify_stack("combination/state_machine_with_schedule_dlq_and_retry_policy")
        outputs = self.get_stack_outputs()
        state_machine_arn = outputs["MyStateMachineArn"]
        schedule_name = outputs["MyScheduleName"]
        state_machine_target_dlq_arn = outputs["MyDLQArn"]
        event_role_name = outputs["MyEventRole"]

        # get the cloudwatch schedule rule
        cloud_watch_event_client = self.client_provider.cloudwatch_event_client
        cw_rule_result = cloud_watch_event_client.describe_rule(Name=schedule_name)

        # checking if the name, description and state properties are correct
        self.assertEqual(cw_rule_result["Name"], schedule_name)
        self.assertEqual(cw_rule_result["Description"], "test schedule")
        self.assertEqual(cw_rule_result["State"], "DISABLED")
        self.assertEqual(cw_rule_result["ScheduleExpression"], "rate(1 minute)")

        # checking if the target's DLQ and RetryPolicy properties are correct
        targets = cloud_watch_event_client.list_targets_by_rule(Rule=schedule_name)["Targets"]

        self.assertEqual(len(targets), 1, "Rule should contain a single target")

        target = targets[0]
        self.assertEqual(target["Arn"], state_machine_arn)
        self.assertEqual(target["DeadLetterConfig"]["Arn"], state_machine_target_dlq_arn)

        self.assertIsNone(target["RetryPolicy"].get("MaximumEventAgeInSeconds"))
        self.assertEqual(target["RetryPolicy"]["MaximumRetryAttempts"], 2)

        # checking if the role used by the event rule to trigger the state machine execution is correct
        start_execution_policy = get_policy_statements(
            event_role_name, "MyStateMachineCWScheduleRoleStartExecutionPolicy", self.client_provider.iam_client
        )
        self.assertEqual(len(start_execution_policy), 1, "Only one statement must be in Start Execution policy")

        start_execution_policy_statement = start_execution_policy[0]

        self.assertFalse(isinstance(start_execution_policy_statement["Action"], list))
        policy_action = start_execution_policy_statement["Action"]
        self.assertEqual(
            policy_action,
            "states:StartExecution",
            "Action referenced in event role policy must be 'states:StartExecution'",
        )

        self.assertFalse(isinstance(start_execution_policy_statement["Resource"], list))
        referenced_state_machine_arn = start_execution_policy_statement["Resource"]
        self.assertEqual(
            referenced_state_machine_arn,
            state_machine_arn,
            "State machine referenced in event role policy is incorrect",
        )
