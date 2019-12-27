from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import is_type, is_str
from samtranslator.model.intrinsics import ref


class SNSSubscription(Resource):
    resource_type = "AWS::SNS::Subscription"
    property_types = {
        "Endpoint": PropertyType(True, is_str()),
        "Protocol": PropertyType(True, is_str()),
        "TopicArn": PropertyType(True, is_str()),
        "Region": PropertyType(False, is_str()),
        "FilterPolicy": PropertyType(False, is_type(dict)),
    }


class SNSTopic(Resource):
    resource_type = "AWS::SNS::Topic"
    property_types = {"TopicName": PropertyType(False, is_str())}
    runtime_attrs = {"arn": lambda self: ref(self.logical_id)}
