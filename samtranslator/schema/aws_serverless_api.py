from __future__ import annotations

from typing import Optional, Dict, Union, List

from typing_extensions import Literal

from samtranslator.schema.common import PassThrough, BaseModel, SamIntrinsicable, get_prop, DictStrAny

resourcepolicy = get_prop("sam-property-api-resourcepolicystatement")
cognitoauthorizeridentity = get_prop("sam-property-api-cognitoauthorizationidentity")
cognitoauthorizer = get_prop("sam-property-api-cognitoauthorizer")
lambdatokenauthorizeridentity = get_prop("sam-property-api-lambdatokenauthorizationidentity")
lambdarequestauthorizeridentity = get_prop("sam-property-api-lambdarequestauthorizationidentity")
lambdatokenauthorizer = get_prop("sam-property-api-lambdatokenauthorizer")
lambdarequestauthorizer = get_prop("sam-property-api-lambdarequestauthorizer")
usageplan = get_prop("sam-property-api-apiusageplan")
auth = get_prop("sam-property-api-apiauth")
cors = get_prop("sam-property-api-corsconfiguration")
route53 = get_prop("sam-property-api-route53configuration")
domain = get_prop("sam-property-api-domainconfiguration")
definitionuri = get_prop("sam-property-api-apidefinition")
endpointconfiguration = get_prop("sam-property-api-endpointconfiguration")
properties = get_prop("sam-resource-api")


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


class CognitoAuthorizerIdentity(BaseModel):
    Header: Optional[str] = cognitoauthorizeridentity("Header")
    ReauthorizeEvery: Optional[SamIntrinsicable[int]] = cognitoauthorizeridentity("ReauthorizeEvery")
    ValidationExpression: Optional[str] = cognitoauthorizeridentity("ValidationExpression")


class CognitoAuthorizer(BaseModel):
    AuthorizationScopes: Optional[List[str]] = cognitoauthorizer("AuthorizationScopes")
    Identity: Optional[CognitoAuthorizerIdentity] = cognitoauthorizer("Identity")
    UserPoolArn: SamIntrinsicable[str] = cognitoauthorizer("UserPoolArn")


class LambdaTokenAuthorizerIdentity(BaseModel):
    ReauthorizeEvery: Optional[SamIntrinsicable[int]] = lambdatokenauthorizeridentity("ReauthorizeEvery")
    ValidationExpression: Optional[str] = lambdatokenauthorizeridentity("ValidationExpression")
    Header: Optional[
        str
    ]  # TODO: This doesn't exist in docs: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-property-api-lambdatokenauthorizationidentity.html


class LambdaRequestAuthorizerIdentity(BaseModel):
    Context: Optional[List[str]] = lambdarequestauthorizeridentity("Context")
    Headers: Optional[List[str]] = lambdarequestauthorizeridentity("Headers")
    QueryStrings: Optional[List[str]] = lambdarequestauthorizeridentity("QueryStrings")
    ReauthorizeEvery: Optional[SamIntrinsicable[int]] = lambdarequestauthorizeridentity("ReauthorizeEvery")
    StageVariables: Optional[List[str]] = lambdarequestauthorizeridentity("StageVariables")


class LambdaTokenAuthorizer(BaseModel):
    AuthorizationScopes: Optional[List[str]] = lambdatokenauthorizer("AuthorizationScopes")
    FunctionArn: SamIntrinsicable[str] = lambdatokenauthorizer("FunctionArn")
    FunctionInvokeRole: Optional[str] = lambdatokenauthorizer("FunctionInvokeRole")
    FunctionPayloadType: Optional[Literal["TOKEN"]] = lambdatokenauthorizer("FunctionPayloadType")
    Identity: Optional[LambdaTokenAuthorizerIdentity] = lambdatokenauthorizer("Identity")


class LambdaRequestAuthorizer(BaseModel):
    AuthorizationScopes: Optional[List[str]] = lambdarequestauthorizer("AuthorizationScopes")
    FunctionArn: SamIntrinsicable[str] = lambdarequestauthorizer("FunctionArn")
    FunctionInvokeRole: Optional[str] = lambdarequestauthorizer("FunctionInvokeRole")
    FunctionPayloadType: Optional[Literal["REQUEST"]] = lambdarequestauthorizer("FunctionPayloadType")
    Identity: Optional[LambdaRequestAuthorizerIdentity] = lambdarequestauthorizer("Identity")


class UsagePlan(BaseModel):
    CreateUsagePlan: SamIntrinsicable[Literal["PER_API", "SHARED", "NONE"]] = usageplan("CreateUsagePlan")
    Description: Optional[PassThrough] = usageplan("Description")
    Quota: Optional[PassThrough] = usageplan("Quota")
    Tags: Optional[PassThrough] = usageplan("Tags")
    Throttle: Optional[PassThrough] = usageplan("Throttle")
    UsagePlanName: Optional[PassThrough] = usageplan("UsagePlanName")


class Auth(BaseModel):
    AddDefaultAuthorizerToCorsPreflight: Optional[bool] = auth("AddDefaultAuthorizerToCorsPreflight")
    ApiKeyRequired: Optional[bool] = auth("ApiKeyRequired")
    Authorizers: Optional[
        Dict[
            str,
            Union[
                CognitoAuthorizer,
                LambdaTokenAuthorizer,
                LambdaRequestAuthorizer,
            ],
        ]
    ] = auth("Authorizers")
    DefaultAuthorizer: Optional[str] = auth("DefaultAuthorizer")
    InvokeRole: Optional[str] = auth("InvokeRole")
    ResourcePolicy: Optional[ResourcePolicy] = auth("ResourcePolicy")
    UsagePlan: Optional[UsagePlan] = auth("UsagePlan")


class Cors(BaseModel):
    AllowCredentials: Optional[bool] = cors("AllowCredentials")
    AllowHeaders: Optional[str] = cors("AllowHeaders")
    AllowMethods: Optional[str] = cors("AllowMethods")
    AllowOrigin: str = cors("AllowOrigin")
    MaxAge: Optional[str] = cors("MaxAge")


class Route53(BaseModel):
    DistributionDomainName: Optional[PassThrough] = route53("DistributionDomainName")
    EvaluateTargetHealth: Optional[PassThrough] = route53("EvaluateTargetHealth")
    HostedZoneId: Optional[PassThrough] = route53("HostedZoneId")
    HostedZoneName: Optional[PassThrough] = route53("HostedZoneName")
    IpV6: Optional[bool] = route53("IpV6")


class Domain(BaseModel):
    BasePath: Optional[PassThrough] = domain("BasePath")
    NormalizeBasePath: Optional[bool]  # TODO: Add documentation for this property
    CertificateArn: PassThrough = domain("CertificateArn")
    DomainName: PassThrough = domain("DomainName")
    EndpointConfiguration: Optional[SamIntrinsicable[Literal["REGIONAL", "EDGE"]]] = domain("EndpointConfiguration")
    MutualTlsAuthentication: Optional[PassThrough] = domain("MutualTlsAuthentication")
    OwnershipVerificationCertificateArn: Optional[PassThrough] = domain("OwnershipVerificationCertificateArn")
    Route53: Optional[Route53] = domain("Route53")
    SecurityPolicy: Optional[PassThrough] = domain("SecurityPolicy")


class DefinitionUri(BaseModel):
    Bucket: PassThrough = definitionuri("Bucket")
    Key: PassThrough = definitionuri("Key")
    Version: Optional[PassThrough] = definitionuri("Version")


class EndpointConfiguration(BaseModel):
    Type: Optional[PassThrough] = endpointconfiguration("Type")
    VPCEndpointIds: Optional[PassThrough] = endpointconfiguration("VPCEndpointIds")


Name = Optional[PassThrough]
DefinitionUriType = Optional[Union[str, DefinitionUri]]
CacheClusterEnabled = Optional[PassThrough]
CacheClusterSize = Optional[PassThrough]
Variables = Optional[PassThrough]
EndpointConfigurationType = Optional[SamIntrinsicable[EndpointConfiguration]]
MethodSettings = Optional[PassThrough]
BinaryMediaTypes = Optional[PassThrough]
MinimumCompressionSize = Optional[PassThrough]
CorsType = Optional[SamIntrinsicable[Union[str, Cors]]]
GatewayResponses = Optional[DictStrAny]
AccessLogSetting = Optional[PassThrough]
CanarySetting = Optional[PassThrough]
TracingEnabled = Optional[PassThrough]
OpenApiVersion = Optional[Union[float, str]]  # TODO: float doesn't exist in documentation


class Properties(BaseModel):
    AccessLogSetting: Optional[AccessLogSetting] = properties("AccessLogSetting")
    ApiKeySourceType: Optional[PassThrough] = properties("ApiKeySourceType")
    Auth: Optional[Auth] = properties("Auth")
    BinaryMediaTypes: Optional[BinaryMediaTypes] = properties("BinaryMediaTypes")
    CacheClusterEnabled: Optional[CacheClusterEnabled] = properties("CacheClusterEnabled")
    CacheClusterSize: Optional[CacheClusterSize] = properties("CacheClusterSize")
    CanarySetting: Optional[CanarySetting] = properties("CanarySetting")
    Cors: Optional[CorsType] = properties("Cors")
    DefinitionBody: Optional[DictStrAny] = properties("DefinitionBody")
    DefinitionUri: Optional[DefinitionUriType] = properties("DefinitionUri")
    Description: Optional[PassThrough] = properties("Description")
    DisableExecuteApiEndpoint: Optional[PassThrough] = properties("DisableExecuteApiEndpoint")
    Domain: Optional[Domain] = properties("Domain")
    EndpointConfiguration: Optional[EndpointConfigurationType] = properties("EndpointConfiguration")
    FailOnWarnings: Optional[PassThrough] = properties("FailOnWarnings")
    GatewayResponses: Optional[GatewayResponses] = properties("GatewayResponses")
    MethodSettings: Optional[MethodSettings] = properties("MethodSettings")
    MinimumCompressionSize: Optional[MinimumCompressionSize] = properties("MinimumCompressionSize")
    Mode: Optional[PassThrough] = properties("Mode")
    Models: Optional[DictStrAny] = properties("Models")
    Name: Optional[Name] = properties("Name")
    OpenApiVersion: Optional[OpenApiVersion] = properties("OpenApiVersion")
    StageName: SamIntrinsicable[str] = properties("StageName")
    Tags: Optional[DictStrAny] = properties("Tags")
    TracingEnabled: Optional[TracingEnabled] = properties("TracingEnabled")
    Variables: Optional[Variables] = properties("Variables")


class Globals(BaseModel):
    Auth: Optional[Auth] = properties("Auth")
    Name: Optional[Name] = properties("Name")
    DefinitionUri: Optional[PassThrough] = properties("DefinitionUri")
    CacheClusterEnabled: Optional[CacheClusterEnabled] = properties("CacheClusterEnabled")
    CacheClusterSize: Optional[CacheClusterSize] = properties("CacheClusterSize")
    Variables: Optional[Variables] = properties("Variables")
    EndpointConfiguration: Optional[PassThrough] = properties("EndpointConfiguration")
    MethodSettings: Optional[MethodSettings] = properties("MethodSettings")
    BinaryMediaTypes: Optional[BinaryMediaTypes] = properties("BinaryMediaTypes")
    MinimumCompressionSize: Optional[MinimumCompressionSize] = properties("MinimumCompressionSize")
    Cors: Optional[CorsType] = properties("Cors")
    GatewayResponses: Optional[GatewayResponses] = properties("GatewayResponses")
    AccessLogSetting: Optional[AccessLogSetting] = properties("AccessLogSetting")
    CanarySetting: Optional[CanarySetting] = properties("CanarySetting")
    TracingEnabled: Optional[TracingEnabled] = properties("TracingEnabled")
    OpenApiVersion: Optional[OpenApiVersion] = properties("OpenApiVersion")
    Domain: Optional[Domain] = properties("Domain")


class Resource(BaseModel):
    Type: Literal["AWS::Serverless::Api"]
    Properties: Properties
    Condition: Optional[PassThrough]
    DeletionPolicy: Optional[PassThrough]
    UpdatePolicy: Optional[PassThrough]
    UpdateReplacePolicy: Optional[PassThrough]
    DependsOn: Optional[PassThrough]
    Metadata: Optional[PassThrough]
