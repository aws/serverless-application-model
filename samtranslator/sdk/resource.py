from enum import Enum
from typing import Any, Dict

from samtranslator.model.exceptions import InvalidDocumentException, InvalidTemplateException
from samtranslator.model.types import is_str


class SamResource(object):
    """
    Class representing a SAM resource. It is designed to make minimal assumptions about the resource structure.
    Any mutating methods also touch only "Properties" and "Type" attributes of the resource. This allows compatibility
    with any CloudFormation constructs, like DependsOn, Conditions etc.
    """

    type = None
    properties: Dict[str, Any] = {}  # TODO: Replace `Any` with something more specific

    def __init__(self, resource_dict):
        """
        Initialize the object given the resource as a dictionary

        :param dict resource_dict: Resource dictionary containing type & properties
        """

        self.resource_dict = resource_dict
        self.type = resource_dict.get("Type")
        self.condition = resource_dict.get("Condition", None)
        self.deletion_policy = resource_dict.get("DeletionPolicy", None)
        self.update_replace_policy = resource_dict.get("UpdateReplacePolicy", None)

        # Properties is *not* required. Ex: SimpleTable resource has no required properties
        self.properties = resource_dict.get("Properties", {})

    def valid(self):
        """
        Checks if the resource data is valid

        :return: True, if the resource is valid
        """
        # As long as the type is valid and type string.
        # validate the condition should be string

        if self.condition:

            if not is_str()(self.condition, should_raise=False):
                raise InvalidDocumentException([InvalidTemplateException("Every Condition member must be a string.")])

        if self.deletion_policy:

            if not is_str()(self.deletion_policy, should_raise=False):
                raise InvalidDocumentException(
                    [InvalidTemplateException("Every DeletionPolicy member must be a string.")]
                )

        if self.update_replace_policy:

            if not is_str()(self.update_replace_policy, should_raise=False):
                raise InvalidDocumentException(
                    [InvalidTemplateException("Every UpdateReplacePolicy member must be a string.")]
                )

        return SamResourceType.has_value(self.type)

    def to_dict(self):

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
    def has_value(cls, value):
        """
        Checks if the given value belongs to the Enum

        :param string value: Value to be checked
        :return: True, if input is in the Enum
        """
        return any(value == item.value for item in cls)
