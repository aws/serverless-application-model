from typing import Any, Dict


class SupportedResourceReferences:
    """
    Class that contains information about the resource references supported in this SAM template, along with the
    value they should resolve to. As the translator processes the SAM template, it keeps building up this
    collection which is finally used to resolve all the references in output CFN template.
    """

    def __init__(self) -> None:
        # This is a two level map like:
        # { "LogicalId": {"Property": "Value"} }
        self._refs: Dict[str, Dict[str, Any]] = {}

    def add(self, logical_id, property_name, value):  # type: ignore[no-untyped-def]
        """
        Add the information that resource with given `logical_id` supports the given `property`, and that a reference
        to `logical_id.property` resolves to given `value.

        Example:

            "MyApi.Deployment" -> "MyApiDeployment1234567890"

        :param logical_id: Logical ID of the resource  (Ex: MyLambdaFunction)
        :param property_name: Property on the resource that can be referenced (Ex: Alias)
        :param value: Value that this reference resolves to.
        :return: nothing
        """

        if not logical_id or not property_name:
            raise ValueError("LogicalId and property must be a non-empty string")

        if not value or not isinstance(value, str):
            raise ValueError("Property value must be a non-empty string")

        if logical_id not in self._refs:
            self._refs[logical_id] = {}

        if property_name in self._refs[logical_id]:
            raise ValueError(f"Cannot add second reference value to {logical_id}.{property_name} property")

        self._refs[logical_id][property_name] = value

    def get(self, logical_id, property_name):  # type: ignore[no-untyped-def]
        """
        Returns the value of the reference for given logical_id at given property. Ex: MyFunction.Alias

        :param logical_id: Logical Id of the resource
        :param property_name: Property of the resource you want to resolve. None if you want to get value of all properties
        :return: Value of this property if present. None otherwise
        """

        # By defaulting to empty dictionary, we can handle the case where logical_id is not in map without if statements
        prop_values = self.get_all(logical_id)  # type: ignore[no-untyped-call]
        if prop_values:
            return prop_values.get(property_name, None)
        return None

    def get_all(self, logical_id):  # type: ignore[no-untyped-def]
        """
        Get all properties and their values supported by the resource with given logical ID

        :param logical_id: Logical ID of the resource
        :return: Map of property names to values. None, if the logicalId does not exist
        """
        return self._refs.get(logical_id, None)

    def __len__(self) -> int:
        """
        To make len(this_object) work
        :return: Number of resource references available
        """
        return len(self._refs)

    def __str__(self) -> str:
        return str(self._refs)
