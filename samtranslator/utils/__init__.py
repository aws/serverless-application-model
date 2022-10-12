import copy
from typing import Any, List


def as_array(x: Any) -> List[Any]:
    """Convert value to list if it already isn't."""
    return x if isinstance(x, list) else [x]


def insert_unique(xs: Any, vs: Any):
    """
    Return list of values from `xs` extended with values from `vs` that do not
    exist in `vs`.

    Inputs are converted to lists if they already aren't.
    Does not mutate original values.
    """
    xs = as_array(copy.deepcopy(xs))
    vs = as_array(copy.deepcopy(vs))

    for v in vs:
        if v not in xs:
            xs.append(v)

    return xs
