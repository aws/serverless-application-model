from __future__ import annotations

from typing import List, Literal, Optional

from samtranslator.internal.schema_source.common import (
    BaseModel,
    DictStrAny,
    PassThroughProp,
    ResourceAttributes,
    SamIntrinsicable,
    get_prop,
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
    SecurityGroupIds: Optional[List[SamIntrinsicable[str]]] = vpcconfig("SecurityGroupIds")
    # Required list of subnet IDs - supports intrinsic functions for dynamic VPC configuration
    SubnetIds: List[SamIntrinsicable[str]] = vpcconfig("SubnetIds")


class InstanceRequirements(BaseModel):
    # Optional list of CPU architectures - maps to CFN InstanceRequirements.Architecture
    # Uses List[SamIntrinsicable[str]] to support intrinsic functions like !Ref for dynamic architecture values
    Architectures: Optional[List[SamIntrinsicable[str]]] = instancerequirements("Architectures")
    # Optional list of allowed EC2 instance types - maps to CFN InstanceRequirements.AllowedInstanceTypes
    # Uses List[SamIntrinsicable[str]] to support intrinsic functions like !Ref for dynamic instance types
    AllowedTypes: Optional[List[SamIntrinsicable[str]]] = instancerequirements("AllowedTypes")
    # Optional list of excluded EC2 instance types - maps to CFN InstanceRequirements.ExcludedInstanceTypes
    # Uses List[SamIntrinsicable[str]] to support intrinsic functions like !Ref for dynamic instance types
    ExcludedTypes: Optional[List[SamIntrinsicable[str]]] = instancerequirements("ExcludedTypes")


class ScalingConfig(BaseModel):
    # Optional maximum instance count - maps to CFN CapacityProviderScalingConfig.MaxVCpuCount
    # Uses SamIntrinsicable[int] to support dynamic scaling limits via parameters/conditions
    MaxVCpuCount: Optional[SamIntrinsicable[int]] = scalingconfig("MaxVCpuCount")
    # Average CPU utilization target (0-100) - maps to CFN ScalingPolicies with CPU metric type
    # When specified, automatically sets ScalingMode to "Manual"
    # Uses SamIntrinsicable[float] to support dynamic scaling targets via parameters/conditions
    AverageCPUUtilization: Optional[SamIntrinsicable[float]] = scalingconfig("AverageCPUUtilization")


class Properties(BaseModel):
    # TODO: Change back to passthrough_prop after CloudFormation schema is updated with AWS::Lambda::CapacityProvider
    # Optional capacity provider name - passes through directly to CFN AWS::Lambda::CapacityProvider
    # Uses PassThroughProp because it's a direct 1:1 mapping with no SAM transformation
    # CapacityProviderName: Optional[PassThroughProp] = passthrough_prop(
    #     PROPERTIES_STEM,
    #     "CapacityProviderName",
    #     ["AWS::Lambda::CapacityProvider", "Properties", "CapacityProviderName"],
    # )
    CapacityProviderName: Optional[PassThroughProp]  # TODO: add documentation

    # Required VPC configuration - preserves CFN structure, required for EC2 instance networking
    # Uses custom VpcConfig class to validate required SubnetIds while maintaining passthrough behavior
    VpcConfig: VpcConfig = properties("VpcConfig")

    # Optional operator role ARN - if not provided, SAM auto-generates one with EC2 management permissions
    OperatorRole: Optional[PassThroughProp] = properties("OperatorRole")

    # Optional tags - SAM transforms key-value pairs to CFN Tag objects before passing to CFN
    # Uses DictStrAny to support flexible tag structure with string keys and any values
    Tags: Optional[DictStrAny] = properties("Tags")

    # Optional flag to propagate tags to resources created by this capacity provider
    # When true, all tags defined on the capacity provider will be propagated to generated resources
    PropagateTags: Optional[bool] = properties("PropagateTags")

    # Optional instance requirements - maps to CFN InstanceRequirements with property name shortening
    # Uses custom InstanceRequirements class because SAM shortens names
    InstanceRequirements: Optional[InstanceRequirements] = properties("InstanceRequirements")

    # Optional scaling configuration - maps to CFN CapacityProviderScalingConfig
    # Uses custom ScalingConfig class because SAM renames construct (CapacityProviderScalingConfig→ScalingConfig)
    ScalingConfig: Optional[ScalingConfig] = properties("ScalingConfig")

    # TODO: Change back to passthrough_prop after CloudFormation schema is updated with AWS::Lambda::CapacityProvider
    # Optional KMS key ARN - passes through directly to CFN for encryption configuration
    # Uses PassThroughProp because it's a direct 1:1 mapping with no SAM transformation
    # KMSKeyArn: Optional[PassThroughProp] = passthrough_prop(
    #     PROPERTIES_STEM,
    #     "KMSKeyArn",
    #     ["AWS::Lambda::CapacityProvider", "Properties", "KMSKeyArn"],
    # )
    KMSKeyArn: Optional[PassThroughProp]  # TODO: add documentation


class Globals(BaseModel):
    # Global VPC configuration - can be inherited by capacity providers if not overridden
    # Uses custom VpcConfig class to validate required SubnetIds while maintaining passthrough behavior
    VpcConfig: Optional[VpcConfig] = properties("VpcConfig")

    # Global operator role ARN - can be inherited by capacity providers if not overridden
    OperatorRole: Optional[PassThroughProp] = properties("OperatorRole")

    # Global tags - can be inherited and merged with resource-specific tags
    # Uses DictStrAny to support flexible tag structure with string keys and any values
    Tags: Optional[DictStrAny] = properties("Tags")

    # Global flag to propagate tags to resources created by capacity providers
    # When true, all tags defined on capacity providers will be propagated to generated resources
    PropagateTags: Optional[bool] = properties("PropagateTags")

    # Global instance requirements - can be inherited by capacity providers if not overridden
    # Uses custom InstanceRequirements class because SAM shortens names
    InstanceRequirements: Optional[InstanceRequirements] = properties("InstanceRequirements")

    # Global scaling configuration - can be inherited by capacity providers if not overridden
    # Uses custom ScalingConfig class because SAM renames construct (CapacityProviderScalingConfig→ScalingConfig)
    ScalingConfig: Optional[ScalingConfig] = properties("ScalingConfig")

    KMSKeyArn: Optional[PassThroughProp]  # TODO: add documentation


class Resource(ResourceAttributes):
    # Literal type ensures only correct resource type is accepted
    Type: Literal["AWS::Serverless::CapacityProvider"]
    # Required properties using the Properties class for full validation
    Properties: Properties
