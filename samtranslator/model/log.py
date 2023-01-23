from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import IS_STR
from samtranslator.model.intrinsics import fnGetAtt, ref


class SubscriptionFilter(Resource):
    resource_type = "AWS::Logs::SubscriptionFilter"
    property_types = {
        "LogGroupName": PropertyType(True, IS_STR),
        "FilterPattern": PropertyType(True, IS_STR),
        "DestinationArn": PropertyType(True, IS_STR),
    }

    runtime_attrs = {"name": lambda self: ref(self.logical_id), "arn": lambda self: fnGetAtt(self.logical_id, "Arn")}
