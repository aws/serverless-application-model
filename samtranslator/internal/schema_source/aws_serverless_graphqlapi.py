from typing import Optional

from typing_extensions import Literal

<<<<<<<< HEAD:samtranslator/schema/aws_serverless_graphqlapi.py
from samtranslator.schema.common import BaseModel, get_prop, DictStrAny
========
from samtranslator.internal.schema_source.common import BaseModel, DictStrAny, get_prop
>>>>>>>> cb9be389 (move schema files over):samtranslator/internal/schema_source/aws_serverless_graphqlapi.py

properties = get_prop("sam-resource-graphqlapi")


# TODO: add docs
class Auth(BaseModel):
    Type: str


class Properties(BaseModel):
    Auth: Auth
    Tags: Optional[DictStrAny]
    Name: Optional[str]
    XrayEnabled: Optional[bool]
    SchemaInline: Optional[str]
    SchemaUri: Optional[str]


class Resource(BaseModel):
    Type: Literal["AWS::Serverless::GraphQLApi"]
    Properties: Properties
