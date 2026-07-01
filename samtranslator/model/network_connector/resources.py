"""
AWS::Lambda::NetworkConnector resource for SAM
"""

from typing import Any

from samtranslator.model import GeneratedProperty, Resource
from samtranslator.utils.types import Intrinsicable


class LambdaNetworkConnector(Resource):
    """
    AWS::Lambda::NetworkConnector resource
    """

    resource_type = "AWS::Lambda::NetworkConnector"
    property_types = {
        "Name": GeneratedProperty(),
        "Configuration": GeneratedProperty(),
        "OperatorRole": GeneratedProperty(),
        "Tags": GeneratedProperty(),
    }

    Name: Intrinsicable[str] | None
    Configuration: dict[str, Any]
    OperatorRole: Intrinsicable[str] | None
    Tags: list[dict[str, Any]] | None
