from __future__ import annotations

from typing import Literal

from samtranslator.compat import pydantic
from samtranslator.internal.schema_source.common import (
    BaseModel,
    DictStrAny,
    ResourceAttributes,
    SamIntrinsicable,
    get_prop,
)

PROPERTIES_STEM = "sam-resource-networkconnector"
VPC_CONFIG_STEM = "sam-property-networkconnector-vpcconfig"

properties = get_prop(PROPERTIES_STEM)
vpc_config_props = get_prop(VPC_CONFIG_STEM)


class VpcConfig(BaseModel):
    SubnetIds: list[SamIntrinsicable[str]] = vpc_config_props("SubnetIds")
    SecurityGroupIds: list[SamIntrinsicable[str]] = vpc_config_props("SecurityGroupIds")
    NetworkProtocol: SamIntrinsicable[Literal["IPv4", "DualStack"]] = vpc_config_props("NetworkProtocol")


class Properties(BaseModel):
    Name: SamIntrinsicable[str] | None = properties("Name")
    VpcConfig: VpcConfig = properties("VpcConfig")
    # The single compute type a connector serves. Constrained here (exactly one item; enum values) so
    # `sam validate --lint` surfaces the same rules as the transform. Plain field (no doc stem) to avoid
    # churning sam-docs.json; intrinsics still validate via SamIntrinsicable.
    ComputeTypes: list[SamIntrinsicable[Literal["MicroVm", "WebFunction"]]] | None = pydantic.Field(
        default=None, min_items=1, max_items=1
    )
    OperatorRole: SamIntrinsicable[str] | None = properties("OperatorRole")
    Tags: DictStrAny | None = properties("Tags")
    PropagateTags: bool | None = properties("PropagateTags")


class Globals(BaseModel):
    OperatorRole: SamIntrinsicable[str] | None = properties("OperatorRole")
    Tags: DictStrAny | None = properties("Tags")
    PropagateTags: bool | None = properties("PropagateTags")


class Resource(ResourceAttributes):
    Type: Literal["AWS::Serverless::NetworkConnector"]
    Properties: Properties
