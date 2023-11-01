from typing import Any, Dict, List

from samtranslator.utils.actions import Action


def traverse(
    input_value: Any,
    actions: List[Action],
) -> Any:
    """
    Driver method that performs the actual traversal of input and calls the execute method of the provided actions.

    Traversal Algorithm:

    Imagine the input dictionary/list as a tree. We are doing a Pre-Order tree traversal here where we first
    process the root node before going to its children. Dict and Lists are the only two iterable nodes.
    Everything else is a leaf node.

    :param input_value: Any primitive type  (dict, array, string etc) whose value might contain a changed value
    :param actions: Method that will be called to actually resolve the function.
    :return: Modified `input` with values resolved
    """

    for action in actions:
        action.execute(input_value)

    if isinstance(input_value, dict):
        return _traverse_dict(input_value, actions)
    if isinstance(input_value, list):
        return _traverse_list(input_value, actions)
    # We can iterate only over dict or list types. Primitive types are terminals

    return input_value


def _traverse_dict(
    input_dict: Dict[str, Any],
    actions: List[Action],
) -> Any:
    """
    Traverse a dictionary to resolves changed values on every value

    :param input_dict: Input dictionary to traverse
    :param actions: This is just to pass it to the template partition
    :return: Modified dictionary with values resolved
    """
    for key, value in input_dict.items():
        input_dict[key] = traverse(value, actions)

    return input_dict


def _traverse_list(
    input_list: List[Any],
    actions: List[Action],
) -> Any:
    """
    Traverse a list to resolve changed values on every element

    :param input_list: List of input
    :param actions: This is just to pass it to the template partition
    :return: Modified list with values functions resolved
    """
    for index, value in enumerate(input_list):
        input_list[index] = traverse(value, actions)

    return input_list
