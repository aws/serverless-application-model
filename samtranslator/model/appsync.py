from typing import Any, Dict, List, Optional

from typing_extensions import TypedDict

from samtranslator.model import PropertyType, Resource
from samtranslator.model.intrinsics import fnGetAtt
from samtranslator.model.types import IS_DICT, IS_STR, is_type, list_of
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


class GraphQLApi(Resource):
    resource_type = "AWS::AppSync::GraphQLApi"
    property_types = {
        "Name": PropertyType(True, IS_STR),
        "Tags": PropertyType(False, list_of(IS_DICT)),
        "XrayEnabled": PropertyType(False, is_type(bool)),
        "AuthenticationType": PropertyType(True, IS_STR),
    }

    Name: str
    AuthenticationType: str
    Tags: Optional[List[Dict[str, Any]]]
    XrayEnabled: Optional[bool]

    runtime_attrs = {"api_id": lambda self: fnGetAtt(self.logical_id, "ApiId")}


class GraphQLSchema(Resource):
    resource_type = "AWS::AppSync::GraphQLSchema"
    property_types = {
        "ApiId": PropertyType(True, IS_DICT),
        "Definition": PropertyType(False, IS_STR),
        "DefinitionS3Location": PropertyType(False, IS_STR),
    }

    ApiId: Intrinsicable[str]
    Definition: Optional[str]
    DefinitionS3Location: Optional[str]


class DataSource(Resource):
    resource_type = "AWS::AppSync::DataSource"
    property_types = {
        "ApiId": PropertyType(True, IS_STR),
        "Description": PropertyType(False, IS_STR),
        "Name": PropertyType(True, IS_STR),
        "Type": PropertyType(True, IS_STR),
        "ServiceRoleArn": PropertyType(True, IS_STR),
        "DynamoDBConfig": PropertyType(True, IS_DICT),
    }

    ApiId: Intrinsicable[str]
    Description: Optional[str]
    Name: str
    Type: str
    ServiceRoleArn: str
    DynamoDBConfig: DynamoDBConfigType
