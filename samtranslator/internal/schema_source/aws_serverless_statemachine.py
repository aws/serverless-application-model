from __future__ import annotations

from typing import Literal, Union

from samtranslator.internal.schema_source.aws_serverless_connector import EmbeddedConnector
from samtranslator.internal.schema_source.common import (
    BaseModel,
    DictStrAny,
    PassThroughProp,
    ResourceAttributes,
    SamIntrinsicable,
    get_prop,
    passthrough_prop,
)

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
scheduletarget = get_prop("sam-property-statemachine-statemachinescheduletarget")
eventtarget = get_prop("sam-property-statemachine-statemachinetarget")


class DeadLetterConfig(BaseModel):
    Arn: PassThroughProp | None = deadletterconfig("Arn")
    QueueLogicalId: str | None = deadletterconfig("QueueLogicalId")
    Type: Literal["SQS"] | None = deadletterconfig("Type")


class ScheduleTarget(BaseModel):
    Id: PassThroughProp = scheduletarget("Id")


class ScheduleEventProperties(BaseModel):
    DeadLetterConfig: DeadLetterConfig | None = scheduleeventproperties("DeadLetterConfig")
    Description: PassThroughProp | None = scheduleeventproperties("Description")
    Enabled: bool | None = scheduleeventproperties("Enabled")
    Input: PassThroughProp | None = scheduleeventproperties("Input")
    Name: PassThroughProp | None = scheduleeventproperties("Name")
    RetryPolicy: PassThroughProp | None = scheduleeventproperties("RetryPolicy")
    Schedule: PassThroughProp | None = scheduleeventproperties("Schedule")
    State: PassThroughProp | None = scheduleeventproperties("State")
    Target: ScheduleTarget | None = scheduleeventproperties("Target")
    RoleArn: PassThroughProp | None = passthrough_prop(
        "sam-property-statemachine-statemachineschedule",
        "RoleArn",
        ["AWS::Scheduler::Schedule.Target", "RoleArn"],
    )


class ScheduleEvent(BaseModel):
    Type: Literal["Schedule"] = event("Type")
    Properties: ScheduleEventProperties = event("Properties")


class ScheduleV2EventProperties(BaseModel):
    DeadLetterConfig: DeadLetterConfig | None = scheduleeventv2properties("DeadLetterConfig")
    Description: PassThroughProp | None = scheduleeventv2properties("Description")
    EndDate: PassThroughProp | None = scheduleeventv2properties("EndDate")
    FlexibleTimeWindow: PassThroughProp | None = scheduleeventv2properties("FlexibleTimeWindow")
    GroupName: PassThroughProp | None = scheduleeventv2properties("GroupName")
    Input: PassThroughProp | None = scheduleeventv2properties("Input")
    KmsKeyArn: PassThroughProp | None = scheduleeventv2properties("KmsKeyArn")
    Name: PassThroughProp | None = scheduleeventv2properties("Name")
    PermissionsBoundary: PassThroughProp | None = scheduleeventv2properties("PermissionsBoundary")
    RetryPolicy: PassThroughProp | None = scheduleeventv2properties("RetryPolicy")
    RoleArn: PassThroughProp | None = scheduleeventv2properties("RoleArn")
    ScheduleExpression: PassThroughProp | None = scheduleeventv2properties("ScheduleExpression")
    ScheduleExpressionTimezone: PassThroughProp | None = scheduleeventv2properties("ScheduleExpressionTimezone")
    StartDate: PassThroughProp | None = scheduleeventv2properties("StartDate")
    State: PassThroughProp | None = scheduleeventv2properties("State")
    OmitName: bool | None = scheduleeventv2properties("OmitName")


class ScheduleV2Event(BaseModel):
    Type: Literal["ScheduleV2"] = event("Type")
    Properties: ScheduleV2EventProperties = event("Properties")


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


class CloudWatchEventProperties(BaseModel):
    EventBusName: PassThroughProp | None = cloudwatcheventproperties("EventBusName")
    Input: PassThroughProp | None = cloudwatcheventproperties("Input")
    InputPath: PassThroughProp | None = cloudwatcheventproperties("InputPath")
    Pattern: PassThroughProp | None = cloudwatcheventproperties("Pattern")


class CloudWatchEvent(BaseModel):
    Type: Literal["CloudWatchEvent"] = event("Type")
    Properties: CloudWatchEventProperties = event("Properties")


class EventBridgeRuleTarget(BaseModel):
    Id: PassThroughProp = eventtarget("Id")


class EventBridgeRuleEventProperties(BaseModel):
    DeadLetterConfig: DeadLetterConfig | None = eventbridgeruleeventproperties("DeadLetterConfig")
    EventBusName: PassThroughProp | None = eventbridgeruleeventproperties("EventBusName")
    Input: PassThroughProp | None = eventbridgeruleeventproperties("Input")
    InputPath: PassThroughProp | None = eventbridgeruleeventproperties("InputPath")
    Pattern: PassThroughProp | None = eventbridgeruleeventproperties("Pattern")
    RetryPolicy: PassThroughProp | None = eventbridgeruleeventproperties("RetryPolicy")
    Target: EventBridgeRuleTarget | None = eventbridgeruleeventproperties("Target")
    RuleName: PassThroughProp | None = eventbridgeruleeventproperties("RuleName")
    InputTransformer: PassThroughProp | None = passthrough_prop(
        "sam-property-statemachine-statemachineeventbridgerule",
        "InputTransformer",
        ["AWS::Events::Rule.Target", "InputTransformer"],
    )


class EventBridgeRuleEvent(BaseModel):
    Type: Literal["EventBridgeRule"] = event("Type")
    Properties: EventBridgeRuleEventProperties = event("Properties")


class Auth(BaseModel):
    ApiKeyRequired: bool | None = apiauth("ApiKeyRequired")
    AuthorizationScopes: list[str] | None = apiauth("AuthorizationScopes")
    Authorizer: str | None = apiauth("Authorizer")
    ResourcePolicy: ResourcePolicy | None = apiauth("ResourcePolicy")


class ApiEventProperties(BaseModel):
    Auth: Auth | None = apieventproperties("Auth")
    Method: str = apieventproperties("Method")
    Path: str = apieventproperties("Path")
    RestApiId: SamIntrinsicable[str] | None = apieventproperties("RestApiId")
    UnescapeMappingTemplate: bool | None = apieventproperties("UnescapeMappingTemplate")


class ApiEvent(BaseModel):
    Type: Literal["Api"] = event("Type")
    Properties: ApiEventProperties = event("Properties")


class Properties(BaseModel):
    Definition: DictStrAny | None = properties("Definition")
    DefinitionSubstitutions: DictStrAny | None = properties("DefinitionSubstitutions")
    DefinitionUri: Union[str, PassThroughProp] | None = properties("DefinitionUri")
    Events: dict[str, Union[ScheduleEvent, ScheduleV2Event, CloudWatchEvent, EventBridgeRuleEvent, ApiEvent]] | None = (
        properties("Events")
    )
    Logging: PassThroughProp | None = properties("Logging")
    Name: PassThroughProp | None = properties("Name")
    PermissionsBoundary: PassThroughProp | None = properties("PermissionsBoundary")
    Policies: Union[str, DictStrAny, list[Union[str, DictStrAny]]] | None = properties("Policies")
    Role: PassThroughProp | None = properties("Role")
    RolePath: PassThroughProp | None = properties("RolePath")
    Tags: DictStrAny | None = properties("Tags")
    PropagateTags: bool | None = properties("PropagateTags")
    Tracing: PassThroughProp | None = properties("Tracing")
    Type: PassThroughProp | None = properties("Type")
    AutoPublishAlias: PassThroughProp | None
    DeploymentPreference: PassThroughProp | None
    UseAliasAsEventTarget: bool | None


class Resource(ResourceAttributes):
    Type: Literal["AWS::Serverless::StateMachine"]
    Properties: Properties
    Connectors: dict[str, EmbeddedConnector] | None


class Globals(BaseModel):
    PropagateTags: bool | None = properties("PropagateTags")
