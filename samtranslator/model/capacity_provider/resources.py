"""
AWS::Lambda::CapacityProvider resources for SAM
"""

from typing import Any, Dict, List, Optional

from samtranslator.model import GeneratedProperty, Resource
from samtranslator.model.intrinsics import fnGetAtt, ref
from samtranslator.utils.types import Intrinsicable


class LambdaCapacityProvider(Resource):
    """
    AWS::Lambda::CapacityProvider resource
    """

    resource_type = "AWS::Lambda::CapacityProvider"
    property_types = {
        "CapacityProviderName": GeneratedProperty(),
        "VpcConfig": GeneratedProperty(),
        "PermissionsConfig": GeneratedProperty(),
        "Tags": GeneratedProperty(),
        "InstanceRequirements": GeneratedProperty(),
        "CapacityProviderScalingConfig": GeneratedProperty(),
        "KMSKeyArn": GeneratedProperty(),
    }

    CapacityProviderName: Optional[Intrinsicable[str]]
    VpcConfig: Dict[str, Any]
    PermissionsConfig: Dict[str, Any]
    Tags: Optional[List[Dict[str, Any]]]
    InstanceRequirements: Optional[Dict[str, Any]]
    CapacityProviderScalingConfig: Optional[Dict[str, Any]]
    KMSKeyArn: Optional[Intrinsicable[str]]

    runtime_attrs = {
        "name": lambda self: ref(self.logical_id),
        "arn": lambda self: fnGetAtt(self.logical_id, "Arn"),
    }
