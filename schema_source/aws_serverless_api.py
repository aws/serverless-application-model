from __future__ import annotations

from typing import Dict, List, Optional, Union

from typing_extensions import Literal

from schema_source.aws_serverless_connector import EmbeddedConnector
from schema_source.common import (
    BaseModel,
    DictStrAny,
    PassThroughProp,
    ResourceAttributes,
    SamIntrinsicable,
    get_prop,
)

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
    Header: Optional[str] = lambdatokenauthorizeridentity("Header")


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
    Description: Optional[PassThroughProp] = usageplan("Description")
    Quota: Optional[PassThroughProp] = usageplan("Quota")
    Tags: Optional[PassThroughProp] = usageplan("Tags")
    Throttle: Optional[PassThroughProp] = usageplan("Throttle")
    UsagePlanName: Optional[PassThroughProp] = usageplan("UsagePlanName")


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
    DistributionDomainName: Optional[PassThroughProp] = route53("DistributionDomainName")
    EvaluateTargetHealth: Optional[PassThroughProp] = route53("EvaluateTargetHealth")
    HostedZoneId: Optional[PassThroughProp] = route53("HostedZoneId")
    HostedZoneName: Optional[PassThroughProp] = route53("HostedZoneName")
    IpV6: Optional[bool] = route53("IpV6")


class Domain(BaseModel):
    BasePath: Optional[PassThroughProp] = domain("BasePath")
    NormalizeBasePath: Optional[bool] = domain("NormalizeBasePath")
    CertificateArn: PassThroughProp = domain("CertificateArn")
    DomainName: PassThroughProp = domain("DomainName")
    EndpointConfiguration: Optional[SamIntrinsicable[Literal["REGIONAL", "EDGE"]]] = domain("EndpointConfiguration")
    MutualTlsAuthentication: Optional[PassThroughProp] = domain("MutualTlsAuthentication")
    OwnershipVerificationCertificateArn: Optional[PassThroughProp] = domain("OwnershipVerificationCertificateArn")
    Route53: Optional[Route53] = domain("Route53")
    SecurityPolicy: Optional[PassThroughProp] = domain("SecurityPolicy")


class DefinitionUri(BaseModel):
    Bucket: PassThroughProp = definitionuri("Bucket")
    Key: PassThroughProp = definitionuri("Key")
    Version: Optional[PassThroughProp] = definitionuri("Version")


class EndpointConfiguration(BaseModel):
    Type: Optional[PassThroughProp] = endpointconfiguration("Type")
    VPCEndpointIds: Optional[PassThroughProp] = endpointconfiguration("VPCEndpointIds")


Name = Optional[PassThroughProp]
DefinitionUriType = Optional[Union[str, DefinitionUri]]
CacheClusterEnabled = Optional[PassThroughProp]
CacheClusterSize = Optional[PassThroughProp]
Variables = Optional[PassThroughProp]
EndpointConfigurationType = Optional[SamIntrinsicable[EndpointConfiguration]]
MethodSettings = Optional[PassThroughProp]
BinaryMediaTypes = Optional[PassThroughProp]
MinimumCompressionSize = Optional[PassThroughProp]
CorsType = Optional[SamIntrinsicable[Union[str, Cors]]]
GatewayResponses = Optional[DictStrAny]
AccessLogSetting = Optional[PassThroughProp]
CanarySetting = Optional[PassThroughProp]
TracingEnabled = Optional[PassThroughProp]
OpenApiVersion = Optional[Union[float, str]]  # TODO: float doesn't exist in documentation


class Properties(BaseModel):
    AccessLogSetting: Optional[AccessLogSetting] = properties("AccessLogSetting")
    ApiKeySourceType: Optional[PassThroughProp] = properties("ApiKeySourceType")
    Auth: Optional[Auth] = properties("Auth")
    BinaryMediaTypes: Optional[BinaryMediaTypes] = properties("BinaryMediaTypes")
    CacheClusterEnabled: Optional[CacheClusterEnabled] = properties("CacheClusterEnabled")
    CacheClusterSize: Optional[CacheClusterSize] = properties("CacheClusterSize")
    CanarySetting: Optional[CanarySetting] = properties("CanarySetting")
    Cors: Optional[CorsType] = properties("Cors")
    DefinitionBody: Optional[DictStrAny] = properties("DefinitionBody")
    DefinitionUri: Optional[DefinitionUriType] = properties("DefinitionUri")
    Description: Optional[PassThroughProp] = properties("Description")
    DisableExecuteApiEndpoint: Optional[PassThroughProp] = properties("DisableExecuteApiEndpoint")
    Domain: Optional[Domain] = properties("Domain")
    EndpointConfiguration: Optional[EndpointConfigurationType] = properties("EndpointConfiguration")
    FailOnWarnings: Optional[PassThroughProp] = properties("FailOnWarnings")
    GatewayResponses: Optional[GatewayResponses] = properties("GatewayResponses")
    MethodSettings: Optional[MethodSettings] = properties("MethodSettings")
    MinimumCompressionSize: Optional[MinimumCompressionSize] = properties("MinimumCompressionSize")
    Mode: Optional[PassThroughProp] = properties("Mode")
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
    DefinitionUri: Optional[PassThroughProp] = properties("DefinitionUri")
    CacheClusterEnabled: Optional[CacheClusterEnabled] = properties("CacheClusterEnabled")
    CacheClusterSize: Optional[CacheClusterSize] = properties("CacheClusterSize")
    Variables: Optional[Variables] = properties("Variables")
    EndpointConfiguration: Optional[PassThroughProp] = properties("EndpointConfiguration")
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


class Resource(ResourceAttributes):
    Type: Literal["AWS::Serverless::Api"]
    Properties: Properties
    Connectors: Optional[Dict[str, EmbeddedConnector]]
