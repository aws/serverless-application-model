from samtranslator.model.sqs import SQSQueue, SQSQueuePolicy, SQSQueuePolicies


class EventBridgeRuleUtils:
    @staticmethod
    def create_dead_letter_queue_with_policy(rule_logical_id, rule_arn, queue_logical_id=None):
        resources = []

        queue = SQSQueue(queue_logical_id or rule_logical_id + "Queue")
        dlq_queue_arn = queue.get_runtime_attr("arn")
        dlq_queue_url = queue.get_runtime_attr("queue_url")

        # grant necessary permission to Eventbridge Rule resource for sending messages to dead-letter queue
        policy = SQSQueuePolicy(rule_logical_id + "QueuePolicy")
        policy.PolicyDocument = SQSQueuePolicies.eventbridge_dlq_send_message_resource_based_policy(
            rule_arn, dlq_queue_arn
        )
        policy.Queues = [dlq_queue_url]

        resources.append(queue)
        resources.append(policy)

        return resources
