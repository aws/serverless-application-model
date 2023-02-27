from typing import Optional

from typing_extensions import Literal

from samtranslator.internal.schema_source.common import BaseModel, PassThroughProp, get_prop

properties = get_prop("sam-resource-graphqldatasource")


# TODO: add docs
class DeltaSyncConfig(BaseModel):
    BaseTableTTL: str
    DeltaSyncTableName: str
    DeltaSyncTableTTL: str


class DynamoDBConfig(BaseModel):
    TableName: str
    Region: Optional[str]
    UseCallerCredentials: Optional[PassThroughProp]
    Versioned: Optional[PassThroughProp]
    DeltaSync: Optional[DeltaSyncConfig]


class Properties(BaseModel):
    ApiId: PassThroughProp
    Type: str
    DynamoDBConfig: DynamoDBConfig
    Name: Optional[str]
    Description: Optional[str]
    ServiceRoleArn: Optional[str]


class Resource(BaseModel):
    Type: Literal["AWS::Serverless::GraphQLDataSource"]
    Properties: Properties
