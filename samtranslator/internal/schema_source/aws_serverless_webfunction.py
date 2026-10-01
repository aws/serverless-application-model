from __future__ import annotations

from typing import Any, Literal

from samtranslator.internal.schema_source.common import (
    BaseModel,
    ResourceAttributes,
    SamIntrinsicable,
)


class Properties(BaseModel):
    Runtime: SamIntrinsicable[str]
    CodeUri: Any | None = None
    FunctionName: SamIntrinsicable[str] | None = None
    Timeout: SamIntrinsicable[int] | None = None
    EnvironmentVariables: dict[str, Any] | None = None
    ExecutionRoleArn: Any | None = None
    EndpointName: SamIntrinsicable[str] | None = None
    EndpointType: SamIntrinsicable[str] | None = None
    EndpointDescription: SamIntrinsicable[str] | None = None
    AuthType: SamIntrinsicable[str]
    AutoDeploymentMode: SamIntrinsicable[str] | None = None
    RevisionWeights: dict[str, Any] | None = None
    ReplicaRegions: Any | None = None
    RevisionDescription: SamIntrinsicable[str] | None = None
    KmsKeyArn: SamIntrinsicable[str] | None = None
    LoggingConfig: dict[str, Any] | None = None
    ScalingConfig: dict[str, Any] | None = None
    ThrottleConfig: dict[str, Any] | None = None
    MaxConcurrencyPerEnvironment: SamIntrinsicable[int] | None = None
    EntryPoint: SamIntrinsicable[str] | None = None
    InlineCode: str | None = None
    Tags: dict[str, Any] | None = None


class Resource(ResourceAttributes):
    Type: Literal["AWS::Serverless::WebFunction"]
    Properties: Properties
