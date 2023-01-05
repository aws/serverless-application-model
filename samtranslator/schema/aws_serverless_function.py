from __future__ import annotations

from typing import Optional, Dict, Union, List

from typing_extensions import Literal

from samtranslator.schema.common import PassThrough, BaseModel, SamIntrinsicable, get_prop, DictStrAny, Ref


alexaskilleventproperties = get_prop("sam-property-function-alexaskill")
apiauth = get_prop("sam-property-function-apifunctionauth")
apieventproperties = get_prop("sam-property-function-api")
cloudwatcheventproperties = get_prop("sam-property-function-cloudwatchevent")
cloudwatchlogseventproperties = get_prop("sam-property-function-cloudwatchlogs")
codeuri = get_prop("sam-property-function-functioncode")
cognitoeventproperties = get_prop("sam-property-function-cognito")
deadletterconfig = get_prop("sam-property-function-deadletterconfig")
deploymentpreference = get_prop("sam-property-function-deploymentpreference")
dlq = get_prop("sam-property-function-deadletterqueue")
dynamodbeventproperties = get_prop("sam-property-function-dynamodb")
event = get_prop("sam-property-function-eventsource")
eventbridgeruleeventproperties = get_prop("sam-property-function-eventbridgerule")
eventbridgeruletarget = get_prop("sam-property-function-target")
eventinvokeconfig = get_prop("sam-property-function-eventinvokeconfiguration")
eventinvokedestinationconfig = get_prop("sam-property-function-eventinvokedestinationconfiguration")
eventinvokeonfailure = get_prop("sam-property-function-onfailure")
eventinvokeonsuccess = get_prop("sam-property-function-onsuccess")
eventsscheduleproperties = get_prop("sam-property-function-schedule")
functionurlconfig = get_prop("sam-property-function-functionurlconfig")
hooks = get_prop("sam-property-function-hooks")
httpapiauth = get_prop("sam-property-function-httpapifunctionauth")
httpapieventproperties = get_prop("sam-property-function-httpapi")
iotruleeventproperties = get_prop("sam-property-function-iotrule")
kinesiseventproperties = get_prop("sam-property-function-kinesis")
mqeventproperties = get_prop("sam-property-function-mq")
mskeventproperties = get_prop("sam-property-function-msk")
prop = get_prop("sam-resource-function")
requestmodel = get_prop("sam-property-function-requestmodel")
requestparameters = get_prop("sam-property-function-requestparameter")
resourcepolicy = get_prop("sam-property-api-resourcepolicystatement")
s3eventproperties = get_prop("sam-property-function-s3")
schedulev2eventproperties = get_prop("sam-property-function-schedulev2")
selfmanagedkafkaeventproperties = get_prop("sam-property-function-selfmanagedkafka")
snseventproperties = get_prop("sam-property-function-sns")
sqseventproperties = get_prop("sam-property-function-sqs")
sqssubscription = get_prop("sam-property-function-sqssubscriptionobject")


class ResourcePolicy(BaseModel):
    AwsAccountBlacklist: Optional[List[Union[str, DictStrAny]]] = resourcepolicy("AwsAccountBlacklist")
    AwsAccountWhitelist: Optional[List[Union[str, DictStrAny]]] = resourcepolicy("AwsAccountWhitelist")
    CustomStatements: Optional[List[Union[str, DictStrAny]]] = resourcepolicy("CustomStatements")
    IntrinsicVpcBlacklist: Optional[List[Union[str, DictStrAny]]] = resourcepolicy("IntrinsicVpcBlacklist")
    IntrinsicVpcWhitelist: Optional[List[Union[str, DictStrAny]]] = resourcepolicy("IntrinsicVpcWhitelist")
    IntrinsicVpceBlacklist: Optional[List[Union[str, DictStrAny]]] = resourcepolicy("IntrinsicVpceBlacklist")
    IntrinsicVpceWhitelist: Optional[List[Union[str, DictStrAny]]] = resourcepolicy("IntrinsicVpceWhitelist")
    IpRangeBlacklist: Optional[List[Union[str, DictStrAny]]] = resourcepolicy("IpRangeBlacklist")
    IpRangeWhitelist: Optional[List[Union[str, DictStrAny]]] = resourcepolicy("IpRangeWhitelist")
    SourceVpcBlacklist: Optional[List[Union[str, DictStrAny]]] = resourcepolicy("SourceVpcBlacklist")
    SourceVpcWhitelist: Optional[List[Union[str, DictStrAny]]] = resourcepolicy("SourceVpcWhitelist")


class CodeUri(BaseModel):
    Bucket: SamIntrinsicable[str] = codeuri("Bucket")
    Key: SamIntrinsicable[str] = codeuri("Key")
    Version: Optional[SamIntrinsicable[str]] = codeuri("Version")


class Hooks(BaseModel):
    PostTraffic: Optional[SamIntrinsicable[str]] = hooks("PostTraffic")
    PreTraffic: Optional[SamIntrinsicable[str]] = hooks("PreTraffic")


class DeploymentPreference(BaseModel):
    Alarms: Optional[SamIntrinsicable[List[DictStrAny]]] = deploymentpreference("Alarms")
    Enabled: Optional[SamIntrinsicable[bool]] = deploymentpreference("Enabled")
    Hooks: Optional[Hooks] = deploymentpreference("Hooks")
    PassthroughCondition: Optional[SamIntrinsicable[bool]] = deploymentpreference("PassthroughCondition")
    Role: Optional[SamIntrinsicable[str]] = deploymentpreference("Role")
    TriggerConfigurations: Optional[PassThrough] = deploymentpreference("TriggerConfigurations")
    Type: Optional[SamIntrinsicable[str]] = deploymentpreference(
        "Type"
    )  # TODO: Should investigate whether this is a required field. This is a required field on documentation. However, we don't seem to use this field.


class DeadLetterQueue(BaseModel):
    TargetArn: str = dlq("TargetArn")
    Type: Literal["SNS", "SQS"] = dlq("Type")


class EventInvokeOnFailure(BaseModel):
    Destination: Optional[SamIntrinsicable[str]] = eventinvokeonfailure("Destination")
    Type: Optional[Literal["SQS", "SNS", "Lambda", "EventBridge"]] = eventinvokeonfailure("Type")


class EventInvokeOnSuccess(BaseModel):
    Destination: Optional[SamIntrinsicable[str]] = eventinvokeonsuccess("Destination")
    Type: Optional[Literal["SQS", "SNS", "Lambda", "EventBridge"]] = eventinvokeonsuccess("Type")


class EventInvokeDestinationConfig(BaseModel):
    OnFailure: Optional[EventInvokeOnFailure] = eventinvokedestinationconfig("OnFailure")
    OnSuccess: Optional[EventInvokeOnSuccess] = eventinvokedestinationconfig("OnSuccess")


class EventInvokeConfig(BaseModel):
    DestinationConfig: Optional[EventInvokeDestinationConfig] = eventinvokeconfig("DestinationConfig")
    MaximumEventAgeInSeconds: Optional[int] = eventinvokeconfig("MaximumEventAgeInSeconds")
    MaximumRetryAttempts: Optional[int] = eventinvokeconfig("MaximumRetryAttempts")


class S3EventProperties(BaseModel):
    Bucket: SamIntrinsicable[str] = s3eventproperties("Bucket")
    Events: PassThrough = s3eventproperties("Events")
    Filter: Optional[PassThrough] = s3eventproperties("Filter")


class S3Event(BaseModel):
    Properties: S3EventProperties = event("Properties")
    Type: Literal["S3"] = event("Type")


class SqsSubscription(BaseModel):
    BatchSize: Optional[SamIntrinsicable[str]] = sqssubscription("BatchSize")
    Enabled: Optional[bool] = sqssubscription("Enabled")
    QueueArn: SamIntrinsicable[str] = sqssubscription("QueueArn")
    QueuePolicyLogicalId: Optional[str] = sqssubscription("QueuePolicyLogicalId")
    QueueUrl: SamIntrinsicable[str] = sqssubscription("QueueUrl")


class SNSEventProperties(BaseModel):
    FilterPolicy: Optional[PassThrough] = snseventproperties("FilterPolicy")
    Region: Optional[PassThrough] = snseventproperties("Region")
    SqsSubscription: Optional[Union[bool, SqsSubscription]] = snseventproperties("SqsSubscription")
    Topic: PassThrough = snseventproperties("Topic")


class SNSEvent(BaseModel):
    Properties: SNSEventProperties = event("Properties")
    Type: Literal["SNS"] = event("Type")


class FunctionUrlConfig(BaseModel):
    AuthType: SamIntrinsicable[str] = functionurlconfig("AuthType")
    Cors: Optional[PassThrough] = functionurlconfig("Cors")


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
    Type: Literal["Kinesis"] = event("Type")
    Properties: KinesisEventProperties = event("Properties")


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
    Type: Literal["DynamoDB"] = event("Type")
    Properties: DynamoDBEventProperties = event("Properties")


class SQSEventProperties(BaseModel):
    BatchSize: Optional[PassThrough] = sqseventproperties("BatchSize")
    Enabled: Optional[PassThrough] = sqseventproperties("Enabled")
    FilterCriteria: Optional[PassThrough] = sqseventproperties("FilterCriteria")
    MaximumBatchingWindowInSeconds: Optional[PassThrough] = sqseventproperties("MaximumBatchingWindowInSeconds")
    Queue: PassThrough = sqseventproperties("Queue")


class SQSEvent(BaseModel):
    Type: Literal["SQS"] = event("Type")
    Properties: SQSEventProperties = event("Properties")


class ApiAuth(BaseModel):
    ApiKeyRequired: Optional[bool] = apiauth("ApiKeyRequired")
    AuthorizationScopes: Optional[List[str]] = apiauth("AuthorizationScopes")
    Authorizer: Optional[str] = apiauth("Authorizer")
    InvokeRole: Optional[SamIntrinsicable[str]] = apiauth("InvokeRole")
    ResourcePolicy: Optional[ResourcePolicy] = apiauth("ResourcePolicy")


class RequestModel(BaseModel):
    Model: str = requestmodel("Model")
    Required: Optional[bool] = requestmodel("Required")
    ValidateBody: Optional[bool] = requestmodel("ValidateBody")
    ValidateParameters: Optional[bool] = requestmodel("ValidateParameters")


class RequestParameters(BaseModel):
    Caching: Optional[bool] = requestparameters("Caching")
    Required: Optional[bool] = requestparameters("Required")


class ApiEventProperties(BaseModel):
    Auth: Optional[ApiAuth] = apieventproperties("Auth")
    Method: str = apieventproperties("Method")
    Path: str = apieventproperties("Path")
    RequestModel: Optional[RequestModel] = apieventproperties("RequestModel")
    RequestParameters: Optional[Union[str, RequestParameters]] = apieventproperties("RequestParameters")
    RestApiId: Optional[Union[str, Ref]] = apieventproperties("RestApiId")


class ApiEvent(BaseModel):
    Type: Literal["Api"] = event("Type")
    Properties: ApiEventProperties = event("Properties")


class CloudWatchEventProperties(BaseModel):
    Enabled: Optional[bool] = cloudwatcheventproperties("Enabled")
    EventBusName: Optional[PassThrough] = cloudwatcheventproperties("EventBusName")
    Input: Optional[PassThrough] = cloudwatcheventproperties("Input")
    InputPath: Optional[PassThrough] = cloudwatcheventproperties("InputPath")
    Pattern: Optional[PassThrough] = cloudwatcheventproperties("Pattern")
    State: Optional[PassThrough] = cloudwatcheventproperties("State")


class CloudWatchEvent(BaseModel):
    Type: Literal["CloudWatchEvent"] = event("Type")
    Properties: CloudWatchEventProperties = event("Properties")


class DeadLetterConfig(BaseModel):
    Arn: Optional[PassThrough] = deadletterconfig("Arn")
    QueueLogicalId: Optional[str] = deadletterconfig("QueueLogicalId")
    Type: Optional[Literal["SQS"]] = deadletterconfig("Type")


class EventsScheduleProperties(BaseModel):
    DeadLetterConfig: Optional[DeadLetterConfig] = eventsscheduleproperties("DeadLetterConfig")
    Description: Optional[PassThrough] = eventsscheduleproperties("Description")
    Enabled: Optional[bool] = eventsscheduleproperties("Enabled")
    Input: Optional[PassThrough] = eventsscheduleproperties("Input")
    Name: Optional[PassThrough] = eventsscheduleproperties("Name")
    RetryPolicy: Optional[PassThrough] = eventsscheduleproperties("RetryPolicy")
    Schedule: Optional[PassThrough] = eventsscheduleproperties("Schedule")
    State: Optional[PassThrough] = eventsscheduleproperties("State")


class ScheduleEvent(BaseModel):
    Type: Literal["Schedule"] = event("Type")
    Properties: EventsScheduleProperties = event("Properties")


class EventBridgeRuleTarget(BaseModel):
    Id: PassThrough = eventbridgeruletarget("Id")


class EventBridgeRuleEventProperties(BaseModel):
    DeadLetterConfig: Optional[DeadLetterConfig] = eventbridgeruleeventproperties("DeadLetterConfig")
    EventBusName: Optional[PassThrough] = eventbridgeruleeventproperties("EventBusName")
    Input: Optional[PassThrough] = eventbridgeruleeventproperties("Input")
    InputPath: Optional[PassThrough] = eventbridgeruleeventproperties("InputPath")
    Pattern: PassThrough = eventbridgeruleeventproperties("Pattern")
    RetryPolicy: Optional[PassThrough] = eventbridgeruleeventproperties("RetryPolicy")
    Target: Optional[EventBridgeRuleTarget] = eventbridgeruleeventproperties("Target")


class EventBridgeRuleEvent(BaseModel):
    Type: Literal["EventBridgeRule"] = event("Type")
    Properties: EventBridgeRuleEventProperties = event("Properties")


class CloudWatchLogsEventProperties(BaseModel):
    FilterPattern: PassThrough = cloudwatchlogseventproperties("FilterPattern")
    LogGroupName: PassThrough = cloudwatchlogseventproperties("LogGroupName")


class CloudWatchLogsEvent(BaseModel):
    Type: Literal["CloudWatchLogs"] = event("Type")
    Properties: CloudWatchLogsEventProperties = event("Properties")


class IoTRuleEventProperties(BaseModel):
    AwsIotSqlVersion: Optional[PassThrough] = iotruleeventproperties("AwsIotSqlVersion")
    Sql: PassThrough = iotruleeventproperties("Sql")


class IoTRuleEvent(BaseModel):
    Type: Literal["IoTRule"] = event("Type")
    Properties: IoTRuleEventProperties = event("Properties")


class AlexaSkillEventProperties(BaseModel):
    SkillId: Optional[str] = alexaskilleventproperties("SkillId")


class AlexaSkillEvent(BaseModel):
    Type: Literal["AlexaSkill"] = event("Type")
    Properties: Optional[AlexaSkillEventProperties] = event("Properties")


class CognitoEventProperties(BaseModel):
    Trigger: PassThrough = cognitoeventproperties("Trigger")
    UserPool: SamIntrinsicable[str] = cognitoeventproperties("UserPool")


class CognitoEvent(BaseModel):
    Type: Literal["Cognito"] = event("Type")
    Properties: CognitoEventProperties = event("Properties")


class HttpApiAuth(BaseModel):
    AuthorizationScopes: Optional[List[str]] = httpapiauth("AuthorizationScopes")
    Authorizer: Optional[str] = httpapiauth("Authorizer")


class HttpApiEventProperties(BaseModel):
    ApiId: Optional[SamIntrinsicable[str]] = httpapieventproperties("ApiId")
    Auth: Optional[HttpApiAuth] = httpapieventproperties("Auth")
    Method: Optional[str] = httpapieventproperties("Method")
    Path: Optional[str] = httpapieventproperties("Path")
    PayloadFormatVersion: Optional[SamIntrinsicable[str]] = httpapieventproperties("PayloadFormatVersion")
    RouteSettings: Optional[PassThrough] = httpapieventproperties("RouteSettings")
    TimeoutInMillis: Optional[SamIntrinsicable[int]] = httpapieventproperties("TimeoutInMillis")


class HttpApiEvent(BaseModel):
    Type: Literal["HttpApi"] = event("Type")
    Properties: Optional[HttpApiEventProperties] = event("Properties")


class MSKEventProperties(BaseModel):
    ConsumerGroupId: Optional[PassThrough] = mskeventproperties("ConsumerGroupId")
    FilterCriteria: Optional[PassThrough] = mskeventproperties("FilterCriteria")
    MaximumBatchingWindowInSeconds: Optional[PassThrough] = mskeventproperties("MaximumBatchingWindowInSeconds")
    StartingPosition: PassThrough = mskeventproperties("StartingPosition")
    Stream: PassThrough = mskeventproperties("Stream")
    Topics: PassThrough = mskeventproperties("Topics")


class MSKEvent(BaseModel):
    Type: Literal["MSK"] = event("Type")
    Properties: MSKEventProperties = event("Properties")


class MQEventProperties(BaseModel):
    BatchSize: Optional[PassThrough] = mqeventproperties("BatchSize")
    Broker: PassThrough = mqeventproperties("Broker")
    Enabled: Optional[PassThrough] = mqeventproperties("Enabled")
    FilterCriteria: Optional[PassThrough] = mqeventproperties("FilterCriteria")
    MaximumBatchingWindowInSeconds: Optional[PassThrough] = mqeventproperties("MaximumBatchingWindowInSeconds")
    Queues: PassThrough = mqeventproperties("Queues")
    SecretsManagerKmsKeyId: Optional[str] = mqeventproperties("SecretsManagerKmsKeyId")
    SourceAccessConfigurations: PassThrough = mqeventproperties("SourceAccessConfigurations")


class MQEvent(BaseModel):
    Type: Literal["MQ"] = event("Type")
    Properties: MQEventProperties = event("Properties")


class SelfManagedKafkaEventProperties(BaseModel):
    BatchSize: Optional[PassThrough] = selfmanagedkafkaeventproperties("BatchSize")
    ConsumerGroupId: Optional[PassThrough] = selfmanagedkafkaeventproperties("ConsumerGroupId")
    Enabled: Optional[PassThrough] = selfmanagedkafkaeventproperties("Enabled")
    FilterCriteria: Optional[PassThrough] = selfmanagedkafkaeventproperties("FilterCriteria")
    KafkaBootstrapServers: Optional[List[SamIntrinsicable[str]]] = selfmanagedkafkaeventproperties(
        "KafkaBootstrapServers"
    )
    SourceAccessConfigurations: PassThrough = selfmanagedkafkaeventproperties("SourceAccessConfigurations")
    Topics: PassThrough = selfmanagedkafkaeventproperties("Topics")


class SelfManagedKafkaEvent(BaseModel):
    Type: Literal["SelfManagedKafka"] = event("Type")
    Properties: SelfManagedKafkaEventProperties = event("Properties")


# TODO: Same as ScheduleV2EventProperties in state machine?
class ScheduleV2EventProperties(BaseModel):
    DeadLetterConfig: Optional[DeadLetterConfig] = schedulev2eventproperties("DeadLetterConfig")
    Description: Optional[PassThrough] = schedulev2eventproperties("Description")
    EndDate: Optional[PassThrough] = schedulev2eventproperties("EndDate")
    FlexibleTimeWindow: Optional[PassThrough] = schedulev2eventproperties("FlexibleTimeWindow")
    GroupName: Optional[PassThrough] = schedulev2eventproperties("GroupName")
    Input: Optional[PassThrough] = schedulev2eventproperties("Input")
    KmsKeyArn: Optional[PassThrough] = schedulev2eventproperties("KmsKeyArn")
    Name: Optional[PassThrough] = schedulev2eventproperties("Name")
    PermissionsBoundary: Optional[PassThrough] = schedulev2eventproperties("PermissionsBoundary")
    RetryPolicy: Optional[PassThrough] = schedulev2eventproperties("RetryPolicy")
    RoleArn: Optional[PassThrough]  # TODO: Add to docs
    ScheduleExpression: Optional[PassThrough] = schedulev2eventproperties("ScheduleExpression")
    ScheduleExpressionTimezone: Optional[PassThrough] = schedulev2eventproperties("ScheduleExpressionTimezone")
    StartDate: Optional[PassThrough] = schedulev2eventproperties("StartDate")
    State: Optional[PassThrough] = schedulev2eventproperties("State")


class ScheduleV2Event(BaseModel):
    Type: Literal["ScheduleV2"] = event("Type")
    Properties: ScheduleV2EventProperties = event("Properties")


Handler = Optional[PassThrough]
Runtime = Optional[PassThrough]
CodeUriType = Optional[Union[str, CodeUri]]
DeadLetterQueueType = Optional[SamIntrinsicable[DeadLetterQueue]]
Description = Optional[PassThrough]
MemorySize = Optional[PassThrough]
Timeout = Optional[PassThrough]
VpcConfig = Optional[PassThrough]
Environment = Optional[PassThrough]
Tags = Optional[DictStrAny]
Tracing = Optional[SamIntrinsicable[Literal["Active", "PassThrough"]]]
KmsKeyArn = Optional[PassThrough]
Layers = Optional[PassThrough]
AutoPublishAlias = Optional[SamIntrinsicable[str]]
RolePath = Optional[PassThrough]  # TODO: update docs when live
PermissionsBoundary = Optional[PassThrough]
ReservedConcurrentExecutions = Optional[PassThrough]
ProvisionedConcurrencyConfig = Optional[PassThrough]
AssumeRolePolicyDocument = Optional[DictStrAny]
Architectures = Optional[PassThrough]
EphemeralStorage = Optional[PassThrough]
SnapStart = Optional[PassThrough]  # TODO: check the type


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
    RolePath: Optional[RolePath]  # TODO: Add to docs
    PermissionsBoundary: Optional[PermissionsBoundary] = prop("PermissionsBoundary")
    Policies: Optional[Union[str, DictStrAny, List[Union[str, DictStrAny]]]] = prop("Policies")
    ProvisionedConcurrencyConfig: Optional[ProvisionedConcurrencyConfig] = prop("ProvisionedConcurrencyConfig")
    ReservedConcurrentExecutions: Optional[ReservedConcurrentExecutions] = prop("ReservedConcurrentExecutions")
    Role: Optional[SamIntrinsicable[str]] = prop("Role")
    Runtime: Optional[Runtime] = prop("Runtime")
    SnapStart: Optional[SnapStart]  # TODO: add prop and types
    Tags: Optional[Tags] = prop("Tags")
    Timeout: Optional[Timeout] = prop("Timeout")
    Tracing: Optional[Tracing] = prop("Tracing")
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
    Tags: Optional[Tags] = prop("Tags")
    Tracing: Optional[Tracing] = prop("Tracing")
    KmsKeyArn: Optional[KmsKeyArn] = prop("KmsKeyArn")
    Layers: Optional[Layers] = prop("Layers")
    AutoPublishAlias: Optional[AutoPublishAlias] = prop("AutoPublishAlias")
    DeploymentPreference: Optional[DeploymentPreference] = prop("DeploymentPreference")
    RolePath: Optional[RolePath]
    PermissionsBoundary: Optional[PermissionsBoundary] = prop("PermissionsBoundary")
    ReservedConcurrentExecutions: Optional[ReservedConcurrentExecutions] = prop("ReservedConcurrentExecutions")
    ProvisionedConcurrencyConfig: Optional[ProvisionedConcurrencyConfig] = prop("ProvisionedConcurrencyConfig")
    AssumeRolePolicyDocument: Optional[AssumeRolePolicyDocument] = prop("AssumeRolePolicyDocument")
    EventInvokeConfig: Optional[EventInvokeConfig] = prop("EventInvokeConfig")
    Architectures: Optional[Architectures] = prop("Architectures")
    EphemeralStorage: Optional[EphemeralStorage] = prop("EphemeralStorage")
    SnapStart: Optional[SnapStart]  # TODO: add prop


class Resource(BaseModel):
    Type: Literal["AWS::Serverless::Function"]
    Properties: Optional[Properties]
    DeletionPolicy: Optional[PassThrough]
    UpdateReplacePolicy: Optional[PassThrough]
    Condition: Optional[PassThrough]
    DependsOn: Optional[PassThrough]
    Metadata: Optional[PassThrough]
