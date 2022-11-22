from typing import Optional, Any, Dict, Union, List

from typing_extensions import Literal

from samtranslator.schema.common import PassThrough, BaseModel, SamIntrinsic, Unknown


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
    Bucket: Union[str, SamIntrinsic]
    Key: Union[str, SamIntrinsic]
    Version: Optional[Union[str, SamIntrinsic]]


class Hooks(BaseModel):
    PostTraffic: Optional[Union[str, SamIntrinsic]]
    PreTraffic: Optional[Union[str, SamIntrinsic]]


class DeploymentPreference(BaseModel):
    Alarms: Optional[Union[List[SamIntrinsic], SamIntrinsic]]
    Enabled: Optional[Union[bool, SamIntrinsic]]
    Hooks: Optional[Hooks]
    PassthroughCondition: Optional[Union[bool, SamIntrinsic]]
    Role: Optional[Union[str, SamIntrinsic]]
    TriggerConfigurations: Optional[PassThrough]
    Type: Optional[
        Union[str, SamIntrinsic]
    ]  # TODO: Should investigate whether this is a required field. This is a required field on documentation. However, we don't seem to use this field.


class DeadLetterQueue(BaseModel):
    TargetArn: str
    Type: Literal["SNS", "SQS"]


class EventInvokeConfig(BaseModel):
    DestinationConfig: Optional[PassThrough]
    MaximumEventAgeInSeconds: Optional[int]
    MaximumRetryAttempts: Optional[int]


class S3EventProperties(BaseModel):
    Bucket: Union[str, SamIntrinsic]
    Events: PassThrough
    Filter: Optional[PassThrough]


class S3Event(BaseModel):
    Properties: S3EventProperties
    Type: Literal["S3"]


class SqsSubscription(BaseModel):
    BatchSize: Optional[Union[str, SamIntrinsic]]
    Enabled: Optional[bool]
    QueueArn: Union[str, SamIntrinsic]
    QueuePolicyLogicalId: Optional[str]
    QueueUrl: Union[str, SamIntrinsic]


class SNSEventProperties(BaseModel):
    FilterPolicy: Optional[PassThrough]
    Region: Optional[PassThrough]
    SqsSubscription: Optional[Union[bool, SqsSubscription]]
    Topic: PassThrough


class SNSEvent(BaseModel):
    Properties: SNSEventProperties
    Type: Literal["SNS"]


class FunctionUrlConfig(BaseModel):
    AuthType: Union[str, SamIntrinsic]
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
    InvokeRole: Optional[Union[str, SamIntrinsic]]
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
    RestApiId: Optional[Union[str, SamIntrinsic]]


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


class EventBridgeRuleEventProperties(BaseModel):
    DeadLetterConfig: Optional[DeadLetterConfig]
    EventBusName: Optional[PassThrough]
    Input: Optional[PassThrough]
    InputPath: Optional[PassThrough]
    Pattern: PassThrough
    RetryPolicy: Optional[PassThrough]
    Target: Optional[PassThrough]


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
    UserPool: Union[str, SamIntrinsic]


class CognitoEvent(BaseModel):
    Type: Literal["Cognito"]
    Properties: CognitoEventProperties


class HttpApiAuth(BaseModel):
    AuthorizationScopes: Optional[List[str]]
    Authorizer: Optional[str]


class HttpApiEventProperties(BaseModel):
    ApiId: Optional[Union[str, SamIntrinsic]]
    Auth: Optional[HttpApiAuth]
    Method: Optional[str]
    Path: Optional[str]
    PayloadFormatVersion: Optional[Union[str, SamIntrinsic]]
    RouteSettings: Optional[PassThrough]
    TimeoutInMillis: Optional[Union[int, SamIntrinsic]]


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
    KafkaBootstrapServers: Optional[List[Union[str, SamIntrinsic]]]
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


class Properties(BaseModel):
    Architectures: Optional[PassThrough]
    AssumeRolePolicyDocument: Optional[Dict[str, Any]]
    AutoPublishAlias: Optional[Union[str, SamIntrinsic]]
    AutoPublishCodeSha256: Optional[Union[str, SamIntrinsic]]
    CodeSigningConfigArn: Optional[Union[str, SamIntrinsic]]
    CodeUri: Optional[Union[str, CodeUri]]
    DeadLetterQueue: Optional[Union[SamIntrinsic, DeadLetterQueue]]
    DeploymentPreference: Optional[DeploymentPreference]
    Description: Optional[PassThrough]
    Environment: Optional[PassThrough]
    EphemeralStorage: Optional[PassThrough]
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


class Globals(BaseModel):
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


class Resource(BaseModel):
    Type: Literal["AWS::Serverless::Function"]
    Properties: Optional[Properties]
    DeletionPolicy: Optional[PassThrough]
    UpdateReplacePolicy: Optional[PassThrough]
    Condition: Optional[PassThrough]
    DependsOn: Optional[PassThrough]
    Metadata: Optional[PassThrough]
