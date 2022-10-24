from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import is_type, list_of, is_str
from samtranslator.model.intrinsics import fnGetAtt, ref


class EventsRule(Resource):
    resource_type = "AWS::Events::Rule"
    property_types = {
        "Description": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "EventBusName": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "EventPattern": PropertyType(False, is_type(dict)),  # type: ignore[no-untyped-call, no-untyped-call]
        "Name": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "RoleArn": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "ScheduleExpression": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "State": PropertyType(False, is_str()),  # type: ignore[no-untyped-call, no-untyped-call]
        "Targets": PropertyType(False, list_of(is_type(dict))),  # type: ignore[no-untyped-call, no-untyped-call, no-untyped-call]
    }

    runtime_attrs = {"rule_id": lambda self: ref(self.logical_id), "arn": lambda self: fnGetAtt(self.logical_id, "Arn")}  # type: ignore[no-untyped-call, no-untyped-call]
