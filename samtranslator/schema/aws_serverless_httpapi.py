from typing import Optional, Any, Dict, Union, List

from typing_extensions import Literal

from samtranslator.schema.common import PassThrough, BaseModel, SamIntrinsic


class OAuth2Authorizer(BaseModel):
    AuthorizationScopes: Optional[List[str]]
    IdentitySource: Optional[str]
    JwtConfiguration: Optional[PassThrough]


class LambdaAuthorizerIdentity(BaseModel):
    Context: Optional[List[str]]
    Headers: Optional[List[str]]
    QueryStrings: Optional[List[str]]
    ReauthorizeEvery: Optional[int]
    StageVariables: Optional[List[str]]


class LambdaAuthorizer(BaseModel):
    # TODO: Many tests use floats for the version string; docs only mention string
    AuthorizerPayloadFormatVersion: Union[Literal["1.0", "2.0"], float]
    EnableSimpleResponses: Optional[bool]
    FunctionArn: SamIntrinsic
    FunctionInvokeRole: Optional[Union[str, SamIntrinsic]]
    Identity: Optional[LambdaAuthorizerIdentity]


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
    ]
    DefaultAuthorizer: Optional[str]
    EnableIamAuthorizer: Optional[bool]


class CorsConfiguration(BaseModel):
    AllowCredentials: Optional[bool]
    AllowHeaders: Optional[List[str]]
    AllowMethods: Optional[List[str]]
    AllowOrigins: Optional[List[str]]
    ExposeHeaders: Optional[List[str]]
    MaxAge: Optional[int]


class DefinitionUri(BaseModel):
    Bucket: str
    Key: str
    Version: Optional[str]


class Route53(BaseModel):
    DistributionDomainName: Optional[PassThrough]
    EvaluateTargetHealth: Optional[PassThrough]
    HostedZoneId: Optional[PassThrough]
    HostedZoneName: Optional[PassThrough]
    IpV6: Optional[bool]


class Domain(BaseModel):
    BasePath: Optional[List[str]]
    CertificateArn: PassThrough
    DomainName: PassThrough
    EndpointConfiguration: Optional[Union[Literal["REGIONAL"], SamIntrinsic]]
    MutualTlsAuthentication: Optional[PassThrough]
    OwnershipVerificationCertificateArn: Optional[PassThrough]
    Route53: Optional[Route53]
    SecurityPolicy: Optional[PassThrough]


AccessLogSettings = Optional[PassThrough]
StageVariables = Optional[PassThrough]
Tags = Optional[Dict[str, Any]]
RouteSettings = Optional[PassThrough]
FailOnWarnings = Optional[PassThrough]
CorsConfigurationType = Optional[PassThrough]
DefaultRouteSettings = Optional[PassThrough]


class Properties(BaseModel):
    AccessLogSettings: Optional[AccessLogSettings]
    Auth: Optional[Auth]
    # TODO: Also string like in the docs?
    CorsConfiguration: Optional[CorsConfigurationType]
    DefaultRouteSettings: Optional[DefaultRouteSettings]
    DefinitionBody: Optional[Dict[str, Any]]
    DefinitionUri: Optional[Union[str, DefinitionUri]]
    Description: Optional[str]
    DisableExecuteApiEndpoint: Optional[PassThrough]
    Domain: Optional[Domain]
    FailOnWarnings: Optional[FailOnWarnings]
    RouteSettings: Optional[RouteSettings]
    StageName: Optional[PassThrough]
    StageVariables: Optional[StageVariables]
    Tags: Optional[Tags]
    Name: Optional[PassThrough]  # TODO: Add to docs


class Globals(BaseModel):
    Auth: Optional[Auth]
    AccessLogSettings: Optional[AccessLogSettings]
    StageVariables: Optional[StageVariables]
    Tags: Optional[Tags]
    RouteSettings: Optional[RouteSettings]
    FailOnWarnings: Optional[FailOnWarnings]
    Domain: Optional[Domain]
    CorsConfiguration: Optional[CorsConfigurationType]
    DefaultRouteSettings: Optional[DefaultRouteSettings]


class Resource(BaseModel):
    Type: Literal["AWS::Serverless::HttpApi"]
    Properties: Optional[Properties]
    Metadata: Optional[PassThrough]
    Condition: Optional[PassThrough]
