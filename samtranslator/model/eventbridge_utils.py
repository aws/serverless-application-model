from samtranslator.model.exceptions import InvalidEventException
from samtranslator.model.sqs import SQSQueue, SQSQueuePolicies, SQSQueuePolicy


class EventBridgeRuleUtils:
    @staticmethod
    def create_dead_letter_queue_with_policy(rule_logical_id, rule_arn, queue_logical_id=None, attributes=None):  # type: ignore[no-untyped-def]
        resources = []

        queue = SQSQueue(queue_logical_id or rule_logical_id + "Queue", attributes=attributes)
        dlq_queue_arn = queue.get_runtime_attr("arn")
        dlq_queue_url = queue.get_runtime_attr("queue_url")

        # grant necessary permission to Eventbridge Rule resource for sending messages to dead-letter queue
        policy = SQSQueuePolicy(rule_logical_id + "QueuePolicy", attributes=attributes)
        policy.PolicyDocument = SQSQueuePolicies.eventbridge_dlq_send_message_resource_based_policy(  # type: ignore[no-untyped-call]
            rule_arn, dlq_queue_arn
        )
        policy.Queues = [dlq_queue_url]

        resources.append(queue)
        resources.append(policy)  # type: ignore[arg-type]

        return resources

    @staticmethod
    def validate_dlq_config(source_logical_id, dead_letter_config):  # type: ignore[no-untyped-def]
        supported_types = ["SQS"]
        is_arn_defined = "Arn" in dead_letter_config
        is_type_defined = "Type" in dead_letter_config
        if is_arn_defined and is_type_defined:
            raise InvalidEventException(
                source_logical_id, "You can either define 'Arn' or 'Type' property of DeadLetterConfig."
            )
        if is_type_defined and dead_letter_config.get("Type") not in supported_types:
            raise InvalidEventException(
                source_logical_id,
                "The only valid value for 'Type' property of DeadLetterConfig is 'SQS'.",
            )
        if not is_arn_defined and not is_type_defined:
            raise InvalidEventException(source_logical_id, "No 'Arn' or 'Type' property provided for DeadLetterConfig.")

    @staticmethod
    def get_dlq_queue_arn_and_resources(cw_event_source, source_arn, attributes):  # type: ignore[no-untyped-def]
        """returns dlq queue arn and dlq_resources, assuming cw_event_source.DeadLetterConfig has been validated"""
        dlq_queue_arn = cw_event_source.DeadLetterConfig.get("Arn")
        if dlq_queue_arn is not None:
            return dlq_queue_arn, []
        queue_logical_id = cw_event_source.DeadLetterConfig.get("QueueLogicalId")
        if queue_logical_id is not None and not isinstance(queue_logical_id, str):
            raise InvalidEventException(
                cw_event_source.logical_id,
                "QueueLogicalId must be a string",
            )
        dlq_resources = EventBridgeRuleUtils.create_dead_letter_queue_with_policy(  # type: ignore[no-untyped-call]
            cw_event_source.logical_id, source_arn, queue_logical_id, attributes
        )
        dlq_queue_arn = dlq_resources[0].get_runtime_attr("arn")
        return dlq_queue_arn, dlq_resources
