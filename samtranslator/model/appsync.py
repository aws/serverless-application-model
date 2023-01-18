from typing import Optional, Dict, Any

from samtranslator.model import PropertyType, Resource
from samtranslator.model.types import IS_DICT, is_type, list_of, IS_STR


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
    Tags: Optional[Dict[str, Any]]
    XrayEnabled: Optional[bool]
