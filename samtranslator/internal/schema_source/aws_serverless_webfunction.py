from __future__ import annotations

from typing import Any, Literal

from samtranslator.internal.schema_source.common import (
    BaseModel,
    ResourceAttributes,
    SamIntrinsicable,
    get_prop,
)

PROPERTIES_STEM = "sam-resource-webfunction"

properties = get_prop(PROPERTIES_STEM)


class Properties(BaseModel):
    Runtime: SamIntrinsicable[str] | None = properties("Runtime")
    CodeUri: Any | None = properties("CodeUri")
    FunctionName: SamIntrinsicable[str] | None = properties("FunctionName")
    Timeout: SamIntrinsicable[int] | None = properties("Timeout")
    EnvironmentVariables: dict[str, Any] | None = properties("EnvironmentVariables")
    ExecutionRoleArn: Any | None = properties("ExecutionRoleArn")
    EndpointName: SamIntrinsicable[str] | None = properties("EndpointName")
    EndpointType: SamIntrinsicable[str] | None = properties("EndpointType")
    EndpointDescription: SamIntrinsicable[str] | None = properties("EndpointDescription")
    AuthType: SamIntrinsicable[str] | None = properties("AuthType")
    AutoDeploymentMode: SamIntrinsicable[str] | None = properties("AutoDeploymentMode")
    RevisionWeights: dict[str, Any] | None = properties("RevisionWeights")
    ReplicaRegions: Any | None = properties("ReplicaRegions")
    RevisionDescription: SamIntrinsicable[str] | None = properties("RevisionDescription")
    KmsKeyArn: SamIntrinsicable[str] | None = properties("KmsKeyArn")
    LoggingConfig: dict[str, Any] | None = properties("LoggingConfig")
    ScalingConfig: dict[str, Any] | None = properties("ScalingConfig")
    ThrottleConfig: dict[str, Any] | None = properties("ThrottleConfig")
    MaxConcurrencyPerEnvironment: SamIntrinsicable[int] | None = properties("MaxConcurrencyPerEnvironment")
    EgressNetworkConnectorArn: SamIntrinsicable[str] | None = properties("EgressNetworkConnectorArn")
    EntryPoint: SamIntrinsicable[str] | None = properties("EntryPoint")
    InlineCode: str | None = properties("InlineCode")
    Tags: dict[str, Any] | None = properties("Tags")


class Globals(BaseModel):
    Runtime: SamIntrinsicable[str] | None = properties("Runtime")
    Timeout: SamIntrinsicable[int] | None = properties("Timeout")
    EnvironmentVariables: dict[str, Any] | None = properties("EnvironmentVariables")
    ExecutionRoleArn: Any | None = properties("ExecutionRoleArn")
    AuthType: SamIntrinsicable[str] | None = properties("AuthType")
    KmsKeyArn: SamIntrinsicable[str] | None = properties("KmsKeyArn")
    LoggingConfig: dict[str, Any] | None = properties("LoggingConfig")
    ScalingConfig: dict[str, Any] | None = properties("ScalingConfig")
    ThrottleConfig: dict[str, Any] | None = properties("ThrottleConfig")
    MaxConcurrencyPerEnvironment: SamIntrinsicable[int] | None = properties("MaxConcurrencyPerEnvironment")
    EgressNetworkConnectorArn: SamIntrinsicable[str] | None = properties("EgressNetworkConnectorArn")
    EndpointType: SamIntrinsicable[str] | None = properties("EndpointType")
    AutoDeploymentMode: SamIntrinsicable[str] | None = properties("AutoDeploymentMode")
    ReplicaRegions: Any | None = properties("ReplicaRegions")
    Tags: dict[str, Any] | None = properties("Tags")


class Resource(ResourceAttributes):
    Type: Literal["AWS::Serverless::WebFunction"]
    Properties: Properties
