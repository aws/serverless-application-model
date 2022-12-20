from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import IS_DICT
from samtranslator.model.intrinsics import ref, fnGetAtt


class IotTopicRule(Resource):
    resource_type = "AWS::IoT::TopicRule"
    property_types = {"TopicRulePayload": PropertyType(False, IS_DICT)}

    runtime_attrs = {"name": lambda self: ref(self.logical_id), "arn": lambda self: fnGetAtt(self.logical_id, "Arn")}
