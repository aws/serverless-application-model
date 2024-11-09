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
    AwsAccountBlacklist: list[str | DictStrAny] | None = resourcepolicy("AwsAccountBlacklist")
    AwsAccountWhitelist: list[str | DictStrAny] | None = resourcepolicy("AwsAccountWhitelist")
    CustomStatements: list[str | DictStrAny] | None = resourcepolicy("CustomStatements")
    IntrinsicVpcBlacklist: list[str | DictStrAny] | None = resourcepolicy("IntrinsicVpcBlacklist")
    IntrinsicVpcWhitelist: list[str | DictStrAny] | None = resourcepolicy("IntrinsicVpcWhitelist")
    IntrinsicVpceBlacklist: list[str | DictStrAny] | None = resourcepolicy("IntrinsicVpceBlacklist")
    IntrinsicVpceWhitelist: list[str | DictStrAny] | None = resourcepolicy("IntrinsicVpceWhitelist")
    IpRangeBlacklist: list[str | DictStrAny] | None = resourcepolicy("IpRangeBlacklist")
    IpRangeWhitelist: list[str | DictStrAny] | None = resourcepolicy("IpRangeWhitelist")
    SourceVpcBlacklist: list[str | DictStrAny] | None = resourcepolicy("SourceVpcBlacklist")
    SourceVpcWhitelist: list[str | DictStrAny] | None = resourcepolicy("SourceVpcWhitelist")


class CognitoAuthorizerIdentity(BaseModel):
    Header: str | None = cognitoauthorizeridentity("Header")
    ReauthorizeEvery: SamIntrinsicable[int] | None = cognitoauthorizeridentity("ReauthorizeEvery")
    ValidationExpression: str | None = cognitoauthorizeridentity("ValidationExpression")


class CognitoAuthorizer(BaseModel):
    AuthorizationScopes: list[str] | None = cognitoauthorizer("AuthorizationScopes")
    Identity: CognitoAuthorizerIdentity | None = cognitoauthorizer("Identity")
    UserPoolArn: SamIntrinsicable[str] = cognitoauthorizer("UserPoolArn")


class LambdaTokenAuthorizerIdentity(BaseModel):
    ReauthorizeEvery: SamIntrinsicable[int] | None = lambdatokenauthorizeridentity("ReauthorizeEvery")
    ValidationExpression: str | None = lambdatokenauthorizeridentity("ValidationExpression")
    Header: str | None = lambdatokenauthorizeridentity("Header")


class LambdaRequestAuthorizerIdentity(BaseModel):
    Context: list[str] | None = lambdarequestauthorizeridentity("Context")
    Headers: list[str] | None = lambdarequestauthorizeridentity("Headers")
    QueryStrings: list[str] | None = lambdarequestauthorizeridentity("QueryStrings")
    ReauthorizeEvery: SamIntrinsicable[int] | None = lambdarequestauthorizeridentity("ReauthorizeEvery")
    StageVariables: list[str] | None = lambdarequestauthorizeridentity("StageVariables")


class LambdaTokenAuthorizer(BaseModel):
    AuthorizationScopes: list[str] | None = lambdatokenauthorizer("AuthorizationScopes")
    FunctionArn: SamIntrinsicable[str] = lambdatokenauthorizer("FunctionArn")
    FunctionInvokeRole: str | None = lambdatokenauthorizer("FunctionInvokeRole")
    FunctionPayloadType: Literal["TOKEN"] | None = lambdatokenauthorizer("FunctionPayloadType")
    Identity: LambdaTokenAuthorizerIdentity | None = lambdatokenauthorizer("Identity")
    DisableFunctionDefaultPermissions: bool | None = lambdatokenauthorizer("DisableFunctionDefaultPermissions")


class LambdaRequestAuthorizer(BaseModel):
    AuthorizationScopes: list[str] | None = lambdarequestauthorizer("AuthorizationScopes")
    FunctionArn: SamIntrinsicable[str] = lambdarequestauthorizer("FunctionArn")
    FunctionInvokeRole: str | None = lambdarequestauthorizer("FunctionInvokeRole")
    FunctionPayloadType: Literal["REQUEST"] | None = lambdarequestauthorizer("FunctionPayloadType")
    Identity: LambdaRequestAuthorizerIdentity | None = lambdarequestauthorizer("Identity")
    DisableFunctionDefaultPermissions: bool | None = lambdarequestauthorizer("DisableFunctionDefaultPermissions")


class UsagePlan(BaseModel):
    CreateUsagePlan: SamIntrinsicable[Literal["PER_API", "SHARED", "NONE"]] = usageplan("CreateUsagePlan")
    Description: PassThroughProp | None = usageplan("Description")
    Quota: PassThroughProp | None = usageplan("Quota")
    Tags: PassThroughProp | None = usageplan("Tags")
    Throttle: PassThroughProp | None = usageplan("Throttle")
    UsagePlanName: PassThroughProp | None = usageplan("UsagePlanName")


class Auth(BaseModel):
    AddDefaultAuthorizerToCorsPreflight: bool | None = auth("AddDefaultAuthorizerToCorsPreflight")
    AddApiKeyRequiredToCorsPreflight: bool | None  # TODO Add Docs
    ApiKeyRequired: bool | None = auth("ApiKeyRequired")
    Authorizers: None | (
        dict[
            str,
            (
                CognitoAuthorizer |
                LambdaTokenAuthorizer |
                LambdaRequestAuthorizer
            ),
        ]
    ) = auth("Authorizers")
    DefaultAuthorizer: str | None = auth("DefaultAuthorizer")
    InvokeRole: str | None = auth("InvokeRole")
    ResourcePolicy: ResourcePolicy | None = auth("ResourcePolicy")
    UsagePlan: UsagePlan | None = auth("UsagePlan")


class Cors(BaseModel):
    AllowCredentials: bool | None = cors("AllowCredentials")
    AllowHeaders: str | None = cors("AllowHeaders")
    AllowMethods: str | None = cors("AllowMethods")
    AllowOrigin: str = cors("AllowOrigin")
    MaxAge: str | None = cors("MaxAge")


class Route53(BaseModel):
    DistributionDomainName: PassThroughProp | None = passthrough_prop(
        ROUTE53_STEM,
        "DistributionDomainName",
        ["AWS::Route53::RecordSetGroup.AliasTarget", "DNSName"],
    )
    EvaluateTargetHealth: PassThroughProp | None = passthrough_prop(
        ROUTE53_STEM,
        "EvaluateTargetHealth",
        ["AWS::Route53::RecordSetGroup.AliasTarget", "EvaluateTargetHealth"],
    )
    HostedZoneId: PassThroughProp | None = passthrough_prop(
        ROUTE53_STEM,
        "HostedZoneId",
        ["AWS::Route53::RecordSetGroup.RecordSet", "HostedZoneId"],
    )
    HostedZoneName: PassThroughProp | None = passthrough_prop(
        ROUTE53_STEM,
        "HostedZoneName",
        ["AWS::Route53::RecordSetGroup.RecordSet", "HostedZoneName"],
    )
    IpV6: bool | None = route53("IpV6")
    SetIdentifier: PassThroughProp | None  # TODO: add docs
    Region: PassThroughProp | None  # TODO: add docs
    SeparateRecordSetGroup: bool | None  # TODO: add docs


class Domain(BaseModel):
    BasePath: PassThroughProp | None = domain("BasePath")
    NormalizeBasePath: bool | None = domain("NormalizeBasePath")
    CertificateArn: PassThroughProp = domain("CertificateArn")
    DomainName: PassThroughProp = passthrough_prop(
        DOMAIN_STEM,
        "DomainName",
        ["AWS::ApiGateway::DomainName", "Properties", "DomainName"],
    )
    EndpointConfiguration: SamIntrinsicable[Literal["REGIONAL", "EDGE"]] | None = domain("EndpointConfiguration")
    MutualTlsAuthentication: PassThroughProp | None = passthrough_prop(
        DOMAIN_STEM,
        "MutualTlsAuthentication",
        ["AWS::ApiGateway::DomainName", "Properties", "MutualTlsAuthentication"],
    )
    OwnershipVerificationCertificateArn: PassThroughProp | None = passthrough_prop(
        DOMAIN_STEM,
        "OwnershipVerificationCertificateArn",
        ["AWS::ApiGateway::DomainName", "Properties", "OwnershipVerificationCertificateArn"],
    )
    Route53: Route53 | None = domain("Route53")
    SecurityPolicy: PassThroughProp | None = passthrough_prop(
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
    Version: PassThroughProp | None = passthrough_prop(
        DEFINITION_URI_STEM,
        "Version",
        ["AWS::ApiGateway::RestApi.S3Location", "Version"],
    )


class EndpointConfiguration(BaseModel):
    Type: PassThroughProp | None = passthrough_prop(
        ENDPOINT_CONFIGURATION_STEM,
        "Type",
        ["AWS::ApiGateway::RestApi.EndpointConfiguration", "Types"],
    )
    VPCEndpointIds: PassThroughProp | None = passthrough_prop(
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
    AccessLogSetting: AccessLogSetting | None = passthrough_prop(
        PROPERTIES_STEM,
        "AccessLogSetting",
        ["AWS::ApiGateway::Stage", "Properties", "AccessLogSetting"],
    )
    ApiKeySourceType: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "ApiKeySourceType",
        ["AWS::ApiGateway::RestApi", "Properties", "ApiKeySourceType"],
    )
    Auth: Auth | None = properties("Auth")
    BinaryMediaTypes: BinaryMediaTypes | None = properties("BinaryMediaTypes")
    CacheClusterEnabled: CacheClusterEnabled | None = passthrough_prop(
        PROPERTIES_STEM,
        "CacheClusterEnabled",
        ["AWS::ApiGateway::Stage", "Properties", "CacheClusterEnabled"],
    )
    CacheClusterSize: CacheClusterSize | None = passthrough_prop(
        PROPERTIES_STEM,
        "CacheClusterSize",
        ["AWS::ApiGateway::Stage", "Properties", "CacheClusterSize"],
    )
    CanarySetting: CanarySetting | None = passthrough_prop(
        PROPERTIES_STEM,
        "CanarySetting",
        ["AWS::ApiGateway::Stage", "Properties", "CanarySetting"],
    )
    Cors: CorsType | None = properties("Cors")
    DefinitionBody: DictStrAny | None = properties("DefinitionBody")
    DefinitionUri: DefinitionUriType | None = properties("DefinitionUri")
    MergeDefinitions: MergeDefinitions | None = properties("MergeDefinitions")
    Description: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "Description",
        ["AWS::ApiGateway::Stage", "Properties", "Description"],
    )
    DisableExecuteApiEndpoint: PassThroughProp | None = properties("DisableExecuteApiEndpoint")
    Domain: Domain | None = properties("Domain")
    EndpointConfiguration: EndpointConfigurationType | None = properties("EndpointConfiguration")
    FailOnWarnings: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "FailOnWarnings",
        ["AWS::ApiGateway::RestApi", "Properties", "FailOnWarnings"],
    )
    GatewayResponses: GatewayResponses | None = properties("GatewayResponses")
    MethodSettings: MethodSettings | None = passthrough_prop(
        PROPERTIES_STEM,
        "MethodSettings",
        ["AWS::ApiGateway::Stage", "Properties", "MethodSettings"],
    )
    MinimumCompressionSize: MinimumCompressionSize | None = passthrough_prop(
        PROPERTIES_STEM,
        "MinimumCompressionSize",
        ["AWS::ApiGateway::RestApi", "Properties", "MinimumCompressionSize"],
    )
    Mode: PassThroughProp | None = passthrough_prop(
        PROPERTIES_STEM,
        "Mode",
        ["AWS::ApiGateway::RestApi", "Properties", "Mode"],
    )
    Models: DictStrAny | None = properties("Models")
    Name: Name | None = passthrough_prop(
        PROPERTIES_STEM,
        "Name",
        ["AWS::ApiGateway::RestApi", "Properties", "Name"],
    )
    OpenApiVersion: OpenApiVersion | None = properties("OpenApiVersion")
    StageName: SamIntrinsicable[str] = properties("StageName")
    Tags: DictStrAny | None = properties("Tags")
    PropagateTags: bool | None  # TODO: add docs
    TracingEnabled: TracingEnabled | None = passthrough_prop(
        PROPERTIES_STEM,
        "TracingEnabled",
        ["AWS::ApiGateway::Stage", "Properties", "TracingEnabled"],
    )
    Variables: Variables | None = passthrough_prop(
        PROPERTIES_STEM,
        "Variables",
        ["AWS::ApiGateway::Stage", "Properties", "Variables"],
    )
    AlwaysDeploy: AlwaysDeploy | None = properties("AlwaysDeploy")


class Globals(BaseModel):
    Auth: Auth | None = properties("Auth")
    Name: Name | None = passthrough_prop(
        PROPERTIES_STEM,
        "Name",
        ["AWS::ApiGateway::RestApi", "Properties", "Name"],
    )
    DefinitionUri: PassThroughProp | None = properties("DefinitionUri")
    CacheClusterEnabled: CacheClusterEnabled | None = passthrough_prop(
        PROPERTIES_STEM,
        "CacheClusterEnabled",
        ["AWS::ApiGateway::Stage", "Properties", "CacheClusterEnabled"],
    )
    CacheClusterSize: CacheClusterSize | None = passthrough_prop(
        PROPERTIES_STEM,
        "CacheClusterSize",
        ["AWS::ApiGateway::Stage", "Properties", "CacheClusterSize"],
    )
    MergeDefinitions: MergeDefinitions | None = properties("MergeDefinitions")
    Variables: Variables | None = passthrough_prop(
        PROPERTIES_STEM,
        "Variables",
        ["AWS::ApiGateway::Stage", "Properties", "Variables"],
    )
    EndpointConfiguration: PassThroughProp | None = properties("EndpointConfiguration")
    MethodSettings: MethodSettings | None = properties("MethodSettings")
    BinaryMediaTypes: BinaryMediaTypes | None = properties("BinaryMediaTypes")
    MinimumCompressionSize: MinimumCompressionSize | None = passthrough_prop(
        PROPERTIES_STEM,
        "MinimumCompressionSize",
        ["AWS::ApiGateway::RestApi", "Properties", "MinimumCompressionSize"],
    )
    Cors: CorsType | None = properties("Cors")
    GatewayResponses: GatewayResponses | None = properties("GatewayResponses")
    AccessLogSetting: AccessLogSetting | None = passthrough_prop(
        PROPERTIES_STEM,
        "AccessLogSetting",
        ["AWS::ApiGateway::Stage", "Properties", "AccessLogSetting"],
    )
    CanarySetting: CanarySetting | None = passthrough_prop(
        PROPERTIES_STEM,
        "CanarySetting",
        ["AWS::ApiGateway::Stage", "Properties", "CanarySetting"],
    )
    TracingEnabled: TracingEnabled | None = passthrough_prop(
        PROPERTIES_STEM,
        "TracingEnabled",
        ["AWS::ApiGateway::Stage", "Properties", "TracingEnabled"],
    )
    OpenApiVersion: OpenApiVersion | None = properties("OpenApiVersion")
    Domain: Domain | None = properties("Domain")
    AlwaysDeploy: AlwaysDeploy | None = properties("AlwaysDeploy")
    PropagateTags: bool | None  # TODO: add docs


class Resource(ResourceAttributes):
    Type: Literal["AWS::Serverless::Api"]
    Properties: Properties
    Connectors: dict[str, EmbeddedConnector] | None
