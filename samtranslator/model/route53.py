from typing import Any, List, Optional

from samtranslator.model import GeneratedProperty, Resource
from samtranslator.utils.types import Intrinsicable


class Route53RecordSetGroup(Resource):
    resource_type = "AWS::Route53::RecordSetGroup"
    property_types = {
        "HostedZoneId": GeneratedProperty(),
        "HostedZoneName": GeneratedProperty(),
        "RecordSets": GeneratedProperty(),
    }

    HostedZoneId: Optional[Intrinsicable[str]]
    HostedZoneName: Optional[Intrinsicable[str]]
    RecordSets: Optional[List[Any]]
