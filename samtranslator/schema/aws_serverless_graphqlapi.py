from typing import Optional, List

from typing_extensions import Literal

from samtranslator.schema.common import BaseModel, get_prop

properties = get_prop("sam-resource-graphqlapi")

# TODO: add docs
class Tags(BaseModel):
    Key: str
    Value: str


class Auth(BaseModel):
    Type: str


class Properties(BaseModel):
    Auth: Auth
    Tags: Optional[List[Tags]]
    Name: Optional[str]
    XrayEnabled: Optional[bool]


class Resource(BaseModel):
    Type: Literal["AWS::Serverless::GraphQLApi"]
    Properties: Properties
