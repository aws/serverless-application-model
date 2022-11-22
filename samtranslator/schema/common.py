from typing import Any, Dict, Optional

import pydantic
from pydantic import Extra

# Value passed directly to CloudFormation; not used by SAM
PassThrough = Any  # TODO: Make it behave like typescript's unknown

# Intrinsic resolvable by the SAM transform
SamIntrinsic = Dict[str, Any]

# TODO: Get rid of this in favor of proper types
Unknown = Optional[Any]

LenientBaseModel = pydantic.BaseModel


class BaseModel(LenientBaseModel):
    """
    By default strict
    https://pydantic-docs.helpmanual.io/usage/model_config/#change-behaviour-globally
    """

    class Config:
        extra = Extra.forbid
