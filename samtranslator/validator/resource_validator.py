"""A resource validator to help validate resource properties and raise exception when some value is unexpected."""
from typing import Any, Dict, Type

from pydantic import BaseModel


class Model:
    """
    Wrapper class around a SAM schema BaseModel to with a new functional "get" method
    """

    def __init__(self, model: BaseModel) -> None:
        self.model = model

    def _process_attr_value(self, attr_value: Any) -> Any:
        if isinstance(attr_value, BaseModel):
            if "__root__" in attr_value.__dict__:
                return attr_value.__dict__["__root__"]
            return Model(attr_value)
        return attr_value

    def _get_item(self, attr_value: Any) -> Any:
        if isinstance(attr_value, list):
            return [self._process_attr_value(attr) for attr in attr_value]
        return self._process_attr_value(attr_value)

    def get(self, attr_key: str, default_value: Any = None) -> Any:
        """Return the value for key if key is in Model properties else default."""
        attr_value = self.model.__dict__.get(attr_key, default_value)
        return self._get_item(attr_value)

    def __getitem__(self, attr_key: str) -> Any:
        """Return the value for key if key is in Model properties else raise KeyError exception."""
        attr_value = self.model.__dict__[attr_key]
        return self._get_item(attr_value)


# Note: For compabitliy issue, we should ONLY use this with new abstraction/resources.
def to_model(resource_properties: Dict[Any, Any], cls: Type[BaseModel]) -> Model:
    """
    Given properties of a SAM resource return a typed object from the definitions of SAM schema model

    param:
        resource_properties: properties from input template
        cls: SAM schema models
    """
    return Model(cls(**resource_properties))
