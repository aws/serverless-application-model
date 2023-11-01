from abc import ABC, abstractmethod
from typing import Any, Dict


class Action(ABC):
    """
    Base class for Resolver function actions. Each Resolver function must subclass this,
    override the , and provide a execute() method
    """

    @abstractmethod
    def execute(self, template: Dict[str, Any]) -> Dict[str, Any]:
        pass


class ResolveDependsOn(Action):
    DependsOn = "DependsOn"

    def __init__(self, resolution_data: Dict[str, str]):
        """
        Initializes ResolveDependsOn. Where data necessary to resolve execute can be provided.

        :param resolution_data: Extra data necessary to resolve execute properly.
        """
        self.resolution_data = resolution_data

    def execute(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve DependsOn when logical ids get changed when transforming (ex: AWS::Serverless::LayerVersion)

        :param input_dict: Chunk of the template that is attempting to be resolved
        :param resolution_data: Dictionary of the original and changed logical ids
        :return: Modified dictionary with values resolved
        """
        # Checks if input dict is resolvable
        if template is None or not self._can_handle_depends_on(input_dict=template):
            return template
        # Checks if DependsOn is valid
        if not (isinstance(template[self.DependsOn], (list, str))):
            return template
        # Check if DependsOn matches the original value of a changed_logical_id key
        for old_logical_id, changed_logical_id in self.resolution_data.items():
            # Done like this as there is no other way to know if this is a DependsOn vs some value named the
            # same as the old logical id. (ex LayerName is commonly the old_logical_id)
            if isinstance(template[self.DependsOn], list):
                for index, value in enumerate(template[self.DependsOn]):
                    if value == old_logical_id:
                        template[self.DependsOn][index] = changed_logical_id
            elif template[self.DependsOn] == old_logical_id:
                template[self.DependsOn] = changed_logical_id
        return template

    def _can_handle_depends_on(self, input_dict: Dict[str, Any]) -> bool:
        """
        Checks if the input dictionary is of length one and contains "DependsOn"

        :param input_dict: the Dictionary that is attempting to be resolved
        :return boolean value of validation attempt
        """
        return isinstance(input_dict, dict) and self.DependsOn in input_dict
