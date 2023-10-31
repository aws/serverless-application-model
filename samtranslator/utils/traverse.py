from typing import Any, Dict, List

from samtranslator.utils.resolve_actions import ResolveAction


def traverse(template: Dict[str, Any], actions: List[ResolveAction]) -> Any:
    """
    Calls the correct traversal method

    :param template: The template that needs modifying
    :param actions: That actions that need to be performed to the template
    :return: Modified Template

    TODO: Add multiple strategies and choose between those with an Optional value
    """
    return _preorder_traverse(template, actions)


def _execute_actions(template: Dict[str, Any], actions: List[ResolveAction]) -> Any:
    """
    Calls the resolver methods when they are in the list of ResolveActions. Then calls the actions passed to traverse.

    :param template: The template that needs modifying
    :param actions: actions to be executed.
    :return: Modified Template
    """
    if len(actions) == 0:
        return template

    for action in actions:
        action.execute(template)

    return template


def _preorder_traverse(
    input_value: Any,
    actions: List[ResolveAction],
) -> Any:
    """
    Driver method that performs the actual traversal of input and calls the appropriate `resolver_method` when
    to perform the resolution.

    :param input_value: Any primitive type  (dict, array, string etc) whose value might contain a changed value
    :param actions: Method that will be called to actually resolve the function.
    :return: Modified `input` with values resolved
    """

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
    input_value = _execute_actions(input_value, actions)
    if isinstance(input_value, dict):
        return _traverse_dict(input_value, actions)
    if isinstance(input_value, list):
        return _traverse_list(input_value, actions)
    # We can iterate only over dict or list types. Primitive types are terminals

    return input_value


def _traverse_dict(
    input_dict: Dict[str, Any],
    actions: List[ResolveAction],
) -> Any:
    """
    Traverse a dictionary to resolves changed values on every value

    :param input_dict: Input dictionary to traverse
    :param actions: This is just to pass it to the template partition
    :return: Modified dictionary with values resolved
    """
    for key, value in input_dict.items():
        input_dict[key] = _preorder_traverse(value, actions)

    return input_dict


def _traverse_list(
    input_list: List[Any],
    actions: List[ResolveAction],
) -> Any:
    """
    Traverse a list to resolve changed values on every element

    :param input_list: List of input
    :param actions: This is just to pass it to the template partition
    :return: Modified list with values functions resolved
    """
    for index, value in enumerate(input_list):
        input_list[index] = _preorder_traverse(value, actions)

    return input_list
