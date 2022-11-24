import json
from pathlib import Path
from typing import Any, Dict, Optional

import pydantic
from pydantic import Extra, Field

# Value passed directly to CloudFormation; not used by SAM
PassThrough = Any  # TODO: Make it behave like typescript's unknown

# Intrinsic resolvable by the SAM transform
SamIntrinsic = Dict[str, Any]

# TODO: Get rid of this in favor of proper types
Unknown = Optional[Any]

LenientBaseModel = pydantic.BaseModel

_DOCS = json.loads(Path("samtranslator", "schema", "docs.json").read_text())


def get_docs_prop(field: str) -> Any:
    docs = _DOCS["properties"][field]
    return Field(
        description=docs,
        # https://code.visualstudio.com/docs/languages/json#_use-rich-formatting-in-hovers
        markdownDescription=docs,
    )


# By default strict: https://pydantic-docs.helpmanual.io/usage/model_config/#change-behaviour-globally
class BaseModel(LenientBaseModel):
    class Config:
        extra = Extra.forbid
