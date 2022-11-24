from __future__ import annotations

from typing import Optional, Any, Dict, Union, List

from typing_extensions import Literal

from samtranslator.schema.common import PassThrough, BaseModel, SamIntrinsicable, get_docs_prop


def resourcepolicy(name: str) -> Any:
    return get_docs_prop("sam-property-api-resourcepolicystatement", name)


class ResourcePolicy(BaseModel):
    AwsAccountBlacklist: Optional[List[Union[str, Dict[str, Any]]]] = resourcepolicy("AwsAccountBlacklist")
    AwsAccountWhitelist: Optional[List[Union[str, Dict[str, Any]]]] = resourcepolicy("AwsAccountWhitelist")
    CustomStatements: Optional[List[Union[str, Dict[str, Any]]]] = resourcepolicy("CustomStatements")
    IntrinsicVpcBlacklist: Optional[List[Union[str, Dict[str, Any]]]] = resourcepolicy("IntrinsicVpcBlacklist")
    IntrinsicVpcWhitelist: Optional[List[Union[str, Dict[str, Any]]]] = resourcepolicy("IntrinsicVpcWhitelist")
    IntrinsicVpceBlacklist: Optional[List[Union[str, Dict[str, Any]]]] = resourcepolicy("IntrinsicVpceBlacklist")
    IntrinsicVpceWhitelist: Optional[List[Union[str, Dict[str, Any]]]] = resourcepolicy("IntrinsicVpceWhitelist")
    IpRangeBlacklist: Optional[List[Union[str, Dict[str, Any]]]] = resourcepolicy("IpRangeBlacklist")
    IpRangeWhitelist: Optional[List[Union[str, Dict[str, Any]]]] = resourcepolicy("IpRangeWhitelist")
    SourceVpcBlacklist: Optional[List[Union[str, Dict[str, Any]]]] = resourcepolicy("SourceVpcBlacklist")
    SourceVpcWhitelist: Optional[List[Union[str, Dict[str, Any]]]] = resourcepolicy("SourceVpcWhitelist")


def codeuri(name: str) -> Any:
    return get_docs_prop("sam-property-function-functioncode", name)


class CodeUri(BaseModel):
    Bucket: SamIntrinsicable[str] = codeuri("Bucket")
    Key: SamIntrinsicable[str] = codeuri("Key")
    Version: Optional[SamIntrinsicable[str]] = codeuri("Version")


def hooks(name: str) -> Any:
    return get_docs_prop("sam-property-function-hooks", name)


class Hooks(BaseModel):
    PostTraffic: Optional[SamIntrinsicable[str]] = hooks("PostTraffic")
    PreTraffic: Optional[SamIntrinsicable[str]] = hooks("PreTraffic")


def deploymentpreference(name: str) -> Any:
    return get_docs_prop("sam-property-function-deploymentpreference", name)


class DeploymentPreference(BaseModel):
    Alarms: Optional[SamIntrinsicable[List[Dict[str, Any]]]] = deploymentpreference("Alarms")
    Enabled: Optional[SamIntrinsicable[bool]] = deploymentpreference("Enabled")
    Hooks: Optional[Hooks] = deploymentpreference("Hooks")
    PassthroughCondition: Optional[SamIntrinsicable[bool]] = deploymentpreference("PassthroughCondition")
    Role: Optional[SamIntrinsicable[str]] = deploymentpreference("Role")
    TriggerConfigurations: Optional[PassThrough] = deploymentpreference("TriggerConfigurations")
    Type: Optional[SamIntrinsicable[str]] = deploymentpreference(
        "Type"
    )  # TODO: Should investigate whether this is a required field. This is a required field on documentation. However, we don't seem to use this field.


def dlq(name: str) -> Any:
    return get_docs_prop("sam-property-function-deadletterqueue", name)


class DeadLetterQueue(BaseModel):
    TargetArn: str = dlq("TargetArn")
    Type: Literal["SNS", "SQS"] = dlq("Type")


def eventinvokeonfailure(name: str) -> Any:
    return get_docs_prop("sam-property-function-onfailure", name)


class EventInvokeOnFailure(BaseModel):
    Destination: Optional[SamIntrinsicable[str]] = eventinvokeonfailure("Destination")
    Type: Optional[Literal["SQS", "SNS", "Lambda", "EventBridge"]] = eventinvokeonfailure("Type")


def eventinvokeonsuccess(name: str) -> Any:
    return get_docs_prop("sam-property-function-onsuccess", name)


class EventInvokeOnSuccess(BaseModel):
    Destination: Optional[SamIntrinsicable[str]] = eventinvokeonsuccess("Destination")
    Type: Optional[Literal["SQS", "SNS", "Lambda", "EventBridge"]] = eventinvokeonsuccess("Type")


def eventinvokedestinationconfig(name: str) -> Any:
    return get_docs_prop("sam-property-function-eventinvokedestinationconfiguration", name)


class EventInvokeDestinationConfig(BaseModel):
    OnFailure: Optional[EventInvokeOnFailure] = eventinvokedestinationconfig("OnFailure")
    OnSuccess: Optional[EventInvokeOnSuccess] = eventinvokedestinationconfig("OnSuccess")


def eventinvokeconfig(name: str) -> Any:
    return get_docs_prop("sam-property-function-eventinvokeconfiguration", name)


class EventInvokeConfig(BaseModel):
    DestinationConfig: Optional[EventInvokeDestinationConfig] = eventinvokeconfig("DestinationConfig")
    MaximumEventAgeInSeconds: Optional[int] = eventinvokeconfig("MaximumEventAgeInSeconds")
    MaximumRetryAttempts: Optional[int] = eventinvokeconfig("MaximumRetryAttempts")


def s3eventproperties(name: str) -> Any:
    return get_docs_prop("sam-property-function-s3", name)


class S3EventProperties(BaseModel):
    Bucket: SamIntrinsicable[str] = s3eventproperties("Bucket")
    Events: PassThrough = s3eventproperties("Events")
    Filter: Optional[PassThrough] = s3eventproperties("Filter")


class S3Event(BaseModel):
    Properties: S3EventProperties
    Type: Literal["S3"]


def sqssubscription(name: str) -> Any:
    return get_docs_prop("sam-property-function-sqssubscriptionobject", name)


class SqsSubscription(BaseModel):
    BatchSize: Optional[SamIntrinsicable[str]] = sqssubscription("BatchSize")
    Enabled: Optional[bool] = sqssubscription("Enabled")
    QueueArn: SamIntrinsicable[str] = sqssubscription("QueueArn")
    QueuePolicyLogicalId: Optional[str] = sqssubscription("QueuePolicyLogicalId")
    QueueUrl: SamIntrinsicable[str] = sqssubscription("QueueUrl")


def snseventproperties(name: str) -> Any:
    return get_docs_prop("sam-property-function-sns", name)


class SNSEventProperties(BaseModel):
    FilterPolicy: Optional[PassThrough] = snseventproperties("FilterPolicy")
    Region: Optional[PassThrough] = snseventproperties("Region")
    SqsSubscription: Optional[Union[bool, SqsSubscription]] = snseventproperties("SqsSubscription")
    Topic: PassThrough = snseventproperties("Topic")


class SNSEvent(BaseModel):
    Properties: SNSEventProperties
    Type: Literal["SNS"]


def functionurlconfig(name: str) -> Any:
    return get_docs_prop("sam-property-function-functionurlconfig", name)


class FunctionUrlConfig(BaseModel):
    AuthType: SamIntrinsicable[str] = functionurlconfig("AuthType")
    Cors: Optional[PassThrough] = functionurlconfig("Cors")


def kinesiseventproperties(name: str) -> Any:
    return get_docs_prop("sam-property-function-kinesis", name)


class KinesisEventProperties(BaseModel):
    BatchSize: Optional[PassThrough] = kinesiseventproperties("BatchSize")
    BisectBatchOnFunctionError: Optional[PassThrough] = kinesiseventproperties("BisectBatchOnFunctionError")
    DestinationConfig: Optional[PassThrough] = kinesiseventproperties("DestinationConfig")
    Enabled: Optional[PassThrough] = kinesiseventproperties("Enabled")
    FilterCriteria: Optional[PassThrough] = kinesiseventproperties("FilterCriteria")
    FunctionResponseTypes: Optional[PassThrough] = kinesiseventproperties("FunctionResponseTypes")
    MaximumBatchingWindowInSeconds: Optional[PassThrough] = kinesiseventproperties("MaximumBatchingWindowInSeconds")
    MaximumRecordAgeInSeconds: Optional[PassThrough] = kinesiseventproperties("MaximumRecordAgeInSeconds")
    MaximumRetryAttempts: Optional[PassThrough] = kinesiseventproperties("MaximumRetryAttempts")
    ParallelizationFactor: Optional[PassThrough] = kinesiseventproperties("ParallelizationFactor")
    StartingPosition: PassThrough = kinesiseventproperties("StartingPosition")
    Stream: PassThrough = kinesiseventproperties("Stream")
    TumblingWindowInSeconds: Optional[PassThrough] = kinesiseventproperties("TumblingWindowInSeconds")


class KinesisEvent(BaseModel):
    Type: Literal["Kinesis"]
    Properties: KinesisEventProperties


def dynamodbeventproperties(name: str) -> Any:
    return get_docs_prop("sam-property-function-dynamodb", name)


class DynamoDBEventProperties(BaseModel):
    BatchSize: Optional[PassThrough] = dynamodbeventproperties("BatchSize")
    BisectBatchOnFunctionError: Optional[PassThrough] = dynamodbeventproperties("BisectBatchOnFunctionError")
    DestinationConfig: Optional[PassThrough] = dynamodbeventproperties("DestinationConfig")
    Enabled: Optional[PassThrough] = dynamodbeventproperties("Enabled")
    FilterCriteria: Optional[PassThrough] = dynamodbeventproperties("FilterCriteria")
    FunctionResponseTypes: Optional[PassThrough] = dynamodbeventproperties("FunctionResponseTypes")
    MaximumBatchingWindowInSeconds: Optional[PassThrough] = dynamodbeventproperties("MaximumBatchingWindowInSeconds")
    MaximumRecordAgeInSeconds: Optional[PassThrough] = dynamodbeventproperties("MaximumRecordAgeInSeconds")
    MaximumRetryAttempts: Optional[PassThrough] = dynamodbeventproperties("MaximumRetryAttempts")
    ParallelizationFactor: Optional[PassThrough] = dynamodbeventproperties("ParallelizationFactor")
    StartingPosition: PassThrough = dynamodbeventproperties("StartingPosition")
    Stream: PassThrough = dynamodbeventproperties("Stream")
    TumblingWindowInSeconds: Optional[PassThrough] = dynamodbeventproperties("TumblingWindowInSeconds")


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


def apieventproperties(name: str) -> Any:
    return get_docs_prop("sam-property-function-api", name)


class ApiEventProperties(BaseModel):
    Auth: Optional[ApiAuth] = apieventproperties("Auth")
    Method: str = apieventproperties("Method")
    Path: str = apieventproperties("Path")
    RequestModel: Optional[RequestModel] = apieventproperties("RequestModel")
    RequestParameters: Optional[Union[str, RequestParameters]] = apieventproperties("RequestParameters")
    RestApiId: Optional[SamIntrinsicable[str]] = apieventproperties("RestApiId")


class ApiEvent(BaseModel):
    Type: Literal["Api"]
    Properties: ApiEventProperties


def cloudwatcheventproperties(name: str) -> Any:
    return get_docs_prop("sam-property-function-cloudwatchevent", name)


class CloudWatchEventProperties(BaseModel):
    Enabled: Optional[bool]  # TODO: Add to docs
    EventBusName: Optional[PassThrough] = cloudwatcheventproperties("EventBusName")
    Input: Optional[PassThrough] = cloudwatcheventproperties("Input")
    InputPath: Optional[PassThrough] = cloudwatcheventproperties("InputPath")
    Pattern: Optional[PassThrough] = cloudwatcheventproperties("Pattern")
    State: Optional[PassThrough]  # TODO: Add to docs


class CloudWatchEvent(BaseModel):
    Type: Literal["CloudWatchEvent"]
    Properties: CloudWatchEventProperties


def deadletterconfig(name: str) -> Any:
    return get_docs_prop("sam-property-function-deadletterconfig", name)


class DeadLetterConfig(BaseModel):
    Arn: Optional[PassThrough] = deadletterconfig("Arn")
    QueueLogicalId: Optional[str] = deadletterconfig("QueueLogicalId")
    Type: Optional[Literal["SQS"]] = deadletterconfig("Type")


def eventsscheduleproperties(name: str) -> Any:
    return get_docs_prop("sam-property-function-schedule", name)


class EventsScheduleProperties(BaseModel):
    DeadLetterConfig: Optional[DeadLetterConfig] = eventsscheduleproperties("DeadLetterConfig")
    Description: Optional[PassThrough] = eventsscheduleproperties("Description")
    Enabled: Optional[bool] = eventsscheduleproperties("Enabled")
    Input: Optional[PassThrough] = eventsscheduleproperties("Input")
    Name: Optional[PassThrough] = eventsscheduleproperties("Name")
    RetryPolicy: Optional[PassThrough] = eventsscheduleproperties("RetryPolicy")
    Schedule: Optional[PassThrough] = eventsscheduleproperties("Schedule")
    State: Optional[PassThrough]  # TODO: Add to docs


class ScheduleEvent(BaseModel):
    Type: Literal["Schedule"]
    Properties: EventsScheduleProperties


class EventBridgeRuleTarget(BaseModel):
    Id: PassThrough


def eventbridgeruleeventproperties(name: str) -> Any:
    return get_docs_prop("sam-property-function-eventbridgerule", name)


class EventBridgeRuleEventProperties(BaseModel):
    DeadLetterConfig: Optional[DeadLetterConfig] = eventbridgeruleeventproperties("DeadLetterConfig")
    EventBusName: Optional[PassThrough] = eventbridgeruleeventproperties("EventBusName")
    Input: Optional[PassThrough] = eventbridgeruleeventproperties("Input")
    InputPath: Optional[PassThrough] = eventbridgeruleeventproperties("InputPath")
    Pattern: PassThrough = eventbridgeruleeventproperties("Pattern")
    RetryPolicy: Optional[PassThrough] = eventbridgeruleeventproperties("RetryPolicy")
    Target: Optional[EventBridgeRuleTarget] = eventbridgeruleeventproperties("Target")


class EventBridgeRuleEvent(BaseModel):
    Type: Literal["EventBridgeRule"]
    Properties: EventBridgeRuleEventProperties


class CloudWatchLogsEventProperties(BaseModel):
    FilterPattern: PassThrough
    LogGroupName: PassThrough


class CloudWatchLogsEvent(BaseModel):
    Type: Literal["CloudWatchLogs"]
    Properties: CloudWatchLogsEventProperties


def iotruleeventproperties(name: str) -> Any:
    return get_docs_prop("sam-property-function-iotrule", name)


class IoTRuleEventProperties(BaseModel):
    AwsIotSqlVersion: Optional[PassThrough] = iotruleeventproperties("AwsIotSqlVersion")
    Sql: PassThrough = iotruleeventproperties("Sql")


class IoTRuleEvent(BaseModel):
    Type: Literal["IoTRule"]
    Properties: IoTRuleEventProperties


def alexaskilleventproperties(name: str) -> Any:
    return get_docs_prop("sam-property-function-alexaskill", name)


class AlexaSkillEventProperties(BaseModel):
    SkillId: Optional[str] = alexaskilleventproperties("SkillId")


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


def mqeventproperties(name: str) -> Any:
    return get_docs_prop("sam-property-function-mq", name)


class MQEventProperties(BaseModel):
    BatchSize: Optional[PassThrough] = mqeventproperties("BatchSize")
    Broker: PassThrough = mqeventproperties("Broker")
    Enabled: Optional[PassThrough] = mqeventproperties("Enabled")
    FilterCriteria: Optional[PassThrough]  # TODO: Add to docs
    MaximumBatchingWindowInSeconds: Optional[PassThrough] = mqeventproperties("MaximumBatchingWindowInSeconds")
    Queues: PassThrough = mqeventproperties("Queues")
    SecretsManagerKmsKeyId: Optional[str] = mqeventproperties("SecretsManagerKmsKeyId")
    SourceAccessConfigurations: PassThrough = mqeventproperties("SourceAccessConfigurations")


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


def prop(name: str) -> Any:
    return get_docs_prop("sam-resource-function", name)


class Properties(BaseModel):
    Architectures: Optional[Architectures] = prop("Architectures")
    AssumeRolePolicyDocument: Optional[AssumeRolePolicyDocument] = prop("AssumeRolePolicyDocument")
    AutoPublishAlias: Optional[AutoPublishAlias] = prop("AutoPublishAlias")
    AutoPublishCodeSha256: Optional[SamIntrinsicable[str]] = prop("AutoPublishCodeSha256")
    CodeSigningConfigArn: Optional[SamIntrinsicable[str]] = prop("CodeSigningConfigArn")
    CodeUri: Optional[CodeUriType] = prop("CodeUri")
    DeadLetterQueue: Optional[DeadLetterQueueType] = prop("DeadLetterQueue")
    DeploymentPreference: Optional[DeploymentPreference] = prop("DeploymentPreference")
    Description: Optional[Description] = prop("Description")
    Environment: Optional[Environment] = prop("Environment")
    EphemeralStorage: Optional[EphemeralStorage] = prop("EphemeralStorage")
    EventInvokeConfig: Optional[EventInvokeConfig] = prop("EventInvokeConfig")
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
    ] = prop("Events")
    FileSystemConfigs: Optional[PassThrough] = prop("FileSystemConfigs")
    FunctionName: Optional[PassThrough] = prop("FunctionName")
    FunctionUrlConfig: Optional[FunctionUrlConfig] = prop("FunctionUrlConfig")
    Handler: Optional[Handler] = prop("Handler")
    ImageConfig: Optional[PassThrough] = prop("ImageConfig")
    ImageUri: Optional[PassThrough] = prop("ImageUri")
    InlineCode: Optional[PassThrough] = prop("InlineCode")
    KmsKeyArn: Optional[KmsKeyArn] = prop("KmsKeyArn")
    Layers: Optional[Layers] = prop("Layers")
    MemorySize: Optional[MemorySize] = prop("MemorySize")
    PackageType: Optional[PassThrough] = prop("PackageType")
    PermissionsBoundary: Optional[PermissionsBoundary] = prop("PermissionsBoundary")
    Policies: Optional[SamIntrinsicable[Union[str, List[SamIntrinsicable[str]]]]] = prop("Policies")
    ProvisionedConcurrencyConfig: Optional[ProvisionedConcurrencyConfig] = prop("ProvisionedConcurrencyConfig")
    ReservedConcurrentExecutions: Optional[ReservedConcurrentExecutions] = prop("ReservedConcurrentExecutions")
    Role: Optional[SamIntrinsicable[str]] = prop("Role")
    Runtime: Optional[Runtime] = prop("Runtime")
    Tags: Optional[Tags] = prop("Tags")
    Timeout: Optional[Timeout] = prop("Timeout")
    Tracing: Optional[Tracing] = prop("Timeout")
    VersionDescription: Optional[PassThrough] = prop("VersionDescription")
    VpcConfig: Optional[VpcConfig] = prop("VpcConfig")


class Globals(BaseModel):
    Handler: Optional[Handler] = prop("Handler")
    Runtime: Optional[Runtime] = prop("Runtime")
    CodeUri: Optional[CodeUriType] = prop("CodeUri")
    DeadLetterQueue: Optional[DeadLetterQueueType] = prop("DeadLetterQueue")
    Description: Optional[Description] = prop("Description")
    MemorySize: Optional[MemorySize] = prop("MemorySize")
    Timeout: Optional[Timeout] = prop("Timeout")
    VpcConfig: Optional[VpcConfig] = prop("VpcConfig")
    Environment: Optional[Environment] = prop("Environment")
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
