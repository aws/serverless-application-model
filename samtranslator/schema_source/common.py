import json
import os
from functools import partial
from pathlib import Path
from typing import Any, Dict, Optional, TypeVar, Union

import pydantic
from pydantic import Extra, Field

from samtranslator.model.types import PassThrough


# If using PassThrough as-is, pydantic will mark the field as not required:
#  - https://github.com/pydantic/pydantic/issues/990
#  - https://github.com/pydantic/pydantic/issues/1223
#
# That isn't what we want; we want it to specify any type, but still required.
# Using a class gets around it.
class PassThroughProp(pydantic.BaseModel):
    __root__: PassThrough


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


class ResourceAttributes(BaseModel):
    DependsOn: Optional[PassThroughProp]
    DeletionPolicy: Optional[PassThroughProp]
    Metadata: Optional[PassThroughProp]
    UpdateReplacePolicy: Optional[PassThroughProp]
    Condition: Optional[PassThroughProp]
