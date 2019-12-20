from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import is_type
from samtranslator.model.intrinsics import ref, fnGetAtt


class IotTopicRule(Resource):
    resource_type = "AWS::IoT::TopicRule"
    property_types = {"TopicRulePayload": PropertyType(False, is_type(dict))}

    runtime_attrs = {"name": lambda self: ref(self.logical_id), "arn": lambda self: fnGetAtt(self.logical_id, "Arn")}
