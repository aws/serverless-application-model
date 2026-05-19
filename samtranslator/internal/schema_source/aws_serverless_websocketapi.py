from __future__ import annotations

from typing import Literal

from samtranslator.internal.schema_source.common import (
    BaseModel,
    DictStrAny,
    PassThroughProp,
    ResourceAttributes,
    SamIntrinsicable,
    get_prop,
)

# TODO add docs

auth_spec = get_prop("sam-property-websocketapi-authconfiguration")
route_spec = get_prop("sam-property-websocketapi-routeconfiguration")
route53 = get_prop("sam-property-gatewayv2-route53configuration")
domain = get_prop("sam-property-gatewayv2-domainconfiguration")
properties = get_prop("sam-resource-websocketapi")

"""
Route53 and Domain are the exact same as in httpapi, which is why their get_prop refers to gatewayv2,
but implementing this for the underlying schema causes a failure when make schema checks to see if resources
are subclasses of the generator they're under, so they stay distinct for now.
"""


class Route53(BaseModel):
    EvaluateTargetHealth: PassThroughProp | None = route53("EvaluateTargetHealth")
    HostedZoneId: PassThroughProp | None = route53("HostedZoneId")
    HostedZoneName: PassThroughProp | None = route53("HostedZoneName")
    IpV6: bool | None = route53("IpV6")
    Region: PassThroughProp | None = route53("Region")
    SetIdentifier: PassThroughProp | None = route53("SetIdentifier")


class Domain(BaseModel):
    BasePath: list[str] | None = domain("BasePath")
    CertificateArn: PassThroughProp = domain("CertificateArn")
    DomainName: PassThroughProp = domain("DomainName")
    EndpointConfiguration: SamIntrinsicable[Literal["REGIONAL"]] | None = domain("EndpointConfiguration")
    MutualTlsAuthentication: PassThroughProp | None = domain("MutualTlsAuthentication")
    OwnershipVerificationCertificateArn: PassThroughProp | None = domain("OwnershipVerificationCertificateArn")
    Route53: Route53 | None = domain("Route53")
    SecurityPolicy: PassThroughProp | None = domain("SecurityPolicy")


class AuthConfig(BaseModel):
    AuthArn: SamIntrinsicable[str] | None = auth_spec("AuthArn")
    AuthType: PassThroughProp = auth_spec("AuthType")
    InvokeRole: SamIntrinsicable[str] | None = auth_spec("InvokeRole")
    IdentitySource: PassThroughProp | None = auth_spec("IdentitySource")
    Name: PassThroughProp | None = auth_spec("Name")


class WebSocketApiRoute(BaseModel):
    ApiKeyRequired: PassThroughProp | None = route_spec("ApiKeyRequired")
    FunctionArn: SamIntrinsicable[str] = route_spec("FunctionArn")
    IntegrationTimeout: PassThroughProp | None = route_spec("IntegrationTimeout")
    ModelSelectionExpression: PassThroughProp | None = route_spec("ModelSelectionExpression")
    OperationName: PassThroughProp | None = route_spec("OperationName")
    RequestModels: PassThroughProp | None = route_spec("RequestModels")
    RequestParameters: PassThroughProp | None = route_spec("RequestParameters")
    RouteResponseSelectionExpression: PassThroughProp | None = route_spec("RouteResponseSelectionExpression")


ApiKeySelectionExpression = PassThroughProp | None
AccessLogSettings = PassThroughProp | None
DefaultRouteSettings = PassThroughProp | None
IpAddressType = PassThroughProp | None
RouteSettings = PassThroughProp | None
RouteSelectionExpression = PassThroughProp | None
StageVariables = PassThroughProp | None
Tags = DictStrAny | None


class Properties(BaseModel):
    ApiKeySelectionExpression: PassThroughProp | None = properties("ApiKeySelectionExpression")
    AccessLogSettings: AccessLogSettings | None = properties("AccessLogSettings")
    Auth: AuthConfig | None = properties("Auth")
    DefaultRouteSettings: RouteSettings | None = properties("DefaultRouteSettings")
    Description: str | None = properties("Description")
    DisableExecuteApiEndpoint: PassThroughProp | None = properties("DisableExecuteApiEndpoint")
    Domain: Domain | None = properties("Domain")
    DisableSchemaValidation: bool | None = properties("DisableSchemaValidation")
    IpAddressType: PassThroughProp | None = properties("IpAddressType")
    Name: PassThroughProp | None = properties("Name")
    PropagateTags: bool | None = properties("PropagateTags")
    Routes: dict[str, WebSocketApiRoute] = properties("Routes")
    RouteSelectionExpression: PassThroughProp = properties("RouteSelectionExpression")
    RouteSettings: RouteSettings | None = properties("RouteSettings")
    StageName: PassThroughProp | None = properties("StageName")
    StageVariables: StageVariables | None = properties("StageVariables")
    Tags: Tags | None = properties("Tags")


class Globals(BaseModel):
    ApiKeySelectionExpression: str | None = properties("ApiKeySelectionExpression")
    AccessLogSettings: AccessLogSettings | None = properties("AccessLogSettings")
    DefaultRouteSettings: RouteSettings | None = properties("DefaultRouteSettings")
    DisableExecuteApiEndpoint: bool | None = properties("DisableExecuteApiEndpoint")
    DisableSchemaValidation: bool | None = properties("DisableSchemaValidation")
    Domain: Domain | None = properties("Domain")
    IpAddressType: str | None = properties("IpAddressType")
    PropagateTags: bool | None = properties("PropagateTags")
    RouteSettings: RouteSettings | None = properties("RouteSettings")
    RouteSelectionExpression: str | None = properties("RouteSelectionExpression")
    StageVariables: StageVariables | None = properties("StageVariables")
    Tags: Tags | None = properties("Tags")


class Resource(ResourceAttributes):
    Type: Literal["AWS::Serverless::WebSocketApi"]
    Properties: Properties | None
