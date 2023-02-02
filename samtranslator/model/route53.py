from typing import Any, List, Optional

from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import IS_STR, is_type
from samtranslator.utils.types import Intrinsicable


class Route53RecordSetGroup(Resource):
    resource_type = "AWS::Route53::RecordSetGroup"
    property_types = {
        "HostedZoneId": PropertyType(False, IS_STR),
        "HostedZoneName": PropertyType(False, IS_STR),
        "RecordSets": PropertyType(False, is_type(list)),
    }

    HostedZoneId: Optional[Intrinsicable[str]]
    HostedZoneName: Optional[Intrinsicable[str]]
    RecordSets: Optional[List[Any]]
