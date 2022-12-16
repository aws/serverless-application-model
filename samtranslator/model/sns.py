from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import IS_DICT, IS_STR, list_of
from samtranslator.model.intrinsics import ref


class SNSSubscription(Resource):
    resource_type = "AWS::SNS::Subscription"
    property_types = {
        "Endpoint": PropertyType(True, IS_STR),
        "Protocol": PropertyType(True, IS_STR),
        "TopicArn": PropertyType(True, IS_STR),
        "Region": PropertyType(False, IS_STR),
        "FilterPolicy": PropertyType(False, IS_DICT),
        "RedrivePolicy": PropertyType(False, IS_DICT),
    }


class SNSTopicPolicy(Resource):
    resource_type = "AWS::SNS::TopicPolicy"
    property_types = {"PolicyDocument": PropertyType(True, IS_DICT), "Topics": PropertyType(True, list_of(str))}


class SNSTopic(Resource):
    resource_type = "AWS::SNS::Topic"
    property_types = {"TopicName": PropertyType(False, IS_STR)}
    runtime_attrs = {"arn": lambda self: ref(self.logical_id)}
