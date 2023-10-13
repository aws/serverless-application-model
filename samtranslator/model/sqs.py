from typing import Dict

from samtranslator.model import GeneratedProperty, PropertyType, Resource
from samtranslator.model.intrinsics import fnGetAtt, ref
from samtranslator.model.types import PassThrough


class SQSQueue(Resource):
    resource_type = "AWS::SQS::Queue"
    property_types: Dict[str, PropertyType] = {
        "FifoQueue": GeneratedProperty(),
        "Tags": GeneratedProperty(),
    }
    runtime_attrs = {
        "queue_url": lambda self: ref(self.logical_id),
        "arn": lambda self: fnGetAtt(self.logical_id, "Arn"),
    }

    FifoQueue: PassThrough


class SQSQueuePolicy(Resource):
    resource_type = "AWS::SQS::QueuePolicy"
    property_types = {
        "PolicyDocument": GeneratedProperty(),
        "Queues": GeneratedProperty(),
    }
    runtime_attrs = {"arn": lambda self: fnGetAtt(self.logical_id, "Arn")}


class SQSQueuePolicies:
    @staticmethod
    def sns_topic_send_message_role_policy(topic_arn, queue_arn):  # type: ignore[no-untyped-def]
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sqs:SendMessage",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Resource": queue_arn,
                    "Condition": {"ArnEquals": {"aws:SourceArn": topic_arn}},
                }
            ],
        }

    @staticmethod
    def eventbridge_dlq_send_message_resource_based_policy(rule_arn, queue_arn):  # type: ignore[no-untyped-def]
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sqs:SendMessage",
                    "Effect": "Allow",
                    "Principal": {"Service": "events.amazonaws.com"},
                    "Resource": queue_arn,
                    "Condition": {"ArnEquals": {"aws:SourceArn": rule_arn}},
                }
            ],
        }
