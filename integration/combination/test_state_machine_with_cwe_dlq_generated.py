from unittest.case import skipIf

from integration.config.service_names import CWE_CWS_DLQ, STATE_MACHINE_CWE_CWS
from integration.helpers.base_test import BaseTest
from integration.helpers.common_api import get_policy_statements, get_queue_policy
from integration.helpers.resource import current_region_does_not_support


@skipIf(
    current_region_does_not_support([CWE_CWS_DLQ, STATE_MACHINE_CWE_CWS]),
    "CweCwsDlq is not supported in this testing region",
)
class TestStateMachineWithCweDlqGenerated(BaseTest):
    def test_state_machine_with_cwe(self):
        self.create_and_verify_stack("combination/state_machine_with_cwe_dlq_generated")
        outputs = self.get_stack_outputs()
        state_machine_arn = outputs["MyStateMachineArn"]
        rule_name = outputs["MyEventName"]
        event_role_name = outputs["MyEventRole"]
        state_machine_target_dlq_arn = outputs["MyDLQArn"]
        state_machine_target_dlq_url = outputs["MyDLQUrl"]

        cloud_watch_events_client = self.client_provider.cloudwatch_event_client
        cw_rule_result = cloud_watch_events_client.describe_rule(Name=rule_name)

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

        # checking if the target has a dead-letter queue attached to it
        targets = cloud_watch_events_client.list_targets_by_rule(Rule=rule_name)["Targets"]

        self.assertEqual(len(targets), 1, "Rule should contain a single target")
        target = targets[0]
        self.assertEqual(target["Arn"], state_machine_arn)
        self.assertEqual(target["DeadLetterConfig"]["Arn"], state_machine_target_dlq_arn)

        # checking target's retry policy properties
        self.assertEqual(target["RetryPolicy"]["MaximumEventAgeInSeconds"], 200)
        self.assertIsNone(target["RetryPolicy"].get("MaximumRetryAttempts"))

        # checking if the generated dead-letter queue has necessary resource based policy attached to it
        dlq_policy = get_queue_policy(state_machine_target_dlq_url, self.client_provider.sqs_client)
        self.assertEqual(len(dlq_policy), 1, "Only one statement must be in Dead-letter queue policy")
        dlq_policy_statement = dlq_policy[0]

        # checking policy action
        self.assertFalse(
            isinstance(dlq_policy_statement["Action"], list), "Only one action must be in dead-letter queue policy"
        )  # if it is an array, it means has more than one action
        self.assertEqual(
            dlq_policy_statement["Action"],
            "sqs:SendMessage",
            "Action referenced in dead-letter queue policy must be 'sqs:SendMessage'",
        )

        # checking service principal
        self.assertEqual(
            len(dlq_policy_statement["Principal"]),
            1,
        )
        self.assertEqual(
            dlq_policy_statement["Principal"]["Service"],
            "events.amazonaws.com",
            "Policy should grant EventBridge service principal to send messages to dead-letter queue",
        )

        # checking condition type
        key, value = get_first_key_value_pair_in_dict(dlq_policy_statement["Condition"])
        self.assertEqual(key, "ArnEquals")

        # checking condition key
        self.assertEqual(len(dlq_policy_statement["Condition"]), 1)
        condition_kay, condition_value = get_first_key_value_pair_in_dict(value)
        self.assertEqual(condition_kay, "aws:SourceArn")

        # checking condition value
        self.assertEqual(len(dlq_policy_statement["Condition"][key]), 1)
        self.assertEqual(
            condition_value,
            cw_rule_result["Arn"],
            "Policy should only allow requests coming from schedule rule resource",
        )


def get_first_key_value_pair_in_dict(dictionary):
    key = next(iter(dictionary.keys()))
    value = dictionary[key]
    return key, value
