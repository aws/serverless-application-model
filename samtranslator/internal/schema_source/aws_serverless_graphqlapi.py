from typing import Dict, List, Literal, Optional, Union

from samtranslator.internal.schema_source.common import (
    BaseModel,
    DictStrAny,
    PassThroughProp,
    PermissionsType,
    SamIntrinsicable,
    get_prop,
)

AuthenticationTypes = Literal["AWS_IAM", "API_KEY", "AWS_LAMBDA", "OPENID_CONNECT", "AMAZON_COGNITO_USER_POOLS"]

properties = get_prop("sam-resource-graphqlapi")


# TODO: add docs
class LambdaAuthorizerConfig(BaseModel):
    AuthorizerResultTtlInSeconds: Optional[PassThroughProp] = None
    AuthorizerUri: PassThroughProp
    IdentityValidationExpression: Optional[PassThroughProp] = None


class OpenIDConnectConfig(BaseModel):
    AuthTTL: Optional[PassThroughProp] = None
    ClientId: Optional[PassThroughProp] = None
    IatTTL: Optional[PassThroughProp] = None
    Issuer: Optional[PassThroughProp] = None


class UserPoolConfig(BaseModel):
    AppIdClientRegex: Optional[PassThroughProp] = None
    AwsRegion: Optional[PassThroughProp] = None
    DefaultAction: Optional[PassThroughProp] = None
    UserPoolId: PassThroughProp


class Authorizer(BaseModel):
    Type: AuthenticationTypes
    LambdaAuthorizer: Optional[LambdaAuthorizerConfig] = None
    OpenIDConnect: Optional[OpenIDConnectConfig] = None
    UserPool: Optional[UserPoolConfig] = None


class Auth(Authorizer):
    Additional: Optional[List[Authorizer]] = None


class ApiKey(BaseModel):
    ApiKeyId: Optional[PassThroughProp] = None
    Description: Optional[PassThroughProp] = None
    ExpiresOn: Optional[PassThroughProp] = None


class Logging(BaseModel):
    CloudWatchLogsRoleArn: Optional[PassThroughProp] = None
    ExcludeVerboseContent: Optional[PassThroughProp] = None
    FieldLogLevel: Optional[PassThroughProp] = None


# Type alias to avoid field name shadowing class name in Pydantic v2
_Logging = Logging


class DeltaSync(BaseModel):
    BaseTableTTL: PassThroughProp
    DeltaSyncTableName: PassThroughProp
    DeltaSyncTableTTL: PassThroughProp


# Type alias to avoid field name shadowing class name in Pydantic v2
_DeltaSync = DeltaSync


class DynamoDBDataSource(BaseModel):
    TableName: PassThroughProp
    ServiceRoleArn: Optional[PassThroughProp] = None
    TableArn: Optional[PassThroughProp] = None
    Permissions: Optional[PermissionsType] = None
    Name: Optional[PassThroughProp] = None
    Description: Optional[PassThroughProp] = None
    Region: Optional[PassThroughProp] = None
    DeltaSync: Optional[_DeltaSync] = None
    UseCallerCredentials: Optional[PassThroughProp] = None
    Versioned: Optional[PassThroughProp] = None


class LambdaDataSource(BaseModel):
    FunctionArn: PassThroughProp
    ServiceRoleArn: Optional[PassThroughProp] = None
    Name: Optional[PassThroughProp] = None
    Description: Optional[PassThroughProp] = None


class DataSources(BaseModel):
    DynamoDb: Optional[Dict[str, DynamoDBDataSource]] = None
    Lambda: Optional[Dict[str, LambdaDataSource]] = None


# Type alias to avoid field name shadowing class name in Pydantic v2
_DataSources = DataSources


class Runtime(BaseModel):
    Name: PassThroughProp
    Version: PassThroughProp


# Type alias to avoid field name shadowing class name in Pydantic v2
_Runtime = Runtime


class LambdaConflictHandlerConfig(BaseModel):
    LambdaConflictHandlerArn: PassThroughProp


# Type alias to avoid field name shadowing class name in Pydantic v2
_LambdaConflictHandlerConfig = LambdaConflictHandlerConfig


class Sync(BaseModel):
    ConflictDetection: PassThroughProp
    ConflictHandler: Optional[PassThroughProp] = None
    LambdaConflictHandlerConfig: Optional[_LambdaConflictHandlerConfig] = None


# Type alias to avoid field name shadowing class name in Pydantic v2
_Sync = Sync


class Function(BaseModel):
    DataSource: Optional[SamIntrinsicable[str]] = None
    Runtime: Optional[_Runtime] = None
    InlineCode: Optional[PassThroughProp] = None
    CodeUri: Optional[PassThroughProp] = None
    Description: Optional[PassThroughProp] = None
    MaxBatchSize: Optional[PassThroughProp] = None
    Name: Optional[str] = None
    Id: Optional[PassThroughProp] = None
    Sync: Optional[_Sync] = None


class Caching(BaseModel):
    Ttl: PassThroughProp
    CachingKeys: Optional[List[PassThroughProp]] = None


# Type alias to avoid field name shadowing class name in Pydantic v2
_Caching = Caching


class Resolver(BaseModel):
    FieldName: Optional[str] = None
    Caching: Optional[_Caching] = None
    InlineCode: Optional[PassThroughProp] = None
    CodeUri: Optional[PassThroughProp] = None
    MaxBatchSize: Optional[PassThroughProp] = None
    Pipeline: Optional[List[str]] = (
        None  # keeping it optional allows for easier validation in to_cloudformation with better error messages
    )
    Runtime: Optional[_Runtime] = None
    Sync: Optional[_Sync] = None


class DomainName(BaseModel):
    CertificateArn: PassThroughProp
    DomainName: PassThroughProp
    Description: Optional[PassThroughProp] = None


# Type alias to avoid field name shadowing class name in Pydantic v2
_DomainName = DomainName


class Cache(BaseModel):
    ApiCachingBehavior: PassThroughProp
    Ttl: PassThroughProp
    Type: PassThroughProp
    AtRestEncryptionEnabled: Optional[PassThroughProp] = None
    TransitEncryptionEnabled: Optional[PassThroughProp] = None


# Type alias to avoid field name shadowing class name in Pydantic v2
_Cache = Cache


class Properties(BaseModel):
    Auth: Auth
    Tags: Optional[DictStrAny] = None
    Name: Optional[PassThroughProp] = None
    XrayEnabled: Optional[bool] = None
    SchemaInline: Optional[PassThroughProp] = None
    SchemaUri: Optional[PassThroughProp] = None
    Logging: Optional[Union[_Logging, bool]] = None
    DataSources: Optional[_DataSources] = None
    Functions: Optional[Dict[str, Function]] = None
    Resolvers: Optional[Dict[str, Dict[str, Resolver]]] = None
    ApiKeys: Optional[Dict[str, ApiKey]] = None
    DomainName: Optional[_DomainName] = None
    Cache: Optional[_Cache] = None
    Visibility: Optional[PassThroughProp] = None
    OwnerContact: Optional[PassThroughProp] = None
    IntrospectionConfig: Optional[PassThroughProp] = None
    QueryDepthLimit: Optional[PassThroughProp] = None
    ResolverCountLimit: Optional[PassThroughProp] = None


class Resource(BaseModel):
    Type: Literal["AWS::Serverless::GraphQLApi"]
    Properties: Properties
