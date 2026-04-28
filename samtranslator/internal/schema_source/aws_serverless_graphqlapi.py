from __future__ import annotations

from typing import Literal, Union

from samtranslator.internal.schema_source.common import (
    BaseModel,
    DictStrAny,
    PassThroughProp,
    PermissionsType,
    SamIntrinsicable,
    get_prop,
)

# All PassThroughProp properties in this file are passed directly to AWS::AppSync CloudFormation resources
# and inherit their documentation from the CloudFormation schema.
#

PROPERTIES_STEM = "sam-resource-graphqlapi"

AuthenticationTypes = Literal["AWS_IAM", "API_KEY", "AWS_LAMBDA", "OPENID_CONNECT", "AMAZON_COGNITO_USER_POOLS"]

properties = get_prop(PROPERTIES_STEM)
authprovider = get_prop("sam-property-graphqlapi-auth-authprovider")
auth = get_prop("sam-property-graphqlapi-auth")
apikey = get_prop("sam-property-graphqlapi-apikeys")
dynamodbdatasource = get_prop("sam-property-graphqlapi-datasource-dynamodb")
lambdadatasource = get_prop("sam-property-graphqlapi-datasource-lambda")
datasource = get_prop("sam-property-graphqlapi-datasource")
function = get_prop("sam-property-graphqlapi-function")
runtime = get_prop("sam-property-graphqlapi-function-runtime")
resolver = get_prop("sam-property-graphqlapi-resolver")


class LambdaAuthorizerConfig(BaseModel):
    # Maps to AWS::AppSync::GraphQLApi.LambdaAuthorizerConfig
    AuthorizerResultTtlInSeconds: PassThroughProp | None
    AuthorizerUri: PassThroughProp
    IdentityValidationExpression: PassThroughProp | None


class OpenIDConnectConfig(BaseModel):
    # Maps to AWS::AppSync::GraphQLApi.OpenIDConnectConfig
    AuthTTL: PassThroughProp | None
    ClientId: PassThroughProp | None
    IatTTL: PassThroughProp | None
    Issuer: PassThroughProp | None


class UserPoolConfig(BaseModel):
    # Maps to AWS::AppSync::GraphQLApi.UserPoolConfig
    AppIdClientRegex: PassThroughProp | None
    AwsRegion: PassThroughProp | None
    DefaultAction: PassThroughProp | None
    UserPoolId: PassThroughProp


class Authorizer(BaseModel):
    Type: AuthenticationTypes = authprovider("Type")
    # Maps to AWS::AppSync::GraphQLApi.AdditionalAuthenticationProvider
    LambdaAuthorizer: LambdaAuthorizerConfig | None
    OpenIDConnect: OpenIDConnectConfig | None
    UserPool: UserPoolConfig | None


class Auth(Authorizer):
    Additional: list[Authorizer] | None = auth("Additional")


class ApiKey(BaseModel):
    ApiKeyId: PassThroughProp | None = apikey("ApiKeyId")
    Description: PassThroughProp | None = apikey("Description")
    ExpiresOn: PassThroughProp | None = apikey("ExpiresOn")


class Logging(BaseModel):
    # Maps to AWS::AppSync::GraphQLApi LogConfig
    CloudWatchLogsRoleArn: PassThroughProp | None
    ExcludeVerboseContent: PassThroughProp | None
    FieldLogLevel: PassThroughProp | None


class DeltaSync(BaseModel):
    # Maps to AWS::AppSync::DataSource.DeltaSyncConfig
    BaseTableTTL: PassThroughProp
    DeltaSyncTableName: PassThroughProp
    DeltaSyncTableTTL: PassThroughProp


class DynamoDBDataSource(BaseModel):
    TableName: PassThroughProp = dynamodbdatasource("TableName")
    ServiceRoleArn: PassThroughProp | None = dynamodbdatasource("ServiceRoleArn")
    TableArn: PassThroughProp | None = dynamodbdatasource("TableArn")
    Permissions: PermissionsType | None = dynamodbdatasource("Permissions")
    Name: PassThroughProp | None = dynamodbdatasource("Name")
    Description: PassThroughProp | None = dynamodbdatasource("Description")
    Region: PassThroughProp | None = dynamodbdatasource("Region")
    DeltaSync: DeltaSync | None = dynamodbdatasource("DeltaSync")
    UseCallerCredentials: PassThroughProp | None = dynamodbdatasource("UseCallerCredentials")
    Versioned: PassThroughProp | None = dynamodbdatasource("Versioned")


class LambdaDataSource(BaseModel):
    FunctionArn: PassThroughProp = lambdadatasource("FunctionArn")
    ServiceRoleArn: PassThroughProp | None = lambdadatasource("ServiceRoleArn")
    Name: PassThroughProp | None = lambdadatasource("Name")
    Description: PassThroughProp | None = lambdadatasource("Description")


class DataSources(BaseModel):
    DynamoDb: dict[str, DynamoDBDataSource] | None = datasource("DynamoDb")
    Lambda: dict[str, LambdaDataSource] | None = datasource("Lambda")


class Runtime(BaseModel):
    Name: PassThroughProp = runtime("Name")
    Version: PassThroughProp = runtime("Version")


class LambdaConflictHandlerConfig(BaseModel):
    # Maps to AWS::AppSync::FunctionConfiguration.LambdaConflictHandlerConfig
    LambdaConflictHandlerArn: PassThroughProp


class Sync(BaseModel):
    # Maps to AWS::AppSync::FunctionConfiguration.SyncConfig
    ConflictDetection: PassThroughProp
    ConflictHandler: PassThroughProp | None
    LambdaConflictHandlerConfig: LambdaConflictHandlerConfig | None


class Function(BaseModel):
    DataSource: SamIntrinsicable[str] | None = function("DataSource")
    Runtime: Runtime | None = function("Runtime")
    InlineCode: PassThroughProp | None = function("InlineCode")
    CodeUri: PassThroughProp | None = function("CodeUri")
    Description: PassThroughProp | None = function("Description")
    MaxBatchSize: PassThroughProp | None = function("MaxBatchSize")
    Name: str | None = function("Name")
    Id: PassThroughProp | None = function("Id")
    Sync: Sync | None = function("Sync")


class Caching(BaseModel):
    # Maps to AWS::AppSync::Resolver.CachingConfig
    Ttl: PassThroughProp
    CachingKeys: list[PassThroughProp] | None


class Resolver(BaseModel):
    FieldName: str | None = resolver("FieldName")
    Caching: Caching | None = resolver("Caching")
    InlineCode: PassThroughProp | None = resolver("InlineCode")
    CodeUri: PassThroughProp | None = resolver("CodeUri")
    MaxBatchSize: PassThroughProp | None = resolver("MaxBatchSize")
    Pipeline: list[str] | None = resolver(
        "Pipeline"
    )  # keeping it optional allows for easier validation in to_cloudformation with better error messages
    Runtime: Runtime | None = resolver("Runtime")
    Sync: Sync | None = resolver("Sync")


class DomainName(BaseModel):
    # Maps to AWS::AppSync::DomainName
    CertificateArn: PassThroughProp
    DomainName: PassThroughProp
    Description: PassThroughProp | None


class Cache(BaseModel):
    # Maps to AWS::AppSync::ApiCache
    ApiCachingBehavior: PassThroughProp
    Ttl: PassThroughProp
    Type: PassThroughProp
    AtRestEncryptionEnabled: PassThroughProp | None
    TransitEncryptionEnabled: PassThroughProp | None


class Properties(BaseModel):
    Auth: Auth = properties("Auth")
    Tags: DictStrAny | None = properties("Tags")
    Name: PassThroughProp | None = properties("Name")
    XrayEnabled: bool | None = properties("XrayEnabled")
    SchemaInline: PassThroughProp | None = properties("SchemaInline")
    SchemaUri: PassThroughProp | None = properties("SchemaUri")
    Logging: Union[Logging, bool] | None = properties("Logging")
    DataSources: DataSources | None = properties("DataSources")
    Functions: dict[str, Function] | None = properties("Functions")
    Resolvers: dict[str, dict[str, Resolver]] | None = properties("Resolvers")
    ApiKeys: dict[str, ApiKey] | None = properties("ApiKeys")
    DomainName: DomainName | None = properties("DomainName")
    Cache: Cache | None = properties("Cache")
    Visibility: PassThroughProp | None  # TODO: add documentation when available in sam-docs.json
    OwnerContact: PassThroughProp | None  # TODO: add documentation when available in sam-docs.json
    IntrospectionConfig: PassThroughProp | None  # TODO: add documentation when available in sam-docs.json
    QueryDepthLimit: PassThroughProp | None  # TODO: add documentation when available in sam-docs.json
    ResolverCountLimit: PassThroughProp | None  # TODO: add documentation when available in sam-docs.json


class Resource(BaseModel):
    Type: Literal["AWS::Serverless::GraphQLApi"]
    Properties: Properties
