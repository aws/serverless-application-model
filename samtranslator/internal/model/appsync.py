from typing import Any, Dict, List, Optional, Union

from typing_extensions import TypedDict

from samtranslator.model import GeneratedProperty, Resource
from samtranslator.model.intrinsics import fnGetAtt
from samtranslator.utils.types import Intrinsicable

NONE_DATASOURCE_LITERALS = {"NONE", "None", "none"}


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

    runtime_attrs = {"arn": lambda self: fnGetAtt(self.logical_id, "DataSourceArn")}


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
    DataSourceName: str
    Name: str
    Code: Optional[str]
    CodeS3Location: Optional[str]
    Description: Optional[str]
    MaxBatchSize: Optional[int]
    Runtime: Optional[AppSyncRuntimeType]
    SyncConfig: Optional[SyncConfigType]
