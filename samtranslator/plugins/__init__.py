import logging
from abc import ABC
from enum import Enum
from typing import Optional

LOG = logging.getLogger(__name__)


class LifeCycleEvents(Enum):
    """
    Enum of LifeCycleEvents
    """

    before_transform_template = "before_transform_template"
    before_transform_resource = "before_transform_resource"
    after_transform_template = "after_transform_template"


class BasePlugin(ABC):
    """
    Base class for a NoOp plugin that implements all available hooks
    """

    _custom_name: Optional[str]

    def __init__(self, name: Optional[str] = None) -> None:
        """
        Initialize the plugin with optional given name.

        The optional name argument is for compatibility purpose.
        In SAM-T codebase all plugins use the default name (class name).
        :param name: Custom name of this plugin.
        """
        self._custom_name = name

    @classmethod
    def _class_name(cls) -> str:
        return cls.__name__

    @property
    def name(self) -> str:
        if self._custom_name:
            return self._custom_name
        return self._class_name()

    # Plugins can choose to skip implementing certain hook methods. In which case we will default to a
    # NoOp implementation
    def on_before_transform_resource(self, logical_id, resource_type, resource_properties):  # type: ignore[no-untyped-def] # noqa: B027
        """
        Hook method to execute on `before_transform_resource` life cycle event. Plugins are free to modify the
        whole template or properties of the resource.

        If you have a SAM resource like:
         {
             "Type": "type",
             Properties: {"key": "value" }
         }

        `resource_type` equals "type"
        `resource_properties` equals {"key": "value" }

        :param string logical_id: LogicalId of the resource that is being processed
        :param string resource_type: Type of the resource being processed
        :param dict resource_properties: Properties of the resource being processed.
        :return: Nothing
        :raises InvalidResourceException: If the hook decides throw this exception on validation failures
        """

    # Plugins can choose to skip implementing certain hook methods. In which case we will default to a
    # NoOp implementation
    def on_before_transform_template(self, template_dict):  # type: ignore[no-untyped-def] # noqa: B027
        """
        Hook method to execute on "before_transform_template" life cycle event. Plugins are free to modify the
        whole template, inject new resources, or modify certain sections of the template.

        This method is called after the template passes basic structural validation. Template dictionary contains a
        "Resources" object is not empty.

        This method is free to change the contents of template dictionary. Take care to produce a valid SAM template.
        Any bugs produced by plugins will be opaque to customers and create cryptic, hard-to-understand error messages
        for customers.

        :param dict template: Entire SAM template as a dictionary.
        :return: nothing
        :raises InvalidDocumentException: If the hook decides that the SAM template is invalid.
        """

    # Plugins can choose to skip implementing certain hook methods. In which case we will default to a
    # NoOp implementation
    def on_after_transform_template(self, template):  # type: ignore[no-untyped-def] # noqa: B027
        """
        Hook method to execute on "after_transform_template" life cycle event. Plugins may further modify
        the template. Warning: any changes made in this lifecycle action by a plugin will not be
        validated and may cause the template to fail deployment with hard-to-understand error messages
        for customers.

        This method is called after the template passes all other template transform actions, right before
        the resources are resolved to their final logical ID names.

        :param dict template: Entire SAM template as a dictionary.
        :return: nothing
        :raises InvalidDocumentException: If the hook decides that the SAM template is invalid.
        :raises InvalidResourceException: If the hook decides that a SAM resource is invalid.
        """
