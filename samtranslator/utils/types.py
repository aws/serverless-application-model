"""Type related utils."""

from typing import Any, Dict, TypeVar, Union

T = TypeVar("T")

Intrinsicable = Union[Dict[str, Any], T]
