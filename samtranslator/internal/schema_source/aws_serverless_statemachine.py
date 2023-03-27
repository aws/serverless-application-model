from __future__ import annotations

from typing import Dict, List, Optional, Union

from typing_extensions import Literal

from samtranslator.internal.schema_source.aws_serverless_connector import EmbeddedConnector
from samtranslator.internal.schema_source.common import (
    BaseModel,
    DictStrAny,
    PassThroughProp,
    ResourceAttributes,
    SamIntrinsicable,
    get_prop,
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
    Arn: Optional[PassThroughProp] = deadletterconfig("Arn")
    QueueLogicalId: Optional[str] = deadletterconfig("QueueLogicalId")
    Type: Optional[Literal["SQS"]] = deadletterconfig("Type")


class ScheduleTarget(BaseModel):
    Id: PassThroughProp = scheduletarget("Id")


class ScheduleEventProperties(BaseModel):
    DeadLetterConfig: Optional[DeadLetterConfig] = scheduleeventproperties("DeadLetterConfig")
    Description: Optional[PassThroughProp] = scheduleeventproperties("Description")
    Enabled: Optional[bool] = scheduleeventproperties("Enabled")
    Input: Optional[PassThroughProp] = scheduleeventproperties("Input")
    Name: Optional[PassThroughProp] = scheduleeventproperties("Name")
    RetryPolicy: Optional[PassThroughProp] = scheduleeventproperties("RetryPolicy")
    Schedule: Optional[PassThroughProp] = scheduleeventproperties("Schedule")
    State: Optional[PassThroughProp] = scheduleeventproperties("State")
    Target: Optional[ScheduleTarget] = scheduleeventproperties("Target")


class ScheduleEvent(BaseModel):
    Type: Literal["Schedule"] = event("Type")
    Properties: ScheduleEventProperties = event("Properties")


class ScheduleV2EventProperties(BaseModel):
    DeadLetterConfig: Optional[DeadLetterConfig] = scheduleeventv2properties("DeadLetterConfig")
    Description: Optional[PassThroughProp] = scheduleeventv2properties("Description")
    EndDate: Optional[PassThroughProp] = scheduleeventv2properties("EndDate")
    FlexibleTimeWindow: Optional[PassThroughProp] = scheduleeventv2properties("FlexibleTimeWindow")
    GroupName: Optional[PassThroughProp] = scheduleeventv2properties("GroupName")
    Input: Optional[PassThroughProp] = scheduleeventv2properties("Input")
    KmsKeyArn: Optional[PassThroughProp] = scheduleeventv2properties("KmsKeyArn")
    Name: Optional[PassThroughProp] = scheduleeventv2properties("Name")
    PermissionsBoundary: Optional[PassThroughProp] = scheduleeventv2properties("PermissionsBoundary")
    RetryPolicy: Optional[PassThroughProp] = scheduleeventv2properties("RetryPolicy")
    RoleArn: Optional[PassThroughProp] = scheduleeventv2properties("RoleArn")
    ScheduleExpression: Optional[PassThroughProp] = scheduleeventv2properties("ScheduleExpression")
    ScheduleExpressionTimezone: Optional[PassThroughProp] = scheduleeventv2properties("ScheduleExpressionTimezone")
    StartDate: Optional[PassThroughProp] = scheduleeventv2properties("StartDate")
    State: Optional[PassThroughProp] = scheduleeventv2properties("State")


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
    EventBusName: Optional[PassThroughProp] = cloudwatcheventproperties("EventBusName")
    Input: Optional[PassThroughProp] = cloudwatcheventproperties("Input")
    InputPath: Optional[PassThroughProp] = cloudwatcheventproperties("InputPath")
    Pattern: Optional[PassThroughProp] = cloudwatcheventproperties("Pattern")


class CloudWatchEvent(BaseModel):
    Type: Literal["CloudWatchEvent"] = event("Type")
    Properties: CloudWatchEventProperties = event("Properties")


class EventBridgeRuleTarget(BaseModel):
    Id: PassThroughProp = eventtarget("Id")


class EventBridgeRuleEventProperties(BaseModel):
    DeadLetterConfig: Optional[DeadLetterConfig] = eventbridgeruleeventproperties("DeadLetterConfig")
    EventBusName: Optional[PassThroughProp] = eventbridgeruleeventproperties("EventBusName")
    Input: Optional[PassThroughProp] = eventbridgeruleeventproperties("Input")
    InputPath: Optional[PassThroughProp] = eventbridgeruleeventproperties("InputPath")
    Pattern: Optional[PassThroughProp] = eventbridgeruleeventproperties("Pattern")
    RetryPolicy: Optional[PassThroughProp] = eventbridgeruleeventproperties("RetryPolicy")
    Target: Optional[EventBridgeRuleTarget] = eventbridgeruleeventproperties("Target")


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
    UnescapeMappingTemplate: Optional[bool] = apieventproperties("UnescapeMappingTemplate")


class ApiEvent(BaseModel):
    Type: Literal["Api"] = event("Type")
    Properties: ApiEventProperties = event("Properties")


class Properties(BaseModel):
    Definition: Optional[DictStrAny] = properties("Definition")
    DefinitionSubstitutions: Optional[DictStrAny] = properties("DefinitionSubstitutions")
    DefinitionUri: Optional[Union[str, PassThroughProp]] = properties("DefinitionUri")
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
    Logging: Optional[PassThroughProp] = properties("Logging")
    Name: Optional[PassThroughProp] = properties("Name")
    PermissionsBoundary: Optional[PassThroughProp] = properties("PermissionsBoundary")
    Policies: Optional[Union[str, DictStrAny, List[Union[str, DictStrAny]]]] = properties("Policies")
    Role: Optional[PassThroughProp] = properties("Role")
    RolePath: Optional[PassThroughProp] = properties("RolePath")
    Tags: Optional[DictStrAny] = properties("Tags")
    Tracing: Optional[PassThroughProp] = properties("Tracing")
    Type: Optional[PassThroughProp] = properties("Type")


class Resource(ResourceAttributes):
    Type: Literal["AWS::Serverless::StateMachine"]
    Properties: Properties
    Connectors: Optional[Dict[str, EmbeddedConnector]]
