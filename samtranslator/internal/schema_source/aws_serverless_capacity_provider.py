from __future__ import annotations

from typing import Literal

from samtranslator.internal.schema_source.common import (
    BaseModel,
    DictStrAny,
    PassThroughProp,
    ResourceAttributes,
    SamIntrinsicable,
    get_prop,
    passthrough_prop,
)

PROPERTIES_STEM = "sam-resource-capacityprovider"
VPC_CONFIG_STEM = "sam-property-capacityprovider-vpcconfig"
INSTANCE_REQUIREMENTS_STEM = "sam-property-capacityprovider-instancerequirements"
SCALING_CONFIG_STEM = "sam-property-capacityprovider-scalingconfig"

properties = get_prop(PROPERTIES_STEM)
vpcconfig = get_prop(VPC_CONFIG_STEM)
instancerequirements = get_prop(INSTANCE_REQUIREMENTS_STEM)
scalingconfig = get_prop(SCALING_CONFIG_STEM)


class VpcConfig(BaseModel):
    # Optional list of security group IDs - supports intrinsic functions for dynamic references
    SecurityGroupIds: SamIntrinsicable[list[SamIntrinsicable[str]]] | None = vpcconfig("SecurityGroupIds")
    # Required list of subnet IDs - supports intrinsic functions for dynamic VPC configuration
    SubnetIds: SamIntrinsicable[list[SamIntrinsicable[str]]] = vpcconfig("SubnetIds")


class InstanceRequirements(BaseModel):
    # Optional list of CPU architectures - maps to CFN InstanceRequirements.Architecture
    # Uses SamIntrinsicable[list[SamIntrinsicable[str]]] to support intrinsic functions like !Ref for both list and list item
    Architectures: SamIntrinsicable[list[SamIntrinsicable[str]]] | None = instancerequirements("Architectures")
    # Optional list of allowed EC2 instance types - maps to CFN InstanceRequirements.AllowedInstanceTypes
    # Uses SamIntrinsicable[list[SamIntrinsicable[str]]] to support intrinsic functions like !Ref for both list and list item
    AllowedTypes: SamIntrinsicable[list[SamIntrinsicable[str]]] | None = instancerequirements("AllowedTypes")
    # Optional list of excluded EC2 instance types - maps to CFN InstanceRequirements.ExcludedInstanceTypes
    # Uses SamIntrinsicable[list[SamIntrinsicable[str]]] to support intrinsic functions like !Ref for both list and list item
    ExcludedTypes: SamIntrinsicable[list[SamIntrinsicable[str]]] | None = instancerequirements("ExcludedTypes")


class ScalingConfig(BaseModel):
    # Optional maximum instance count - maps to CFN CapacityProviderScalingConfig.MaxVCpuCount
    # Uses SamIntrinsicable[int] to support dynamic scaling limits via parameters/conditions
    MaxVCpuCount: SamIntrinsicable[int] | None = scalingconfig("MaxVCpuCount")
    # Average CPU utilization target (0-100) - maps to CFN ScalingPolicies with CPU metric type
    # When specified, automatically sets ScalingMode to "Manual"
    # Uses SamIntrinsicable[float] to support dynamic scaling targets via parameters/conditions
    AverageCPUUtilization: SamIntrinsicable[float] | None = scalingconfig("AverageCPUUtilization")


class Properties(BaseModel):
    CapacityProviderName: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "CapacityProviderName",
        ["AWS::Lambda::CapacityProvider", "Properties", "CapacityProviderName"],
    )

    # Required VPC configuration - preserves CFN structure, required for EC2 instance networking
    # Uses custom VpcConfig class to validate required SubnetIds while maintaining passthrough behavior
    VpcConfig: VpcConfig = properties("VpcConfig")

    # Optional operator role ARN - if not provided, SAM auto-generates one with EC2 management permissions
    OperatorRole: PassThroughProp | None = properties("OperatorRole")

    # Optional tags - SAM transforms key-value pairs to CFN Tag objects before passing to CFN
    # Uses DictStrAny to support flexible tag structure with string keys and any values
    Tags: DictStrAny | None = properties("Tags")

    # Optional flag to propagate tags to resources created by this capacity provider
    # When true, all tags defined on the capacity provider will be propagated to generated resources
    PropagateTags: bool | None = properties("PropagateTags")

    # Optional instance requirements - maps to CFN InstanceRequirements with property name shortening
    # Uses custom InstanceRequirements class because SAM shortens names
    InstanceRequirements: InstanceRequirements | None = properties("InstanceRequirements")

    # Optional scaling configuration - maps to CFN CapacityProviderScalingConfig
    # Uses custom ScalingConfig class because SAM renames construct (CapacityProviderScalingConfig→ScalingConfig)
    ScalingConfig: ScalingConfig | None = properties("ScalingConfig")

    KmsKeyArn: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "KmsKeyArn",
        ["AWS::Lambda::CapacityProvider", "Properties", "KmsKeyArn"],
    )


class Globals(BaseModel):
    # Global VPC configuration - can be inherited by capacity providers if not overridden
    # Uses custom VpcConfig class to validate required SubnetIds while maintaining passthrough behavior
    VpcConfig: VpcConfig | None = properties("VpcConfig")

    # Global operator role ARN - can be inherited by capacity providers if not overridden
    OperatorRole: PassThroughProp | None = properties("OperatorRole")

    # Global tags - can be inherited and merged with resource-specific tags
    # Uses DictStrAny to support flexible tag structure with string keys and any values
    Tags: DictStrAny | None = properties("Tags")

    # Global flag to propagate tags to resources created by capacity providers
    # When true, all tags defined on capacity providers will be propagated to generated resources
    PropagateTags: bool | None = properties("PropagateTags")

    # Global instance requirements - can be inherited by capacity providers if not overridden
    # Uses custom InstanceRequirements class because SAM shortens names
    InstanceRequirements: InstanceRequirements | None = properties("InstanceRequirements")

    # Global scaling configuration - can be inherited by capacity providers if not overridden
    # Uses custom ScalingConfig class because SAM renames construct (CapacityProviderScalingConfig→ScalingConfig)
    ScalingConfig: ScalingConfig | None = properties("ScalingConfig")

    KmsKeyArn: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "KmsKeyArn",
        ["AWS::Lambda::CapacityProvider", "Properties", "KmsKeyArn"],
    )


class Resource(ResourceAttributes):
    # Literal type ensures only correct resource type is accepted
    Type: Literal["AWS::Serverless::CapacityProvider"]
    # Required properties using the Properties class for full validation
    Properties: Properties
