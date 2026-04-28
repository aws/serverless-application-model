from typing import Any, Union

from samtranslator.intrinsics.resolver import IntrinsicsResolver
from samtranslator.model.exceptions import InvalidResourceException


def resolve_string_parameter_in_resource(
    logical_id: str,
    intrinsics_resolver: IntrinsicsResolver,
    parameter_value: Union[str, dict[str, Any]] | None,
    parameter_name: str,
) -> Union[str, dict[str, Any]] | None:
    """Try to resolve values in a resource from template parameters."""
    if not parameter_value:
        return parameter_value
    value = intrinsics_resolver.resolve_parameter_refs(parameter_value)

    if not isinstance(value, str) and not isinstance(value, dict):
        raise InvalidResourceException(
            logical_id,
            f"Could not resolve parameter for '{parameter_name}' or parameter is not a String.",
        )
    return value
