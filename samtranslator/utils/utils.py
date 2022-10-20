import copy
from typing import cast, Any, List


def as_array(x: Any) -> List[Any]:
    """Convert value to list if it already isn't."""
    return x if isinstance(x, list) else [x]


def insert_unique(xs: Any, vs: Any) -> List[Any]:
    """
    Return copy of `xs` extended with values of `vs` that do not exist in `xs`.

    Inputs are converted to lists if they already aren't.
    """
    xs = as_array(copy.deepcopy(xs))
    vs = as_array(copy.deepcopy(vs))

    for v in vs:
        if v not in xs:
            xs.append(v)

    return cast(List[Any], xs)  # mypy doesn't recognize it
