"""A plug-able validator to help raise exception when some value is unexpected."""
from enum import Enum
from typing import Generic, Optional, TypeVar

from samtranslator.model.exceptions import InvalidResourceException


class ExpectedType(Enum):
    MAP = ("map", dict)
    LIST = ("list", list)
    STRING = ("string", str)
    INTEGER = ("integer", int)


T = TypeVar("T")


class _ResourcePropertyValueValidator(Generic[T]):
    value: Optional[T]
    resource_logical_id: str
    property_identifier: str

    def __init__(self, value: Optional[T], resource_logical_id: str, property_identifier: str) -> None:
        self.value = value
        self.resource_logical_id = resource_logical_id
        self.property_identifier = property_identifier

    def to_be_a(self, expected_type: ExpectedType, message: Optional[str] = "") -> Optional[T]:
        """
        Validate the type of the value and return the value if valid.

        raise InvalidResourceException for invalid values.
        """
        type_description, type_class = expected_type.value
        if not isinstance(self.value, type_class):
            if not message:
                message = f"Property '{self.property_identifier}' should be a {type_description}."
            raise InvalidResourceException(self.resource_logical_id, message)
        # mypy is not smart to derive class from expected_type.value[1], ignore types:
        return self.value  # type: ignore

    def to_not_be_none(self, message: Optional[str] = "") -> T:
        """
        Validate the value is not None and return the value if valid.

        raise InvalidResourceException for None values.
        """
        if self.value is None:
            if not message:
                message = f"Property '{self.property_identifier}' is required."
            raise InvalidResourceException(self.resource_logical_id, message)
        return self.value

    #
    # alias methods:
    #
    def to_be_a_map(self, message: Optional[str] = "") -> Optional[T]:
        return self.to_be_a(ExpectedType.MAP, message)

    def to_be_a_list(self, message: Optional[str] = "") -> Optional[T]:
        return self.to_be_a(ExpectedType.LIST, message)

    def to_be_a_string(self, message: Optional[str] = "") -> Optional[T]:
        return self.to_be_a(ExpectedType.STRING, message)

    def to_be_an_integer(self, message: Optional[str] = "") -> Optional[T]:
        return self.to_be_a(ExpectedType.INTEGER, message)


sam_expect = _ResourcePropertyValueValidator
