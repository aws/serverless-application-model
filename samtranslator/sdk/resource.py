from enum import Enum
from typing import Any, Dict, List, Optional, Union

from samtranslator.model.exceptions import InvalidDocumentException, InvalidTemplateException
from samtranslator.model.types import IS_STR


class SamResource:
    """
    Class representing a SAM resource. It is designed to make minimal assumptions about the resource structure.
    Any mutating methods also touch only "Properties" and "Type" attributes of the resource. This allows compatibility
    with any CloudFormation constructs, like DependsOn, Conditions etc.
    """

    type = None  # noqa: A003
    properties: Dict[str, Any] = {}  # TODO: Replace `Any` with something more specific

    def __init__(self, resource_dict: Dict[str, Any]) -> None:
        """
        Initialize the object given the resource as a dictionary

        :param dict resource_dict: Resource dictionary containing type & properties
        """

        self.resource_dict = resource_dict
        self.type = resource_dict.get("Type")
        self.condition = resource_dict.get("Condition", None)
        self.deletion_policy = resource_dict.get("DeletionPolicy", None)
        self.update_replace_policy = resource_dict.get("UpdateReplacePolicy", None)
        self.ignore_globals: Optional[Union[str, List[str]]] = resource_dict.get("IgnoreGlobals", None)

        # Properties is *not* required. Ex: SimpleTable resource has no required properties
        self.properties = resource_dict.get("Properties", {})

    def valid(self) -> bool:
        """
        Checks if the resource data is valid

        :return: True, if the resource is valid
        """
        # As long as the type is valid and type string.
        # validate the condition should be string
        # TODO Refactor this file so that it has logical id, can use sam_expect here after that
        if self.condition and not IS_STR(self.condition, should_raise=False):
            raise InvalidDocumentException([InvalidTemplateException("Every Condition member must be a string.")])

        # TODO: should we raise exception if `self.type` is not a string?
        return isinstance(self.type, str) and SamResourceType.has_value(self.type)

    def to_dict(self) -> Dict[str, Any]:
        if self.valid():
            # Touch a resource dictionary ONLY if it is valid
            # Modify only Type & Properties section to preserve CloudFormation properties like DependsOn, Conditions etc
            self.resource_dict["Type"] = self.type
            self.resource_dict["Properties"] = self.properties

        return self.resource_dict


class SamResourceType(Enum):
    """
    Enum of supported SAM types
    """

    Api = "AWS::Serverless::Api"
    Function = "AWS::Serverless::Function"
    SimpleTable = "AWS::Serverless::SimpleTable"
    Application = "AWS::Serverless::Application"
    LambdaLayerVersion = "AWS::Serverless::LayerVersion"
    HttpApi = "AWS::Serverless::HttpApi"
    StateMachine = "AWS::Serverless::StateMachine"

    @classmethod
    def has_value(cls, value: str) -> bool:
        """
        Checks if the given value belongs to the Enum

        :param string value: Value to be checked
        :return: True, if input is in the Enum
        """
        return any(value == item.value for item in cls)
