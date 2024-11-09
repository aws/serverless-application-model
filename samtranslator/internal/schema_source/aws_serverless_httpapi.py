from __future__ import annotations

from typing import Dict, List, Literal, Optional, Union

from samtranslator.internal.schema_source.aws_serverless_connector import EmbeddedConnector
from samtranslator.internal.schema_source.common import (
    BaseModel,
    DictStrAny,
    PassThroughProp,
    ResourceAttributes,
    SamIntrinsicable,
    get_prop,
)

oauth2authorizer = get_prop("sam-property-httpapi-oauth2authorizer")
lambdauthorizeridentity = get_prop("sam-property-httpapi-lambdaauthorizationidentity")
lambdaauthorizer = get_prop("sam-property-httpapi-lambdaauthorizer")
auth = get_prop("sam-property-httpapi-httpapiauth")
corsconfiguration = get_prop("sam-property-httpapi-httpapicorsconfiguration")
definitionuri = get_prop("sam-property-httpapi-httpapidefinition")
route53 = get_prop("sam-property-httpapi-route53configuration")
domain = get_prop("sam-property-httpapi-httpapidomainconfiguration")
properties = get_prop("sam-resource-httpapi")


class OAuth2Authorizer(BaseModel):
    AuthorizationScopes: list[str] | None = oauth2authorizer("AuthorizationScopes")
    IdentitySource: str | None = oauth2authorizer("IdentitySource")
    JwtConfiguration: PassThroughProp | None = oauth2authorizer("JwtConfiguration")


class LambdaAuthorizerIdentity(BaseModel):
    Context: list[str] | None = lambdauthorizeridentity("Context")
    Headers: list[str] | None = lambdauthorizeridentity("Headers")
    QueryStrings: list[str] | None = lambdauthorizeridentity("QueryStrings")
    ReauthorizeEvery: int | None = lambdauthorizeridentity("ReauthorizeEvery")
    StageVariables: list[str] | None = lambdauthorizeridentity("StageVariables")


class LambdaAuthorizer(BaseModel):
    # TODO: Many tests use floats for the version string; docs only mention string
    AuthorizerPayloadFormatVersion: Literal["1.0", "2.0"] | float = lambdaauthorizer(
        "AuthorizerPayloadFormatVersion"
    )
    EnableSimpleResponses: bool | None = lambdaauthorizer("EnableSimpleResponses")
    FunctionArn: SamIntrinsicable[str] = lambdaauthorizer("FunctionArn")
    FunctionInvokeRole: SamIntrinsicable[str] | None = lambdaauthorizer("FunctionInvokeRole")
    EnableFunctionDefaultPermissions: bool | None  # TODO: add docs
    Identity: LambdaAuthorizerIdentity | None = lambdaauthorizer("Identity")


class Auth(BaseModel):
    # TODO: Docs doesn't say it's a map
    Authorizers: None | (
        dict[
            str,
            (
                OAuth2Authorizer |
                LambdaAuthorizer
            ),
        ]
    ) = auth("Authorizers")
    DefaultAuthorizer: str | None = auth("DefaultAuthorizer")
    EnableIamAuthorizer: bool | None = auth("EnableIamAuthorizer")


class CorsConfiguration(BaseModel):
    AllowCredentials: bool | None = corsconfiguration("AllowCredentials")
    AllowHeaders: list[str] | None = corsconfiguration("AllowHeaders")
    AllowMethods: list[str] | None = corsconfiguration("AllowMethods")
    AllowOrigins: list[str] | None = corsconfiguration("AllowOrigins")
    ExposeHeaders: list[str] | None = corsconfiguration("ExposeHeaders")
    MaxAge: int | None = corsconfiguration("MaxAge")


class DefinitionUri(BaseModel):
    Bucket: str = definitionuri("Bucket")
    Key: str = definitionuri("Key")
    Version: str | None = definitionuri("Version")


class Route53(BaseModel):
    DistributionDomainName: PassThroughProp | None = route53("DistributionDomainName")
    EvaluateTargetHealth: PassThroughProp | None = route53("EvaluateTargetHealth")
    HostedZoneId: PassThroughProp | None = route53("HostedZoneId")
    HostedZoneName: PassThroughProp | None = route53("HostedZoneName")
    IpV6: bool | None = route53("IpV6")
    SetIdentifier: PassThroughProp | None  # TODO: add docs
    Region: PassThroughProp | None  # TODO: add docs


class Domain(BaseModel):
    BasePath: list[str] | None = domain("BasePath")
    CertificateArn: PassThroughProp = domain("CertificateArn")
    DomainName: PassThroughProp = domain("DomainName")
    EndpointConfiguration: SamIntrinsicable[Literal["REGIONAL"]] | None = domain("EndpointConfiguration")
    MutualTlsAuthentication: PassThroughProp | None = domain("MutualTlsAuthentication")
    OwnershipVerificationCertificateArn: PassThroughProp | None = domain("OwnershipVerificationCertificateArn")
    Route53: Route53 | None = domain("Route53")
    SecurityPolicy: PassThroughProp | None = domain("SecurityPolicy")


AccessLogSettings = Optional[PassThroughProp]
StageVariables = Optional[PassThroughProp]
Tags = Optional[DictStrAny]
RouteSettings = Optional[PassThroughProp]
FailOnWarnings = Optional[PassThroughProp]
CorsConfigurationType = Optional[PassThroughProp]
DefaultRouteSettings = Optional[PassThroughProp]


class Properties(BaseModel):
    AccessLogSettings: AccessLogSettings | None = properties("AccessLogSettings")
    Auth: Auth | None = properties("Auth")
    # TODO: Also string like in the docs?
    CorsConfiguration: CorsConfigurationType | None = properties("CorsConfiguration")
    DefaultRouteSettings: DefaultRouteSettings | None = properties("DefaultRouteSettings")
    DefinitionBody: DictStrAny | None = properties("DefinitionBody")
    DefinitionUri: str | DefinitionUri | None = properties("DefinitionUri")
    Description: str | None = properties("Description")
    DisableExecuteApiEndpoint: PassThroughProp | None = properties("DisableExecuteApiEndpoint")
    Domain: Domain | None = properties("Domain")
    FailOnWarnings: FailOnWarnings | None = properties("FailOnWarnings")
    RouteSettings: RouteSettings | None = properties("RouteSettings")
    StageName: PassThroughProp | None = properties("StageName")
    StageVariables: StageVariables | None = properties("StageVariables")
    Tags: Tags | None = properties("Tags")
    PropagateTags: bool | None  # TODO: add docs
    Name: PassThroughProp | None = properties("Name")


class Globals(BaseModel):
    Auth: Auth | None = properties("Auth")
    AccessLogSettings: AccessLogSettings | None = properties("AccessLogSettings")
    StageVariables: StageVariables | None = properties("StageVariables")
    Tags: Tags | None = properties("Tags")
    RouteSettings: RouteSettings | None = properties("RouteSettings")
    FailOnWarnings: FailOnWarnings | None = properties("FailOnWarnings")
    Domain: Domain | None = properties("Domain")
    CorsConfiguration: CorsConfigurationType | None = properties("CorsConfiguration")
    DefaultRouteSettings: DefaultRouteSettings | None = properties("DefaultRouteSettings")
    PropagateTags: bool | None  # TODO: add docs


class Resource(ResourceAttributes):
    Type: Literal["AWS::Serverless::HttpApi"]
    Properties: Properties | None
    Connectors: dict[str, EmbeddedConnector] | None
