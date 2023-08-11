from typing import Any, Dict, List, Optional, Union

from typing_extensions import Required, TypedDict

from samtranslator.model import GeneratedProperty, Resource
from samtranslator.model.intrinsics import fnGetAtt, ref
from samtranslator.utils.types import Intrinsicable

# This JavaScript default resolver code is the template AppSync provides by default as well in the AWS Console.
# Arguments are available in every function within that resolver by accessing `ctx.args`.
APPSYNC_PIPELINE_RESOLVER_JS_CODE = """
export function request(ctx) {
    return {};
}

export function response(ctx) {
    return ctx.prev.result;
}
"""


class LambdaAuthorizerConfigType(TypedDict, total=False):
    AuthorizerResultTtlInSeconds: float
    AuthorizerUri: Required[str]
    IdentityValidationExpression: str


class OpenIDConnectConfigType(TypedDict, total=False):
    AuthTTL: float
    ClientId: str
    IatTTL: float
    Issuer: str


class UserPoolConfigType(TypedDict, total=False):
    AppIdClientRegex: str
    AwsRegion: str
    DefaultAction: str
    UserPoolId: Required[str]


class AdditionalAuthenticationProviderType(TypedDict, total=False):
    AuthenticationType: str
    LambdaAuthorizerConfig: LambdaAuthorizerConfigType
    OpenIDConnectConfig: OpenIDConnectConfigType
    UserPoolConfig: UserPoolConfigType


class DeltaSyncConfigType(TypedDict):
    BaseTableTTL: str
    DeltaSyncTableName: str
    DeltaSyncTableTTL: str


class DynamoDBConfigType(TypedDict, total=False):
    AwsRegion: Union[str, Dict[str, str]]
    TableName: str
    UseCallerCredentials: bool
    Versioned: bool
    DeltaSyncConfig: DeltaSyncConfigType


class LambdaConfigType(TypedDict, total=False):
    LambdaFunctionArn: str


class LogConfigType(TypedDict, total=False):
    CloudWatchLogsRoleArn: Intrinsicable[str]
    ExcludeVerboseContent: bool
    FieldLogLevel: str


class AppSyncRuntimeType(TypedDict):
    Name: str
    RuntimeVersion: str


# Runtime for the default generated resolver code (see APPSYNC_PIPELINE_RESOLVER_JS_CODE above)
APPSYNC_PIPELINE_RESOLVER_JS_RUNTIME: AppSyncRuntimeType = {
    "Name": "APPSYNC_JS",
    "RuntimeVersion": "1.0.0",
}


class LambdaConflictHandlerConfigType(TypedDict):
    LambdaConflictHandlerArn: str


class SyncConfigType(TypedDict, total=False):
    ConflictDetection: str
    ConflictHandler: str
    LambdaConflictHandlerConfig: LambdaConflictHandlerConfigType


class CachingConfigType(TypedDict, total=False):
    CachingKeys: List[str]
    Ttl: float


class PipelineConfigType(TypedDict, total=False):
    Functions: List[Intrinsicable[str]]


class GraphQLApi(Resource):
    resource_type = "AWS::AppSync::GraphQLApi"
    property_types = {
        "Name": GeneratedProperty(),
        "Tags": GeneratedProperty(),
        "XrayEnabled": GeneratedProperty(),
        "AuthenticationType": GeneratedProperty(),
        "LogConfig": GeneratedProperty(),
        "LambdaAuthorizerConfig": GeneratedProperty(),
        "OpenIDConnectConfig": GeneratedProperty(),
        "UserPoolConfig": GeneratedProperty(),
        "AdditionalAuthenticationProviders": GeneratedProperty(),
    }

    Name: str
    AuthenticationType: str
    LambdaAuthorizerConfig: Optional[LambdaAuthorizerConfigType]
    OpenIDConnectConfig: Optional[OpenIDConnectConfigType]
    UserPoolConfig: Optional[UserPoolConfigType]
    AdditionalAuthenticationProviders: Optional[List[AdditionalAuthenticationProviderType]]
    Tags: Optional[List[Dict[str, Any]]]
    XrayEnabled: Optional[bool]
    LogConfig: Optional[LogConfigType]

    runtime_attrs = {"api_id": lambda self: fnGetAtt(self.logical_id, "ApiId")}


class GraphQLSchema(Resource):
    resource_type = "AWS::AppSync::GraphQLSchema"
    property_types = {
        "ApiId": GeneratedProperty(),
        "Definition": GeneratedProperty(),
        "DefinitionS3Location": GeneratedProperty(),
    }

    ApiId: Intrinsicable[str]
    Definition: Optional[str]
    DefinitionS3Location: Optional[str]


class DataSource(Resource):
    resource_type = "AWS::AppSync::DataSource"
    property_types = {
        "ApiId": GeneratedProperty(),
        "Description": GeneratedProperty(),
        "Name": GeneratedProperty(),
        "Type": GeneratedProperty(),
        "ServiceRoleArn": GeneratedProperty(),
        "DynamoDBConfig": GeneratedProperty(),
        "LambdaConfig": GeneratedProperty(),
    }

    ApiId: Intrinsicable[str]
    Description: Optional[str]
    Name: str
    Type: str
    ServiceRoleArn: str
    DynamoDBConfig: Optional[DynamoDBConfigType]
    LambdaConfig: Optional[LambdaConfigType]

    runtime_attrs = {
        "arn": lambda self: fnGetAtt(self.logical_id, "DataSourceArn"),
        "name": lambda self: fnGetAtt(self.logical_id, "Name"),
    }


class FunctionConfiguration(Resource):
    resource_type = "AWS::AppSync::FunctionConfiguration"
    property_types = {
        "ApiId": GeneratedProperty(),
        "Code": GeneratedProperty(),
        "CodeS3Location": GeneratedProperty(),
        "DataSourceName": GeneratedProperty(),
        "Description": GeneratedProperty(),
        "MaxBatchSize": GeneratedProperty(),
        "Name": GeneratedProperty(),
        "Runtime": GeneratedProperty(),
        "SyncConfig": GeneratedProperty(),
    }

    ApiId: Intrinsicable[str]
    DataSourceName: Intrinsicable[str]
    Name: str
    Code: Optional[str]
    CodeS3Location: Optional[str]
    Description: Optional[str]
    MaxBatchSize: Optional[int]
    Runtime: Optional[AppSyncRuntimeType]
    SyncConfig: Optional[SyncConfigType]

    runtime_attrs = {"function_id": lambda self: fnGetAtt(self.logical_id, "FunctionId")}


class Resolver(Resource):
    resource_type = "AWS::AppSync::Resolver"
    property_types = {
        "ApiId": GeneratedProperty(),
        "CachingConfig": GeneratedProperty(),
        "Code": GeneratedProperty(),
        "CodeS3Location": GeneratedProperty(),
        "DataSourceName": GeneratedProperty(),
        "FieldName": GeneratedProperty(),
        "Kind": GeneratedProperty(),
        "MaxBatchSize": GeneratedProperty(),
        "PipelineConfig": GeneratedProperty(),
        "Runtime": GeneratedProperty(),
        "SyncConfig": GeneratedProperty(),
        "TypeName": GeneratedProperty(),
    }

    ApiId: Intrinsicable[str]
    CachingConfig: Optional[CachingConfigType]
    Code: Optional[str]
    CodeS3Location: Optional[str]
    DataSourceName: Optional[str]
    FieldName: str
    Kind: Optional[str]
    MaxBatchSize: Optional[int]
    PipelineConfig: Optional[PipelineConfigType]
    Runtime: Optional[AppSyncRuntimeType]
    SyncConfig: Optional[SyncConfigType]
    TypeName: str


class ApiKey(Resource):
    resource_type = "AWS::AppSync::ApiKey"
    property_types = {
        "ApiId": GeneratedProperty(),
        "ApiKeyId": GeneratedProperty(),
        "Description": GeneratedProperty(),
        "Expires": GeneratedProperty(),
    }

    ApiId: Intrinsicable[str]
    ApiKeyId: Optional[str]
    Description: Optional[str]
    Expires: Optional[float]


class DomainName(Resource):
    resource_type = "AWS::AppSync::DomainName"
    property_types = {
        "CertificateArn": GeneratedProperty(),
        "Description": GeneratedProperty(),
        "DomainName": GeneratedProperty(),
    }

    CertificateArn: str
    DomainName: str
    Description: Optional[str]

    runtime_attrs = {"domain_name": lambda self: ref(self.logical_id)}


class DomainNameApiAssociation(Resource):
    resource_type = "AWS::AppSync::DomainNameApiAssociation"
    property_types = {
        "ApiId": GeneratedProperty(),
        "DomainName": GeneratedProperty(),
    }

    ApiId: Intrinsicable[str]
    DomainName: str


class ApiCache(Resource):
    resource_type = "AWS::AppSync::ApiCache"
    property_types = {
        "ApiCachingBehavior": GeneratedProperty(),
        "ApiId": GeneratedProperty(),
        "AtRestEncryptionEnabled": GeneratedProperty(),
        "TransitEncryptionEnabled": GeneratedProperty(),
        "Ttl": GeneratedProperty(),
        "Type": GeneratedProperty(),
    }

    ApiCachingBehavior: str
    ApiId: Intrinsicable[str]
    Type: str
    Ttl: float
    AtRestEncryptionEnabled: Optional[bool]
    TransitEncryptionEnabled: Optional[bool]
