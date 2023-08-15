from unittest.case import skipIf

from integration.config.service_names import CWE_CWS_DLQ
from integration.helpers.base_test import BaseTest
from integration.helpers.common_api import get_queue_policy
from integration.helpers.resource import current_region_does_not_support


@skipIf(current_region_does_not_support([CWE_CWS_DLQ]), "CweCwsDlq is not supported in this testing region")
class TestStateMachineWithScheduleDlqGenerated(BaseTest):
    def test_state_machine_with_schedule(self):
        self.create_and_verify_stack("combination/state_machine_with_schedule_dlq_generated")
        outputs = self.get_stack_outputs()
        schedule_name = outputs["MyScheduleName"]
        state_machine_arn = outputs["MyStateMachineArn"]
        state_machine_target_dlq_arn = outputs["MyDLQArn"]
        state_machine_target_dlq_url = outputs["MyDLQUrl"]

        # get the cloudwatch schedule rule
        cloud_watch_event_client = self.client_provider.cloudwatch_event_client
        cw_rule_result = cloud_watch_event_client.describe_rule(Name=schedule_name)

        # checking if the name, description and state properties are correct
        self.assertEqual(cw_rule_result["Name"], schedule_name)
        self.assertEqual(cw_rule_result["Description"], "test schedule")
        self.assertEqual(cw_rule_result["State"], "DISABLED")
        self.assertEqual(cw_rule_result["ScheduleExpression"], "rate(1 minute)")

        # checking if the target has a dead-letter queue attached to it
        targets = cloud_watch_event_client.list_targets_by_rule(Rule=schedule_name)["Targets"]

        self.assertEqual(len(targets), 1, "Rule should contain a single target")
        target = targets[0]
        self.assertEqual(target["Arn"], state_machine_arn)
        self.assertEqual(target["DeadLetterConfig"]["Arn"], state_machine_target_dlq_arn)

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
