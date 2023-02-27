from samtranslator.model import GeneratedProperty, Resource
from samtranslator.model.intrinsics import fnGetAtt, ref


class SubscriptionFilter(Resource):
    resource_type = "AWS::Logs::SubscriptionFilter"
    property_types = {
        "LogGroupName": GeneratedProperty(),
        "FilterPattern": GeneratedProperty(),
        "DestinationArn": GeneratedProperty(),
    }

    runtime_attrs = {"name": lambda self: ref(self.logical_id), "arn": lambda self: fnGetAtt(self.logical_id, "Arn")}
