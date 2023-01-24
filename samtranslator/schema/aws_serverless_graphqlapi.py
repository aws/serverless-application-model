from typing import Optional

from typing_extensions import Literal

from samtranslator.schema.common import BaseModel, get_prop, DictStrAny

properties = get_prop("sam-resource-graphqlapi")

# TODO: add docs
class Auth(BaseModel):
    Type: str


class Properties(BaseModel):
    Auth: Auth
    Tags: Optional[DictStrAny]
    Name: Optional[str]
    XrayEnabled: Optional[bool]


class Resource(BaseModel):
    Type: Literal["AWS::Serverless::GraphQLApi"]
    Properties: Properties
