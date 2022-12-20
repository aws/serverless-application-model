"""A plug-able validator to help raise exception when some value is unexpected."""
from typing import Any, Dict, Generic, Optional, TypeVar, cast

from samtranslator.model.exceptions import (
    ExpectedType,
    InvalidEventException,
    InvalidResourceException,
    InvalidResourcePropertyTypeException,
)

T = TypeVar("T")


class _ResourcePropertyValueValidator(Generic[T]):
    value: Optional[T]
    resource_id: str
    property_identifier: str
    is_sam_event: bool

    def __init__(
        self, value: Optional[T], resource_id: str, property_identifier: str, is_sam_event: bool = False
    ) -> None:
        self.value = value
        self.resource_id = resource_id
        self.property_identifier = property_identifier
        self.is_sam_event = is_sam_event

    @property
    def resource_logical_id(self) -> Optional[str]:
        return None if self.is_sam_event else self.resource_id

    @property
    def event_id(self) -> Optional[str]:
        return self.resource_id if self.is_sam_event else None

    def to_be_a(self, expected_type: ExpectedType, message: Optional[str] = "") -> T:
        """
        Validate the type of the value and return the value if valid.

        raise InvalidResourceException for invalid values.
        """
        type_description, type_class = expected_type.value
        if not isinstance(self.value, type_class):
            if self.event_id:
                raise InvalidEventException(
                    self.event_id, message or f"Property '{self.property_identifier}' should be a {type_description}."
                )
            if self.resource_logical_id:
                raise InvalidResourcePropertyTypeException(
                    self.resource_logical_id, self.property_identifier, expected_type, message
                )
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
    def to_be_a_map(self, message: Optional[str] = "") -> Dict[str, Any]:
        return cast(Dict[str, Any], self.to_be_a(ExpectedType.MAP, message))

    def to_be_a_list(self, message: Optional[str] = "") -> T:
        return self.to_be_a(ExpectedType.LIST, message)

    def to_be_a_list_of(self, expected_type: ExpectedType, message: Optional[str] = "") -> T:
        value = self.to_be_a(ExpectedType.LIST, message)
        for index, item in enumerate(value):  # type: ignore
            sam_expect(
                item, self.resource_id, f"{self.property_identifier}[{index}]", is_sam_event=self.is_sam_event
            ).to_be_a(expected_type, message)
        return value

    def to_be_a_string(self, message: Optional[str] = "") -> T:
        return self.to_be_a(ExpectedType.STRING, message)

    def to_be_an_integer(self, message: Optional[str] = "") -> T:
        return self.to_be_a(ExpectedType.INTEGER, message)


sam_expect = _ResourcePropertyValueValidator
