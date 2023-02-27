from typing import Any, Dict, List, Optional

from typing_extensions import TypedDict

from samtranslator.model import GeneratedProperty, Resource
from samtranslator.model.intrinsics import fnGetAtt
from samtranslator.utils.types import Intrinsicable

# Data source constants can be found here under "Type" property:
# https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-appsync-datasource.html
SUPPORTED_DATASOURCES = {"AMAZON_DYNAMODB"}


class DeltaSyncConfigType(TypedDict):
    BaseTableTTL: str
    DeltaSyncTableName: str
    DeltaSyncTableTTL: str


class DynamoDBConfigType(TypedDict, total=False):
    AwsRegion: str
    TableName: str
    UseCallerCredentials: bool
    Versioned: bool
    DeltaSyncConfig: DeltaSyncConfigType


class LogConfigType(TypedDict, total=False):
    CloudWatchLogsRoleArn: Intrinsicable[str]
    ExcludeVerboseContent: bool
    FieldLogLevel: str


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
