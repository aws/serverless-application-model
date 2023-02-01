from typing import Optional, Dict, Any, List
from typing_extensions import TypedDict

from samtranslator.model import PropertyType, Resource
from samtranslator.model.intrinsics import fnGetAtt
from samtranslator.model.types import IS_DICT, IS_STR, is_type, list_of
from samtranslator.utils.types import Intrinsicable


class Auth(TypedDict, total=False):
    Type: str


class GraphQLApi(Resource):
    resource_type = "AWS::AppSync::GraphQLApi"
    property_types = {
        "Name": PropertyType(True, IS_STR),
        "Tags": PropertyType(False, list_of(IS_DICT)),
        "XrayEnabled": PropertyType(False, is_type(bool)),
        "AuthenticationType": PropertyType(True, IS_STR),
    }

    Name: str
    AuthenticationType: str
    Tags: Optional[List[Dict[str, Any]]]
    XrayEnabled: Optional[bool]

    runtime_attrs = {"api_id": lambda self: fnGetAtt(self.logical_id, "ApiId")}


class GraphQLSchema(Resource):
    resource_type = "AWS::AppSync::GraphQLSchema"
    property_types = {
        "ApiId": PropertyType(True, IS_DICT),
        "Definition": PropertyType(False, IS_STR),
        "DefinitionS3Location": PropertyType(False, IS_STR),
    }

    ApiId: Intrinsicable[str]
    Definition: Optional[str]
    DefinitionS3Location: Optional[str]
