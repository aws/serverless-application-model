from typing import Optional, Dict, Any

from typing_extensions import Literal

from samtranslator.schema.common import BaseModel, PassThrough, get_prop

properties = get_prop("sam-resource-graphqlapi")

# TODO: add docs
class Properties(BaseModel):
    Auth: Dict[str, Any]
    Tags: Optional[PassThrough]
    Name: Optional[str]
    XrayEnabled: Optional[bool]


class Resource(BaseModel):
    Type: Literal["AWS::Serverless::GraphQLApi"]
    Properties: Properties
