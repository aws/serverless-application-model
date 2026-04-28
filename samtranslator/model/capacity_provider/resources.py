"""
AWS::Lambda::CapacityProvider resources for SAM
"""

from typing import Any

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
        "KmsKeyArn": GeneratedProperty(),
    }

    CapacityProviderName: Intrinsicable[str] | None
    VpcConfig: dict[str, Any]
    PermissionsConfig: dict[str, Any]
    Tags: list[dict[str, Any]] | None
    InstanceRequirements: dict[str, Any] | None
    CapacityProviderScalingConfig: dict[str, Any] | None
    KmsKeyArn: Intrinsicable[str] | None

    runtime_attrs = {
        "name": lambda self: ref(self.logical_id),
        "arn": lambda self: fnGetAtt(self.logical_id, "Arn"),
    }
