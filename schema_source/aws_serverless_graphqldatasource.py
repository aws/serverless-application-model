from typing import Optional

from typing_extensions import Literal

from schema_source.common import BaseModel, SamIntrinsicable, get_prop

properties = get_prop("sam-resource-graphqldatasource")


# TODO: add docs
class DeltaSync(BaseModel):
    BaseTableTTL: str
    DeltaSyncTableName: str
    DeltaSyncTableTTL: str


class DynamoDB(BaseModel):
    TableName: str
    Region: Optional[str]
    UseCallerCredentials: Optional[bool]
    Versioned: Optional[bool]
    DeltaSync: Optional[DeltaSync]


class DataSourceConfig(BaseModel):
    DynamoDB: Optional[DynamoDB]


class Properties(BaseModel):
    ApiId: SamIntrinsicable[str]
    Type: str
    DataSourceConfig: DataSourceConfig
    Name: Optional[str]
    Description: Optional[str]
    ServiceRoleArn: Optional[str]


class Resource(BaseModel):
    Type: Literal["AWS::Serverless::GraphQLDataSource"]
    Properties: Properties
