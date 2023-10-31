from typing import Any, Callable, Dict, List


class Traverse:
    """
    Base Class for traversing
    """

    def traverse_wrapper(self, input_value: Any, resolution_data: Dict[str, Any], resolver_method_name: str) -> Any:
        """
        Wraps the Driver Method which allows the resolver method to be changed as needed

        :param input_value: Any primitive type  (dict, array, string etc) whose value might contain a changed value
        :param resolution_data: Data that will help with resolution. For example, changed logical ids from hashing
        LayerVersion
        :param resolver_method_name: Name of the method that will be called to actually resolve an the function. This method
            is called with the parameters `(input, resolution_data)`.
        :return: Modified `input` with values resolved
        """
        if resolver_method_name == "DependsOn":
            return self._traverse(input_value, resolution_data, self._resolve_depends_on)

        return input_value

    # here is where I would put constant variables
    def _traverse(
        self,
        input_value: Any,
        resolution_data: Dict[str, Any],
        resolver_method: Callable[[Dict[str, Any], Any], Any],
    ) -> Any:
        """
        Driver method that performs the actual traversal of input and calls the appropriate `resolver_method` when
        to perform the resolution.

        :param input_value: Any primitive type  (dict, array, string etc) whose value might contain a changed value
        :param resolution_data: Data that will help with resolution. For example, changed logical ids from hashing
            LayerVersion
        :param resolver_method: Method that will be called to actually resolve an the function. This method
            is called with the parameters `(input, resolution_data)`.
        :return: Modified `input` with values resolved
        """

        # There is data to help with resolution. Skip the traversal altogether
        if len(resolution_data) == 0:
            return input_value

        #
        # Traversal Algorithm:
        #
        # Imagine the input dictionary/list as a tree. We are doing a Pre-Order tree traversal here where we first
        # process the root node before going to its children. Dict and Lists are the only two iterable nodes.
        # Everything else is a leaf node.
        #
        #
        # We will try to resolve if we can, otherwise return the original input. In some cases, resolving
        # an value will result in a terminal state ie. {"Depends": "foo"} could resolve to a string "Foo1234". In other
        # cases, resolving values is only partial and we might need to continue traversing the tree
        # to handle nested values in the future. All of these cases lend well towards a Pre-Order traversal where we try and
        # process the value which results in a modified sub-tree to traverse.
        #
        input_value = resolver_method(input_value, resolution_data)
        if isinstance(input_value, dict):
            return self._traverse_dict(input_value, resolution_data, resolver_method)
        if isinstance(input_value, list):
            return self._traverse_list(input_value, resolution_data, resolver_method)
        # We can iterate only over dict or list types. Primitive types are terminals

        return input_value

    def _traverse_dict(
        self,
        input_dict: Dict[str, Any],
        resolution_data: Dict[str, Any],
        resolver_method: Callable[[Dict[str, Any], Any], Any],
    ) -> Any:
        """
        Traverse a dictionary to resolves changed values on every value

        :param input_dict: Input dictionary to traverse
        :param resolution_data: Data that the `resolver_method` needs to operate
        :param resolver_method: Method that can actually resolve values, if it detects one
        :return: Modified dictionary with values resolved
        """
        for key, value in input_dict.items():
            input_dict[key] = self._traverse(value, resolution_data, resolver_method)

        return input_dict

    def _traverse_list(
        self,
        input_list: List[Any],
        resolution_data: Dict[str, Any],
        resolver_method: Callable[[Dict[str, Any], Any], Any],
    ) -> Any:
        """
        Traverse a list to resolve changed values on every element

        :param input_list: List of input
        :param resolution_data: Data that the `resolver_method` needs to operate
        :param resolver_method: Method that can actually resolves values, if it detects one
        :return: Modified list with values functions resolved
        """
        for index, value in enumerate(input_list):
            input_list[index] = self._traverse(value, resolution_data, resolver_method)

        return input_list

    def _can_handle_depends_on(self, input_dict: Dict[str, Any]) -> bool:
        """
        Checks if the input dictionary is of length one and contains "DependsOn"

        :param input_dict: the Dictionary that is attempting to be resolved
        :return boolean value of validation attempt
        """
        return isinstance(input_dict, dict) and "DependsOn" in input_dict

    def _resolve_depends_on(self, input_dict: Dict[str, Any], resolution_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Resolve DependsOn when logical ids get changed when transforming (ex: AWS::Serverless::LayerVersion)

        :param input_dict: Chunk of the template that is attempting to be resolved
        :param resolution_data: Dictionary of the original and changed logical ids
        :return: Modified dictionary with values resolved
        """
        # Checks if input dict is resolvable
        if input_dict is None or not self._can_handle_depends_on(input_dict=input_dict):
            return input_dict
        # Checks if DependsOn is valid
        if not (isinstance(input_dict["DependsOn"], (list, str))):
            return input_dict
        # Check if DependsOn matches the original value of a changed_logical_id key
        for old_logical_id, changed_logical_id in resolution_data.items():
            # Done like this as there is no other way to know if this is a DependsOn vs some value named the
            # same as the old logical id. (ex LayerName is commonly the old_logical_id)
            if isinstance(input_dict["DependsOn"], list):
                for index, value in enumerate(input_dict["DependsOn"]):
                    if value == old_logical_id:
                        input_dict["DependsOn"][index] = changed_logical_id
            elif input_dict["DependsOn"] == old_logical_id:
                input_dict["DependsOn"] = changed_logical_id
        return input_dict
