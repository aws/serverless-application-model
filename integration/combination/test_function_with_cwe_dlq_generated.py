from unittest.case import skipIf

from integration.config.service_names import CWE_CWS_DLQ
from integration.helpers.base_test import BaseTest
from integration.helpers.common_api import get_queue_policy
from integration.helpers.resource import current_region_does_not_support, first_item_in_dict


@skipIf(current_region_does_not_support([CWE_CWS_DLQ]), "CweCwsDlq is not supported in this testing region")
class TestFunctionWithCweDlqGenerated(BaseTest):
    def test_function_with_cwe(self):
        # Verifying that following resources were created is correct
        self.create_and_verify_stack("combination/function_with_cwe_dlq_generated")
        outputs = self.get_stack_outputs()
        lambda_target_arn = outputs["MyLambdaArn"]
        rule_name = outputs["MyEventName"]
        lambda_target_dlq_arn = outputs["MyDLQArn"]
        lambda_target_dlq_url = outputs["MyDLQUrl"]

        cloud_watch_event_client = self.client_provider.cloudwatch_event_client
        cw_rule_result = cloud_watch_event_client.describe_rule(Name=rule_name)
        # checking if the target has a dead-letter queue attached to it
        targets = cloud_watch_event_client.list_targets_by_rule(Rule=rule_name)["Targets"]

        self.assertEqual(len(targets), 1, "Rule should contain a single target")

        target = targets[0]
        self.assertEqual(target["Arn"], lambda_target_arn)
        self.assertEqual(target["DeadLetterConfig"]["Arn"], lambda_target_dlq_arn)

        # checking if the generated dead-letter queue has necessary resource based policy attached to it
        sqs_client = self.client_provider.sqs_client
        dlq_policy = get_queue_policy(queue_url=lambda_target_dlq_url, sqs_client=sqs_client)
        self.assertEqual(len(dlq_policy), 1, "Only one statement must be in Dead-letter queue policy")
        dlq_policy_statement = dlq_policy[0]

        # checking policy action
        actions = dlq_policy_statement["Action"]
        action_list = actions if isinstance(actions, list) == list else [actions]
        self.assertEqual(len(action_list), 1, "Only one action must be in dead-letter queue policy")
        self.assertEqual(
            action_list[0], "sqs:SendMessage", "Action referenced in dead-letter queue policy must be 'sqs:SendMessage'"
        )

        # checking service principal
        self.assertEqual(len(dlq_policy_statement["Principal"]), 1)
        _, service_principal = first_item_in_dict(dlq_policy_statement["Principal"])
        self.assertEqual(
            service_principal,
            "events.amazonaws.com",
            "Policy should grant EventBridge service principal to send messages to dead-letter queue",
        )

        # checking condition type
        condition_type, condition_content = first_item_in_dict(dlq_policy_statement["Condition"])
        self.assertEqual(condition_type, "ArnEquals")

        # checking condition key
        self.assertEqual(len(dlq_policy_statement["Condition"]), 1)
        condition_key, condition_value = first_item_in_dict(condition_content)
        self.assertEqual(condition_key, "aws:SourceArn")

        # checking condition value
        self.assertEqual(len(condition_content), 1)
        self.assertEqual(
            condition_value, cw_rule_result["Arn"], "Policy should only allow requests coming from cwe rule resource"
        )
