from __future__ import annotations

from typing import Optional, Dict, Union, List

from typing_extensions import Literal

from samtranslator.schema.common import PassThrough, BaseModel, SamIntrinsicable, get_prop, DictStrAny

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
    JwtConfiguration: Optional[PassThrough] = oauth2authorizer("JwtConfiguration")


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
    DistributionDomainName: Optional[PassThrough] = route53("DistributionDomainName")
    EvaluateTargetHealth: Optional[PassThrough] = route53("EvaluateTargetHealth")
    HostedZoneId: Optional[PassThrough] = route53("HostedZoneId")
    HostedZoneName: Optional[PassThrough] = route53("HostedZoneName")
    IpV6: Optional[bool] = route53("IpV6")


class Domain(BaseModel):
    BasePath: Optional[List[str]] = domain("BasePath")
    CertificateArn: PassThrough = domain("CertificateArn")
    DomainName: PassThrough = domain("DomainName")
    EndpointConfiguration: Optional[SamIntrinsicable[Literal["REGIONAL"]]] = domain("EndpointConfiguration")
    MutualTlsAuthentication: Optional[PassThrough] = domain("MutualTlsAuthentication")
    OwnershipVerificationCertificateArn: Optional[PassThrough] = domain("OwnershipVerificationCertificateArn")
    Route53: Optional[Route53] = domain("Route53")
    SecurityPolicy: Optional[PassThrough] = domain("SecurityPolicy")


AccessLogSettings = Optional[PassThrough]
StageVariables = Optional[PassThrough]
Tags = Optional[DictStrAny]
RouteSettings = Optional[PassThrough]
FailOnWarnings = Optional[PassThrough]
CorsConfigurationType = Optional[PassThrough]
DefaultRouteSettings = Optional[PassThrough]


class Properties(BaseModel):
    AccessLogSettings: Optional[AccessLogSettings] = properties("AccessLogSettings")
    Auth: Optional[Auth] = properties("Auth")
    # TODO: Also string like in the docs?
    CorsConfiguration: Optional[CorsConfigurationType] = properties("CorsConfiguration")
    DefaultRouteSettings: Optional[DefaultRouteSettings] = properties("DefaultRouteSettings")
    DefinitionBody: Optional[DictStrAny] = properties("DefinitionBody")
    DefinitionUri: Optional[Union[str, DefinitionUri]] = properties("DefinitionUri")
    Description: Optional[str] = properties("Description")
    DisableExecuteApiEndpoint: Optional[PassThrough] = properties("DisableExecuteApiEndpoint")
    Domain: Optional[Domain] = properties("Domain")
    FailOnWarnings: Optional[FailOnWarnings] = properties("FailOnWarnings")
    RouteSettings: Optional[RouteSettings] = properties("RouteSettings")
    StageName: Optional[PassThrough] = properties("StageName")
    StageVariables: Optional[StageVariables] = properties("StageVariables")
    Tags: Optional[Tags] = properties("Tags")
    Name: Optional[PassThrough]  # TODO: Add to docs


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


class Resource(BaseModel):
    Type: Literal["AWS::Serverless::HttpApi"]
    Properties: Optional[Properties]
    Metadata: Optional[PassThrough]
    Condition: Optional[PassThrough]
