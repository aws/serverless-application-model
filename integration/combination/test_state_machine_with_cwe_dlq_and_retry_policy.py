from integration.helpers.base_test import BaseTest


class TestStateMachineWithCweDlqAndRetryPolicy(BaseTest):
    def test_state_machine_with_api(self):
        self.create_and_verify_stack("combination/state_machine_with_cwe_with_dlq_and_retry_policy")
        outputs = self.get_stack_outputs()
        state_machine_arn = outputs["MyStateMachineArn"]
        rule_name = outputs["MyEventName"]
        state_machine_target_dlq_arn = outputs["MyDLQArn"]

        cloud_watch_event_client = self.client_provider.cloudwatch_event_client

        # checking if the target's DLQ and RetryPolicy properties are correct
        targets = cloud_watch_event_client.list_targets_by_rule(Rule=rule_name)["Targets"]

        self.assertEqual(len(targets), 1, "Rule should contain a single target")

        target = targets[0]
        self.assertEqual(target["Arn"], state_machine_arn)
        self.assertEqual(target["DeadLetterConfig"]["Arn"], state_machine_target_dlq_arn)

        self.assertEqual(target["RetryPolicy"]["MaximumEventAgeInSeconds"], 400)
        self.assertEqual(target["RetryPolicy"]["MaximumRetryAttempts"], 5)
