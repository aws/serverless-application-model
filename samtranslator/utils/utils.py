import copy
from typing import Optional, cast, Any, List


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


class InvalidValueType(Exception):
    def __init__(self, relative_path: str) -> None:
        self.relative_path = relative_path

    def full_path(self, path_prefix: str) -> str:
        if not self.relative_path:
            return path_prefix
        return path_prefix + "." + self.relative_path


def dict_deep_get(d: Any, path: str) -> Optional[Any]:
    relative_path = ""
    _path_nodes = path.split(".")
    while _path_nodes:
        if d is None:
            return None
        if not isinstance(d, dict):
            raise InvalidValueType(relative_path)
        d = d.get(_path_nodes[0])
        relative_path = (relative_path + f".{_path_nodes[0]}").lstrip(".")
        _path_nodes = _path_nodes[1:]
    return d
