from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import is_str
from samtranslator.model.intrinsics import fnGetAtt, ref


class SubscriptionFilter(Resource):
    resource_type = "AWS::Logs::SubscriptionFilter"
    property_types = {
        "LogGroupName": PropertyType(True, is_str()),
        "FilterPattern": PropertyType(True, is_str()),
        "DestinationArn": PropertyType(True, is_str()),
    }

    runtime_attrs = {"name": lambda self: ref(self.logical_id), "arn": lambda self: fnGetAtt(self.logical_id, "Arn")}
