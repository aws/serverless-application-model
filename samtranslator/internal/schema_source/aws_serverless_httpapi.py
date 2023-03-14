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
    AuthorizationScopes: Optional[List[str]] = oauth2authorizer("AuthorizationScopes")
    IdentitySource: Optional[str] = oauth2authorizer("IdentitySource")
    JwtConfiguration: Optional[PassThroughProp] = oauth2authorizer("JwtConfiguration")


class LambdaAuthorizerIdentity(BaseModel):
    Context: Optional[List[str]] = lambdauthorizeridentity("Context")
    Headers: Optional[List[str]] = lambdauthorizeridentity("Headers")
    QueryStrings: Optional[List[str]] = lambdauthorizeridentity("QueryStrings")
    ReauthorizeEvery: Optional[int] = lambdauthorizeridentity("ReauthorizeEvery")
    StageVariables: Optional[List[str]] = lambdauthorizeridentity("StageVariables")


class LambdaAuthorizer(BaseModel):
    # TODO: Many tests use floats for the version string; docs only mention string
    AuthorizerPayloadFormatVersion: Union[Literal["1.0", "2.0"], float] = lambdaauthorizer(
        "AuthorizerPayloadFormatVersion"
    )
    EnableSimpleResponses: Optional[bool] = lambdaauthorizer("EnableSimpleResponses")
    FunctionArn: SamIntrinsicable[str] = lambdaauthorizer("FunctionArn")
    FunctionInvokeRole: Optional[SamIntrinsicable[str]] = lambdaauthorizer("FunctionInvokeRole")
    EnableFunctionDefaultPermissions: Optional[bool]  # TODO: add docs
    Identity: Optional[LambdaAuthorizerIdentity] = lambdaauthorizer("Identity")


class Auth(BaseModel):
    # TODO: Docs doesn't say it's a map
    Authorizers: Optional[
        Dict[
            str,
            Union[
                OAuth2Authorizer,
                LambdaAuthorizer,
            ],
        ]
    ] = auth("Authorizers")
    DefaultAuthorizer: Optional[str] = auth("DefaultAuthorizer")
    EnableIamAuthorizer: Optional[bool] = auth("EnableIamAuthorizer")


class CorsConfiguration(BaseModel):
    AllowCredentials: Optional[bool] = corsconfiguration("AllowCredentials")
    AllowHeaders: Optional[List[str]] = corsconfiguration("AllowHeaders")
    AllowMethods: Optional[List[str]] = corsconfiguration("AllowMethods")
    AllowOrigins: Optional[List[str]] = corsconfiguration("AllowOrigins")
    ExposeHeaders: Optional[List[str]] = corsconfiguration("ExposeHeaders")
    MaxAge: Optional[int] = corsconfiguration("MaxAge")


class DefinitionUri(BaseModel):
    Bucket: str = definitionuri("Bucket")
    Key: str = definitionuri("Key")
    Version: Optional[str] = definitionuri("Version")


class Route53(BaseModel):
    DistributionDomainName: Optional[PassThroughProp] = route53("DistributionDomainName")
    EvaluateTargetHealth: Optional[PassThroughProp] = route53("EvaluateTargetHealth")
    HostedZoneId: Optional[PassThroughProp] = route53("HostedZoneId")
    HostedZoneName: Optional[PassThroughProp] = route53("HostedZoneName")
    IpV6: Optional[bool] = route53("IpV6")
    SetIdentifier: Optional[PassThroughProp]  # TODO: add docs
    Region: Optional[PassThroughProp]  # TODO: add docs


class Domain(BaseModel):
    BasePath: Optional[List[str]] = domain("BasePath")
    CertificateArn: PassThroughProp = domain("CertificateArn")
    DomainName: PassThroughProp = domain("DomainName")
    EndpointConfiguration: Optional[SamIntrinsicable[Literal["REGIONAL"]]] = domain("EndpointConfiguration")
    MutualTlsAuthentication: Optional[PassThroughProp] = domain("MutualTlsAuthentication")
    OwnershipVerificationCertificateArn: Optional[PassThroughProp] = domain("OwnershipVerificationCertificateArn")
    Route53: Optional[Route53] = domain("Route53")
    SecurityPolicy: Optional[PassThroughProp] = domain("SecurityPolicy")


AccessLogSettings = Optional[PassThroughProp]
StageVariables = Optional[PassThroughProp]
Tags = Optional[DictStrAny]
RouteSettings = Optional[PassThroughProp]
FailOnWarnings = Optional[PassThroughProp]
CorsConfigurationType = Optional[PassThroughProp]
DefaultRouteSettings = Optional[PassThroughProp]


class Properties(BaseModel):
    AccessLogSettings: Optional[AccessLogSettings] = properties("AccessLogSettings")
    Auth: Optional[Auth] = properties("Auth")
    # TODO: Also string like in the docs?
    CorsConfiguration: Optional[CorsConfigurationType] = properties("CorsConfiguration")
    DefaultRouteSettings: Optional[DefaultRouteSettings] = properties("DefaultRouteSettings")
    DefinitionBody: Optional[DictStrAny] = properties("DefinitionBody")
    DefinitionUri: Optional[Union[str, DefinitionUri]] = properties("DefinitionUri")
    Description: Optional[str] = properties("Description")
    DisableExecuteApiEndpoint: Optional[PassThroughProp] = properties("DisableExecuteApiEndpoint")
    Domain: Optional[Domain] = properties("Domain")
    FailOnWarnings: Optional[FailOnWarnings] = properties("FailOnWarnings")
    RouteSettings: Optional[RouteSettings] = properties("RouteSettings")
    StageName: Optional[PassThroughProp] = properties("StageName")
    StageVariables: Optional[StageVariables] = properties("StageVariables")
    Tags: Optional[Tags] = properties("Tags")
    Name: Optional[PassThroughProp] = properties("Name")


class Globals(BaseModel):
    Auth: Optional[Auth] = properties("Auth")
    AccessLogSettings: Optional[AccessLogSettings] = properties("AccessLogSettings")
    StageVariables: Optional[StageVariables] = properties("StageVariables")
    Tags: Optional[Tags] = properties("Tags")
    RouteSettings: Optional[RouteSettings] = properties("RouteSettings")
    FailOnWarnings: Optional[FailOnWarnings] = properties("FailOnWarnings")
    Domain: Optional[Domain] = properties("Domain")
    CorsConfiguration: Optional[CorsConfigurationType] = properties("CorsConfiguration")
    DefaultRouteSettings: Optional[DefaultRouteSettings] = properties("DefaultRouteSettings")


class Resource(ResourceAttributes):
    Type: Literal["AWS::Serverless::HttpApi"]
    Properties: Optional[Properties]
    Connectors: Optional[Dict[str, EmbeddedConnector]]
