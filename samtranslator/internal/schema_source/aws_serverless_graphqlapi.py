from abc import ABC, abstractmethod
from typing import Dict, Iterator, Optional, Union

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


class LambdaConflictHandlerConfig(BaseModel):
    LambdaConflictHandlerArn: PassThroughProp


class Sync(BaseModel):
    ConflictDetection: PassThroughProp
    ConflictHandler: Optional[PassThroughProp]
    LambdaConflictHandlerConfig: LambdaConflictHandlerConfig


class ResourceWithCodeMixIn(ABC):
    @abstractmethod
    def get_code_uri(self) -> Optional[str]:
        """Return it if it exists"""

    @abstractmethod
    def set_code_uri(self, value: str) -> None:
        """Set it if it exists"""

    @abstractmethod
    def _resolve_code_uri(self, logical_id: str = "", path_to_function_file: str = "") -> None:
        """Set all code uri"""


class Function(BaseModel, ResourceWithCodeMixIn):
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

    def _resolve_code_uri(self, logical_id: str = "", path_to_code_file: str = "") -> None:
        """It's ok to add a method https://stackoverflow.com/a/60048805"""
        if all([not self.get_code_uri(), not self.InlineCode, path_to_code_file]):
            name = self.Name or logical_id
            self.set_code_uri(f"{path_to_code_file}/{name}.js")

    def get_code_uri(self) -> Optional[str]:
        return self.CodeUri

    def set_code_uri(self, value: str) -> None:
        self.CodeUri = value


class Properties(BaseModel, ResourceWithCodeMixIn):
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

    def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        self._resolve_code_uri()

    def get_code_uri(self) -> Optional[str]:
        return self.SchemaUri

    def set_code_uri(self, value: str) -> None:
        self.SchemaUri = value

    def _resolve_code_uri(self, logical_id: str = "", path_to_code_file: str = "") -> None:
        if not self.ResolverCodeSettings:
            return

        root_path = self.ResolverCodeSettings.CodeRootPath
        function_folder = self.ResolverCodeSettings.FunctionsFolder or "functions"

        if self.get_code_uri() and self._is_relative_path(self.get_code_uri() or ""):
            self.set_code_uri(f"{root_path}/{self.get_code_uri()}")
        path_to_code_file = f"{root_path}/{function_folder}"
        for logical_id, function in (self.Functions or {}).items():
            function._resolve_code_uri(logical_id=logical_id, path_to_code_file=path_to_code_file)

    def list_resources_with_code(self) -> Iterator[ResourceWithCodeMixIn]:
        yield self
        for _, function in (self.Functions or {}).items():
            yield function

    @staticmethod
    def _is_relative_path(path: str) -> bool:
        # TODO: implement
        return True


class Resource(BaseModel):
    Type: Literal["AWS::Serverless::GraphQLApi"]
    Properties: Properties
