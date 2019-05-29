from samtranslator.model import PropertyType, Resource
from samtranslator.model.intrinsics import ref
from samtranslator.model.types import is_type, is_str


class CloudWatchLogGroup(Resource):
    resource_type = 'AWS::Logs::LogGroup'
    property_types = {
        'LogGroupName': PropertyType(False, is_str()),
        'RetentionInDays': PropertyType(False, is_type(int)),
    }

    runtime_attrs = {
        "name": lambda self: ref(self.logical_id),
    }
