"""
Classes representing SAM template and resources.
"""

from typing import Any, Dict, Iterator, Optional, Set, Tuple, Union

from samtranslator.sdk.resource import SamResource


class SamTemplate:
    """
    Class representing the SAM template
    """

    def __init__(self, template_dict: Dict[str, Any]) -> None:
        """
        Initialize with a template dictionary, that contains "Resources" dictionary

        :param dict template_dict: Template Dictionary
        """
        self.template_dict = template_dict
        self.resources = template_dict["Resources"]

    def iterate(self, resource_types: Optional[Set[str]] = None) -> Iterator[Tuple[str, SamResource]]:
        """
        Iterate over all resources within the SAM template, optionally filtering by type

        :param set resource_types: Optional types to filter the resources by
        :yields (string, SamResource): Tuple containing LogicalId and the resource
        """
        if resource_types is None:
            resource_types = set()
        for logicalId, resource_dict in self.resources.items():
            resource = SamResource(resource_dict)
            needs_filter = resource.valid()
            if resource_types:
                needs_filter = needs_filter and resource.type in resource_types

            if needs_filter:
                yield logicalId, resource

    def set(  # noqa: builtin-attribute-shadowing
        self, logical_id: str, resource: Union[SamResource, Dict[str, Any]]
    ) -> None:
        """
        Adds the resource to dictionary with given logical Id. It will overwrite, if the logical_id is already used.

        :param string logical_id: Logical Id to set to
        :param SamResource or dict resource: The actual resource data
        """

        resource_dict = resource
        if isinstance(resource, SamResource):
            resource_dict = resource.to_dict()

        self.resources[logical_id] = resource_dict

    def get_globals(self) -> Dict[str, Any]:
        """
        Gets the global section of the template

        :return dict: Global section of the template
        """
        return self.template_dict.get("Globals") or {}

    def get(self, logical_id: str) -> Optional[SamResource]:
        """
        Gets the resource at the given logical_id if present

        :param string logical_id: Id of the resource
        :return SamResource: Resource, if available at the Id. None, otherwise
        """
        if logical_id not in self.resources:
            return None

        return SamResource(self.resources.get(logical_id))

    def delete(self, logicalId):  # type: ignore[no-untyped-def]
        """
        Deletes a resource at the given ID

        :param string logicalId: Resource to delete
        """

        if logicalId in self.resources:
            del self.resources[logicalId]

    def to_dict(self) -> Dict[str, Any]:
        """
        Returns the template as a dictionary

        :return dict: SAM template as a dictionary
        """
        self.template_dict["Resource"] = self.resources
        return self.template_dict
