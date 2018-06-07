from samtranslator.model import PropertyType, Resource
from samtranslator.model.intrinsics import ref
from samtranslator.model.types import is_type, is_str


class LogGroup(Resource):
    resource_type = 'AWS::Logs::LogGroup'
    property_types = {
        'LogGroupName': PropertyType(True, is_str()),
        'RetentionInDays': PropertyType(True, is_type(int))
    }

    runtime_attrs = {
        "name": lambda self: ref(self.logical_id),
    }



