from __future__ import annotations

from typing import Dict, List, Literal, Optional, Union

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
    AuthorizerResultTtlInSeconds: Optional[PassThroughProp]
    AuthorizerUri: PassThroughProp
    IdentityValidationExpression: Optional[PassThroughProp]


class OpenIDConnectConfig(BaseModel):
    # Maps to AWS::AppSync::GraphQLApi.OpenIDConnectConfig
    AuthTTL: Optional[PassThroughProp]
    ClientId: Optional[PassThroughProp]
    IatTTL: Optional[PassThroughProp]
    Issuer: Optional[PassThroughProp]


class UserPoolConfig(BaseModel):
    # Maps to AWS::AppSync::GraphQLApi.UserPoolConfig
    AppIdClientRegex: Optional[PassThroughProp]
    AwsRegion: Optional[PassThroughProp]
    DefaultAction: Optional[PassThroughProp]
    UserPoolId: PassThroughProp


class Authorizer(BaseModel):
    Type: AuthenticationTypes = authprovider("Type")
    # Maps to AWS::AppSync::GraphQLApi.AdditionalAuthenticationProvider
    LambdaAuthorizer: Optional[LambdaAuthorizerConfig]
    OpenIDConnect: Optional[OpenIDConnectConfig]
    UserPool: Optional[UserPoolConfig]


class Auth(Authorizer):
    Additional: Optional[List[Authorizer]] = auth("Additional")


class ApiKey(BaseModel):
    ApiKeyId: Optional[PassThroughProp] = apikey("ApiKeyId")
    Description: Optional[PassThroughProp] = apikey("Description")
    ExpiresOn: Optional[PassThroughProp] = apikey("ExpiresOn")


class Logging(BaseModel):
    # Maps to AWS::AppSync::GraphQLApi LogConfig
    CloudWatchLogsRoleArn: Optional[PassThroughProp]
    ExcludeVerboseContent: Optional[PassThroughProp]
    FieldLogLevel: Optional[PassThroughProp]


class DeltaSync(BaseModel):
    # Maps to AWS::AppSync::DataSource.DeltaSyncConfig
    BaseTableTTL: PassThroughProp
    DeltaSyncTableName: PassThroughProp
    DeltaSyncTableTTL: PassThroughProp


class DynamoDBDataSource(BaseModel):
    TableName: PassThroughProp = dynamodbdatasource("TableName")
    ServiceRoleArn: Optional[PassThroughProp] = dynamodbdatasource("ServiceRoleArn")
    TableArn: Optional[PassThroughProp] = dynamodbdatasource("TableArn")
    Permissions: Optional[PermissionsType] = dynamodbdatasource("Permissions")
    Name: Optional[PassThroughProp] = dynamodbdatasource("Name")
    Description: Optional[PassThroughProp] = dynamodbdatasource("Description")
    Region: Optional[PassThroughProp] = dynamodbdatasource("Region")
    DeltaSync: Optional[DeltaSync] = dynamodbdatasource("DeltaSync")
    UseCallerCredentials: Optional[PassThroughProp] = dynamodbdatasource("UseCallerCredentials")
    Versioned: Optional[PassThroughProp] = dynamodbdatasource("Versioned")


class LambdaDataSource(BaseModel):
    FunctionArn: PassThroughProp = lambdadatasource("FunctionArn")
    ServiceRoleArn: Optional[PassThroughProp] = lambdadatasource("ServiceRoleArn")
    Name: Optional[PassThroughProp] = lambdadatasource("Name")
    Description: Optional[PassThroughProp] = lambdadatasource("Description")


class DataSources(BaseModel):
    DynamoDb: Optional[Dict[str, DynamoDBDataSource]] = datasource("DynamoDb")
    Lambda: Optional[Dict[str, LambdaDataSource]] = datasource("Lambda")


class Runtime(BaseModel):
    Name: PassThroughProp = runtime("Name")
    Version: PassThroughProp = runtime("Version")


class LambdaConflictHandlerConfig(BaseModel):
    # Maps to AWS::AppSync::FunctionConfiguration.LambdaConflictHandlerConfig
    LambdaConflictHandlerArn: PassThroughProp


class Sync(BaseModel):
    # Maps to AWS::AppSync::FunctionConfiguration.SyncConfig
    ConflictDetection: PassThroughProp
    ConflictHandler: Optional[PassThroughProp]
    LambdaConflictHandlerConfig: Optional[LambdaConflictHandlerConfig]


class Function(BaseModel):
    DataSource: Optional[SamIntrinsicable[str]] = function("DataSource")
    Runtime: Optional[Runtime] = function("Runtime")
    InlineCode: Optional[PassThroughProp] = function("InlineCode")
    CodeUri: Optional[PassThroughProp] = function("CodeUri")
    Description: Optional[PassThroughProp] = function("Description")
    MaxBatchSize: Optional[PassThroughProp] = function("MaxBatchSize")
    Name: Optional[str] = function("Name")
    Id: Optional[PassThroughProp] = function("Id")
    Sync: Optional[Sync] = function("Sync")


class Caching(BaseModel):
    # Maps to AWS::AppSync::Resolver.CachingConfig
    Ttl: PassThroughProp
    CachingKeys: Optional[List[PassThroughProp]]


class Resolver(BaseModel):
    FieldName: Optional[str] = resolver("FieldName")
    Caching: Optional[Caching] = resolver("Caching")
    InlineCode: Optional[PassThroughProp] = resolver("InlineCode")
    CodeUri: Optional[PassThroughProp] = resolver("CodeUri")
    MaxBatchSize: Optional[PassThroughProp] = resolver("MaxBatchSize")
    Pipeline: Optional[List[str]] = resolver(
        "Pipeline"
    )  # keeping it optional allows for easier validation in to_cloudformation with better error messages
    Runtime: Optional[Runtime] = resolver("Runtime")
    Sync: Optional[Sync] = resolver("Sync")


class DomainName(BaseModel):
    # Maps to AWS::AppSync::DomainName
    CertificateArn: PassThroughProp
    DomainName: PassThroughProp
    Description: Optional[PassThroughProp]


class Cache(BaseModel):
    # Maps to AWS::AppSync::ApiCache
    ApiCachingBehavior: PassThroughProp
    Ttl: PassThroughProp
    Type: PassThroughProp
    AtRestEncryptionEnabled: Optional[PassThroughProp]
    TransitEncryptionEnabled: Optional[PassThroughProp]


class Properties(BaseModel):
    Auth: Auth = properties("Auth")
    Tags: Optional[DictStrAny] = properties("Tags")
    Name: Optional[PassThroughProp] = properties("Name")
    XrayEnabled: Optional[bool] = properties("XrayEnabled")
    SchemaInline: Optional[PassThroughProp] = properties("SchemaInline")
    SchemaUri: Optional[PassThroughProp] = properties("SchemaUri")
    Logging: Optional[Union[Logging, bool]] = properties("Logging")
    DataSources: Optional[DataSources] = properties("DataSources")
    Functions: Optional[Dict[str, Function]] = properties("Functions")
    Resolvers: Optional[Dict[str, Dict[str, Resolver]]] = properties("Resolvers")
    ApiKeys: Optional[Dict[str, ApiKey]] = properties("ApiKeys")
    DomainName: Optional[DomainName] = properties("DomainName")
    Cache: Optional[Cache] = properties("Cache")
    Visibility: Optional[PassThroughProp]  # TODO: add documentation when available in sam-docs.json
    OwnerContact: Optional[PassThroughProp]  # TODO: add documentation when available in sam-docs.json
    IntrospectionConfig: Optional[PassThroughProp]  # TODO: add documentation when available in sam-docs.json
    QueryDepthLimit: Optional[PassThroughProp]  # TODO: add documentation when available in sam-docs.json
    ResolverCountLimit: Optional[PassThroughProp]  # TODO: add documentation when available in sam-docs.json


class Resource(BaseModel):
    Type: Literal["AWS::Serverless::GraphQLApi"]
    Properties: Properties
