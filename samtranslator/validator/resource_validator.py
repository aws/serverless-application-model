"""A resource validator to help validate resource properties and raise exception when some value is unexpected."""
from typing import Any, Dict, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


# Note: For compabitliy issue, we should ONLY use this with new abstraction/resources.
def to_model(resource_properties: Dict[Any, Any], cls: Type[T]) -> T:
    """
    Given a resource properties, return a typed object from the definitions of SAM schema model

    param:
        resource_properties: properties from input template
        cls: schema models
    """
    return cls.parse_obj(resource_properties)
