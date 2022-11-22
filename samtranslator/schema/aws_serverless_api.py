from typing import Optional, Any, Dict, Union, List

from typing_extensions import Literal

from samtranslator.schema.common import PassThrough, BaseModel, SamIntrinsic


class ResourcePolicy(BaseModel):
    AwsAccountBlacklist: Optional[List[Union[str, Dict[str, Any]]]]
    AwsAccountWhitelist: Optional[List[Union[str, Dict[str, Any]]]]
    CustomStatements: Optional[List[Union[str, Dict[str, Any]]]]
    IntrinsicVpcBlacklist: Optional[List[Union[str, Dict[str, Any]]]]
    IntrinsicVpcWhitelist: Optional[List[Union[str, Dict[str, Any]]]]
    IntrinsicVpceBlacklist: Optional[List[Union[str, Dict[str, Any]]]]
    IntrinsicVpceWhitelist: Optional[List[Union[str, Dict[str, Any]]]]
    IpRangeBlacklist: Optional[List[Union[str, Dict[str, Any]]]]
    IpRangeWhitelist: Optional[List[Union[str, Dict[str, Any]]]]
    SourceVpcBlacklist: Optional[List[Union[str, Dict[str, Any]]]]
    SourceVpcWhitelist: Optional[List[Union[str, Dict[str, Any]]]]


class CognitoAuthorizerIdentity(BaseModel):
    Header: Optional[str]
    ReauthorizeEvery: Optional[Union[int, SamIntrinsic]]
    ValidationExpression: Optional[str]


class CognitoAuthorizer(BaseModel):
    AuthorizationScopes: Optional[List[str]]
    Identity: Optional[CognitoAuthorizerIdentity]
    UserPoolArn: Union[str, SamIntrinsic]


class LambdaTokenAuthorizerIdentity(BaseModel):
    ReauthorizeEvery: Optional[Union[int, SamIntrinsic]]
    ValidationExpression: Optional[str]
    Header: Optional[
        str
    ]  # TODO: This doesn't exist in docs: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-property-api-lambdatokenauthorizationidentity.html


class LambdaRequestAuthorizerIdentity(BaseModel):
    Context: Optional[List[str]]
    Headers: Optional[List[str]]
    QueryStrings: Optional[List[str]]
    ReauthorizeEvery: Optional[Union[int, SamIntrinsic]]
    StageVariables: Optional[List[str]]


class LambdaTokenAuthorizer(BaseModel):
    AuthorizationScopes: Optional[List[str]]
    FunctionArn: Union[str, SamIntrinsic]
    FunctionInvokeRole: Optional[str]
    FunctionPayloadType: Optional[Literal["REQUEST", "TOKEN"]]
    Identity: Optional[LambdaTokenAuthorizerIdentity]


class LambdaRequestAuthorizer(BaseModel):
    AuthorizationScopes: Optional[List[str]]
    FunctionArn: Union[str, SamIntrinsic]
    FunctionInvokeRole: Optional[str]
    FunctionPayloadType: Optional[Literal["REQUEST", "TOKEN"]]
    Identity: Optional[LambdaRequestAuthorizerIdentity]


class UsagePlan(BaseModel):
    CreateUsagePlan: Union[Literal["PER_API", "SHARED", "NONE"], SamIntrinsic]
    Description: Optional[PassThrough]
    Quota: Optional[PassThrough]
    Tags: Optional[PassThrough]
    Throttle: Optional[PassThrough]
    UsagePlanName: Optional[PassThrough]


class Auth(BaseModel):
    AddDefaultAuthorizerToCorsPreflight: Optional[bool]
    ApiKeyRequired: Optional[bool]
    Authorizers: Optional[
        Dict[
            str,
            Union[
                CognitoAuthorizer,
                LambdaTokenAuthorizer,
                LambdaRequestAuthorizer,
            ],
        ]
    ]
    DefaultAuthorizer: Optional[str]
    InvokeRole: Optional[str]
    ResourcePolicy: Optional[ResourcePolicy]
    UsagePlan: Optional[UsagePlan]


class Cors(BaseModel):
    AllowCredentials: Optional[bool]
    AllowHeaders: Optional[str]
    AllowMethods: Optional[str]
    AllowOrigin: str
    MaxAge: Optional[str]


class Route53(BaseModel):
    DistributionDomainName: Optional[PassThrough]
    EvaluateTargetHealth: Optional[PassThrough]
    HostedZoneId: Optional[PassThrough]
    HostedZoneName: Optional[PassThrough]
    IpV6: Optional[bool]


class Domain(BaseModel):
    BasePath: Optional[PassThrough]
    CertificateArn: PassThrough
    DomainName: PassThrough
    EndpointConfiguration: Optional[Union[Literal["REGIONAL", "EDGE"], SamIntrinsic]]
    MutualTlsAuthentication: Optional[PassThrough]
    OwnershipVerificationCertificateArn: Optional[PassThrough]
    Route53: Optional[Route53]
    SecurityPolicy: Optional[PassThrough]


Name = Optional[PassThrough]
DefinitionUri = Optional[PassThrough]
CacheClusterEnabled = Optional[PassThrough]
CacheClusterSize = Optional[PassThrough]
Variables = Optional[PassThrough]
EndpointConfiguration = Optional[PassThrough]
MethodSettings = Optional[PassThrough]
BinaryMediaTypes = Optional[PassThrough]
MinimumCompressionSize = Optional[PassThrough]
CorsType = Optional[Union[str, SamIntrinsic, Cors]]
GatewayResponses = Optional[SamIntrinsic]
AccessLogSetting = Optional[PassThrough]
CanarySetting = Optional[PassThrough]
TracingEnabled = Optional[PassThrough]
OpenApiVersion = Optional[Union[float, str]]  # TODO: float doesn't exist in documentation


class Properties(BaseModel):
    AccessLogSetting: Optional[AccessLogSetting]
    ApiKeySourceType: Optional[PassThrough]
    Auth: Optional[Auth]
    BinaryMediaTypes: Optional[BinaryMediaTypes]
    CacheClusterEnabled: Optional[CacheClusterEnabled]
    CacheClusterSize: Optional[CacheClusterSize]
    CanarySetting: Optional[CanarySetting]
    Cors: Optional[CorsType]
    DefinitionBody: Optional[PassThrough]
    DefinitionUri: Optional[DefinitionUri]
    Description: Optional[PassThrough]
    DisableExecuteApiEndpoint: Optional[PassThrough]
    Domain: Optional[Domain]
    EndpointConfiguration: Optional[EndpointConfiguration]
    FailOnWarnings: Optional[PassThrough]
    GatewayResponses: Optional[GatewayResponses]
    MethodSettings: Optional[MethodSettings]
    MinimumCompressionSize: Optional[MinimumCompressionSize]
    Mode: Optional[PassThrough]
    Models: Optional[SamIntrinsic]
    Name: Optional[Name]
    OpenApiVersion: Optional[OpenApiVersion]
    StageName: Union[str, SamIntrinsic]
    Tags: Optional[PassThrough]
    TracingEnabled: Optional[TracingEnabled]
    Variables: Optional[Variables]


class Globals(BaseModel):
    Auth: Optional[Auth]
    Name: Optional[Name]
    DefinitionUri: Optional[DefinitionUri]
    CacheClusterEnabled: Optional[CacheClusterEnabled]
    CacheClusterSize: Optional[CacheClusterSize]
    Variables: Optional[Variables]
    EndpointConfiguration: Optional[EndpointConfiguration]
    MethodSettings: Optional[MethodSettings]
    BinaryMediaTypes: Optional[BinaryMediaTypes]
    MinimumCompressionSize: Optional[MinimumCompressionSize]
    Cors: Optional[CorsType]
    GatewayResponses: Optional[GatewayResponses]
    AccessLogSetting: Optional[AccessLogSetting]
    CanarySetting: Optional[CanarySetting]
    TracingEnabled: Optional[TracingEnabled]
    OpenApiVersion: Optional[OpenApiVersion]
    Domain: Optional[Domain]


class Resource(BaseModel):
    Type: Literal["AWS::Serverless::Api"]
    Properties: Properties
    Condition: Optional[PassThrough]
    DeletionPolicy: Optional[PassThrough]
    UpdatePolicy: Optional[PassThrough]
    UpdateReplacePolicy: Optional[PassThrough]
    DependsOn: Optional[PassThrough]
    Metadata: Optional[PassThrough]
