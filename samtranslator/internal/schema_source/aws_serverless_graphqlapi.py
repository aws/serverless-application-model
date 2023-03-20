from typing import Dict, Optional, Union

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
    TableName: str
    ServiceRoleArn: Optional[PassThroughProp]
    TableArn: Optional[str]
    Permissions: Optional[PermissionsType]
    Name: Optional[str]
    Description: Optional[PassThroughProp]
    Region: Optional[PassThroughProp]
    DeltaSync: Optional[DeltaSync]
    UseCallerCredentials: Optional[PassThroughProp]
    Versioned: Optional[PassThroughProp]


class Runtime(BaseModel):
    Name: PassThroughProp
    Version: PassThroughProp


class ResolverCodeSettings(BaseModel):
    CodeRootPath: str
    Runtime: Runtime
    ResolversFolder: Optional[str]
    FunctionsFolder: Optional[str]


class CachingConfig(BaseModel):
    pass


class Resolver(BaseModel):
    FieldName: Optional[str]
    CachingConfig: Optional[CachingConfig]
    InlineCode: Optional[str]
    CodeUri: Optional[str]
    DataSource: Optional[str]
    DataSourceName: Optional[str]
    MaxBatchSize: Optional[PassThroughProp]
    Functions: PassThroughProp  # TODO: EDIT THIS TO FUNCTIONS WHEN I MERGE
    Runtime: Optional[Runtime]
    GenerateCode: Optional[bool]


class LambdaConflictHandlerConfig(BaseModel):
    LambdaConflictHandlerArn: PassThroughProp


class Sync(BaseModel):
    ConflictDetection: PassThroughProp
    ConflictHandler: Optional[PassThroughProp]
    LambdaConflictHandlerConfig: LambdaConflictHandlerConfig


class Function(BaseModel):
    DataSource: Optional[str]
    DataSourceName: Optional[str]
    Runtime: Optional[Runtime]
    InlineCode: Optional[str]
    CodeUri: Optional[str]
    Description: Optional[PassThroughProp]
    MaxBatchSize: Optional[PassThroughProp]
    Name: Optional[str]
    Id: Optional[PassThroughProp]
    Sync: Optional[Sync]


class Properties(BaseModel):
    Auth: Auth
    Tags: Optional[DictStrAny]
    Name: Optional[str]
    XrayEnabled: Optional[bool]
    SchemaInline: Optional[str]
    SchemaUri: Optional[str]
    Logging: Optional[Union[Logging, bool]]
    DynamoDBDataSources: Optional[Dict[str, DynamoDBDataSource]]
    ResolverCodeSettings: Optional[ResolverCodeSettings]
    Functions: Optional[Dict[str, Function]]


class Resource(BaseModel):
    Type: Literal["AWS::Serverless::GraphQLApi"]
    Properties: Properties
