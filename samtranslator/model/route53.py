from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import is_type, is_str


class Route53RecordSetGroup(Resource):
    resource_type = "AWS::Route53::RecordSetGroup"
    property_types = {
        "HostedZoneId": PropertyType(False, is_str()),
        "HostedZoneName": PropertyType(False, is_str()),
        "RecordSets": PropertyType(False, is_type(list)),
    }
