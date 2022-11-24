from pathlib import Path
from typing import Any, Dict, Optional, Union, TypeVar

import pydantic
from pydantic import Extra, Field
import yaml

# Value passed directly to CloudFormation; not used by SAM
PassThrough = Any  # TODO: Make it behave like typescript's unknown

# Intrinsic resolvable by the SAM transform
T = TypeVar("T")
SamIntrinsicable = Union[Dict[str, Any], T]
SamIntrinsic = Dict[str, Any]

# TODO: Get rid of this in favor of proper types
Unknown = Optional[Any]

LenientBaseModel = pydantic.BaseModel

_DOCS = yaml.safe_load(Path("samtranslator", "schema", "docs.yaml").read_bytes())


def get_docs_prop(field: str) -> Any:
    docs = _DOCS["docs"]["properties"][field]
    return Field(
        description=docs,
        # https://code.visualstudio.com/docs/languages/json#_use-rich-formatting-in-hovers
        markdownDescription=docs,
    )


# By default strict: https://pydantic-docs.helpmanual.io/usage/model_config/#change-behaviour-globally
class BaseModel(LenientBaseModel):
    class Config:
        extra = Extra.forbid
