from __future__ import annotations

from typing import Optional, Dict, Union, List

from typing_extensions import Literal

from samtranslator.schema.common import PassThrough, BaseModel, SamIntrinsicable, DictStrAny, get_prop

properties = get_prop("sam-resource-statemachine")
deadletterconfig = get_prop("sam-property-statemachine-statemachinedeadletterconfig")
scheduleeventproperties = get_prop("sam-property-statemachine-statemachineschedule")
scheduledeadletterconfig = get_prop("sam-property-statemachine-statemachinescheduledeadletterconfig")
scheduleeventv2properties = get_prop("sam-property-statemachine-statemachineschedulev2")
resourcepolicy = get_prop("sam-property-statemachine-resourcepolicystatement")
cloudwatcheventproperties = get_prop("sam-property-statemachine-statemachinecloudwatchevent")
eventbridgeruleeventproperties = get_prop("sam-property-statemachine-statemachineeventbridgerule")
apieventproperties = get_prop("sam-property-statemachine-statemachineapi")
apiauth = get_prop("sam-property-statemachine-apistatemachineauth")
event = get_prop("sam-property-statemachine-statemachineeventsource")


class DeadLetterConfig(BaseModel):
    Arn: Optional[PassThrough] = deadletterconfig("Arn")
    QueueLogicalId: Optional[str] = deadletterconfig("QueueLogicalId")
    Type: Optional[Literal["SQS"]] = deadletterconfig("Type")


class ScheduleTarget(BaseModel):
    Id: PassThrough  # TODO: Add docs


class ScheduleEventProperties(BaseModel):
    DeadLetterConfig: Optional[DeadLetterConfig] = scheduleeventproperties("DeadLetterConfig")
    Description: Optional[PassThrough] = scheduleeventproperties("Description")
    Enabled: Optional[bool] = scheduleeventproperties("Enabled")
    Input: Optional[PassThrough] = scheduleeventproperties("Input")
    Name: Optional[PassThrough] = scheduleeventproperties("Name")
    RetryPolicy: Optional[PassThrough] = scheduleeventproperties("RetryPolicy")
    Schedule: Optional[PassThrough] = scheduleeventproperties("Schedule")
    State: Optional[PassThrough] = scheduleeventproperties("State")
    Target: Optional[ScheduleTarget]  # TODO: Add docs


class ScheduleEvent(BaseModel):
    Type: Literal["Schedule"] = event("Type")
    Properties: ScheduleEventProperties = event("Properties")


class ScheduleV2EventProperties(BaseModel):
    DeadLetterConfig: Optional[DeadLetterConfig] = scheduleeventv2properties("DeadLetterConfig")
    Description: Optional[PassThrough] = scheduleeventv2properties("Description")
    EndDate: Optional[PassThrough] = scheduleeventv2properties("EndDate")
    FlexibleTimeWindow: Optional[PassThrough] = scheduleeventv2properties("FlexibleTimeWindow")
    GroupName: Optional[PassThrough] = scheduleeventv2properties("GroupName")
    Input: Optional[PassThrough] = scheduleeventv2properties("Input")
    KmsKeyArn: Optional[PassThrough] = scheduleeventv2properties("KmsKeyArn")
    Name: Optional[PassThrough] = scheduleeventv2properties("Name")
    PermissionsBoundary: Optional[PassThrough] = scheduleeventv2properties("PermissionsBoundary")
    RetryPolicy: Optional[PassThrough] = scheduleeventv2properties("RetryPolicy")
    RoleArn: Optional[PassThrough]  # TODO: Add to docs
    ScheduleExpression: Optional[PassThrough] = scheduleeventv2properties("ScheduleExpression")
    ScheduleExpressionTimezone: Optional[PassThrough] = scheduleeventv2properties("ScheduleExpressionTimezone")
    StartDate: Optional[PassThrough] = scheduleeventv2properties("StartDate")
    State: Optional[PassThrough] = scheduleeventv2properties("State")


class ScheduleV2Event(BaseModel):
    Type: Literal["ScheduleV2"] = event("Type")
    Properties: ScheduleV2EventProperties = event("Properties")


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


class CloudWatchEventProperties(BaseModel):
    EventBusName: Optional[PassThrough] = cloudwatcheventproperties("EventBusName")
    Input: Optional[PassThrough] = cloudwatcheventproperties("Input")
    InputPath: Optional[PassThrough] = cloudwatcheventproperties("InputPath")
    Pattern: Optional[PassThrough] = cloudwatcheventproperties("Pattern")


class CloudWatchEvent(BaseModel):
    Type: Literal["CloudWatchEvent"] = event("Type")
    Properties: CloudWatchEventProperties = event("Properties")


class EventBridgeRuleTarget(BaseModel):
    Id: PassThrough  # TODO: Add docs


class EventBridgeRuleEventProperties(BaseModel):
    DeadLetterConfig: Optional[DeadLetterConfig] = eventbridgeruleeventproperties("DeadLetterConfig")
    EventBusName: Optional[PassThrough] = eventbridgeruleeventproperties("EventBusName")
    Input: Optional[PassThrough] = eventbridgeruleeventproperties("Input")
    InputPath: Optional[PassThrough] = eventbridgeruleeventproperties("InputPath")
    Pattern: Optional[PassThrough] = eventbridgeruleeventproperties("Pattern")
    RetryPolicy: Optional[PassThrough] = eventbridgeruleeventproperties("RetryPolicy")
    Target: Optional[EventBridgeRuleTarget]  # TODO: Add docs


class EventBridgeRuleEvent(BaseModel):
    Type: Literal["EventBridgeRule"] = event("Type")
    Properties: EventBridgeRuleEventProperties = event("Properties")


class Auth(BaseModel):
    ApiKeyRequired: Optional[bool] = apiauth("ApiKeyRequired")
    AuthorizationScopes: Optional[List[str]] = apiauth("AuthorizationScopes")
    Authorizer: Optional[str] = apiauth("Authorizer")
    ResourcePolicy: Optional[ResourcePolicy] = apiauth("ResourcePolicy")


class ApiEventProperties(BaseModel):
    Auth: Optional[Auth] = apieventproperties("Auth")
    Method: str = apieventproperties("Method")
    Path: str = apieventproperties("Path")
    RestApiId: Optional[SamIntrinsicable[str]] = apieventproperties("RestApiId")
    UnescapeMappingTemplate: Optional[bool]  # TODO: Add to docs


class ApiEvent(BaseModel):
    Type: Literal["Api"] = event("Type")
    Properties: ApiEventProperties = event("Properties")


class Properties(BaseModel):
    Definition: Optional[DictStrAny] = properties("Definition")
    DefinitionSubstitutions: Optional[DictStrAny] = properties("DefinitionSubstitutions")
    DefinitionUri: Optional[Union[str, PassThrough]] = properties("DefinitionUri")
    Events: Optional[
        Dict[
            str,
            Union[
                ScheduleEvent,
                ScheduleV2Event,
                CloudWatchEvent,
                EventBridgeRuleEvent,
                ApiEvent,
            ],
        ]
    ] = properties("Events")
    Logging: Optional[PassThrough] = properties("Logging")
    Name: Optional[PassThrough] = properties("Name")
    PermissionsBoundary: Optional[PassThrough] = properties("PermissionsBoundary")
    Policies: Optional[Union[str, DictStrAny, List[Union[str, DictStrAny]]]] = properties("Policies")
    Role: Optional[PassThrough] = properties("Role")
    RolePath: Optional[PassThrough]  # TODO: Add docs
    Tags: Optional[DictStrAny] = properties("Tags")
    Tracing: Optional[PassThrough] = properties("Tracing")
    Type: Optional[PassThrough] = properties("Type")


class Resource(BaseModel):
    Type: Literal["AWS::Serverless::StateMachine"]
    Properties: Properties
    Condition: Optional[PassThrough]
