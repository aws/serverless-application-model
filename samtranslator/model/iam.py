from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import is_type, is_str, list_of
from samtranslator.model.intrinsics import ref, fnGetAtt


class IAMRole(Resource):
    resource_type = "AWS::IAM::Role"
    property_types = {
        "AssumeRolePolicyDocument": PropertyType(True, is_type(dict)),
        "ManagedPolicyArns": PropertyType(False, is_type(list)),
        "Path": PropertyType(False, is_str()),
        "Policies": PropertyType(False, is_type(list)),
        "PermissionsBoundary": PropertyType(False, is_str()),
        "Tags": PropertyType(False, list_of(is_type(dict))),
    }

    runtime_attrs = {"name": lambda self: ref(self.logical_id), "arn": lambda self: fnGetAtt(self.logical_id, "Arn")}


class IAMRolePolicies:
    @classmethod
    def construct_assume_role_policy_for_service_principal(cls, service_principal):
        document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": ["sts:AssumeRole"],
                    "Effect": "Allow",
                    "Principal": {"Service": [service_principal]},
                }
            ],
        }
        return document

    @classmethod
    def step_functions_start_execution_role_policy(cls, state_machine_arn, logical_id):
        document = {
            "PolicyName": logical_id + "StartExecutionPolicy",
            "PolicyDocument": {
                "Statement": [{"Action": "states:StartExecution", "Effect": "Allow", "Resource": state_machine_arn}]
            },
        }
        return document

    @classmethod
    def stepfunctions_assume_role_policy(cls):
        document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": ["sts:AssumeRole"],
                    "Effect": "Allow",
                    "Principal": {"Service": ["states.amazonaws.com"]},
                }
            ],
        }
        return document

    @classmethod
    def cloud_watch_log_assume_role_policy(cls):
        document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": ["sts:AssumeRole"],
                    "Effect": "Allow",
                    "Principal": {"Service": ["apigateway.amazonaws.com"]},
                }
            ],
        }
        return document

    @classmethod
    def lambda_assume_role_policy(cls):
        document = {
            "Version": "2012-10-17",
            "Statement": [
                {"Action": ["sts:AssumeRole"], "Effect": "Allow", "Principal": {"Service": ["lambda.amazonaws.com"]}}
            ],
        }
        return document

    @classmethod
    def dead_letter_queue_policy(cls, action, resource):
        """Return the DeadLetterQueue Policy to be added to the LambdaRole
        :returns: Policy for the DeadLetterQueue
        :rtype: Dict
        """
        return {
            "PolicyName": "DeadLetterQueuePolicy",
            "PolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [{"Action": action, "Resource": resource, "Effect": "Allow"}],
            },
        }

    @classmethod
    def sqs_send_message_role_policy(cls, queue_arn, logical_id):
        document = {
            "PolicyName": logical_id + "SQSPolicy",
            "PolicyDocument": {"Statement": [{"Action": "sqs:SendMessage", "Effect": "Allow", "Resource": queue_arn}]},
        }
        return document

    @classmethod
    def sns_publish_role_policy(cls, topic_arn, logical_id):
        document = {
            "PolicyName": logical_id + "SNSPolicy",
            "PolicyDocument": {"Statement": [{"Action": "sns:publish", "Effect": "Allow", "Resource": topic_arn}]},
        }
        return document

    @classmethod
    def event_bus_put_events_role_policy(cls, event_bus_arn, logical_id):
        document = {
            "PolicyName": logical_id + "EventBridgePolicy",
            "PolicyDocument": {
                "Statement": [{"Action": "events:PutEvents", "Effect": "Allow", "Resource": event_bus_arn}]
            },
        }
        return document

    @classmethod
    def lambda_invoke_function_role_policy(cls, function_arn, logical_id):
        document = {
            "PolicyName": logical_id + "LambdaPolicy",
            "PolicyDocument": {
                "Statement": [{"Action": "lambda:InvokeFunction", "Effect": "Allow", "Resource": function_arn}]
            },
        }
        return document
