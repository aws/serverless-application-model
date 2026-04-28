"""A plug-able validator to help raise exception when some value is unexpected."""

from typing import Any, Generic, TypeVar, cast

from samtranslator.model.exceptions import (
    ExpectedType,
    InvalidEventException,
    InvalidResourceAttributeTypeException,
    InvalidResourceException,
    InvalidResourcePropertyTypeException,
)

T = TypeVar("T")


class _ResourcePropertyValueValidator(Generic[T]):
    value: T | None
    resource_id: str
    key_path: str
    is_sam_event: bool
    is_resource_attribute: bool

    def __init__(
        self,
        value: T | None,
        resource_id: str,
        key_path: str,
        is_sam_event: bool = False,
        is_resource_attribute: bool = False,
    ) -> None:
        self.value = value
        self.resource_id = resource_id
        self.key_path = key_path
        self.is_sam_event = is_sam_event
        self.is_resource_attribute = is_resource_attribute

    @property
    def resource_logical_id(self) -> str | None:
        return None if self.is_sam_event else self.resource_id

    @property
    def event_id(self) -> str | None:
        return self.resource_id if self.is_sam_event else None

    def to_be_a(self, expected_type: ExpectedType, message: str | None = "") -> T:
        """
        Validate the type of the value and return the value if valid.

        raise InvalidResourceException for invalid values.
        """
        type_description, type_class = expected_type.value
        if not isinstance(self.value, type_class):
            if self.event_id:
                raise InvalidEventException(
                    self.event_id, message or f"Property '{self.key_path}' should be a {type_description}."
                )
            if self.resource_logical_id:
                if self.is_resource_attribute:
                    raise InvalidResourceAttributeTypeException(
                        self.resource_logical_id, self.key_path, expected_type, message
                    )
                raise InvalidResourcePropertyTypeException(
                    self.resource_logical_id, self.key_path, expected_type, message
                )
            raise RuntimeError("event_id and resource_logical_id are both None")
        # mypy is not smart to derive class from expected_type.value[1], ignore types:
        return self.value  # type: ignore

    def to_not_be_none(self, message: str | None = "") -> T:
        """
        Validate the value is not None and return the value if valid.

        raise InvalidResourceException for None values.
        """
        if self.value is None:
            if not message:
                message = f"Property '{self.key_path}' is required."
            if self.event_id:
                raise InvalidEventException(self.event_id, message)
            if self.resource_logical_id:
                raise InvalidResourceException(self.resource_logical_id, message)
            raise RuntimeError("event_id and resource_logical_id are both None")
        return self.value

    #
    # alias methods:
    #
    def to_be_a_map(self, message: str | None = "") -> dict[str, Any]:
        """
        Return the value with type hint "dict[str, Any]".
        Raise InvalidResourceException/InvalidEventException if the value is not.
        """
        return cast(dict[str, Any], self.to_be_a(ExpectedType.MAP, message))

    def to_be_a_list(self, message: str | None = "") -> T:
        return self.to_be_a(ExpectedType.LIST, message)

    def to_be_a_list_of(self, expected_type: ExpectedType, message: str | None = "") -> T:
        """
        Return the value with type hint "List[T]".
        Raise InvalidResourceException/InvalidEventException if the value is not.
        """
        value = self.to_be_a(ExpectedType.LIST, message)
        for index, item in enumerate(value):  # type: ignore
            sam_expect(item, self.resource_id, f"{self.key_path}[{index}]", is_sam_event=self.is_sam_event).to_be_a(
                expected_type, message
            )
        return value

    def to_be_a_string(self, message: str | None = "") -> str:
        """
        Return the value with type hint "str".
        Raise InvalidResourceException/InvalidEventException if the value is not.
        """
        return cast(str, self.to_be_a(ExpectedType.STRING, message))

    def to_be_an_integer(self, message: str | None = "") -> int:
        """
        Return the value with type hint "int".
        Raise InvalidResourceException/InvalidEventException if the value is not.
        """
        return cast(int, self.to_be_a(ExpectedType.INTEGER, message))

    def to_be_a_bool(self, message: str | None = "") -> bool:
        """
        Return the value with type hint "bool".
        Raise InvalidResourceException/InvalidEventException if the value is not.
        """
        return cast(bool, self.to_be_a(ExpectedType.BOOLEAN, message))


sam_expect = _ResourcePropertyValueValidator
