"""Type related utils."""

from typing import Any, TypeVar, Union

T = TypeVar("T")

Intrinsicable = Union[dict[str, Any], T]
