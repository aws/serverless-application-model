from typing import Any

from samtranslator.model import GeneratedProperty, Resource
from samtranslator.utils.types import Intrinsicable


class Route53RecordSetGroup(Resource):
    resource_type = "AWS::Route53::RecordSetGroup"
    property_types = {
        "HostedZoneId": GeneratedProperty(),
        "HostedZoneName": GeneratedProperty(),
        "RecordSets": GeneratedProperty(),
    }

    HostedZoneId: Intrinsicable[str] | None
    HostedZoneName: Intrinsicable[str] | None
    RecordSets: list[Any] | None
