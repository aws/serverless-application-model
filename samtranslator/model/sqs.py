from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import is_type, list_of
from samtranslator.model.intrinsics import fnGetAtt, ref


class SQSQueue(Resource):
    resource_type = "AWS::SQS::Queue"
    property_types = {}
    runtime_attrs = {
        "queue_url": lambda self: ref(self.logical_id),
        "arn": lambda self: fnGetAtt(self.logical_id, "Arn"),
    }


class SQSQueuePolicy(Resource):
    resource_type = "AWS::SQS::QueuePolicy"
    property_types = {"PolicyDocument": PropertyType(True, is_type(dict)), "Queues": PropertyType(True, list_of(str))}
    runtime_attrs = {"arn": lambda self: fnGetAtt(self.logical_id, "Arn")}


class SQSQueuePolicies:
    @staticmethod
    def sns_topic_send_message_role_policy(topic_arn, queue_arn):
        document = {
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
        return document

    @staticmethod
    def eventbridge_dlq_send_message_resource_based_policy(rule_arn, queue_arn):
        document = {
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
        return document
