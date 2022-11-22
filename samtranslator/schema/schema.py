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


class EventsDeadLetterConfig(BaseModel):
    Arn: Optional[PassThrough]
    QueueLogicalId: Optional[str]
    Type: Optional[Literal["SQS"]]


class EventsScheduleProperties(BaseModel):
    DeadLetterConfig: Optional[EventsDeadLetterConfig]
    Description: Optional[PassThrough]
    Enabled: Optional[bool]
    Input: Optional[PassThrough]
    Name: Optional[PassThrough]
    RetryPolicy: Optional[PassThrough]
    Schedule: Optional[PassThrough]
    State: Optional[PassThrough]


class EventsSchedule(BaseModel):
    Type: Literal["Schedule"]
    Properties: EventsScheduleProperties


class EventsScheduleV2Properties(BaseModel):
    DeadLetterConfig: Optional[EventsDeadLetterConfig]
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


class EventsScheduleV2(BaseModel):
    Type: Literal["ScheduleV2"]
    Properties: EventsScheduleV2Properties


class ResourcePolicy(BaseModel):
    AwsAccountBlacklist: Optional[List[Union[str, Dict[str, Any]]]]
    AwsAccountWhitelist: Optional[List[Union[str, Dict[str, Any]]]]
    CustomStatements: Optional[List[Union[str, Dict[str, Any]]]]
    IntrinsicVpcBlacklist: Optional[List[Union[str, Dict[str, Any]]]]
    IntrinsicVpcWhitelist: Optional[List[Union[str, Dict[str, Any]]]]
    IntrinsicVpceBlacklist: Optional[List[Union[str, Dict[str, Any]]]]
    IntrinsicVpceWhitelist: Optional[List[Union[str, Dict[str, Any]]]]
    IpRangeBlacklist: Optional[List[Union[str, Dict[str, Any]]]]
    IpRangeWhitelist: Optional[List[Union[str, Dict[str, Any]]]]
    SourceVpcBlacklist: Optional[List[Union[str, Dict[str, Any]]]]
    SourceVpcWhitelist: Optional[List[Union[str, Dict[str, Any]]]]


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


class FunctionS3Properties(BaseModel):
    Bucket: Union[str, SamIntrinsic]
    Events: PassThrough
    Filter: Optional[PassThrough]


class FunctionS3Event(BaseModel):
    Properties: FunctionS3Properties
    Type: Literal["S3"]


class SqsSubscription(BaseModel):
    BatchSize: Optional[Union[str, SamIntrinsic]]
    Enabled: Optional[bool]
    QueueArn: Union[str, SamIntrinsic]
    QueuePolicyLogicalId: Optional[str]
    QueueUrl: Union[str, SamIntrinsic]


class FunctionSNSProperties(BaseModel):
    FilterPolicy: Optional[PassThrough]
    Region: Optional[PassThrough]
    SqsSubscription: Optional[Union[bool, SqsSubscription]]
    Topic: PassThrough


class FunctionSNSEvent(BaseModel):
    Properties: FunctionSNSProperties
    Type: Literal["SNS"]


class FunctionUrlConfig(BaseModel):
    AuthType: Union[str, SamIntrinsic]
    Cors: Optional[PassThrough]


class FunctionKinesisProperties(BaseModel):
    BatchSize: Optional[PassThrough]
    BisectBatchOnFunctionError: Optional[PassThrough]
    DestinationConfig: Optional[PassThrough]
    Enabled: Optional[PassThrough]
    FilterCriteria: Optional[PassThrough]
    FunctionResponseTypes: Optional[PassThrough]
    MaximumBatchingWindowInSeconds: Optional[PassThrough]
    MaximumRecordAgeInSeconds: Optional[PassThrough]
    MaximumRetryAttempts: Optional[PassThrough]
    ParallelizationFactor: Optional[PassThrough]
    StartingPosition: PassThrough
    Stream: PassThrough
    TumblingWindowInSeconds: Optional[PassThrough]


class FunctionKinesisEvent(BaseModel):
    Type: Literal["Kinesis"]
    Properties: FunctionKinesisProperties


class FunctionDynamoDBProperties(BaseModel):
    BatchSize: Optional[PassThrough]
    BisectBatchOnFunctionError: Optional[PassThrough]
    DestinationConfig: Optional[PassThrough]
    Enabled: Optional[PassThrough]
    FilterCriteria: Optional[PassThrough]
    FunctionResponseTypes: Optional[PassThrough]
    MaximumBatchingWindowInSeconds: Optional[PassThrough]
    MaximumRecordAgeInSeconds: Optional[PassThrough]
    MaximumRetryAttempts: Optional[PassThrough]
    ParallelizationFactor: Optional[PassThrough]
    StartingPosition: PassThrough
    Stream: PassThrough
    TumblingWindowInSeconds: Optional[PassThrough]


class FunctionDynamoDBEvent(BaseModel):
    Type: Literal["DynamoDB"]
    Properties: FunctionDynamoDBProperties


class FunctionSqsProperties(BaseModel):
    BatchSize: Optional[PassThrough]
    Enabled: Optional[PassThrough]
    FilterCriteria: Optional[PassThrough]
    MaximumBatchingWindowInSeconds: Optional[PassThrough]
    Queue: PassThrough


class FunctionSqsEvent(BaseModel):
    Type: Literal["SQS"]
    Properties: FunctionSqsProperties


class FunctionApiFunctionAuth(BaseModel):
    ApiKeyRequired: Optional[bool]
    AuthorizationScopes: Optional[List[str]]
    Authorizer: Optional[str]
    InvokeRole: Optional[Union[str, SamIntrinsic]]
    ResourcePolicy: Optional[ResourcePolicy]


class FunctionRequestModel(BaseModel):
    Model: str
    Required: Optional[bool]
    ValidateBody: Optional[bool]
    ValidateParameters: Optional[bool]


class FunctionRequestParameter(BaseModel):
    Caching: Optional[bool]
    Required: Optional[bool]


class FunctionApiProperties(BaseModel):
    Auth: Optional[FunctionApiFunctionAuth]
    Method: str
    Path: str
    RequestModel: Optional[FunctionRequestModel]
    RequestParameters: Optional[Union[str, FunctionRequestParameter]]
    RestApiId: Optional[Union[str, SamIntrinsic]]


class FunctionApiEvent(BaseModel):
    Type: Literal["Api"]
    Properties: FunctionApiProperties


class FunctionCloudWatchProperties(BaseModel):
    Enabled: Optional[bool]
    EventBusName: Optional[PassThrough]
    Input: Optional[PassThrough]
    InputPath: Optional[PassThrough]
    Pattern: Optional[PassThrough]
    State: Optional[PassThrough]


class FunctionCloudWatchEvent(BaseModel):
    Type: Literal["CloudWatchEvent"]
    Properties: FunctionCloudWatchProperties


class FunctionEventBridgeRuleProperties(BaseModel):
    DeadLetterConfig: Optional[EventsDeadLetterConfig]
    EventBusName: Optional[PassThrough]
    Input: Optional[PassThrough]
    InputPath: Optional[PassThrough]
    Pattern: PassThrough
    RetryPolicy: Optional[PassThrough]
    Target: Optional[PassThrough]


class FunctionEventBridgeRuleEvent(BaseModel):
    Type: Literal["EventBridgeRule"]
    Properties: FunctionEventBridgeRuleProperties


class FunctionCloudWatchLogsProperties(BaseModel):
    FilterPattern: PassThrough
    LogGroupName: PassThrough


class FunctionCloudWatchLogsEvent(BaseModel):
    Type: Literal["CloudWatchLogs"]
    Properties: FunctionCloudWatchLogsProperties


class FunctionIoTRuleProperties(BaseModel):
    AwsIotSqlVersion: Optional[PassThrough]
    Sql: PassThrough


class FunctionIoTRuleEvent(BaseModel):
    Type: Literal["IoTRule"]
    Properties: FunctionIoTRuleProperties


class FunctionAlexaSkillProperties(BaseModel):
    SkillId: Optional[str]


class FunctionAlexaSkillEvent(BaseModel):
    Type: Literal["AlexaSkill"]
    Properties: Optional[FunctionAlexaSkillProperties]


class FunctionCognitoProperties(BaseModel):
    Trigger: PassThrough
    UserPool: Union[str, SamIntrinsic]


class FunctionCognitoEvent(BaseModel):
    Type: Literal["Cognito"]
    Properties: FunctionCognitoProperties


class FunctionHttpApiAuth(BaseModel):
    AuthorizationScopes: Optional[List[str]]
    Authorizer: Optional[str]


class FunctionHttpApiProperties(BaseModel):
    ApiId: Optional[Union[str, SamIntrinsic]]
    Auth: Optional[FunctionHttpApiAuth]
    Method: Optional[str]
    Path: Optional[str]
    PayloadFormatVersion: Optional[Union[str, SamIntrinsic]]
    RouteSettings: Optional[PassThrough]
    TimeoutInMillis: Optional[Union[int, SamIntrinsic]]


class FunctionHttpApiEvent(BaseModel):
    Type: Literal["HttpApi"]
    Properties: Optional[FunctionHttpApiProperties]


class FunctionMSKProperties(BaseModel):
    ConsumerGroupId: Optional[PassThrough]
    FilterCriteria: Optional[PassThrough]
    MaximumBatchingWindowInSeconds: Optional[PassThrough]
    StartingPosition: PassThrough
    Stream: PassThrough
    Topics: PassThrough


class FunctionMSKEvent(BaseModel):
    Type: Literal["MSK"]
    Properties: FunctionMSKProperties


class FunctionMQProperties(BaseModel):
    BatchSize: Optional[PassThrough]
    Broker: PassThrough
    Enabled: Optional[PassThrough]
    FilterCriteria: Optional[PassThrough]
    MaximumBatchingWindowInSeconds: Optional[PassThrough]
    Queues: PassThrough
    SecretsManagerKmsKeyId: Optional[str]
    SourceAccessConfigurations: PassThrough


class FunctionMQEvent(BaseModel):
    Type: Literal["MQ"]
    Properties: FunctionMQProperties


class FunctionSelfManagedKafkaProperties(BaseModel):
    BatchSize: Optional[PassThrough]
    ConsumerGroupId: Optional[PassThrough]
    Enabled: Optional[PassThrough]
    FilterCriteria: Optional[PassThrough]
    KafkaBootstrapServers: Optional[List[Union[str, SamIntrinsic]]]
    SourceAccessConfigurations: PassThrough
    Topics: PassThrough


class FunctionSelfManagedKafkaEvent(BaseModel):
    Type: Literal["SelfManagedKafka"]
    Properties: FunctionSelfManagedKafkaProperties


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
    Events: Optional[
        Dict[
            str,
            Union[
                FunctionS3Event,
                FunctionSNSEvent,
                FunctionKinesisEvent,
                FunctionDynamoDBEvent,
                FunctionSqsEvent,
                FunctionApiEvent,
                EventsSchedule,
                EventsScheduleV2,
                FunctionCloudWatchEvent,
                FunctionEventBridgeRuleEvent,
                FunctionCloudWatchLogsEvent,
                FunctionIoTRuleEvent,
                FunctionAlexaSkillEvent,
                FunctionCognitoEvent,
                FunctionHttpApiEvent,
                FunctionMSKEvent,
                FunctionMQEvent,
                FunctionSelfManagedKafkaEvent,
            ],
        ]
    ]
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
    DeletionPolicy: Optional[PassThrough]
    UpdateReplacePolicy: Optional[PassThrough]
    Condition: Optional[PassThrough]
    DependsOn: Optional[PassThrough]
    Metadata: Optional[PassThrough]


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


class StateMachineEventsApiAuth(BaseModel):
    ApiKeyRequired: Optional[bool]
    AuthorizationScopes: Optional[List[str]]
    Authorizer: Optional[str]
    ResourcePolicy: Optional[ResourcePolicy]


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
                EventsSchedule,
                EventsScheduleV2,
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


class ApiAuthCognitoAuthorizationIdentity(BaseModel):
    Header: Optional[str]
    ReauthorizeEvery: Optional[Union[int, SamIntrinsic]]
    ValidationExpression: Optional[str]


class ApiAuthCognitoAuthorizer(BaseModel):
    AuthorizationScopes: Optional[List[str]]
    Identity: Optional[ApiAuthCognitoAuthorizationIdentity]
    UserPoolArn: Union[str, SamIntrinsic]


class ApiAuthLambdaTokenAuthorizationIdentity(BaseModel):
    Header: Optional[str]
    ReauthorizeEvery: Optional[Union[int, SamIntrinsic]]
    ValidationExpression: Optional[str]


class ApiAuthLambdaRequestAuthorizationIdentity(BaseModel):
    Context: Optional[List[str]]
    Headers: Optional[List[str]]
    QueryStrings: Optional[List[str]]
    ReauthorizeEvery: Optional[Union[int, SamIntrinsic]]
    StageVariables: Optional[List[str]]


class ApiAuthLambdaAuthorizer(BaseModel):
    AuthorizationScopes: Optional[List[str]]
    FunctionArn: Union[str, SamIntrinsic]
    FunctionInvokeRole: Optional[str]
    FunctionPayloadType: Optional[Literal["REQUEST", "TOKEN"]]
    Identity: Optional[Union[ApiAuthLambdaRequestAuthorizationIdentity, ApiAuthLambdaTokenAuthorizationIdentity]]


class ApiAuthUsagePlan(BaseModel):
    CreateUsagePlan: Literal["PER_API", "SHARED", "NONE"]
    Description: Optional[PassThrough]
    Quota: Optional[PassThrough]
    Tags: Optional[PassThrough]
    Throttle: Optional[PassThrough]
    UsagePlanName: Optional[PassThrough]


class ApiAuthProperties(BaseModel):
    AddDefaultAuthorizerToCorsPreflight: Optional[bool]
    ApiKeyRequired: Optional[bool]
    Authorizers: Optional[Dict[str, Union[ApiAuthCognitoAuthorizer, ApiAuthLambdaAuthorizer]]]
    DefaultAuthorizer: Optional[str]
    InvokeRole: Optional[str]
    ResourcePolicy: Optional[ResourcePolicy]
    UsagePlan: Optional[ApiAuthUsagePlan]


class ApiCorsConfiguration(BaseModel):
    AllowCredentials: Optional[bool]
    AllowHeaders: Optional[str]
    AllowMethods: Optional[str]
    AllowOrigin: str
    MaxAge: Optional[str]


class ApiDomainRoute53Configuration(BaseModel):
    DistributionDomainName: Optional[PassThrough]
    EvaluateTargetHealth: Optional[PassThrough]
    HostedZoneId: Optional[PassThrough]
    HostedZoneName: Optional[PassThrough]
    IpV6: Optional[bool]


class ApiDomainConfiguration(BaseModel):
    BasePath: Optional[PassThrough]
    CertificateArn: PassThrough
    DomainName: PassThrough
    EndpointConfiguration: Optional[Union[Literal["REGIONAL", "EDGE"], SamIntrinsic]]
    MutualTlsAuthentication: Optional[PassThrough]
    OwnershipVerificationCertificateArn: Optional[PassThrough]
    Route53: Optional[ApiDomainRoute53Configuration]
    SecurityPolicy: Optional[PassThrough]


class ApiProperties(BaseModel):
    AccessLogSetting: Optional[PassThrough]
    ApiKeySourceType: Optional[PassThrough]
    Auth: Optional[ApiAuthProperties]
    BinaryMediaTypes: Optional[PassThrough]
    CacheClusterEnabled: Optional[PassThrough]
    CacheClusterSize: Optional[PassThrough]
    CanarySetting: Optional[PassThrough]
    Cors: Optional[Union[str, ApiCorsConfiguration]]
    DefinitionBody: Optional[PassThrough]
    DefinitionUri: Optional[PassThrough]
    Description: Optional[PassThrough]
    DisableExecuteApiEndpoint: Optional[PassThrough]
    Domain: Optional[ApiDomainConfiguration]
    EndpointConfiguration: Optional[PassThrough]
    FailOnWarnings: Optional[PassThrough]
    GatewayResponses: Optional[SamIntrinsic]
    MethodSettings: Optional[PassThrough]
    MinimumCompressionSize: Optional[PassThrough]
    Mode: Optional[PassThrough]
    Models: Optional[SamIntrinsic]
    Name: Optional[PassThrough]
    OpenApiVersion: Optional[Union[float, str]]  # TODO: float doesn't exist in documentation
    StageName: Union[str, SamIntrinsic]
    Tags: Optional[PassThrough]
    TracingEnabled: Optional[PassThrough]
    Variables: Optional[PassThrough]


class AwsServerlessApi(BaseModel):
    Type: Literal["AWS::Serverless::Api"]
    Properties: ApiProperties
    Condition: Optional[PassThrough]
    DeletionPolicy: Optional[PassThrough]
    UpdatePolicy: Optional[PassThrough]
    UpdateReplacePolicy: Optional[PassThrough]
    DependsOn: Optional[PassThrough]
    Metadata: Optional[PassThrough]


class HttpApiAuthOAuth2Authorizer(BaseModel):
    AuthorizationScopes: Optional[List[str]]
    IdentitySource: Optional[str]
    JwtConfiguration: Optional[PassThrough]


class HttpApiAuthLambdaAuthorizerIdentity(BaseModel):
    Context: Optional[List[str]]
    Headers: Optional[List[str]]
    QueryStrings: Optional[List[str]]
    ReauthorizeEvery: Optional[int]
    StageVariables: Optional[List[str]]


class HttpApiAuthLambdaAuthorizer(BaseModel):
    # TODO: Many tests use floats for the version string; docs only mention string
    AuthorizerPayloadFormatVersion: Union[Literal["1.0", "2.0"], float]
    EnableSimpleResponses: Optional[bool]
    FunctionArn: SamIntrinsic
    FunctionInvokeRole: Optional[Union[str, SamIntrinsic]]
    Identity: Optional[HttpApiAuthLambdaAuthorizerIdentity]


class HttpApiAuth(BaseModel):
    # TODO: Docs doesn't say it's a map
    Authorizers: Optional[
        Dict[
            str,
            Union[
                HttpApiAuthOAuth2Authorizer,
                HttpApiAuthLambdaAuthorizer,
            ],
        ]
    ]
    DefaultAuthorizer: Optional[str]
    EnableIamAuthorizer: Optional[bool]


class HttpApiCorsConfiguration(BaseModel):
    AllowCredentials: Optional[bool]
    AllowHeaders: Optional[List[str]]
    AllowMethods: Optional[List[str]]
    AllowOrigins: Optional[List[str]]
    ExposeHeaders: Optional[List[str]]
    MaxAge: Optional[int]


class HttpApiDefinitionUri(BaseModel):
    Bucket: str
    Key: str
    Version: Optional[str]


class HttpApiDomainRoute53(BaseModel):
    DistributionDomainName: Optional[PassThrough]
    EvaluateTargetHealth: Optional[PassThrough]
    HostedZoneId: Optional[PassThrough]
    HostedZoneName: Optional[PassThrough]
    IpV6: Optional[bool]


class HttpApiDomain(BaseModel):
    BasePath: Optional[List[str]]
    CertificateArn: PassThrough
    DomainName: PassThrough
    EndpointConfiguration: Optional[Union[Literal["REGIONAL"], SamIntrinsic]]
    MutualTlsAuthentication: Optional[PassThrough]
    OwnershipVerificationCertificateArn: Optional[PassThrough]
    Route53: Optional[HttpApiDomainRoute53]
    SecurityPolicy: Optional[PassThrough]


class HttpApiProperties(BaseModel):
    AccessLogSettings: Optional[PassThrough]
    Auth: Optional[HttpApiAuth]
    # TODO: Also string like in the docs?
    CorsConfiguration: Optional[Union[SamIntrinsic, HttpApiCorsConfiguration]]
    DefaultRouteSettings: Optional[PassThrough]
    DefinitionBody: Optional[Dict[str, Any]]
    DefinitionUri: Optional[Union[str, HttpApiDefinitionUri]]
    Description: Optional[str]
    DisableExecuteApiEndpoint: Optional[PassThrough]
    Domain: Optional[HttpApiDomain]
    FailOnWarnings: Optional[PassThrough]
    RouteSettings: Optional[PassThrough]
    StageName: Optional[PassThrough]
    StageVariables: Optional[PassThrough]
    Tags: Optional[Dict[str, Any]]
    Name: Optional[PassThrough]  # TODO: Add to docs


class AwsServerlessHttpApi(BaseModel):
    Type: Literal["AWS::Serverless::HttpApi"]
    Properties: Optional[HttpApiProperties]
    Metadata: Optional[PassThrough]
    Condition: Optional[PassThrough]


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
