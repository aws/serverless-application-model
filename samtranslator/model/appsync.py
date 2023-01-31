from typing import Any, Dict, List, Optional

from typing_extensions import TypedDict

from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import IS_DICT, IS_STR, is_type, list_of


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
