from six import string_types


class SupportedResourceReferences(object):
    """
    Class that contains information about the resource references supported in this SAM template, along with the
    value they should resolve to. As the translator processes the SAM template, it keeps building up this
    collection which is finally used to resolve all the references in output CFN template.
    """

    def __init__(self):

        # This is a two level map like:
        # { "LogicalId": {"Property": "Value"} }
        self._refs = {}

    def add(self, logical_id, property, value):
        """
        Add the information that resource with given `logical_id` supports the given `property`, and that a reference
        to `logical_id.property` resolves to given `value.

        Example:

            "MyApi.Deployment" -> "MyApiDeployment1234567890"

        :param logical_id: Logical ID of the resource  (Ex: MyLambdaFunction)
        :param property: Property on the resource that can be referenced (Ex: Alias)
        :param value: Value that this reference resolves to.
        :return: nothing
        """

        if not logical_id or not property:
            raise ValueError("LogicalId and property must be a non-empty string")

        if not value or not isinstance(value, string_types):
            raise ValueError("Property value must be a non-empty string")

        if logical_id not in self._refs:
            self._refs[logical_id] = {}

        if property in self._refs[logical_id]:
            raise ValueError("Cannot add second reference value to {}.{} property".format(logical_id, property))

        self._refs[logical_id][property] = value

    def get(self, logical_id, property):
        """
        Returns the value of the reference for given logical_id at given property. Ex: MyFunction.Alias

        :param logical_id: Logical Id of the resource
        :param property: Property of the resource you want to resolve. None if you want to get value of all properties
        :return: Value of this property if present. None otherwise
        """

        # By defaulting to empty dictionary, we can handle the case where logical_id is not in map without if statements
        prop_values = self.get_all(logical_id)
        if prop_values:
            return prop_values.get(property, None)
        else:
            return None

    def get_all(self, logical_id):
        """
        Get all properties and their values supported by the resource with given logical ID

        :param logical_id: Logical ID of the resource
        :return: Map of property names to values. None, if the logicalId does not exist
        """
        return self._refs.get(logical_id, None)

    def __len__(self):
        """
        To make len(this_object) work
        :return: Number of resource references available
        """
        return len(self._refs)

    def __str__(self):
        return str(self._refs)
