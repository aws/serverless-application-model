from typing import Any, Dict, Optional, cast

from samtranslator.internal.schema_source.common import PassThroughProp
from samtranslator.model.types import PassThrough


def remove_none_values(d: Dict[Any, Any]) -> Dict[Any, Any]:
    """Returns a copy of the dictionary with no items that have the value None."""
    return {k: v for k, v in d.items() if v is not None}


def passthrough_value(v: Optional[PassThroughProp]) -> PassThrough:
    """
    Cast PassThroughProp values to PassThrough.

    PassThroughProp has a __root__ value which is of type PassThrough. But mypy
    does not look deep enough to see this type, and does not recognize it as Any,
    so assignments to CFN resource types fail. So we cast to PassThrough here.

    We also accept None values so that it is a one line assignment for the consumer.
    """
    return cast(PassThrough, v)
