from typing import Any, Dict, List, Optional

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


class Route53RecordSet(Resource):
    resource_type = "AWS::Route53::RecordSet"
    property_types = {
        "HostedZoneId": GeneratedProperty(),
        "HostedZoneName": GeneratedProperty(),
        "AliasTarget": GeneratedProperty(),
        "Name": GeneratedProperty(),
        "Type": GeneratedProperty(),
    }
    HostedZoneId: Optional[Intrinsicable[str]]
    HostedZoneName: Optional[Intrinsicable[str]]
    AliasTarget: Optional[Dict[str, Any]]
    Name: Optional[Intrinsicable[str]]
    Type: Optional[Intrinsicable[str]]
