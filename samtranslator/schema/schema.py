from __future__ import annotations

from typing_extensions import Literal
from typing import Any, Dict, List, Optional, Union

import pydantic
from pydantic import Extra

# TODO: Get rid of this in favor of proper types
Unknown = Optional[Any]

# Value passed directly to CloudFormation; not used by SAM
PassThrough = Any  # TODO: Make it behave like typescript's unknown

# Intrinsic resolvable by the SAM transform
SamIntrinsic = Dict[str, Any]

_LenientBaseModel = pydantic.BaseModel
constr = pydantic.constr


class BaseModel(_LenientBaseModel):
    """
    By default strict
    https://pydantic-docs.helpmanual.io/usage/model_config/#change-behaviour-globally
    """

    class Config:
        extra = Extra.forbid


class ResourceReference(BaseModel):
    Id: Optional[str]
    Arn: Optional[PassThrough]
    Name: Optional[PassThrough]
    Qualifier: Optional[PassThrough]
    QueueUrl: Optional[PassThrough]
    ResourceId: Optional[PassThrough]
    RoleName: Optional[PassThrough]
    Type: Optional[str]


class ConnectorProperties(BaseModel):
    Source: ResourceReference
    Destination: ResourceReference
    Permissions: List[Literal["Read", "Write"]]


class AwsServerlessConnector(BaseModel):
    Type: Literal["AWS::Serverless::Connector"]
    Properties: ConnectorProperties


class FunctionCodeUri(BaseModel):
    Bucket: Union[str, SamIntrinsic]
    Key: Union[str, SamIntrinsic]
    Version: Optional[Union[str, SamIntrinsic]]


class FunctionDeploymentPreferenceHooks(BaseModel):
    PostTraffic: Optional[Union[str, SamIntrinsic]]
    PreTraffic: Optional[Union[str, SamIntrinsic]]


class FunctionDeploymentPreference(BaseModel):
    Alarms: Optional[Union[List[SamIntrinsic], SamIntrinsic]]
    Enabled: Optional[Union[bool, SamIntrinsic]]
    Hooks: Optional[FunctionDeploymentPreferenceHooks]
    PassthroughCondition: Optional[Union[bool, SamIntrinsic]]
    Role: Optional[Union[str, SamIntrinsic]]
    TriggerConfigurations: Optional[PassThrough]
    Type: Optional[
        Union[str, SamIntrinsic]
    ]  # TODO: Should investigate whether this is a required field. This is a required field on documentation. However, we don't seem to use this field.


class FunctionDeadLetterQueue(BaseModel):
    TargetArn: str
    Type: Literal["SNS", "SQS"]


class FunctionEventInvokeConfig(BaseModel):
    DestinationConfig: Optional[PassThrough]
    MaximumEventAgeInSeconds: Optional[int]
    MaximumRetryAttempts: Optional[int]


class FunctionEvent(BaseModel):
    Properties: Any
    Type: str


class FunctionUrlConfig(BaseModel):
    AuthType: Union[str, SamIntrinsic]
    Cors: Optional[PassThrough]


class FunctionProperties(BaseModel):
    Architectures: Optional[PassThrough]
    AssumeRolePolicyDocument: Optional[Dict[str, Any]]
    AutoPublishAlias: Optional[Union[str, SamIntrinsic]]
    AutoPublishCodeSha256: Optional[Union[str, SamIntrinsic]]
    CodeSigningConfigArn: Optional[Union[str, SamIntrinsic]]
    CodeUri: Optional[Union[str, FunctionCodeUri]]
    DeadLetterQueue: Optional[Union[SamIntrinsic, FunctionDeadLetterQueue]]
    DeploymentPreference: Optional[FunctionDeploymentPreference]
    Description: Optional[PassThrough]
    Environment: Optional[PassThrough]
    EphemeralStorage: Optional[PassThrough]
    EventInvokeConfig: Optional[FunctionEventInvokeConfig]
    Events: Optional[Dict[str, FunctionEvent]]
    FileSystemConfigs: Optional[PassThrough]
    FunctionName: Optional[PassThrough]
    FunctionUrlConfig: Optional[FunctionUrlConfig]
    Handler: Optional[PassThrough]
    ImageConfig: Optional[PassThrough]
    ImageUri: Optional[PassThrough]
    InlineCode: Optional[PassThrough]
    KmsKeyArn: Optional[PassThrough]
    Layers: Optional[PassThrough]
    MemorySize: Optional[PassThrough]
    PackageType: Optional[PassThrough]
    PermissionsBoundary: Optional[PassThrough]
    Policies: Optional[Union[str, List[Union[str, SamIntrinsic]], SamIntrinsic]]
    ProvisionedConcurrencyConfig: Optional[PassThrough]
    ReservedConcurrentExecutions: Optional[PassThrough]
    Role: Optional[Union[str, SamIntrinsic]]
    Runtime: Optional[PassThrough]
    Tags: Optional[Dict[str, Any]]
    Timeout: Optional[PassThrough]
    Tracing: Optional[Union[str, SamIntrinsic]]
    VersionDescription: Optional[PassThrough]
    VpcConfig: Optional[PassThrough]


class AwsServerlessFunction(BaseModel):
    Type: Literal["AWS::Serverless::Function"]
    Properties: Optional[FunctionProperties]
    DeletionPolicy: Unknown
    UpdateReplacePolicy: Unknown
    Condition: Unknown
    DependsOn: Unknown
    Metadata: Unknown


class SimpleTablePrimaryKey(BaseModel):
    Name: PassThrough
    Type: PassThrough


class SimpleTableProperties(BaseModel):
    PrimaryKey: Optional[SimpleTablePrimaryKey]
    ProvisionedThroughput: Optional[PassThrough]
    SSESpecification: Optional[PassThrough]
    TableName: Optional[PassThrough]
    Tags: Optional[Dict[str, Any]]


class AwsServerlessSimpleTable(BaseModel):
    Type: Literal["AWS::Serverless::SimpleTable"]
    Properties: Optional[SimpleTableProperties]


class StateMachineEventsScheduleDeadLetterConfig(BaseModel):
    Arn: Optional[PassThrough]
    QueueLogicalId: Optional[str]
    Type: Optional[Literal["SQS"]]


class StateMachineEventsScheduleProperties(BaseModel):
    DeadLetterConfig: Optional[StateMachineEventsScheduleDeadLetterConfig]
    Description: Optional[PassThrough]
    Enabled: Optional[bool]
    Input: Optional[PassThrough]
    Name: Optional[PassThrough]
    RetryPolicy: Optional[PassThrough]
    Schedule: Optional[PassThrough]
    State: Optional[PassThrough]


class StateMachineEventsSchedule(BaseModel):
    Type: Literal["Schedule"]
    Properties: StateMachineEventsScheduleProperties


class StateMachineEventsScheduleV2Properties(BaseModel):
    DeadLetterConfig: Optional[StateMachineEventsScheduleDeadLetterConfig]
    Description: Optional[PassThrough]
    EndDate: Optional[PassThrough]
    FlexibleTimeWindow: Optional[PassThrough]
    GroupName: Optional[PassThrough]
    Input: Optional[PassThrough]
    KmsKeyArn: Optional[PassThrough]
    Name: Optional[PassThrough]
    PermissionsBoundary: Optional[PassThrough]
    RetryPolicy: Optional[PassThrough]
    RoleArn: Optional[PassThrough]  # TODO: Add to docs
    ScheduleExpression: Optional[PassThrough]
    ScheduleExpressionTimezone: Optional[PassThrough]
    StartDate: Optional[PassThrough]
    State: Optional[PassThrough]


class StateMachineEventsScheduleV2(BaseModel):
    Type: Literal["ScheduleV2"]
    Properties: StateMachineEventsScheduleV2Properties


class StateMachineEventsCloudWatchEventProperties(BaseModel):
    EventBusName: Optional[PassThrough]
    Input: Optional[PassThrough]
    InputPath: Optional[PassThrough]
    Pattern: Optional[PassThrough]


class StateMachineEventsCloudWatchEvent(BaseModel):
    Type: Literal["CloudWatchEvent"]
    Properties: StateMachineEventsCloudWatchEventProperties


class StateMachineEventsEventBridgeRuleDeadLetterConfig(BaseModel):
    Arn: Optional[PassThrough]
    QueueLogicalId: Optional[str]
    Type: Optional[Literal["SQS"]]


class StateMachineEventsEventBridgeRuleProperties(BaseModel):
    DeadLetterConfig: Optional[StateMachineEventsEventBridgeRuleDeadLetterConfig]
    EventBusName: Optional[PassThrough]
    Input: Optional[PassThrough]
    InputPath: Optional[PassThrough]
    Pattern: Optional[PassThrough]
    RetryPolicy: Optional[PassThrough]


class StateMachineEventsEventBridgeRule(BaseModel):
    Type: Literal["EventBridgeRule"]
    Properties: StateMachineEventsEventBridgeRuleProperties


class StateMachineEventsApiAuthResourcePolicy(BaseModel):
    AwsAccountBlacklist: Optional[List[str]]
    AwsAccountWhitelist: Optional[List[str]]
    CustomStatements: Optional[List[str]]
    IntrinsicVpcBlacklist: Optional[List[str]]
    IntrinsicVpcWhitelist: Optional[List[str]]
    IntrinsicVpceBlacklist: Optional[List[str]]
    IntrinsicVpceWhitelist: Optional[List[str]]
    IpRangeBlacklist: Optional[List[str]]
    IpRangeWhitelist: Optional[List[str]]
    SourceVpcBlacklist: Optional[List[str]]
    SourceVpcWhitelist: Optional[List[str]]


class StateMachineEventsApiAuth(BaseModel):
    ApiKeyRequired: Optional[bool]
    AuthorizationScopes: Optional[List[str]]
    Authorizer: Optional[str]
    ResourcePolicy: Optional[StateMachineEventsApiAuthResourcePolicy]


class StateMachineEventsApiProperties(BaseModel):
    Auth: Optional[StateMachineEventsApiAuth]
    Method: str
    Path: str
    RestApiId: Optional[SamIntrinsic]
    UnescapeMappingTemplate: Optional[bool]  # TODO: Add to docs


class StateMachineEventsApi(BaseModel):
    Type: Literal["Api"]
    Properties: StateMachineEventsApiProperties


class StateMachineProperties(BaseModel):
    Definition: Optional[Dict[str, Any]]
    DefinitionSubstitutions: Optional[Dict[str, Any]]
    DefinitionUri: Optional[Union[str, PassThrough]]
    Events: Optional[
        Dict[
            str,
            Union[
                StateMachineEventsSchedule,
                StateMachineEventsScheduleV2,
                StateMachineEventsCloudWatchEvent,
                StateMachineEventsEventBridgeRule,
                StateMachineEventsApi,
            ],
        ]
    ]
    Logging: Optional[PassThrough]
    Name: Optional[PassThrough]
    PermissionsBoundary: Optional[PassThrough]
    Policies: Optional[Union[str, List[str], Dict[str, Any], List[Dict[str, Any]]]]
    Role: Optional[PassThrough]
    Tags: Optional[Dict[str, Any]]
    Tracing: Optional[PassThrough]
    Type: Optional[PassThrough]


class AwsServerlessStateMachine(BaseModel):
    Type: Literal["AWS::Serverless::StateMachine"]
    Properties: StateMachineProperties
    Condition: Optional[PassThrough]


class LayerVersionContentUri(BaseModel):
    Bucket: PassThrough
    Key: PassThrough
    Version: Optional[PassThrough]


class LayerVersionProperties(BaseModel):
    CompatibleArchitectures: Optional[PassThrough]
    CompatibleRuntimes: Optional[PassThrough]
    ContentUri: Union[str, LayerVersionContentUri]
    Description: Optional[PassThrough]
    LayerName: Optional[PassThrough]
    LicenseInfo: Optional[PassThrough]
    RetentionPolicy: Optional[Union[str, SamIntrinsic]]


class AwsServerlessLayerVersion(BaseModel):
    Type: Literal["AWS::Serverless::LayerVersion"]
    Properties: LayerVersionProperties
    Condition: Optional[PassThrough]
    DeletionPolicy: Optional[PassThrough]


class ApiProperties(BaseModel):
    AccessLogSetting: Unknown
    ApiKeySourceType: Unknown
    Auth: Unknown
    BinaryMediaTypes: Unknown
    CacheClusterEnabled: Unknown
    CacheClusterSize: Unknown
    CanarySetting: Unknown
    Cors: Unknown
    DefinitionBody: Unknown
    DefinitionUri: Unknown
    Description: Unknown
    DisableExecuteApiEndpoint: Unknown
    Domain: Unknown
    EndpointConfiguration: Unknown
    FailOnWarnings: Unknown
    GatewayResponses: Unknown
    MethodSettings: Unknown
    MinimumCompressionSize: Unknown
    Mode: Unknown
    Models: Unknown
    Name: Unknown
    OpenApiVersion: Unknown
    StageName: Unknown
    Tags: Unknown
    TracingEnabled: Unknown
    Variables: Unknown


class AwsServerlessApi(BaseModel):
    Type: Literal["AWS::Serverless::Api"]
    Properties: ApiProperties
    Condition: Unknown
    DeletionPolicy: Unknown
    UpdatePolicy: Unknown
    UpdateReplacePolicy: Unknown
    DependsOn: Unknown
    Metadata: Unknown


class HttpApiProperties(BaseModel):
    AccessLogSettings: Unknown
    Auth: Unknown
    CorsConfiguration: Unknown
    DefaultRouteSettings: Unknown
    DefinitionBody: Unknown
    DefinitionUri: Unknown
    Description: Unknown
    DisableExecuteApiEndpoint: Unknown
    Domain: Unknown
    FailOnWarnings: Unknown
    RouteSettings: Unknown
    StageName: Unknown
    StageVariables: Unknown
    Tags: Unknown
    Name: Unknown


class AwsServerlessHttpApi(BaseModel):
    Type: Literal["AWS::Serverless::HttpApi"]
    Properties: Optional[HttpApiProperties]
    Metadata: Unknown
    Condition: Unknown


class ApplicationLocation(BaseModel):
    ApplicationId: Union[str, SamIntrinsic]
    SemanticVersion: Union[str, SamIntrinsic]


class ApplicationProperties(BaseModel):
    Location: Union[str, ApplicationLocation]
    NotificationARNs: Optional[PassThrough]
    Parameters: Optional[PassThrough]
    Tags: Optional[Dict[str, Any]]
    TimeoutInMinutes: Optional[PassThrough]


class AwsServerlessApplication(BaseModel):
    Type: Literal["AWS::Serverless::Application"]
    Properties: ApplicationProperties
    Condition: Optional[PassThrough]


# Match anything not containing Serverless
class AnyNonServerlessResource(_LenientBaseModel):
    Type: constr(regex=r"^((?!::Serverless::).)*$")  # type: ignore


class GlobalsFunction(BaseModel):
    Handler: Unknown
    Runtime: Unknown
    CodeUri: Unknown
    DeadLetterQueue: Unknown
    Description: Unknown
    MemorySize: Unknown
    Timeout: Unknown
    VpcConfig: Unknown
    Environment: Unknown
    Tags: Unknown
    Tracing: Unknown
    KmsKeyArn: Unknown
    Layers: Unknown
    AutoPublishAlias: Unknown
    DeploymentPreference: Unknown
    PermissionsBoundary: Unknown
    ReservedConcurrentExecutions: Unknown
    ProvisionedConcurrencyConfig: Unknown
    AssumeRolePolicyDocument: Unknown
    EventInvokeConfig: Unknown
    Architectures: Unknown
    EphemeralStorage: Unknown


class GlobalsApi(BaseModel):
    Auth: Unknown
    Name: Unknown
    DefinitionUri: Unknown
    CacheClusterEnabled: Unknown
    CacheClusterSize: Unknown
    Variables: Unknown
    EndpointConfiguration: Unknown
    MethodSettings: Unknown
    BinaryMediaTypes: Unknown
    MinimumCompressionSize: Unknown
    Cors: Unknown
    GatewayResponses: Unknown
    AccessLogSetting: Unknown
    CanarySetting: Unknown
    TracingEnabled: Unknown
    OpenApiVersion: Unknown
    Domain: Unknown


class GlobalsHttpApi(BaseModel):
    Auth: Unknown
    AccessLogSettings: Unknown
    StageVariables: Unknown
    Tags: Unknown
    RouteSettings: Unknown
    FailOnWarnings: Unknown
    Domain: Unknown
    CorsConfiguration: Unknown
    DefaultRouteSettings: Unknown


class GlobalsSimpleTable(BaseModel):
    SSESpecification: Unknown


class Globals(BaseModel):
    Function: Optional[GlobalsFunction]
    Api: Optional[GlobalsApi]
    HttpApi: Optional[GlobalsHttpApi]
    SimpleTable: Optional[GlobalsSimpleTable]


class Model(_LenientBaseModel):
    Globals: Optional[Globals]
    Resources: Dict[
        str,
        Union[
            AwsServerlessConnector,
            AwsServerlessFunction,
            AwsServerlessSimpleTable,
            AwsServerlessStateMachine,
            AwsServerlessLayerVersion,
            AwsServerlessApi,
            AwsServerlessHttpApi,
            AwsServerlessApplication,
            AnyNonServerlessResource,
        ],
    ]


if __name__ == "__main__":
    print(Model.schema_json(indent=2))
