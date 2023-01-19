import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, TypeVar
from functools import partial

import pydantic
from pydantic import Extra, Field

# Value passed directly to CloudFormation; not used by SAM
#
# Need a type other than Any, otherwise value won't be required. See:
#  - https://github.com/pydantic/pydantic/issues/990
#  - https://github.com/pydantic/pydantic/issues/1223
#
# So we use "any CloudFormation type", and since CloudFormation doesn't support null
# and uses JSON, we use all JSON types except null.
#
# Using a class to reduce schema size; makes it go to definitions instead of
# inlining everywhere. See https://docs.pydantic.dev/usage/models/#custom-root-types
class PassThrough(pydantic.BaseModel):
    __root__: Union[Dict[Any, Any], List[Any], int, float, bool, str]


# Intrinsic resolvable by the SAM transform
T = TypeVar("T")
SamIntrinsicable = Union[Dict[str, Any], T]
SamIntrinsic = Dict[str, Any]

# TODO: Get rid of this in favor of proper types
Unknown = Optional[Any]

DictStrAny = Dict[str, Any]

LenientBaseModel = pydantic.BaseModel

_thisdir = os.path.dirname(os.path.abspath(__file__))
_DOCS = json.loads(Path(_thisdir, "docs.json").read_bytes())


def get_prop(stem: str) -> Any:
    return partial(_get_prop, stem)


def _get_prop(stem: str, name: str) -> Any:
    docs = _DOCS["properties"][stem][name]
    return Field(
        title=name,
        description=docs,
        # https://code.visualstudio.com/docs/languages/json#_use-rich-formatting-in-hovers
        markdownDescription=docs,
    )


# By default strict: https://pydantic-docs.helpmanual.io/usage/model_config/#change-behaviour-globally
class BaseModel(LenientBaseModel):
    class Config:
        extra = Extra.forbid


# https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-ref.html
class Ref(BaseModel):
    Ref: str
