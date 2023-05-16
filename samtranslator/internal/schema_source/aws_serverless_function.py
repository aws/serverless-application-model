from __future__ import annotations

from typing import Dict, List, Optional, Union

from typing_extensions import Literal

from samtranslator.internal.schema_source.aws_serverless_connector import EmbeddedConnector
from samtranslator.internal.schema_source.common import (
    BaseModel,
    DictStrAny,
    PassThroughProp,
    Ref,
    ResourceAttributes,
    SamIntrinsicable,
    get_prop,
    passthrough_prop,
)

PROPERTIES_STEM = "sam-resource-function"
DEPLOYMENT_PREFERENCE_STEM = "sam-property-function-deploymentpreference"

alexaskilleventproperties = get_prop("sam-property-function-alexaskill")
apiauth = get_prop("sam-property-function-apifunctionauth")
apieventproperties = get_prop("sam-property-function-api")
cloudwatcheventproperties = get_prop("sam-property-function-cloudwatchevent")
cloudwatchlogseventproperties = get_prop("sam-property-function-cloudwatchlogs")
codeuri = get_prop("sam-property-function-functioncode")
cognitoeventproperties = get_prop("sam-property-function-cognito")
deadletterconfig = get_prop("sam-property-function-deadletterconfig")
deploymentpreference = get_prop(DEPLOYMENT_PREFERENCE_STEM)
dlq = get_prop("sam-property-function-deadletterqueue")
documentdbeventproperties = get_prop("sam-property-function-documentdb")
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
prop = get_prop(PROPERTIES_STEM)
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
    TriggerConfigurations: Optional[PassThroughProp] = passthrough_prop(
        DEPLOYMENT_PREFERENCE_STEM,
        "TriggerConfigurations",
        ["AWS::CodeDeploy::DeploymentGroup", "Properties", "TriggerConfigurations"],
    )
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
    Events: PassThroughProp = s3eventproperties("Events")
    Filter: Optional[PassThroughProp] = s3eventproperties("Filter")


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
    FilterPolicy: Optional[PassThroughProp] = snseventproperties("FilterPolicy")
    FilterPolicyScope: Optional[PassThroughProp]  # TODO: add documentation
    Region: Optional[PassThroughProp] = snseventproperties("Region")
    SqsSubscription: Optional[Union[bool, SqsSubscription]] = snseventproperties("SqsSubscription")
    Topic: PassThroughProp = snseventproperties("Topic")


class SNSEvent(BaseModel):
    Properties: SNSEventProperties = event("Properties")
    Type: Literal["SNS"] = event("Type")


class FunctionUrlConfig(BaseModel):
    AuthType: SamIntrinsicable[str] = functionurlconfig("AuthType")
    Cors: Optional[PassThroughProp] = functionurlconfig("Cors")
    InvokeMode: Optional[PassThroughProp]  # TODO: add to doc


class KinesisEventProperties(BaseModel):
    BatchSize: Optional[PassThroughProp] = kinesiseventproperties("BatchSize")
    BisectBatchOnFunctionError: Optional[PassThroughProp] = kinesiseventproperties("BisectBatchOnFunctionError")
    DestinationConfig: Optional[PassThroughProp] = kinesiseventproperties("DestinationConfig")
    Enabled: Optional[PassThroughProp] = kinesiseventproperties("Enabled")
    FilterCriteria: Optional[PassThroughProp] = kinesiseventproperties("FilterCriteria")
    FunctionResponseTypes: Optional[PassThroughProp] = kinesiseventproperties("FunctionResponseTypes")
    MaximumBatchingWindowInSeconds: Optional[PassThroughProp] = kinesiseventproperties("MaximumBatchingWindowInSeconds")
    MaximumRecordAgeInSeconds: Optional[PassThroughProp] = kinesiseventproperties("MaximumRecordAgeInSeconds")
    MaximumRetryAttempts: Optional[PassThroughProp] = kinesiseventproperties("MaximumRetryAttempts")
    ParallelizationFactor: Optional[PassThroughProp] = kinesiseventproperties("ParallelizationFactor")
    StartingPosition: Optional[PassThroughProp] = kinesiseventproperties("StartingPosition")
    StartingPositionTimestamp: Optional[PassThroughProp] = kinesiseventproperties("StartingPositionTimestamp")
    Stream: PassThroughProp = kinesiseventproperties("Stream")
    TumblingWindowInSeconds: Optional[PassThroughProp] = kinesiseventproperties("TumblingWindowInSeconds")


class KinesisEvent(BaseModel):
    Type: Literal["Kinesis"] = event("Type")
    Properties: KinesisEventProperties = event("Properties")


class DynamoDBEventProperties(BaseModel):
    BatchSize: Optional[PassThroughProp] = dynamodbeventproperties("BatchSize")
    BisectBatchOnFunctionError: Optional[PassThroughProp] = dynamodbeventproperties("BisectBatchOnFunctionError")
    DestinationConfig: Optional[PassThroughProp] = dynamodbeventproperties("DestinationConfig")
    Enabled: Optional[PassThroughProp] = dynamodbeventproperties("Enabled")
    FilterCriteria: Optional[PassThroughProp] = dynamodbeventproperties("FilterCriteria")
    FunctionResponseTypes: Optional[PassThroughProp] = dynamodbeventproperties("FunctionResponseTypes")
    MaximumBatchingWindowInSeconds: Optional[PassThroughProp] = dynamodbeventproperties(
        "MaximumBatchingWindowInSeconds"
    )
    MaximumRecordAgeInSeconds: Optional[PassThroughProp] = dynamodbeventproperties("MaximumRecordAgeInSeconds")
    MaximumRetryAttempts: Optional[PassThroughProp] = dynamodbeventproperties("MaximumRetryAttempts")
    ParallelizationFactor: Optional[PassThroughProp] = dynamodbeventproperties("ParallelizationFactor")
    StartingPosition: Optional[PassThroughProp] = dynamodbeventproperties("StartingPosition")
    StartingPositionTimestamp: Optional[PassThroughProp] = dynamodbeventproperties("StartingPositionTimestamp")
    Stream: PassThroughProp = dynamodbeventproperties("Stream")
    TumblingWindowInSeconds: Optional[PassThroughProp] = dynamodbeventproperties("TumblingWindowInSeconds")


class DynamoDBEvent(BaseModel):
    Type: Literal["DynamoDB"] = event("Type")
    Properties: DynamoDBEventProperties = event("Properties")


class DocumentDBEventProperties(BaseModel):
    BatchSize: Optional[PassThroughProp] = documentdbeventproperties("BatchSize")
    Cluster: PassThroughProp = documentdbeventproperties("Cluster")
    CollectionName: Optional[PassThroughProp] = documentdbeventproperties("CollectionName")
    DatabaseName: PassThroughProp = documentdbeventproperties("DatabaseName")
    Enabled: Optional[PassThroughProp] = documentdbeventproperties("Enabled")
    FilterCriteria: Optional[PassThroughProp] = documentdbeventproperties("FilterCriteria")
    FullDocument: Optional[PassThroughProp] = documentdbeventproperties("FullDocument")
    MaximumBatchingWindowInSeconds: Optional[PassThroughProp] = documentdbeventproperties(
        "MaximumBatchingWindowInSeconds"
    )
    SecretsManagerKmsKeyId: Optional[str] = documentdbeventproperties("SecretsManagerKmsKeyId")
    SourceAccessConfigurations: PassThroughProp = documentdbeventproperties("SourceAccessConfigurations")
    StartingPosition: Optional[PassThroughProp] = documentdbeventproperties("StartingPosition")
    StartingPositionTimestamp: Optional[PassThroughProp] = documentdbeventproperties("StartingPositionTimestamp")


class DocumentDBEvent(BaseModel):
    Type: Literal["DocumentDB"] = event("Type")
    Properties: DocumentDBEventProperties = event("Properties")


class SQSEventProperties(BaseModel):
    BatchSize: Optional[PassThroughProp] = sqseventproperties("BatchSize")
    Enabled: Optional[PassThroughProp] = sqseventproperties("Enabled")
    FilterCriteria: Optional[PassThroughProp] = sqseventproperties("FilterCriteria")
    MaximumBatchingWindowInSeconds: Optional[PassThroughProp] = sqseventproperties("MaximumBatchingWindowInSeconds")
    Queue: PassThroughProp = sqseventproperties("Queue")
    ScalingConfig: Optional[PassThroughProp]  # Update docs when live


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


# TODO: docs says either str or RequestParameter but implementation is an array of str or RequestParameter
# remove this comment once updated documentation
RequestModelProperty = List[Union[str, Dict[str, RequestParameters]]]


class ApiEventProperties(BaseModel):
    Auth: Optional[ApiAuth] = apieventproperties("Auth")
    Method: str = apieventproperties("Method")
    Path: str = apieventproperties("Path")
    RequestModel: Optional[RequestModel] = apieventproperties("RequestModel")
    RequestParameters: Optional[RequestModelProperty] = apieventproperties("RequestParameters")
    RestApiId: Optional[Union[str, Ref]] = apieventproperties("RestApiId")


class ApiEvent(BaseModel):
    Type: Literal["Api"] = event("Type")
    Properties: ApiEventProperties = event("Properties")


class CloudWatchEventProperties(BaseModel):
    Enabled: Optional[bool] = cloudwatcheventproperties("Enabled")
    EventBusName: Optional[PassThroughProp] = cloudwatcheventproperties("EventBusName")
    Input: Optional[PassThroughProp] = cloudwatcheventproperties("Input")
    InputPath: Optional[PassThroughProp] = cloudwatcheventproperties("InputPath")
    Pattern: Optional[PassThroughProp] = cloudwatcheventproperties("Pattern")
    State: Optional[PassThroughProp] = cloudwatcheventproperties("State")


class CloudWatchEvent(BaseModel):
    Type: Literal["CloudWatchEvent"] = event("Type")
    Properties: CloudWatchEventProperties = event("Properties")


class DeadLetterConfig(BaseModel):
    Arn: Optional[PassThroughProp] = deadletterconfig("Arn")
    QueueLogicalId: Optional[str] = deadletterconfig("QueueLogicalId")
    Type: Optional[Literal["SQS"]] = deadletterconfig("Type")


class EventsScheduleProperties(BaseModel):
    DeadLetterConfig: Optional[DeadLetterConfig] = eventsscheduleproperties("DeadLetterConfig")
    Description: Optional[PassThroughProp] = eventsscheduleproperties("Description")
    Enabled: Optional[bool] = eventsscheduleproperties("Enabled")
    Input: Optional[PassThroughProp] = eventsscheduleproperties("Input")
    Name: Optional[PassThroughProp] = eventsscheduleproperties("Name")
    RetryPolicy: Optional[PassThroughProp] = eventsscheduleproperties("RetryPolicy")
    Schedule: Optional[PassThroughProp] = eventsscheduleproperties("Schedule")
    State: Optional[PassThroughProp] = eventsscheduleproperties("State")


class ScheduleEvent(BaseModel):
    Type: Literal["Schedule"] = event("Type")
    Properties: EventsScheduleProperties = event("Properties")


class EventBridgeRuleTarget(BaseModel):
    Id: PassThroughProp = eventbridgeruletarget("Id")


class EventBridgeRuleEventProperties(BaseModel):
    DeadLetterConfig: Optional[DeadLetterConfig] = eventbridgeruleeventproperties("DeadLetterConfig")
    EventBusName: Optional[PassThroughProp] = eventbridgeruleeventproperties("EventBusName")
    Input: Optional[PassThroughProp] = eventbridgeruleeventproperties("Input")
    InputPath: Optional[PassThroughProp] = eventbridgeruleeventproperties("InputPath")
    Pattern: PassThroughProp = eventbridgeruleeventproperties("Pattern")
    RetryPolicy: Optional[PassThroughProp] = eventbridgeruleeventproperties("RetryPolicy")
    Target: Optional[EventBridgeRuleTarget] = eventbridgeruleeventproperties("Target")


class EventBridgeRuleEvent(BaseModel):
    Type: Literal["EventBridgeRule"] = event("Type")
    Properties: EventBridgeRuleEventProperties = event("Properties")


class CloudWatchLogsEventProperties(BaseModel):
    FilterPattern: PassThroughProp = cloudwatchlogseventproperties("FilterPattern")
    LogGroupName: PassThroughProp = cloudwatchlogseventproperties("LogGroupName")


class CloudWatchLogsEvent(BaseModel):
    Type: Literal["CloudWatchLogs"] = event("Type")
    Properties: CloudWatchLogsEventProperties = event("Properties")


class IoTRuleEventProperties(BaseModel):
    AwsIotSqlVersion: Optional[PassThroughProp] = iotruleeventproperties("AwsIotSqlVersion")
    Sql: PassThroughProp = iotruleeventproperties("Sql")


class IoTRuleEvent(BaseModel):
    Type: Literal["IoTRule"] = event("Type")
    Properties: IoTRuleEventProperties = event("Properties")


class AlexaSkillEventProperties(BaseModel):
    SkillId: Optional[str] = alexaskilleventproperties("SkillId")


class AlexaSkillEvent(BaseModel):
    Type: Literal["AlexaSkill"] = event("Type")
    Properties: Optional[AlexaSkillEventProperties] = event("Properties")


class CognitoEventProperties(BaseModel):
    Trigger: PassThroughProp = cognitoeventproperties("Trigger")
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
    RouteSettings: Optional[PassThroughProp] = httpapieventproperties("RouteSettings")
    TimeoutInMillis: Optional[SamIntrinsicable[int]] = httpapieventproperties("TimeoutInMillis")


class HttpApiEvent(BaseModel):
    Type: Literal["HttpApi"] = event("Type")
    Properties: Optional[HttpApiEventProperties] = event("Properties")


class MSKEventProperties(BaseModel):
    ConsumerGroupId: Optional[PassThroughProp] = mskeventproperties("ConsumerGroupId")
    FilterCriteria: Optional[PassThroughProp] = mskeventproperties("FilterCriteria")
    MaximumBatchingWindowInSeconds: Optional[PassThroughProp] = mskeventproperties("MaximumBatchingWindowInSeconds")
    StartingPosition: Optional[PassThroughProp] = mskeventproperties("StartingPosition")
    StartingPositionTimestamp: Optional[PassThroughProp] = mskeventproperties("StartingPositionTimestamp")
    Stream: PassThroughProp = mskeventproperties("Stream")
    Topics: PassThroughProp = mskeventproperties("Topics")
    SourceAccessConfigurations: Optional[PassThroughProp] = mskeventproperties("SourceAccessConfigurations")


class MSKEvent(BaseModel):
    Type: Literal["MSK"] = event("Type")
    Properties: MSKEventProperties = event("Properties")


class MQEventProperties(BaseModel):
    BatchSize: Optional[PassThroughProp] = mqeventproperties("BatchSize")
    Broker: PassThroughProp = mqeventproperties("Broker")
    DynamicPolicyName: Optional[bool] = mqeventproperties("DynamicPolicyName")
    Enabled: Optional[PassThroughProp] = mqeventproperties("Enabled")
    FilterCriteria: Optional[PassThroughProp] = mqeventproperties("FilterCriteria")
    MaximumBatchingWindowInSeconds: Optional[PassThroughProp] = mqeventproperties("MaximumBatchingWindowInSeconds")
    Queues: PassThroughProp = mqeventproperties("Queues")
    SecretsManagerKmsKeyId: Optional[str] = mqeventproperties("SecretsManagerKmsKeyId")
    SourceAccessConfigurations: PassThroughProp = mqeventproperties("SourceAccessConfigurations")


class MQEvent(BaseModel):
    Type: Literal["MQ"] = event("Type")
    Properties: MQEventProperties = event("Properties")


class SelfManagedKafkaEventProperties(BaseModel):
    BatchSize: Optional[PassThroughProp] = selfmanagedkafkaeventproperties("BatchSize")
    ConsumerGroupId: Optional[PassThroughProp] = selfmanagedkafkaeventproperties("ConsumerGroupId")
    Enabled: Optional[PassThroughProp] = selfmanagedkafkaeventproperties("Enabled")
    FilterCriteria: Optional[PassThroughProp] = selfmanagedkafkaeventproperties("FilterCriteria")
    KafkaBootstrapServers: Optional[List[SamIntrinsicable[str]]] = selfmanagedkafkaeventproperties(
        "KafkaBootstrapServers"
    )
    SourceAccessConfigurations: PassThroughProp = selfmanagedkafkaeventproperties("SourceAccessConfigurations")
    Topics: PassThroughProp = selfmanagedkafkaeventproperties("Topics")


class SelfManagedKafkaEvent(BaseModel):
    Type: Literal["SelfManagedKafka"] = event("Type")
    Properties: SelfManagedKafkaEventProperties = event("Properties")


# TODO: Same as ScheduleV2EventProperties in state machine?
class ScheduleV2EventProperties(BaseModel):
    DeadLetterConfig: Optional[DeadLetterConfig] = schedulev2eventproperties("DeadLetterConfig")
    Description: Optional[PassThroughProp] = schedulev2eventproperties("Description")
    EndDate: Optional[PassThroughProp] = schedulev2eventproperties("EndDate")
    FlexibleTimeWindow: Optional[PassThroughProp] = schedulev2eventproperties("FlexibleTimeWindow")
    GroupName: Optional[PassThroughProp] = schedulev2eventproperties("GroupName")
    Input: Optional[PassThroughProp] = schedulev2eventproperties("Input")
    KmsKeyArn: Optional[PassThroughProp] = schedulev2eventproperties("KmsKeyArn")
    Name: Optional[PassThroughProp] = schedulev2eventproperties("Name")
    PermissionsBoundary: Optional[PassThroughProp] = schedulev2eventproperties("PermissionsBoundary")
    RetryPolicy: Optional[PassThroughProp] = schedulev2eventproperties("RetryPolicy")
    RoleArn: Optional[PassThroughProp] = schedulev2eventproperties("RoleArn")
    ScheduleExpression: Optional[PassThroughProp] = schedulev2eventproperties("ScheduleExpression")
    ScheduleExpressionTimezone: Optional[PassThroughProp] = schedulev2eventproperties("ScheduleExpressionTimezone")
    StartDate: Optional[PassThroughProp] = schedulev2eventproperties("StartDate")
    State: Optional[PassThroughProp] = schedulev2eventproperties("State")
    OmitName: Optional[bool]  # TODO: add doc


class ScheduleV2Event(BaseModel):
    Type: Literal["ScheduleV2"] = event("Type")
    Properties: ScheduleV2EventProperties = event("Properties")


Handler = Optional[PassThroughProp]
Runtime = Optional[PassThroughProp]
CodeUriType = Optional[Union[str, CodeUri]]
DeadLetterQueueType = Optional[SamIntrinsicable[DeadLetterQueue]]
Description = Optional[PassThroughProp]
MemorySize = Optional[PassThroughProp]
Timeout = Optional[PassThroughProp]
VpcConfig = Optional[PassThroughProp]
Environment = Optional[PassThroughProp]
Tags = Optional[DictStrAny]
Tracing = Optional[SamIntrinsicable[Literal["Active", "PassThrough"]]]
KmsKeyArn = Optional[PassThroughProp]
Layers = Optional[PassThroughProp]
AutoPublishAlias = Optional[SamIntrinsicable[str]]
AutoPublishAliasAllProperties = Optional[bool]
RolePath = Optional[PassThroughProp]
PermissionsBoundary = Optional[PassThroughProp]
ReservedConcurrentExecutions = Optional[PassThroughProp]
ProvisionedConcurrencyConfig = Optional[PassThroughProp]
AssumeRolePolicyDocument = Optional[DictStrAny]
Architectures = Optional[PassThroughProp]
EphemeralStorage = Optional[PassThroughProp]
SnapStart = Optional[PassThroughProp]  # TODO: check the type
RuntimeManagementConfig = Optional[PassThroughProp]  # TODO: check the type


class Properties(BaseModel):
    Architectures: Optional[Architectures] = passthrough_prop(
        PROPERTIES_STEM,
        "Architectures",
        ["AWS::Lambda::Function", "Properties", "Architectures"],
    )
    AssumeRolePolicyDocument: Optional[AssumeRolePolicyDocument] = prop("AssumeRolePolicyDocument")
    AutoPublishAlias: Optional[AutoPublishAlias] = prop("AutoPublishAlias")
    AutoPublishAliasAllProperties: Optional[AutoPublishAliasAllProperties] = prop("AutoPublishAliasAllProperties")
    AutoPublishCodeSha256: Optional[SamIntrinsicable[str]] = prop("AutoPublishCodeSha256")
    CodeSigningConfigArn: Optional[SamIntrinsicable[str]] = passthrough_prop(
        PROPERTIES_STEM,
        "CodeSigningConfigArn",
        ["AWS::Lambda::Function", "Properties", "CodeSigningConfigArn"],
    )
    CodeUri: Optional[CodeUriType] = prop("CodeUri")
    DeadLetterQueue: Optional[DeadLetterQueueType] = prop("DeadLetterQueue")
    DeploymentPreference: Optional[DeploymentPreference] = prop("DeploymentPreference")
    Description: Optional[Description] = passthrough_prop(
        PROPERTIES_STEM,
        "Description",
        ["AWS::Lambda::Function", "Properties", "Description"],
    )
    # TODO: Make the notation shorter; resource type and SAM/CFN property names usually same
    Environment: Optional[Environment] = passthrough_prop(
        PROPERTIES_STEM,
        "Environment",
        ["AWS::Lambda::Function", "Properties", "Environment"],
    )
    EphemeralStorage: Optional[EphemeralStorage] = passthrough_prop(
        PROPERTIES_STEM,
        "EphemeralStorage",
        ["AWS::Lambda::Function", "Properties", "EphemeralStorage"],
    )
    EventInvokeConfig: Optional[EventInvokeConfig] = prop("EventInvokeConfig")
    Events: Optional[
        Dict[
            str,
            Union[
                S3Event,
                SNSEvent,
                KinesisEvent,
                DynamoDBEvent,
                DocumentDBEvent,
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
    FileSystemConfigs: Optional[PassThroughProp] = passthrough_prop(
        PROPERTIES_STEM,
        "FileSystemConfigs",
        ["AWS::Lambda::Function", "Properties", "FileSystemConfigs"],
    )
    FunctionName: Optional[PassThroughProp] = passthrough_prop(
        PROPERTIES_STEM,
        "FunctionName",
        ["AWS::Lambda::Function", "Properties", "FunctionName"],
    )
    FunctionUrlConfig: Optional[FunctionUrlConfig] = prop("FunctionUrlConfig")
    Handler: Optional[Handler] = passthrough_prop(
        PROPERTIES_STEM,
        "Handler",
        ["AWS::Lambda::Function", "Properties", "Handler"],
    )
    ImageConfig: Optional[PassThroughProp] = passthrough_prop(
        PROPERTIES_STEM,
        "ImageConfig",
        ["AWS::Lambda::Function", "Properties", "ImageConfig"],
    )
    ImageUri: Optional[PassThroughProp] = passthrough_prop(
        PROPERTIES_STEM,
        "ImageUri",
        ["AWS::Lambda::Function.Code", "ImageUri"],
    )
    InlineCode: Optional[PassThroughProp] = prop("InlineCode")
    KmsKeyArn: Optional[KmsKeyArn] = prop("KmsKeyArn")
    Layers: Optional[Layers] = prop("Layers")
    MemorySize: Optional[MemorySize] = prop("MemorySize")
    PackageType: Optional[PassThroughProp] = prop("PackageType")
    RolePath: Optional[RolePath] = passthrough_prop(
        PROPERTIES_STEM,
        "RolePath",
        ["AWS::IAM::Role", "Properties", "Path"],
    )
    PermissionsBoundary: Optional[PermissionsBoundary] = passthrough_prop(
        PROPERTIES_STEM,
        "PermissionsBoundary",
        ["AWS::IAM::Role", "Properties", "PermissionsBoundary"],
    )
    Policies: Optional[Union[str, DictStrAny, List[Union[str, DictStrAny]]]] = prop("Policies")
    ProvisionedConcurrencyConfig: Optional[ProvisionedConcurrencyConfig] = passthrough_prop(
        PROPERTIES_STEM,
        "ProvisionedConcurrencyConfig",
        ["AWS::Lambda::Alias", "Properties", "ProvisionedConcurrencyConfig"],
    )
    ReservedConcurrentExecutions: Optional[ReservedConcurrentExecutions] = prop("ReservedConcurrentExecutions")
    Role: Optional[SamIntrinsicable[str]] = prop("Role")
    Runtime: Optional[Runtime] = passthrough_prop(
        PROPERTIES_STEM,
        "Runtime",
        ["AWS::Lambda::Function", "Properties", "Runtime"],
    )
    SnapStart: Optional[SnapStart] = prop("SnapStart")
    RuntimeManagementConfig: Optional[RuntimeManagementConfig] = prop("RuntimeManagementConfig")
    Tags: Optional[Tags] = prop("Tags")
    Timeout: Optional[Timeout] = prop("Timeout")
    Tracing: Optional[Tracing] = prop("Tracing")
    VersionDescription: Optional[PassThroughProp] = prop("VersionDescription")
    VpcConfig: Optional[VpcConfig] = prop("VpcConfig")


class Globals(BaseModel):
    Handler: Optional[Handler] = passthrough_prop(
        PROPERTIES_STEM,
        "Handler",
        ["AWS::Lambda::Function", "Properties", "Handler"],
    )
    Runtime: Optional[Runtime] = passthrough_prop(
        PROPERTIES_STEM,
        "Runtime",
        ["AWS::Lambda::Function", "Properties", "Runtime"],
    )
    CodeUri: Optional[CodeUriType] = prop("CodeUri")
    DeadLetterQueue: Optional[DeadLetterQueueType] = prop("DeadLetterQueue")
    Description: Optional[Description] = prop("Description")
    MemorySize: Optional[MemorySize] = prop("MemorySize")
    Timeout: Optional[Timeout] = prop("Timeout")
    VpcConfig: Optional[VpcConfig] = prop("VpcConfig")
    Environment: Optional[Environment] = passthrough_prop(
        PROPERTIES_STEM,
        "Environment",
        ["AWS::Lambda::Function", "Properties", "Environment"],
    )
    Tags: Optional[Tags] = prop("Tags")
    Tracing: Optional[Tracing] = prop("Tracing")
    KmsKeyArn: Optional[KmsKeyArn] = prop("KmsKeyArn")
    Layers: Optional[Layers] = prop("Layers")
    AutoPublishAlias: Optional[AutoPublishAlias] = prop("AutoPublishAlias")
    DeploymentPreference: Optional[DeploymentPreference] = prop("DeploymentPreference")
    RolePath: Optional[RolePath] = passthrough_prop(
        PROPERTIES_STEM,
        "RolePath",
        ["AWS::IAM::Role", "Properties", "Path"],
    )
    PermissionsBoundary: Optional[PermissionsBoundary] = passthrough_prop(
        PROPERTIES_STEM,
        "PermissionsBoundary",
        ["AWS::IAM::Role", "Properties", "PermissionsBoundary"],
    )
    ReservedConcurrentExecutions: Optional[ReservedConcurrentExecutions] = prop("ReservedConcurrentExecutions")
    ProvisionedConcurrencyConfig: Optional[ProvisionedConcurrencyConfig] = prop("ProvisionedConcurrencyConfig")
    AssumeRolePolicyDocument: Optional[AssumeRolePolicyDocument] = prop("AssumeRolePolicyDocument")
    EventInvokeConfig: Optional[EventInvokeConfig] = prop("EventInvokeConfig")
    Architectures: Optional[Architectures] = passthrough_prop(
        PROPERTIES_STEM,
        "Architectures",
        ["AWS::Lambda::Function", "Properties", "Architectures"],
    )
    EphemeralStorage: Optional[EphemeralStorage] = passthrough_prop(
        PROPERTIES_STEM,
        "EphemeralStorage",
        ["AWS::Lambda::Function", "Properties", "EphemeralStorage"],
    )
    SnapStart: Optional[SnapStart] = prop("SnapStart")
    RuntimeManagementConfig: Optional[RuntimeManagementConfig] = prop("RuntimeManagementConfig")


class Resource(ResourceAttributes):
    Type: Literal["AWS::Serverless::Function"]
    Properties: Optional[Properties]
    Connectors: Optional[Dict[str, EmbeddedConnector]]
