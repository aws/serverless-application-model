from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import is_type, list_of, is_str
from samtranslator.model.intrinsics import fnGetAtt, ref


class EventsRule(Resource):
    resource_type = 'AWS::Events::Rule'
    property_types = {
            'Description': PropertyType(False, is_str()),
            'EventPattern': PropertyType(False, is_type(dict)),
            'Name': PropertyType(False, is_str()),
            'RoleArn': PropertyType(False, is_str()),
            'ScheduleExpression': PropertyType(False, is_str()),
            'State': PropertyType(False, is_str()),
            'Targets': PropertyType(False, list_of(is_type(dict)))
    }

    runtime_attrs = {
        "rule_id": lambda self: ref(self.logical_id),
        "arn": lambda self: fnGetAtt(self.logical_id, "Arn")
    }
