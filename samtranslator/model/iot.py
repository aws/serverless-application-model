from samtranslator.model import GeneratedProperty, Resource
from samtranslator.model.intrinsics import fnGetAtt, ref


class IotTopicRule(Resource):
    resource_type = "AWS::IoT::TopicRule"
    property_types = {
        "TopicRulePayload": GeneratedProperty(),
        "Tags": GeneratedProperty(),
    }

    runtime_attrs = {"name": lambda self: ref(self.logical_id), "arn": lambda self: fnGetAtt(self.logical_id, "Arn")}
