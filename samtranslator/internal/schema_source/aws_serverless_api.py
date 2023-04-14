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
    passthrough_prop,
)

PROPERTIES_STEM = "sam-resource-api"
DOMAIN_STEM = "sam-property-api-domainconfiguration"
ROUTE53_STEM = "sam-property-api-route53configuration"
ENDPOINT_CONFIGURATION_STEM = "sam-property-api-endpointconfiguration"
DEFINITION_URI_STEM = "sam-property-api-apidefinition"

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
route53 = get_prop(ROUTE53_STEM)
domain = get_prop(DOMAIN_STEM)
definitionuri = get_prop(DEFINITION_URI_STEM)
endpointconfiguration = get_prop(ENDPOINT_CONFIGURATION_STEM)
properties = get_prop(PROPERTIES_STEM)


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
    DisableFunctionDefaultPermissions: Optional[bool] = lambdatokenauthorizer("DisableFunctionDefaultPermissions")


class LambdaRequestAuthorizer(BaseModel):
    AuthorizationScopes: Optional[List[str]] = lambdarequestauthorizer("AuthorizationScopes")
    FunctionArn: SamIntrinsicable[str] = lambdarequestauthorizer("FunctionArn")
    FunctionInvokeRole: Optional[str] = lambdarequestauthorizer("FunctionInvokeRole")
    FunctionPayloadType: Optional[Literal["REQUEST"]] = lambdarequestauthorizer("FunctionPayloadType")
    Identity: Optional[LambdaRequestAuthorizerIdentity] = lambdarequestauthorizer("Identity")
    DisableFunctionDefaultPermissions: Optional[bool] = lambdarequestauthorizer("DisableFunctionDefaultPermissions")


class UsagePlan(BaseModel):
    CreateUsagePlan: SamIntrinsicable[Literal["PER_API", "SHARED", "NONE"]] = usageplan("CreateUsagePlan")
    Description: Optional[PassThroughProp] = usageplan("Description")
    Quota: Optional[PassThroughProp] = usageplan("Quota")
    Tags: Optional[PassThroughProp] = usageplan("Tags")
    Throttle: Optional[PassThroughProp] = usageplan("Throttle")
    UsagePlanName: Optional[PassThroughProp] = usageplan("UsagePlanName")


class Auth(BaseModel):
    AddDefaultAuthorizerToCorsPreflight: Optional[bool] = auth("AddDefaultAuthorizerToCorsPreflight")
    AddApiKeyRequiredToCorsPreflight: Optional[bool]  # TODO Add Docs
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
    DistributionDomainName: Optional[PassThroughProp] = passthrough_prop(
        ROUTE53_STEM,
        "DistributionDomainName",
        ["AWS::Route53::RecordSetGroup.AliasTarget", "DNSName"],
    )
    EvaluateTargetHealth: Optional[PassThroughProp] = passthrough_prop(
        ROUTE53_STEM,
        "EvaluateTargetHealth",
        ["AWS::Route53::RecordSetGroup.AliasTarget", "EvaluateTargetHealth"],
    )
    HostedZoneId: Optional[PassThroughProp] = passthrough_prop(
        ROUTE53_STEM,
        "HostedZoneId",
        ["AWS::Route53::RecordSetGroup.RecordSet", "HostedZoneId"],
    )
    HostedZoneName: Optional[PassThroughProp] = passthrough_prop(
        ROUTE53_STEM,
        "HostedZoneName",
        ["AWS::Route53::RecordSetGroup.RecordSet", "HostedZoneName"],
    )
    IpV6: Optional[bool] = route53("IpV6")
    SetIdentifier: Optional[PassThroughProp]  # TODO: add docs
    Region: Optional[PassThroughProp]  # TODO: add docs
    SeparateRecordSetGroup: Optional[bool]  # TODO: add docs


class Domain(BaseModel):
    BasePath: Optional[PassThroughProp] = domain("BasePath")
    NormalizeBasePath: Optional[bool] = domain("NormalizeBasePath")
    CertificateArn: PassThroughProp = domain("CertificateArn")
    DomainName: PassThroughProp = passthrough_prop(
        DOMAIN_STEM,
        "DomainName",
        ["AWS::ApiGateway::DomainName", "Properties", "DomainName"],
    )
    EndpointConfiguration: Optional[SamIntrinsicable[Literal["REGIONAL", "EDGE"]]] = domain("EndpointConfiguration")
    MutualTlsAuthentication: Optional[PassThroughProp] = passthrough_prop(
        DOMAIN_STEM,
        "MutualTlsAuthentication",
        ["AWS::ApiGateway::DomainName", "Properties", "MutualTlsAuthentication"],
    )
    OwnershipVerificationCertificateArn: Optional[PassThroughProp] = passthrough_prop(
        DOMAIN_STEM,
        "OwnershipVerificationCertificateArn",
        ["AWS::ApiGateway::DomainName", "Properties", "OwnershipVerificationCertificateArn"],
    )
    Route53: Optional[Route53] = domain("Route53")
    SecurityPolicy: Optional[PassThroughProp] = passthrough_prop(
        DOMAIN_STEM,
        "SecurityPolicy",
        ["AWS::ApiGateway::DomainName", "Properties", "SecurityPolicy"],
    )


class DefinitionUri(BaseModel):
    Bucket: PassThroughProp = passthrough_prop(
        DEFINITION_URI_STEM,
        "Bucket",
        ["AWS::ApiGateway::RestApi.S3Location", "Bucket"],
    )
    Key: PassThroughProp = passthrough_prop(
        DEFINITION_URI_STEM,
        "Key",
        ["AWS::ApiGateway::RestApi.S3Location", "Key"],
    )
    Version: Optional[PassThroughProp] = passthrough_prop(
        DEFINITION_URI_STEM,
        "Version",
        ["AWS::ApiGateway::RestApi.S3Location", "Version"],
    )


class EndpointConfiguration(BaseModel):
    Type: Optional[PassThroughProp] = passthrough_prop(
        ENDPOINT_CONFIGURATION_STEM,
        "Type",
        ["AWS::ApiGateway::RestApi.EndpointConfiguration", "Types"],
    )
    VPCEndpointIds: Optional[PassThroughProp] = passthrough_prop(
        ENDPOINT_CONFIGURATION_STEM,
        "VPCEndpointIds",
        ["AWS::ApiGateway::RestApi.EndpointConfiguration", "VpcEndpointIds"],
    )


Name = Optional[PassThroughProp]
DefinitionUriType = Optional[Union[str, DefinitionUri]]
MergeDefinitions = Optional[bool]
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
AlwaysDeploy = Optional[bool]


class Properties(BaseModel):
    AccessLogSetting: Optional[AccessLogSetting] = passthrough_prop(
        PROPERTIES_STEM,
        "AccessLogSetting",
        ["AWS::ApiGateway::Stage", "Properties", "AccessLogSetting"],
    )
    ApiKeySourceType: Optional[PassThroughProp] = passthrough_prop(
        PROPERTIES_STEM,
        "ApiKeySourceType",
        ["AWS::ApiGateway::RestApi", "Properties", "ApiKeySourceType"],
    )
    Auth: Optional[Auth] = properties("Auth")
    BinaryMediaTypes: Optional[BinaryMediaTypes] = properties("BinaryMediaTypes")
    CacheClusterEnabled: Optional[CacheClusterEnabled] = passthrough_prop(
        PROPERTIES_STEM,
        "CacheClusterEnabled",
        ["AWS::ApiGateway::Stage", "Properties", "CacheClusterEnabled"],
    )
    CacheClusterSize: Optional[CacheClusterSize] = passthrough_prop(
        PROPERTIES_STEM,
        "CacheClusterSize",
        ["AWS::ApiGateway::Stage", "Properties", "CacheClusterSize"],
    )
    CanarySetting: Optional[CanarySetting] = passthrough_prop(
        PROPERTIES_STEM,
        "CanarySetting",
        ["AWS::ApiGateway::Stage", "Properties", "CanarySetting"],
    )
    Cors: Optional[CorsType] = properties("Cors")
    DefinitionBody: Optional[DictStrAny] = properties("DefinitionBody")
    DefinitionUri: Optional[DefinitionUriType] = properties("DefinitionUri")
    MergeDefinitions: Optional[MergeDefinitions] = properties("MergeDefinitions")
    Description: Optional[PassThroughProp] = passthrough_prop(
        PROPERTIES_STEM,
        "Description",
        ["AWS::ApiGateway::Stage", "Properties", "Description"],
    )
    DisableExecuteApiEndpoint: Optional[PassThroughProp] = properties("DisableExecuteApiEndpoint")
    Domain: Optional[Domain] = properties("Domain")
    EndpointConfiguration: Optional[EndpointConfigurationType] = properties("EndpointConfiguration")
    FailOnWarnings: Optional[PassThroughProp] = passthrough_prop(
        PROPERTIES_STEM,
        "FailOnWarnings",
        ["AWS::ApiGateway::RestApi", "Properties", "FailOnWarnings"],
    )
    GatewayResponses: Optional[GatewayResponses] = properties("GatewayResponses")
    MethodSettings: Optional[MethodSettings] = passthrough_prop(
        PROPERTIES_STEM,
        "MethodSettings",
        ["AWS::ApiGateway::Stage", "Properties", "MethodSettings"],
    )
    MinimumCompressionSize: Optional[MinimumCompressionSize] = passthrough_prop(
        PROPERTIES_STEM,
        "MinimumCompressionSize",
        ["AWS::ApiGateway::RestApi", "Properties", "MinimumCompressionSize"],
    )
    Mode: Optional[PassThroughProp] = passthrough_prop(
        PROPERTIES_STEM,
        "Mode",
        ["AWS::ApiGateway::RestApi", "Properties", "Mode"],
    )
    Models: Optional[DictStrAny] = properties("Models")
    Name: Optional[Name] = passthrough_prop(
        PROPERTIES_STEM,
        "Name",
        ["AWS::ApiGateway::RestApi", "Properties", "Name"],
    )
    OpenApiVersion: Optional[OpenApiVersion] = properties("OpenApiVersion")
    StageName: SamIntrinsicable[str] = properties("StageName")
    Tags: Optional[DictStrAny] = properties("Tags")
    TracingEnabled: Optional[TracingEnabled] = passthrough_prop(
        PROPERTIES_STEM,
        "TracingEnabled",
        ["AWS::ApiGateway::Stage", "Properties", "TracingEnabled"],
    )
    Variables: Optional[Variables] = passthrough_prop(
        PROPERTIES_STEM,
        "Variables",
        ["AWS::ApiGateway::Stage", "Properties", "Variables"],
    )
    AlwaysDeploy: Optional[AlwaysDeploy] = properties("AlwaysDeploy")


class Globals(BaseModel):
    Auth: Optional[Auth] = properties("Auth")
    Name: Optional[Name] = passthrough_prop(
        PROPERTIES_STEM,
        "Name",
        ["AWS::ApiGateway::RestApi", "Properties", "Name"],
    )
    DefinitionUri: Optional[PassThroughProp] = properties("DefinitionUri")
    CacheClusterEnabled: Optional[CacheClusterEnabled] = passthrough_prop(
        PROPERTIES_STEM,
        "CacheClusterEnabled",
        ["AWS::ApiGateway::Stage", "Properties", "CacheClusterEnabled"],
    )
    CacheClusterSize: Optional[CacheClusterSize] = passthrough_prop(
        PROPERTIES_STEM,
        "CacheClusterSize",
        ["AWS::ApiGateway::Stage", "Properties", "CacheClusterSize"],
    )
    MergeDefinitions: Optional[MergeDefinitions] = properties("MergeDefinitions")
    Variables: Optional[Variables] = passthrough_prop(
        PROPERTIES_STEM,
        "Variables",
        ["AWS::ApiGateway::Stage", "Properties", "Variables"],
    )
    EndpointConfiguration: Optional[PassThroughProp] = properties("EndpointConfiguration")
    MethodSettings: Optional[MethodSettings] = properties("MethodSettings")
    BinaryMediaTypes: Optional[BinaryMediaTypes] = properties("BinaryMediaTypes")
    MinimumCompressionSize: Optional[MinimumCompressionSize] = passthrough_prop(
        PROPERTIES_STEM,
        "MinimumCompressionSize",
        ["AWS::ApiGateway::RestApi", "Properties", "MinimumCompressionSize"],
    )
    Cors: Optional[CorsType] = properties("Cors")
    GatewayResponses: Optional[GatewayResponses] = properties("GatewayResponses")
    AccessLogSetting: Optional[AccessLogSetting] = passthrough_prop(
        PROPERTIES_STEM,
        "AccessLogSetting",
        ["AWS::ApiGateway::Stage", "Properties", "AccessLogSetting"],
    )
    CanarySetting: Optional[CanarySetting] = passthrough_prop(
        PROPERTIES_STEM,
        "CanarySetting",
        ["AWS::ApiGateway::Stage", "Properties", "CanarySetting"],
    )
    TracingEnabled: Optional[TracingEnabled] = passthrough_prop(
        PROPERTIES_STEM,
        "TracingEnabled",
        ["AWS::ApiGateway::Stage", "Properties", "TracingEnabled"],
    )
    OpenApiVersion: Optional[OpenApiVersion] = properties("OpenApiVersion")
    Domain: Optional[Domain] = properties("Domain")
    AlwaysDeploy: Optional[AlwaysDeploy] = properties("AlwaysDeploy")


class Resource(ResourceAttributes):
    Type: Literal["AWS::Serverless::Api"]
    Properties: Properties
    Connectors: Optional[Dict[str, EmbeddedConnector]]
