from samtranslator.model import GeneratedProperty, Resource
from samtranslator.model.intrinsics import fnGetAtt, ref


class EventsRule(Resource):
    resource_type = "AWS::Events::Rule"
    property_types = {
        "Description": GeneratedProperty(),
        "EventBusName": GeneratedProperty(),
        "EventPattern": GeneratedProperty(),
        "Name": GeneratedProperty(),
        "RoleArn": GeneratedProperty(),
        "ScheduleExpression": GeneratedProperty(),
        "State": GeneratedProperty(),
        "Targets": GeneratedProperty(),
    }

    runtime_attrs = {"rule_id": lambda self: ref(self.logical_id), "arn": lambda self: fnGetAtt(self.logical_id, "Arn")}
