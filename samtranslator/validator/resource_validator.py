"""A resource validator to help validate resource properties and raise exception when some value is unexpected."""
from typing import Any, Dict, Type

from pydantic import BaseModel


class ResourceModel:
    """
    Wrapper class around a SAM schema BaseModel to with a new functional "get" method
    """

    def __init__(self, model: BaseModel) -> None:
        self.model = model

    def get(self, attr: str, default_value: Any = None) -> Any:
        attr_value = self.model.__dict__.get(attr, default_value)
        if isinstance(attr_value, BaseModel):
            if "__root__" in attr_value.__dict__:
                return attr_value.__dict__["__root__"]
            return ResourceModel(attr_value)
        return attr_value

    def __getitem__(self, attr):
        attr_value = self.model.__dict__[attr]
        if isinstance(attr_value, BaseModel):
            if "__root__" in attr_value.__dict__:
                return attr_value.__dict__["__root__"]
            return ResourceModel(attr_value)
        return attr_value


def to_resource_model(resource_properties: Dict[Any, Any], cls: Type[BaseModel]) -> ResourceModel:
    """
    Given properties of a SAM resource return a typed object from the definitions of SAM schema model

    param:
        resource_properties: properties from input template
        cls: SAM schema models
    """
    return ResourceModel(cls(**resource_properties))
