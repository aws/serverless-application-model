from typing import Optional, Any, Dict, Union, List

from typing_extensions import Literal

from samtranslator.schema.common import PassThrough, BaseModel, SamIntrinsicable, get_docs_prop


def prop(field: str) -> Any:
    return get_docs_prop("AWS::Serverless::Function.Properties." + field)


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


class CodeUri(BaseModel):
    Bucket: SamIntrinsicable[str]
    Key: SamIntrinsicable[str]
    Version: Optional[SamIntrinsicable[str]]


class Hooks(BaseModel):
    PostTraffic: Optional[SamIntrinsicable[str]]
    PreTraffic: Optional[SamIntrinsicable[str]]


class DeploymentPreference(BaseModel):
    Alarms: Optional[SamIntrinsicable[List[Dict[str, Any]]]]
    Enabled: Optional[SamIntrinsicable[bool]]
    Hooks: Optional[Hooks]
    PassthroughCondition: Optional[SamIntrinsicable[bool]]
    Role: Optional[SamIntrinsicable[str]]
    TriggerConfigurations: Optional[PassThrough]
    Type: Optional[
        SamIntrinsicable[str]
    ]  # TODO: Should investigate whether this is a required field. This is a required field on documentation. However, we don't seem to use this field.


class DeadLetterQueue(BaseModel):
    TargetArn: str
    Type: Literal["SNS", "SQS"]


class EventInvokeOnFailure(BaseModel):
    Destination: Optional[SamIntrinsicable[str]]
    Type: Optional[Literal["SQS", "SNS", "Lambda", "EventBridge"]]


class EventInvokeOnSuccess(BaseModel):
    Destination: Optional[SamIntrinsicable[str]]
    Type: Optional[Literal["SQS", "SNS", "Lambda", "EventBridge"]]


class EventInvokeDestinationConfig(BaseModel):
    OnFailure: Optional[EventInvokeOnFailure]
    OnSuccess: Optional[EventInvokeOnSuccess]


class EventInvokeConfig(BaseModel):
    DestinationConfig: Optional[EventInvokeDestinationConfig]
    MaximumEventAgeInSeconds: Optional[int]
    MaximumRetryAttempts: Optional[int]


class S3EventProperties(BaseModel):
    Bucket: SamIntrinsicable[str]
    Events: PassThrough
    Filter: Optional[PassThrough]


class S3Event(BaseModel):
    Properties: S3EventProperties
    Type: Literal["S3"]


class SqsSubscription(BaseModel):
    BatchSize: Optional[SamIntrinsicable[str]]
    Enabled: Optional[bool]
    QueueArn: SamIntrinsicable[str]
    QueuePolicyLogicalId: Optional[str]
    QueueUrl: SamIntrinsicable[str]


class SNSEventProperties(BaseModel):
    FilterPolicy: Optional[PassThrough]
    Region: Optional[PassThrough]
    SqsSubscription: Optional[Union[bool, SqsSubscription]]
    Topic: PassThrough


class SNSEvent(BaseModel):
    Properties: SNSEventProperties
    Type: Literal["SNS"]


class FunctionUrlConfig(BaseModel):
    AuthType: SamIntrinsicable[str]
    Cors: Optional[PassThrough]


class KinesisEventProperties(BaseModel):
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


class KinesisEvent(BaseModel):
    Type: Literal["Kinesis"]
    Properties: KinesisEventProperties


class DynamoDBEventProperties(BaseModel):
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


class DynamoDBEvent(BaseModel):
    Type: Literal["DynamoDB"]
    Properties: DynamoDBEventProperties


class SQSEventProperties(BaseModel):
    BatchSize: Optional[PassThrough]
    Enabled: Optional[PassThrough]
    FilterCriteria: Optional[PassThrough]
    MaximumBatchingWindowInSeconds: Optional[PassThrough]
    Queue: PassThrough


class SQSEvent(BaseModel):
    Type: Literal["SQS"]
    Properties: SQSEventProperties


class ApiAuth(BaseModel):
    ApiKeyRequired: Optional[bool]
    AuthorizationScopes: Optional[List[str]]
    Authorizer: Optional[str]
    InvokeRole: Optional[SamIntrinsicable[str]]
    ResourcePolicy: Optional[ResourcePolicy]


class RequestModel(BaseModel):
    Model: str
    Required: Optional[bool]
    ValidateBody: Optional[bool]
    ValidateParameters: Optional[bool]


class RequestParameters(BaseModel):
    Caching: Optional[bool]
    Required: Optional[bool]


class ApiEventProperties(BaseModel):
    Auth: Optional[ApiAuth]
    Method: str
    Path: str
    RequestModel: Optional[RequestModel]
    RequestParameters: Optional[Union[str, RequestParameters]]
    RestApiId: Optional[SamIntrinsicable[str]]


class ApiEvent(BaseModel):
    Type: Literal["Api"]
    Properties: ApiEventProperties


class CloudWatchEventProperties(BaseModel):
    Enabled: Optional[bool]
    EventBusName: Optional[PassThrough]
    Input: Optional[PassThrough]
    InputPath: Optional[PassThrough]
    Pattern: Optional[PassThrough]
    State: Optional[PassThrough]


class CloudWatchEvent(BaseModel):
    Type: Literal["CloudWatchEvent"]
    Properties: CloudWatchEventProperties


class DeadLetterConfig(BaseModel):
    Arn: Optional[PassThrough]
    QueueLogicalId: Optional[str]
    Type: Optional[Literal["SQS"]]


class EventsScheduleProperties(BaseModel):
    DeadLetterConfig: Optional[DeadLetterConfig]
    Description: Optional[PassThrough]
    Enabled: Optional[bool]
    Input: Optional[PassThrough]
    Name: Optional[PassThrough]
    RetryPolicy: Optional[PassThrough]
    Schedule: Optional[PassThrough]
    State: Optional[PassThrough]


class ScheduleEvent(BaseModel):
    Type: Literal["Schedule"]
    Properties: EventsScheduleProperties


class EventBridgeRuleTarget(BaseModel):
    Id: PassThrough


class EventBridgeRuleEventProperties(BaseModel):
    DeadLetterConfig: Optional[DeadLetterConfig]
    EventBusName: Optional[PassThrough]
    Input: Optional[PassThrough]
    InputPath: Optional[PassThrough]
    Pattern: PassThrough
    RetryPolicy: Optional[PassThrough]
    Target: Optional[EventBridgeRuleTarget]


class EventBridgeRuleEvent(BaseModel):
    Type: Literal["EventBridgeRule"]
    Properties: EventBridgeRuleEventProperties


class CloudWatchLogsEventProperties(BaseModel):
    FilterPattern: PassThrough
    LogGroupName: PassThrough


class CloudWatchLogsEvent(BaseModel):
    Type: Literal["CloudWatchLogs"]
    Properties: CloudWatchLogsEventProperties


class IoTRuleEventProperties(BaseModel):
    AwsIotSqlVersion: Optional[PassThrough]
    Sql: PassThrough


class IoTRuleEvent(BaseModel):
    Type: Literal["IoTRule"]
    Properties: IoTRuleEventProperties


class AlexaSkillEventProperties(BaseModel):
    SkillId: Optional[str]


class AlexaSkillEvent(BaseModel):
    Type: Literal["AlexaSkill"]
    Properties: Optional[AlexaSkillEventProperties]


class CognitoEventProperties(BaseModel):
    Trigger: PassThrough
    UserPool: SamIntrinsicable[str]


class CognitoEvent(BaseModel):
    Type: Literal["Cognito"]
    Properties: CognitoEventProperties


class HttpApiAuth(BaseModel):
    AuthorizationScopes: Optional[List[str]]
    Authorizer: Optional[str]


class HttpApiEventProperties(BaseModel):
    ApiId: Optional[SamIntrinsicable[str]]
    Auth: Optional[HttpApiAuth]
    Method: Optional[str]
    Path: Optional[str]
    PayloadFormatVersion: Optional[SamIntrinsicable[str]]
    RouteSettings: Optional[PassThrough]
    TimeoutInMillis: Optional[SamIntrinsicable[int]]


class HttpApiEvent(BaseModel):
    Type: Literal["HttpApi"]
    Properties: Optional[HttpApiEventProperties]


class MSKEventProperties(BaseModel):
    ConsumerGroupId: Optional[PassThrough]
    FilterCriteria: Optional[PassThrough]
    MaximumBatchingWindowInSeconds: Optional[PassThrough]
    StartingPosition: PassThrough
    Stream: PassThrough
    Topics: PassThrough


class MSKEvent(BaseModel):
    Type: Literal["MSK"]
    Properties: MSKEventProperties


class MQEventProperties(BaseModel):
    BatchSize: Optional[PassThrough]
    Broker: PassThrough
    Enabled: Optional[PassThrough]
    FilterCriteria: Optional[PassThrough]
    MaximumBatchingWindowInSeconds: Optional[PassThrough]
    Queues: PassThrough
    SecretsManagerKmsKeyId: Optional[str]
    SourceAccessConfigurations: PassThrough


class MQEvent(BaseModel):
    Type: Literal["MQ"]
    Properties: MQEventProperties


class SelfManagedKafkaEventProperties(BaseModel):
    BatchSize: Optional[PassThrough]
    ConsumerGroupId: Optional[PassThrough]
    Enabled: Optional[PassThrough]
    FilterCriteria: Optional[PassThrough]
    KafkaBootstrapServers: Optional[List[SamIntrinsicable[str]]]
    SourceAccessConfigurations: PassThrough
    Topics: PassThrough


class SelfManagedKafkaEvent(BaseModel):
    Type: Literal["SelfManagedKafka"]
    Properties: SelfManagedKafkaEventProperties


# TODO: Same as ScheduleV2EventProperties in state machine?
class ScheduleV2EventProperties(BaseModel):
    # pylint: disable=duplicate-code
    DeadLetterConfig: Optional[DeadLetterConfig]
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


class ScheduleV2Event(BaseModel):
    Type: Literal["ScheduleV2"]
    Properties: ScheduleV2EventProperties


Handler = Optional[PassThrough]
Runtime = Optional[PassThrough]
CodeUriType = Optional[Union[str, CodeUri]]
DeadLetterQueueType = Optional[SamIntrinsicable[DeadLetterQueue]]
Description = Optional[PassThrough]
MemorySize = Optional[PassThrough]
Timeout = Optional[PassThrough]
VpcConfig = Optional[PassThrough]
Environment = Optional[PassThrough]
Tags = Optional[Dict[str, Any]]
Tracing = Optional[SamIntrinsicable[Literal["Active", "PassThrough"]]]
KmsKeyArn = Optional[PassThrough]
Layers = Optional[PassThrough]
AutoPublishAlias = Optional[SamIntrinsicable[str]]
PermissionsBoundary = Optional[PassThrough]
ReservedConcurrentExecutions = Optional[PassThrough]
ProvisionedConcurrencyConfig = Optional[PassThrough]
AssumeRolePolicyDocument = Optional[Dict[str, Any]]
Architectures = Optional[PassThrough]
EphemeralStorage = Optional[PassThrough]


class Properties(BaseModel):
    Architectures: Optional[Architectures]
    AssumeRolePolicyDocument: Optional[AssumeRolePolicyDocument]
    AutoPublishAlias: Optional[AutoPublishAlias]
    AutoPublishCodeSha256: Optional[SamIntrinsicable[str]]
    CodeSigningConfigArn: Optional[SamIntrinsicable[str]]
    CodeUri: Optional[CodeUriType] = prop("CodeUri")
    DeadLetterQueue: Optional[DeadLetterQueueType]
    DeploymentPreference: Optional[DeploymentPreference]
    Description: Optional[Description]
    Environment: Optional[Environment]
    EphemeralStorage: Optional[EphemeralStorage]
    EventInvokeConfig: Optional[EventInvokeConfig]
    Events: Optional[
        Dict[
            str,
            Union[
                S3Event,
                SNSEvent,
                KinesisEvent,
                DynamoDBEvent,
                SQSEvent,
                ApiEvent,
                ScheduleEvent,
                ScheduleV2Event,
                CloudWatchEvent,
                EventBridgeRuleEvent,
                CloudWatchLogsEvent,
                IoTRuleEvent,
                AlexaSkillEvent,
                CognitoEvent,
                HttpApiEvent,
                MSKEvent,
                MQEvent,
                SelfManagedKafkaEvent,
            ],
        ]
    ]
    FileSystemConfigs: Optional[PassThrough]
    FunctionName: Optional[PassThrough]
    FunctionUrlConfig: Optional[FunctionUrlConfig]
    Handler: Optional[Handler]
    ImageConfig: Optional[PassThrough]
    ImageUri: Optional[PassThrough]
    InlineCode: Optional[PassThrough] = prop("InlineCode")
    KmsKeyArn: Optional[KmsKeyArn]
    Layers: Optional[Layers]
    MemorySize: Optional[MemorySize]
    PackageType: Optional[PassThrough]
    PermissionsBoundary: Optional[PermissionsBoundary]
    Policies: Optional[SamIntrinsicable[Union[str, List[SamIntrinsicable[str]]]]]
    ProvisionedConcurrencyConfig: Optional[ProvisionedConcurrencyConfig]
    ReservedConcurrentExecutions: Optional[ReservedConcurrentExecutions]
    Role: Optional[SamIntrinsicable[str]]
    Runtime: Optional[Runtime]
    Tags: Optional[Tags]
    Timeout: Optional[Timeout]
    Tracing: Optional[Tracing]
    VersionDescription: Optional[PassThrough]
    VpcConfig: Optional[VpcConfig]


class Globals(BaseModel):
    Handler: Optional[Handler]
    Runtime: Optional[Runtime]
    CodeUri: Optional[CodeUriType]
    DeadLetterQueue: Optional[DeadLetterQueueType]
    Description: Optional[Description]
    MemorySize: Optional[MemorySize]
    Timeout: Optional[Timeout]
    VpcConfig: Optional[VpcConfig]
    Environment: Optional[Environment]
    Tags: Optional[Tags]
    Tracing: Optional[Tracing]
    KmsKeyArn: Optional[KmsKeyArn]
    Layers: Optional[Layers]
    AutoPublishAlias: Optional[AutoPublishAlias]
    DeploymentPreference: Optional[DeploymentPreference]
    PermissionsBoundary: Optional[PermissionsBoundary]
    ReservedConcurrentExecutions: Optional[ReservedConcurrentExecutions]
    ProvisionedConcurrencyConfig: Optional[ProvisionedConcurrencyConfig]
    AssumeRolePolicyDocument: Optional[AssumeRolePolicyDocument]
    EventInvokeConfig: Optional[EventInvokeConfig]
    Architectures: Optional[Architectures]
    EphemeralStorage: Optional[EphemeralStorage]


class Resource(BaseModel):
    Type: Literal["AWS::Serverless::Function"]
    Properties: Optional[Properties]
    DeletionPolicy: Optional[PassThrough]
    UpdateReplacePolicy: Optional[PassThrough]
    Condition: Optional[PassThrough]
    DependsOn: Optional[PassThrough]
    Metadata: Optional[PassThrough]
