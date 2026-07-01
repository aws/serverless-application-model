"""
AWS::Lambda::MicrovmImage resource for SAM
"""

from typing import Any

from samtranslator.model import GeneratedProperty, Resource
from samtranslator.utils.types import Intrinsicable


class LambdaMicroVMImage(Resource):
    """
    AWS::Lambda::MicrovmImage resource
    """

    resource_type = "AWS::Lambda::MicrovmImage"
    property_types = {
        "Name": GeneratedProperty(),
        "CodeArtifact": GeneratedProperty(),
        "BaseImageArn": GeneratedProperty(),
        "BuildRoleArn": GeneratedProperty(),
        "BaseImageVersion": GeneratedProperty(),
        "Description": GeneratedProperty(),
        "Tags": GeneratedProperty(),
        "Logging": GeneratedProperty(),
        "EgressNetworkConnectors": GeneratedProperty(),
        "CpuConfigurations": GeneratedProperty(),
        "Resources": GeneratedProperty(),
        "AdditionalOsCapabilities": GeneratedProperty(),
        "Hooks": GeneratedProperty(),
        "EnvironmentVariables": GeneratedProperty(),
    }

    Name: Intrinsicable[str]
    CodeArtifact: dict[str, Any]
    BaseImageArn: Intrinsicable[str]
    BuildRoleArn: Intrinsicable[str] | None
    BaseImageVersion: Intrinsicable[str] | None
    Description: Intrinsicable[str] | None
    Tags: list[dict[str, Any]] | None
    Logging: dict[str, Any] | None
    EgressNetworkConnectors: list[Any] | None
    CpuConfigurations: list[dict[str, Any]] | None
    Resources: list[dict[str, Any]] | None
    AdditionalOsCapabilities: list[str] | None
    Hooks: dict[str, Any] | None
    EnvironmentVariables: list[dict[str, Any]] | None
