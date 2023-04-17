from typing import Any, Dict, List, Optional, Union

from typing_extensions import TypedDict

from samtranslator.model import GeneratedProperty, Resource
from samtranslator.model.intrinsics import fnGetAtt
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


class LogConfigType(TypedDict, total=False):
    CloudWatchLogsRoleArn: Intrinsicable[str]
    ExcludeVerboseContent: bool
    FieldLogLevel: str


class AppSyncRuntimeType(TypedDict):
    Name: str
    RuntimeVersion: str


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
    }

    Name: str
    AuthenticationType: str
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
    }

    ApiId: Intrinsicable[str]
    Description: Optional[str]
    Name: str
    Type: str
    ServiceRoleArn: str
    DynamoDBConfig: DynamoDBConfigType

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
