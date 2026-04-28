from __future__ import annotations

from typing import Literal, Union

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
capacityproviderconfig = get_prop("sam-property-function-capacityproviderconfig")
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
    AwsAccountBlacklist: list[Union[str, DictStrAny]] | None = resourcepolicy("AwsAccountBlacklist")
    AwsAccountWhitelist: list[Union[str, DictStrAny]] | None = resourcepolicy("AwsAccountWhitelist")
    CustomStatements: list[Union[str, DictStrAny]] | None = resourcepolicy("CustomStatements")
    IntrinsicVpcBlacklist: list[Union[str, DictStrAny]] | None = resourcepolicy("IntrinsicVpcBlacklist")
    IntrinsicVpcWhitelist: list[Union[str, DictStrAny]] | None = resourcepolicy("IntrinsicVpcWhitelist")
    IntrinsicVpceBlacklist: list[Union[str, DictStrAny]] | None = resourcepolicy("IntrinsicVpceBlacklist")
    IntrinsicVpceWhitelist: list[Union[str, DictStrAny]] | None = resourcepolicy("IntrinsicVpceWhitelist")
    IpRangeBlacklist: list[Union[str, DictStrAny]] | None = resourcepolicy("IpRangeBlacklist")
    IpRangeWhitelist: list[Union[str, DictStrAny]] | None = resourcepolicy("IpRangeWhitelist")
    SourceVpcBlacklist: list[Union[str, DictStrAny]] | None = resourcepolicy("SourceVpcBlacklist")
    SourceVpcWhitelist: list[Union[str, DictStrAny]] | None = resourcepolicy("SourceVpcWhitelist")


class CodeUri(BaseModel):
    Bucket: SamIntrinsicable[str] = codeuri("Bucket")
    Key: SamIntrinsicable[str] = codeuri("Key")
    Version: SamIntrinsicable[str] | None = codeuri("Version")


class Hooks(BaseModel):
    PostTraffic: SamIntrinsicable[str] | None = hooks("PostTraffic")
    PreTraffic: SamIntrinsicable[str] | None = hooks("PreTraffic")


class DeploymentPreference(BaseModel):
    Alarms: SamIntrinsicable[list[DictStrAny]] | None = deploymentpreference("Alarms")
    Enabled: SamIntrinsicable[bool] | None = deploymentpreference("Enabled")
    Hooks: Hooks | None = deploymentpreference("Hooks")
    PassthroughCondition: SamIntrinsicable[bool] | None = deploymentpreference("PassthroughCondition")
    Role: SamIntrinsicable[str] | None = deploymentpreference("Role")
    TriggerConfigurations: PassThroughProp | None = passthrough_prop(
        DEPLOYMENT_PREFERENCE_STEM,
        "TriggerConfigurations",
        ["AWS::CodeDeploy::DeploymentGroup", "Properties", "TriggerConfigurations"],
    )
    Type: SamIntrinsicable[str] | None = deploymentpreference(
        "Type"
    )  # TODO: Should investigate whether this is a required field. This is a required field on documentation. However, we don't seem to use this field.


class DeadLetterQueue(BaseModel):
    TargetArn: str = dlq("TargetArn")
    Type: Literal["SNS", "SQS"] = dlq("Type")


class EventInvokeOnFailure(BaseModel):
    Destination: SamIntrinsicable[str] | None = eventinvokeonfailure("Destination")
    Type: Literal["SQS", "SNS", "Lambda", "EventBridge", "S3Bucket"] | None = eventinvokeonfailure("Type")


class EventInvokeOnSuccess(BaseModel):
    Destination: SamIntrinsicable[str] | None = eventinvokeonsuccess("Destination")
    Type: Literal["SQS", "SNS", "Lambda", "EventBridge", "S3Bucket"] | None = eventinvokeonsuccess("Type")


class EventInvokeDestinationConfig(BaseModel):
    OnFailure: EventInvokeOnFailure | None = eventinvokedestinationconfig("OnFailure")
    OnSuccess: EventInvokeOnSuccess | None = eventinvokedestinationconfig("OnSuccess")


class EventInvokeConfig(BaseModel):
    DestinationConfig: EventInvokeDestinationConfig | None = eventinvokeconfig("DestinationConfig")
    MaximumEventAgeInSeconds: int | None = eventinvokeconfig("MaximumEventAgeInSeconds")
    MaximumRetryAttempts: int | None = eventinvokeconfig("MaximumRetryAttempts")


class S3EventProperties(BaseModel):
    Bucket: SamIntrinsicable[str] = s3eventproperties("Bucket")
    Events: PassThroughProp = s3eventproperties("Events")
    Filter: PassThroughProp | None = s3eventproperties("Filter")


class S3Event(BaseModel):
    Properties: S3EventProperties = event("Properties")
    Type: Literal["S3"] = event("Type")


class SqsSubscription(BaseModel):
    BatchSize: SamIntrinsicable[str] | None = sqssubscription("BatchSize")
    Enabled: bool | None = sqssubscription("Enabled")
    QueueArn: SamIntrinsicable[str] = sqssubscription("QueueArn")
    QueuePolicyLogicalId: str | None = sqssubscription("QueuePolicyLogicalId")
    QueueUrl: SamIntrinsicable[str] = sqssubscription("QueueUrl")


class SNSEventProperties(BaseModel):
    FilterPolicy: PassThroughProp | None = snseventproperties("FilterPolicy")
    FilterPolicyScope: PassThroughProp | None = passthrough_prop(
        "sam-property-function-sns",
        "FilterPolicyScope",
        ["AWS::SNS::Subscription", "Properties", "FilterPolicyScope"],
    )
    Region: PassThroughProp | None = snseventproperties("Region")
    SqsSubscription: Union[bool, SqsSubscription] | None = snseventproperties("SqsSubscription")
    Topic: PassThroughProp = snseventproperties("Topic")


class SNSEvent(BaseModel):
    Properties: SNSEventProperties = event("Properties")
    Type: Literal["SNS"] = event("Type")


class FunctionUrlConfig(BaseModel):
    AuthType: SamIntrinsicable[str] = functionurlconfig("AuthType")
    Cors: PassThroughProp | None = functionurlconfig("Cors")
    InvokeMode: PassThroughProp | None = functionurlconfig("InvokeMode")


class KinesisEventProperties(BaseModel):
    BatchSize: PassThroughProp | None = kinesiseventproperties("BatchSize")
    BisectBatchOnFunctionError: PassThroughProp | None = kinesiseventproperties("BisectBatchOnFunctionError")
    DestinationConfig: PassThroughProp | None = kinesiseventproperties("DestinationConfig")
    Enabled: PassThroughProp | None = kinesiseventproperties("Enabled")
    FilterCriteria: PassThroughProp | None = kinesiseventproperties("FilterCriteria")
    FunctionResponseTypes: PassThroughProp | None = kinesiseventproperties("FunctionResponseTypes")
    KmsKeyArn: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "KmsKeyArn",
        ["AWS::Lambda::EventSourceMapping", "Properties", "KmsKeyArn"],
    )
    MaximumBatchingWindowInSeconds: PassThroughProp | None = kinesiseventproperties("MaximumBatchingWindowInSeconds")
    MaximumRecordAgeInSeconds: PassThroughProp | None = kinesiseventproperties("MaximumRecordAgeInSeconds")
    MaximumRetryAttempts: PassThroughProp | None = kinesiseventproperties("MaximumRetryAttempts")
    ParallelizationFactor: PassThroughProp | None = kinesiseventproperties("ParallelizationFactor")
    StartingPosition: PassThroughProp | None = kinesiseventproperties("StartingPosition")
    StartingPositionTimestamp: PassThroughProp | None = kinesiseventproperties("StartingPositionTimestamp")
    Stream: PassThroughProp = kinesiseventproperties("Stream")
    TumblingWindowInSeconds: PassThroughProp | None = kinesiseventproperties("TumblingWindowInSeconds")
    MetricsConfig: PassThroughProp | None


class KinesisEvent(BaseModel):
    Type: Literal["Kinesis"] = event("Type")
    Properties: KinesisEventProperties = event("Properties")


class DynamoDBEventProperties(BaseModel):
    BatchSize: PassThroughProp | None = dynamodbeventproperties("BatchSize")
    BisectBatchOnFunctionError: PassThroughProp | None = dynamodbeventproperties("BisectBatchOnFunctionError")
    DestinationConfig: PassThroughProp | None = dynamodbeventproperties("DestinationConfig")
    Enabled: PassThroughProp | None = dynamodbeventproperties("Enabled")
    FilterCriteria: PassThroughProp | None = dynamodbeventproperties("FilterCriteria")
    FunctionResponseTypes: PassThroughProp | None = dynamodbeventproperties("FunctionResponseTypes")
    KmsKeyArn: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "KmsKeyArn",
        ["AWS::Lambda::EventSourceMapping", "Properties", "KmsKeyArn"],
    )
    MaximumBatchingWindowInSeconds: PassThroughProp | None = dynamodbeventproperties("MaximumBatchingWindowInSeconds")
    MaximumRecordAgeInSeconds: PassThroughProp | None = dynamodbeventproperties("MaximumRecordAgeInSeconds")
    MaximumRetryAttempts: PassThroughProp | None = dynamodbeventproperties("MaximumRetryAttempts")
    ParallelizationFactor: PassThroughProp | None = dynamodbeventproperties("ParallelizationFactor")
    StartingPosition: PassThroughProp | None = dynamodbeventproperties("StartingPosition")
    StartingPositionTimestamp: PassThroughProp | None = dynamodbeventproperties("StartingPositionTimestamp")
    Stream: PassThroughProp = dynamodbeventproperties("Stream")
    TumblingWindowInSeconds: PassThroughProp | None = dynamodbeventproperties("TumblingWindowInSeconds")
    MetricsConfig: PassThroughProp | None


class DynamoDBEvent(BaseModel):
    Type: Literal["DynamoDB"] = event("Type")
    Properties: DynamoDBEventProperties = event("Properties")


class DocumentDBEventProperties(BaseModel):
    BatchSize: PassThroughProp | None = documentdbeventproperties("BatchSize")
    Cluster: PassThroughProp = documentdbeventproperties("Cluster")
    CollectionName: PassThroughProp | None = documentdbeventproperties("CollectionName")
    DatabaseName: PassThroughProp = documentdbeventproperties("DatabaseName")
    Enabled: PassThroughProp | None = documentdbeventproperties("Enabled")
    FilterCriteria: PassThroughProp | None = documentdbeventproperties("FilterCriteria")
    FullDocument: PassThroughProp | None = documentdbeventproperties("FullDocument")
    KmsKeyArn: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "KmsKeyArn",
        ["AWS::Lambda::EventSourceMapping", "Properties", "KmsKeyArn"],
    )
    MaximumBatchingWindowInSeconds: PassThroughProp | None = documentdbeventproperties("MaximumBatchingWindowInSeconds")
    SecretsManagerKmsKeyId: str | None = documentdbeventproperties("SecretsManagerKmsKeyId")
    SourceAccessConfigurations: PassThroughProp = documentdbeventproperties("SourceAccessConfigurations")
    StartingPosition: PassThroughProp | None = documentdbeventproperties("StartingPosition")
    StartingPositionTimestamp: PassThroughProp | None = documentdbeventproperties("StartingPositionTimestamp")


class DocumentDBEvent(BaseModel):
    Type: Literal["DocumentDB"] = event("Type")
    Properties: DocumentDBEventProperties = event("Properties")


class SQSEventProperties(BaseModel):
    BatchSize: PassThroughProp | None = sqseventproperties("BatchSize")
    Enabled: PassThroughProp | None = sqseventproperties("Enabled")
    FilterCriteria: PassThroughProp | None = sqseventproperties("FilterCriteria")
    FunctionResponseTypes: PassThroughProp | None = sqseventproperties("FunctionResponseTypes")
    KmsKeyArn: PassThroughProp | None = sqseventproperties("KmsKeyArn")
    MaximumBatchingWindowInSeconds: PassThroughProp | None = sqseventproperties("MaximumBatchingWindowInSeconds")
    Queue: PassThroughProp = sqseventproperties("Queue")
    ScalingConfig: PassThroughProp | None  # Update docs when live
    MetricsConfig: PassThroughProp | None


class SQSEvent(BaseModel):
    Type: Literal["SQS"] = event("Type")
    Properties: SQSEventProperties = event("Properties")


class ApiAuth(BaseModel):
    ApiKeyRequired: bool | None = apiauth("ApiKeyRequired")
    AuthorizationScopes: list[str] | None = apiauth("AuthorizationScopes")
    Authorizer: str | None = apiauth("Authorizer")
    InvokeRole: SamIntrinsicable[str] | None = apiauth("InvokeRole")
    ResourcePolicy: ResourcePolicy | None = apiauth("ResourcePolicy")
    # TODO explicitly mention in docs that intrinsics are not supported for OverrideApiAuth
    OverrideApiAuth: bool | None = apiauth("OverrideApiAuth")


class RequestModel(BaseModel):
    Model: str = requestmodel("Model")
    Required: bool | None = requestmodel("Required")
    ValidateBody: bool | None = requestmodel("ValidateBody")
    ValidateParameters: bool | None = requestmodel("ValidateParameters")


class RequestParameters(BaseModel):
    Caching: bool | None = requestparameters("Caching")
    Required: bool | None = requestparameters("Required")


# TODO: docs says either str or RequestParameter but implementation is an array of str or RequestParameter
# remove this comment once updated documentation
RequestModelProperty = list[Union[str, dict[str, RequestParameters]]]


class ApiEventProperties(BaseModel):
    Auth: ApiAuth | None = apieventproperties("Auth")
    Method: str = apieventproperties("Method")
    Path: str = apieventproperties("Path")
    RequestModel: RequestModel | None = apieventproperties("RequestModel")
    RequestParameters: RequestModelProperty | None = apieventproperties("RequestParameters")
    RestApiId: Union[str, Ref] | None = apieventproperties("RestApiId")
    TimeoutInMillis: PassThroughProp | None = passthrough_prop(
        "sam-property-function-api",
        "TimeoutInMillis",
        ["AWS::ApiGateway::Method.Integration", "TimeoutInMillis"],
    )
    ResponseTransferMode: PassThroughProp | None = apieventproperties("ResponseTransferMode")


class ApiEvent(BaseModel):
    Type: Literal["Api"] = event("Type")
    Properties: ApiEventProperties = event("Properties")


class CloudWatchEventProperties(BaseModel):
    Enabled: bool | None = cloudwatcheventproperties("Enabled")
    EventBusName: PassThroughProp | None = cloudwatcheventproperties("EventBusName")
    Input: PassThroughProp | None = cloudwatcheventproperties("Input")
    InputPath: PassThroughProp | None = cloudwatcheventproperties("InputPath")
    Pattern: PassThroughProp | None = cloudwatcheventproperties("Pattern")
    State: PassThroughProp | None = cloudwatcheventproperties("State")


class CloudWatchEvent(BaseModel):
    Type: Literal["CloudWatchEvent"] = event("Type")
    Properties: CloudWatchEventProperties = event("Properties")


class DeadLetterConfig(BaseModel):
    Arn: PassThroughProp | None = deadletterconfig("Arn")
    QueueLogicalId: str | None = deadletterconfig("QueueLogicalId")
    Type: Literal["SQS"] | None = deadletterconfig("Type")


class EventsScheduleProperties(BaseModel):
    DeadLetterConfig: DeadLetterConfig | None = eventsscheduleproperties("DeadLetterConfig")
    Description: PassThroughProp | None = eventsscheduleproperties("Description")
    Enabled: bool | None = eventsscheduleproperties("Enabled")
    Input: PassThroughProp | None = eventsscheduleproperties("Input")
    Name: PassThroughProp | None = eventsscheduleproperties("Name")
    RetryPolicy: PassThroughProp | None = eventsscheduleproperties("RetryPolicy")
    Schedule: PassThroughProp | None = eventsscheduleproperties("Schedule")
    State: PassThroughProp | None = eventsscheduleproperties("State")


class ScheduleEvent(BaseModel):
    Type: Literal["Schedule"] = event("Type")
    Properties: EventsScheduleProperties = event("Properties")


class EventBridgeRuleTarget(BaseModel):
    Id: PassThroughProp = eventbridgeruletarget("Id")


class EventBridgeRuleEventProperties(BaseModel):
    DeadLetterConfig: DeadLetterConfig | None = eventbridgeruleeventproperties("DeadLetterConfig")
    EventBusName: PassThroughProp | None = eventbridgeruleeventproperties("EventBusName")
    Input: PassThroughProp | None = eventbridgeruleeventproperties("Input")
    InputPath: PassThroughProp | None = eventbridgeruleeventproperties("InputPath")
    Pattern: PassThroughProp = eventbridgeruleeventproperties("Pattern")
    RetryPolicy: PassThroughProp | None = eventbridgeruleeventproperties("RetryPolicy")
    Target: EventBridgeRuleTarget | None = eventbridgeruleeventproperties("Target")
    InputTransformer: PassThroughProp | None = eventbridgeruleeventproperties("InputTransformer")
    RuleName: PassThroughProp | None = eventbridgeruleeventproperties("RuleName")


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
    AwsIotSqlVersion: PassThroughProp | None = iotruleeventproperties("AwsIotSqlVersion")
    Sql: PassThroughProp = iotruleeventproperties("Sql")


class IoTRuleEvent(BaseModel):
    Type: Literal["IoTRule"] = event("Type")
    Properties: IoTRuleEventProperties = event("Properties")


class AlexaSkillEventProperties(BaseModel):
    SkillId: str | None = alexaskilleventproperties("SkillId")


class AlexaSkillEvent(BaseModel):
    Type: Literal["AlexaSkill"] = event("Type")
    Properties: AlexaSkillEventProperties | None = event("Properties")


class CognitoEventProperties(BaseModel):
    Trigger: PassThroughProp = cognitoeventproperties("Trigger")
    UserPool: SamIntrinsicable[str] = cognitoeventproperties("UserPool")


class CognitoEvent(BaseModel):
    Type: Literal["Cognito"] = event("Type")
    Properties: CognitoEventProperties = event("Properties")


class HttpApiAuth(BaseModel):
    AuthorizationScopes: list[str] | None = httpapiauth("AuthorizationScopes")
    Authorizer: str | None = httpapiauth("Authorizer")


class HttpApiEventProperties(BaseModel):
    ApiId: SamIntrinsicable[str] | None = httpapieventproperties("ApiId")
    Auth: HttpApiAuth | None = httpapieventproperties("Auth")
    Method: str | None = httpapieventproperties("Method")
    Path: str | None = httpapieventproperties("Path")
    PayloadFormatVersion: SamIntrinsicable[str] | None = httpapieventproperties("PayloadFormatVersion")
    RouteSettings: PassThroughProp | None = httpapieventproperties("RouteSettings")
    TimeoutInMillis: SamIntrinsicable[int] | None = httpapieventproperties("TimeoutInMillis")


class HttpApiEvent(BaseModel):
    Type: Literal["HttpApi"] = event("Type")
    Properties: HttpApiEventProperties | None = event("Properties")


class MSKEventProperties(BaseModel):
    BatchSize: PassThroughProp | None = passthrough_prop(
        "sam-property-function-msk",
        "BatchSize",
        ["AWS::Lambda::EventSourceMapping", "Properties", "BatchSize"],
    )
    ConsumerGroupId: PassThroughProp | None = mskeventproperties("ConsumerGroupId")
    Enabled: PassThroughProp | None = passthrough_prop(
        "sam-property-function-msk",
        "Enabled",
        ["AWS::Lambda::EventSourceMapping", "Properties", "Enabled"],
    )
    FilterCriteria: PassThroughProp | None = mskeventproperties("FilterCriteria")
    KmsKeyArn: PassThroughProp | None = mskeventproperties("KmsKeyArn")
    MaximumBatchingWindowInSeconds: PassThroughProp | None = mskeventproperties("MaximumBatchingWindowInSeconds")
    StartingPosition: PassThroughProp | None = mskeventproperties("StartingPosition")
    StartingPositionTimestamp: PassThroughProp | None = mskeventproperties("StartingPositionTimestamp")
    Stream: PassThroughProp = mskeventproperties("Stream")
    Topics: PassThroughProp = mskeventproperties("Topics")
    SourceAccessConfigurations: PassThroughProp | None = mskeventproperties("SourceAccessConfigurations")
    DestinationConfig: PassThroughProp | None = passthrough_prop(
        "sam-property-function-msk",
        "DestinationConfig",
        ["AWS::Lambda::EventSourceMapping", "Properties", "DestinationConfig"],
    )
    ProvisionedPollerConfig: PassThroughProp | None = mskeventproperties("ProvisionedPollerConfig")
    SchemaRegistryConfig: PassThroughProp | None = mskeventproperties("SchemaRegistryConfig")
    MetricsConfig: PassThroughProp | None = mskeventproperties("MetricsConfig")
    LoggingConfig: PassThroughProp | None = mskeventproperties("LoggingConfig")
    BisectBatchOnFunctionError: PassThroughProp | None = mskeventproperties("BisectBatchOnFunctionError")
    FunctionResponseTypes: PassThroughProp | None = mskeventproperties("FunctionResponseTypes")
    MaximumRecordAgeInSeconds: PassThroughProp | None = mskeventproperties("MaximumRecordAgeInSeconds")
    MaximumRetryAttempts: PassThroughProp | None = mskeventproperties("MaximumRetryAttempts")


class MSKEvent(BaseModel):
    Type: Literal["MSK"] = event("Type")
    Properties: MSKEventProperties = event("Properties")


class MQEventProperties(BaseModel):
    BatchSize: PassThroughProp | None = mqeventproperties("BatchSize")
    Broker: PassThroughProp = mqeventproperties("Broker")
    DynamicPolicyName: bool | None = mqeventproperties("DynamicPolicyName")
    Enabled: PassThroughProp | None = mqeventproperties("Enabled")
    FilterCriteria: PassThroughProp | None = mqeventproperties("FilterCriteria")
    KmsKeyArn: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "KmsKeyArn",
        ["AWS::Lambda::EventSourceMapping", "Properties", "KmsKeyArn"],
    )
    MaximumBatchingWindowInSeconds: PassThroughProp | None = mqeventproperties("MaximumBatchingWindowInSeconds")
    Queues: PassThroughProp = mqeventproperties("Queues")
    SecretsManagerKmsKeyId: str | None = mqeventproperties("SecretsManagerKmsKeyId")
    SourceAccessConfigurations: PassThroughProp = mqeventproperties("SourceAccessConfigurations")


class MQEvent(BaseModel):
    Type: Literal["MQ"] = event("Type")
    Properties: MQEventProperties = event("Properties")


class SelfManagedKafkaEventProperties(BaseModel):
    BatchSize: PassThroughProp | None = selfmanagedkafkaeventproperties("BatchSize")
    ConsumerGroupId: PassThroughProp | None = selfmanagedkafkaeventproperties("ConsumerGroupId")
    Enabled: PassThroughProp | None = selfmanagedkafkaeventproperties("Enabled")
    FilterCriteria: PassThroughProp | None = selfmanagedkafkaeventproperties("FilterCriteria")
    KafkaBootstrapServers: list[SamIntrinsicable[str]] | None = selfmanagedkafkaeventproperties("KafkaBootstrapServers")
    KmsKeyArn: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "KmsKeyArn",
        ["AWS::Lambda::EventSourceMapping", "Properties", "KmsKeyArn"],
    )
    SourceAccessConfigurations: PassThroughProp = selfmanagedkafkaeventproperties("SourceAccessConfigurations")
    StartingPosition: PassThroughProp | None = selfmanagedkafkaeventproperties("StartingPosition")
    StartingPositionTimestamp: PassThroughProp | None = selfmanagedkafkaeventproperties("StartingPositionTimestamp")
    Topics: PassThroughProp = selfmanagedkafkaeventproperties("Topics")
    MetricsConfig: PassThroughProp | None = selfmanagedkafkaeventproperties("MetricsConfig")
    ProvisionedPollerConfig: PassThroughProp | None = selfmanagedkafkaeventproperties("ProvisionedPollerConfig")
    SchemaRegistryConfig: PassThroughProp | None = selfmanagedkafkaeventproperties("SchemaRegistryConfig")
    LoggingConfig: PassThroughProp | None = selfmanagedkafkaeventproperties("LoggingConfig")
    BisectBatchOnFunctionError: PassThroughProp | None = selfmanagedkafkaeventproperties("BisectBatchOnFunctionError")
    MaximumRecordAgeInSeconds: PassThroughProp | None = selfmanagedkafkaeventproperties("MaximumRecordAgeInSeconds")
    MaximumRetryAttempts: PassThroughProp | None = selfmanagedkafkaeventproperties("MaximumRetryAttempts")
    FunctionResponseTypes: PassThroughProp | None = selfmanagedkafkaeventproperties("FunctionResponseTypes")


class SelfManagedKafkaEvent(BaseModel):
    Type: Literal["SelfManagedKafka"] = event("Type")
    Properties: SelfManagedKafkaEventProperties = event("Properties")


# TODO: Same as ScheduleV2EventProperties in state machine?
class ScheduleV2EventProperties(BaseModel):
    DeadLetterConfig: DeadLetterConfig | None = schedulev2eventproperties("DeadLetterConfig")
    Description: PassThroughProp | None = schedulev2eventproperties("Description")
    EndDate: PassThroughProp | None = schedulev2eventproperties("EndDate")
    FlexibleTimeWindow: PassThroughProp | None = schedulev2eventproperties("FlexibleTimeWindow")
    GroupName: PassThroughProp | None = schedulev2eventproperties("GroupName")
    Input: PassThroughProp | None = schedulev2eventproperties("Input")
    KmsKeyArn: PassThroughProp | None = schedulev2eventproperties("KmsKeyArn")
    Name: PassThroughProp | None = schedulev2eventproperties("Name")
    PermissionsBoundary: PassThroughProp | None = schedulev2eventproperties("PermissionsBoundary")
    RetryPolicy: PassThroughProp | None = schedulev2eventproperties("RetryPolicy")
    RoleArn: PassThroughProp | None = schedulev2eventproperties("RoleArn")
    ScheduleExpression: PassThroughProp | None = schedulev2eventproperties("ScheduleExpression")
    ScheduleExpressionTimezone: PassThroughProp | None = schedulev2eventproperties("ScheduleExpressionTimezone")
    StartDate: PassThroughProp | None = schedulev2eventproperties("StartDate")
    State: PassThroughProp | None = schedulev2eventproperties("State")
    # OmitName is a SAM-specific boolean property, not a CloudFormation pass-through property
    OmitName: bool | None


class ScheduleV2Event(BaseModel):
    Type: Literal["ScheduleV2"] = event("Type")
    Properties: ScheduleV2EventProperties = event("Properties")


Handler = PassThroughProp | None
Runtime = PassThroughProp | None
CodeUriType = Union[str, CodeUri] | None
DeadLetterQueueType = SamIntrinsicable[DeadLetterQueue] | None
Description = PassThroughProp | None
MemorySize = PassThroughProp | None
Timeout = PassThroughProp | None
VpcConfig = PassThroughProp | None
Environment = PassThroughProp | None
Tags = DictStrAny | None
Tracing = SamIntrinsicable[Literal["Active", "PassThrough", "Disabled"]] | None
KmsKeyArn = PassThroughProp | None
Layers = PassThroughProp | None
AutoPublishAlias = SamIntrinsicable[str] | None
AutoPublishAliasAllProperties = bool | None
RolePath = PassThroughProp | None
PermissionsBoundary = PassThroughProp | None
ReservedConcurrentExecutions = PassThroughProp | None
ProvisionedConcurrencyConfig = PassThroughProp | None
AssumeRolePolicyDocument = DictStrAny | None
Architectures = PassThroughProp | None
EphemeralStorage = PassThroughProp | None
SnapStart = PassThroughProp | None  # TODO: check the type
RuntimeManagementConfig = PassThroughProp | None  # TODO: check the type
LoggingConfig = PassThroughProp | None  # Type alias - documentation added to Properties and Globals classes
RecursiveLoop = PassThroughProp | None
SourceKMSKeyArn = PassThroughProp | None
TenancyConfig = PassThroughProp | None


class CapacityProviderConfig(BaseModel):
    Arn: SamIntrinsicable[str] = capacityproviderconfig("Arn")
    PerExecutionEnvironmentMaxConcurrency: SamIntrinsicable[int] | None = capacityproviderconfig(
        "PerExecutionEnvironmentMaxConcurrency"
    )
    ExecutionEnvironmentMemoryGiBPerVCpu: SamIntrinsicable[Union[int, float]] | None = capacityproviderconfig(
        "ExecutionEnvironmentMemoryGiBPerVCpu"
    )


class Properties(BaseModel):
    Architectures: Architectures | None = passthrough_prop(
        PROPERTIES_STEM,
        "Architectures",
        ["AWS::Lambda::Function", "Properties", "Architectures"],
    )
    AssumeRolePolicyDocument: AssumeRolePolicyDocument | None = prop("AssumeRolePolicyDocument")
    AutoPublishAlias: AutoPublishAlias | None = prop("AutoPublishAlias")
    AutoPublishAliasAllProperties: AutoPublishAliasAllProperties | None = prop("AutoPublishAliasAllProperties")
    AutoPublishCodeSha256: SamIntrinsicable[str] | None = prop("AutoPublishCodeSha256")
    CodeSigningConfigArn: SamIntrinsicable[str] | None = passthrough_prop(
        PROPERTIES_STEM,
        "CodeSigningConfigArn",
        ["AWS::Lambda::Function", "Properties", "CodeSigningConfigArn"],
    )
    CodeUri: CodeUriType | None = prop("CodeUri")
    DeadLetterQueue: DeadLetterQueueType | None = prop("DeadLetterQueue")
    DeploymentPreference: DeploymentPreference | None = prop("DeploymentPreference")
    Description: Description | None = passthrough_prop(
        PROPERTIES_STEM,
        "Description",
        ["AWS::Lambda::Function", "Properties", "Description"],
    )
    # TODO: Make the notation shorter; resource type and SAM/CFN property names usually same
    Environment: Environment | None = passthrough_prop(
        PROPERTIES_STEM,
        "Environment",
        ["AWS::Lambda::Function", "Properties", "Environment"],
    )
    EphemeralStorage: EphemeralStorage | None = passthrough_prop(
        PROPERTIES_STEM,
        "EphemeralStorage",
        ["AWS::Lambda::Function", "Properties", "EphemeralStorage"],
    )
    EventInvokeConfig: EventInvokeConfig | None = prop("EventInvokeConfig")
    Events: (
        dict[
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
        | None
    ) = prop("Events")
    FileSystemConfigs: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "FileSystemConfigs",
        ["AWS::Lambda::Function", "Properties", "FileSystemConfigs"],
    )
    FunctionName: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "FunctionName",
        ["AWS::Lambda::Function", "Properties", "FunctionName"],
    )
    FunctionUrlConfig: FunctionUrlConfig | None = prop("FunctionUrlConfig")
    Handler: Handler | None = passthrough_prop(
        PROPERTIES_STEM,
        "Handler",
        ["AWS::Lambda::Function", "Properties", "Handler"],
    )
    ImageConfig: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "ImageConfig",
        ["AWS::Lambda::Function", "Properties", "ImageConfig"],
    )
    ImageUri: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "ImageUri",
        ["AWS::Lambda::Function.Code", "ImageUri"],
    )
    InlineCode: PassThroughProp | None = prop("InlineCode")
    KmsKeyArn: KmsKeyArn | None = prop("KmsKeyArn")
    Layers: Layers | None = prop("Layers")
    MemorySize: MemorySize | None = prop("MemorySize")
    PackageType: PassThroughProp | None = prop("PackageType")
    RolePath: RolePath | None = passthrough_prop(
        PROPERTIES_STEM,
        "RolePath",
        ["AWS::IAM::Role", "Properties", "Path"],
    )
    PermissionsBoundary: PermissionsBoundary | None = passthrough_prop(
        PROPERTIES_STEM,
        "PermissionsBoundary",
        ["AWS::IAM::Role", "Properties", "PermissionsBoundary"],
    )
    Policies: Union[str, DictStrAny, list[Union[str, DictStrAny]]] | None = prop("Policies")
    ProvisionedConcurrencyConfig: ProvisionedConcurrencyConfig | None = passthrough_prop(
        PROPERTIES_STEM,
        "ProvisionedConcurrencyConfig",
        ["AWS::Lambda::Alias", "Properties", "ProvisionedConcurrencyConfig"],
    )
    ReservedConcurrentExecutions: ReservedConcurrentExecutions | None = prop("ReservedConcurrentExecutions")
    Role: SamIntrinsicable[str] | None = prop("Role")
    Runtime: Runtime | None = passthrough_prop(
        PROPERTIES_STEM,
        "Runtime",
        ["AWS::Lambda::Function", "Properties", "Runtime"],
    )
    SnapStart: SnapStart | None = prop("SnapStart")
    RuntimeManagementConfig: RuntimeManagementConfig | None = prop("RuntimeManagementConfig")
    Tags: Tags | None = prop("Tags")
    PropagateTags: bool | None = prop("PropagateTags")
    Timeout: Timeout | None = prop("Timeout")
    Tracing: Tracing | None = prop("Tracing")
    VersionDescription: PassThroughProp | None = prop("VersionDescription")
    VpcConfig: VpcConfig | None = prop("VpcConfig")
    LoggingConfig: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "LoggingConfig",
        ["AWS::Lambda::Function", "Properties", "LoggingConfig"],
    )
    RecursiveLoop: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "RecursiveLoop",
        ["AWS::Lambda::Function", "Properties", "RecursiveLoop"],
    )
    SourceKMSKeyArn: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "SourceKMSKeyArn",
        ["AWS::Lambda::Function.Code", "SourceKMSKeyArn"],
    )
    CapacityProviderConfig: CapacityProviderConfig | None = prop("CapacityProviderConfig")
    FunctionScalingConfig: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "FunctionScalingConfig",
        ["AWS::Lambda::Function", "Properties", "FunctionScalingConfig"],
    )
    VersionDeletionPolicy: SamIntrinsicable[Union[str, bool]] | None = prop("VersionDeletionPolicy")
    PublishToLatestPublished: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "PublishToLatestPublished",
        ["AWS::Lambda::Function", "Properties", "PublishToLatestPublished"],
    )
    TenancyConfig: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "TenancyConfig",
        ["AWS::Lambda::Function", "Properties", "TenancyConfig"],
    )
    DurableConfig: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "DurableConfig",
        ["AWS::Lambda::Function", "Properties", "DurableConfig"],
    )


class Globals(BaseModel):
    Handler: Handler | None = passthrough_prop(
        PROPERTIES_STEM,
        "Handler",
        ["AWS::Lambda::Function", "Properties", "Handler"],
    )
    Runtime: Runtime | None = passthrough_prop(
        PROPERTIES_STEM,
        "Runtime",
        ["AWS::Lambda::Function", "Properties", "Runtime"],
    )
    CodeUri: CodeUriType | None = prop("CodeUri")
    DeadLetterQueue: DeadLetterQueueType | None = prop("DeadLetterQueue")
    Description: Description | None = prop("Description")
    MemorySize: MemorySize | None = prop("MemorySize")
    Timeout: Timeout | None = prop("Timeout")
    VpcConfig: VpcConfig | None = prop("VpcConfig")
    Environment: Environment | None = passthrough_prop(
        PROPERTIES_STEM,
        "Environment",
        ["AWS::Lambda::Function", "Properties", "Environment"],
    )
    Tags: Tags | None = prop("Tags")
    PropagateTags: bool | None = prop("PropagateTags")
    Tracing: Tracing | None = prop("Tracing")
    KmsKeyArn: KmsKeyArn | None = prop("KmsKeyArn")
    Layers: Layers | None = prop("Layers")
    AutoPublishAlias: AutoPublishAlias | None = prop("AutoPublishAlias")
    DeploymentPreference: DeploymentPreference | None = prop("DeploymentPreference")
    RolePath: RolePath | None = passthrough_prop(
        PROPERTIES_STEM,
        "RolePath",
        ["AWS::IAM::Role", "Properties", "Path"],
    )
    PermissionsBoundary: PermissionsBoundary | None = passthrough_prop(
        PROPERTIES_STEM,
        "PermissionsBoundary",
        ["AWS::IAM::Role", "Properties", "PermissionsBoundary"],
    )
    ReservedConcurrentExecutions: ReservedConcurrentExecutions | None = prop("ReservedConcurrentExecutions")
    ProvisionedConcurrencyConfig: ProvisionedConcurrencyConfig | None = prop("ProvisionedConcurrencyConfig")
    AssumeRolePolicyDocument: AssumeRolePolicyDocument | None = prop("AssumeRolePolicyDocument")
    EventInvokeConfig: EventInvokeConfig | None = prop("EventInvokeConfig")
    Architectures: Architectures | None = passthrough_prop(
        PROPERTIES_STEM,
        "Architectures",
        ["AWS::Lambda::Function", "Properties", "Architectures"],
    )
    EphemeralStorage: EphemeralStorage | None = passthrough_prop(
        PROPERTIES_STEM,
        "EphemeralStorage",
        ["AWS::Lambda::Function", "Properties", "EphemeralStorage"],
    )
    SnapStart: SnapStart | None = prop("SnapStart")
    RuntimeManagementConfig: RuntimeManagementConfig | None = prop("RuntimeManagementConfig")
    LoggingConfig: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "LoggingConfig",
        ["AWS::Lambda::Function", "Properties", "LoggingConfig"],
    )
    RecursiveLoop: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "RecursiveLoop",
        ["AWS::Lambda::Function", "Properties", "RecursiveLoop"],
    )
    SourceKMSKeyArn: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "SourceKMSKeyArn",
        ["AWS::Lambda::Function.Code", "SourceKMSKeyArn"],
    )
    CapacityProviderConfig: CapacityProviderConfig | None = prop("CapacityProviderConfig")
    FunctionScalingConfig: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "FunctionScalingConfig",
        ["AWS::Lambda::Function", "Properties", "FunctionScalingConfig"],
    )
    VersionDeletionPolicy: SamIntrinsicable[Union[str, bool]] | None = prop("VersionDeletionPolicy")
    PublishToLatestPublished: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "PublishToLatestPublished",
        ["AWS::Lambda::Function", "Properties", "PublishToLatestPublished"],
    )
    TenancyConfig: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "TenancyConfig",
        ["AWS::Lambda::Function", "Properties", "TenancyConfig"],
    )
    DurableConfig: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "DurableConfig",
        ["AWS::Lambda::Function", "Properties", "DurableConfig"],
    )


class Resource(ResourceAttributes):
    Type: Literal["AWS::Serverless::Function"]
    Properties: Properties | None
    Connectors: dict[str, EmbeddedConnector] | None
