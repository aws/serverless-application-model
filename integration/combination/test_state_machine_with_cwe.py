from unittest.case import skipIf

from integration.config.service_names import STATE_MACHINE_CWE_CWS
from integration.helpers.base_test import BaseTest
from integration.helpers.common_api import get_policy_statements
from integration.helpers.resource import current_region_does_not_support


@skipIf(
    current_region_does_not_support([STATE_MACHINE_CWE_CWS]),
    "StateMachineCWECWS is not supported in this testing region",
)
class TestStateMachineWithCwe(BaseTest):
    def test_state_machine_with_cwe(self):
        self.create_and_verify_stack("combination/state_machine_with_cwe")
        outputs = self.get_stack_outputs()
        state_machine_arn = outputs["MyStateMachineArn"]
        rule_name = outputs["MyEventName"]
        event_role_name = outputs["MyEventRole"]

        cloud_watch_events_client = self.client_provider.cloudwatch_event_client

        # Check if the CWE rule is created with the state machine as the target
        rule_name_by_target_result = cloud_watch_events_client.list_rule_names_by_target(TargetArn=state_machine_arn)
        self.assertEqual(len(rule_name_by_target_result["RuleNames"]), 1)
        rule_name_with_state_machine_target = rule_name_by_target_result["RuleNames"][0]
        self.assertEqual(rule_name_with_state_machine_target, rule_name)

        # checking if the role used by the event rule to trigger the state machine execution is correct
        start_execution_policy = get_policy_statements(
            event_role_name, "MyStateMachineCWEventRoleStartExecutionPolicy", self.client_provider.iam_client
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
