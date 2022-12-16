from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import IS_DICT, list_of, IS_STR
from samtranslator.model.intrinsics import fnGetAtt, ref


class EventsRule(Resource):
    resource_type = "AWS::Events::Rule"
    property_types = {
        "Description": PropertyType(False, IS_STR),
        "EventBusName": PropertyType(False, IS_STR),
        "EventPattern": PropertyType(False, IS_DICT),
        "Name": PropertyType(False, IS_STR),
        "RoleArn": PropertyType(False, IS_STR),
        "ScheduleExpression": PropertyType(False, IS_STR),
        "State": PropertyType(False, IS_STR),
        "Targets": PropertyType(False, list_of(IS_DICT)),
    }

    runtime_attrs = {"rule_id": lambda self: ref(self.logical_id), "arn": lambda self: fnGetAtt(self.logical_id, "Arn")}
