from samtranslator.model import GeneratedProperty, Resource
from samtranslator.model.intrinsics import ref


class SNSSubscription(Resource):
    resource_type = "AWS::SNS::Subscription"
    property_types = {
        "Endpoint": GeneratedProperty(),
        "Protocol": GeneratedProperty(),
        "TopicArn": GeneratedProperty(),
        "Region": GeneratedProperty(),
        "FilterPolicy": GeneratedProperty(),
        "FilterPolicyScope": GeneratedProperty(),
        "RedrivePolicy": GeneratedProperty(),
    }


class SNSTopicPolicy(Resource):
    resource_type = "AWS::SNS::TopicPolicy"
    property_types = {
        "PolicyDocument": GeneratedProperty(),
        "Topics": GeneratedProperty(),
    }


class SNSTopic(Resource):
    resource_type = "AWS::SNS::Topic"
    property_types = {
        "TopicName": GeneratedProperty(),
        "Tags": GeneratedProperty(),
    }
    runtime_attrs = {"arn": lambda self: ref(self.logical_id)}
