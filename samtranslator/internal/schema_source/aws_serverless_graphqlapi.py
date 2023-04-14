from typing import Dict, List, Optional, Union

from typing_extensions import Literal

from samtranslator.internal.schema_source.common import (
    BaseModel,
    DictStrAny,
    PassThroughProp,
    PermissionsType,
    get_prop,
)

properties = get_prop("sam-resource-graphqlapi")


# TODO: add docs
class Auth(BaseModel):
    Type: str


class Logging(BaseModel):
    CloudWatchLogsRoleArn: Optional[PassThroughProp]
    ExcludeVerboseContent: Optional[PassThroughProp]
    FieldLogLevel: Optional[str]


class DeltaSync(BaseModel):
    BaseTableTTL: str
    DeltaSyncTableName: str
    DeltaSyncTableTTL: str


class DynamoDBDataSource(BaseModel):
    TableName: PassThroughProp
    ServiceRoleArn: Optional[PassThroughProp]
    TableArn: Optional[PassThroughProp]
    Permissions: Optional[PermissionsType]
    Name: Optional[str]
    Description: Optional[PassThroughProp]
    Region: Optional[PassThroughProp]
    DeltaSync: Optional[DeltaSync]
    UseCallerCredentials: Optional[PassThroughProp]
    Versioned: Optional[PassThroughProp]


class DataSources(BaseModel):
    DynamoDB: Optional[Dict[str, DynamoDBDataSource]]


class Runtime(BaseModel):
    Name: PassThroughProp
    Version: PassThroughProp


class ResolverCodeSettings(BaseModel):
    CodeRootPath: str
    Runtime: Runtime
    FunctionsFolder: Optional[str]


class LambdaConflictHandlerConfig(BaseModel):
    LambdaConflictHandlerArn: PassThroughProp


class Sync(BaseModel):
    ConflictDetection: PassThroughProp
    ConflictHandler: Optional[PassThroughProp]
    LambdaConflictHandlerConfig: Optional[LambdaConflictHandlerConfig]


class Function(BaseModel):
    DataSource: Optional[str]
    DataSourceName: Optional[str]
    Runtime: Optional[Runtime]
    InlineCode: Optional[PassThroughProp]
    CodeUri: Optional[PassThroughProp]
    Description: Optional[PassThroughProp]
    MaxBatchSize: Optional[PassThroughProp]
    Name: Optional[str]
    Id: Optional[PassThroughProp]
    Sync: Optional[Sync]


class Caching(BaseModel):
    Ttl: PassThroughProp
    CachingKeys: Optional[List[PassThroughProp]]


class AppSyncResolver(BaseModel):
    FieldName: Optional[str]
    Caching: Optional[Caching]
    InlineCode: Optional[PassThroughProp]
    CodeUri: Optional[PassThroughProp]
    DataSource: Optional[str]
    DataSourceName: Optional[str]
    MaxBatchSize: Optional[PassThroughProp]
    Functions: Optional[List[Union[str, Dict[str, Function]]]]
    Runtime: Optional[Runtime]
    Sync: Optional[Sync]


class Properties(BaseModel):
    Auth: Auth
    Tags: Optional[DictStrAny]
    Name: Optional[str]
    XrayEnabled: Optional[bool]
    SchemaInline: Optional[PassThroughProp]
    SchemaUri: Optional[PassThroughProp]
    Logging: Optional[Union[Logging, bool]]
    DataSources: Optional[DataSources]
    ResolverCodeSettings: Optional[ResolverCodeSettings]
    Functions: Optional[Dict[str, Function]]
    AppSyncResolvers: Optional[Dict[str, Dict[str, AppSyncResolver]]]


class Resource(BaseModel):
    Type: Literal["AWS::Serverless::GraphQLApi"]
    Properties: Properties
