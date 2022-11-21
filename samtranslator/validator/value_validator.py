"""A plug-able validator to help raise exception when some value is unexpected."""
from enum import Enum
from typing import Generic, Optional, TypeVar

from samtranslator.model.exceptions import InvalidEventException, InvalidResourceException


class ExpectedType(Enum):
    MAP = ("map", dict)
    LIST = ("list", list)
    STRING = ("string", str)
    INTEGER = ("integer", int)


T = TypeVar("T")


class _ResourcePropertyValueValidator(Generic[T]):
    value: Optional[T]
    resource_logical_id: Optional[str]
    event_id: Optional[str]
    property_identifier: str

    def __init__(
        self, value: Optional[T], resource_id: str, property_identifier: str, is_sam_event: bool = False
    ) -> None:
        self.value = value
        self.property_identifier = property_identifier
        self.resource_logical_id, self.event_id = (None, None)
        if is_sam_event:
            self.event_id = resource_id
        else:
            self.resource_logical_id = resource_id

    def to_be_a(self, expected_type: ExpectedType, message: Optional[str] = "") -> T:
        """
        Validate the type of the value and return the value if valid.

        raise InvalidResourceException for invalid values.
        """
        type_description, type_class = expected_type.value
        if not isinstance(self.value, type_class):
            if not message:
                message = f"Property '{self.property_identifier}' should be a {type_description}."
            if self.event_id:
                raise InvalidEventException(self.event_id, message)
            if self.resource_logical_id:
                raise InvalidResourceException(self.resource_logical_id, message)
            raise RuntimeError("event_id and resource_logical_id are both None")
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
            if self.event_id:
                raise InvalidEventException(self.event_id, message)
            if self.resource_logical_id:
                raise InvalidResourceException(self.resource_logical_id, message)
            raise RuntimeError("event_id and resource_logical_id are both None")
        return self.value

    #
    # alias methods:
    #
    def to_be_a_map(self, message: Optional[str] = "") -> T:
        return self.to_be_a(ExpectedType.MAP, message)

    def to_be_a_list(self, message: Optional[str] = "") -> T:
        return self.to_be_a(ExpectedType.LIST, message)

    def to_be_a_string(self, message: Optional[str] = "") -> T:
        return self.to_be_a(ExpectedType.STRING, message)

    def to_be_an_integer(self, message: Optional[str] = "") -> T:
        return self.to_be_a(ExpectedType.INTEGER, message)


sam_expect = _ResourcePropertyValueValidator
