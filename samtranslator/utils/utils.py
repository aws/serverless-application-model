import copy
from typing import Dict, Optional, cast, Any, List


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
        if relative_path:
            super().__init__(f"The value of '{relative_path}' should be a map")
        else:
            super().__init__("It should be a map")


def dict_deep_get(d: Any, path: str) -> Optional[Any]:
    """
    Get the value deep in the dict.

    If any value along the path doesn't exist, return None.
    If any parent node exists but is not a dict, raise InvalidValueType.
    """
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


def dict_deep_update(d: Any, dict_to_merge: Dict[str, Any]) -> None:
    """
    Update the value deep in the dict. The dict_to_merge looks like
    {
      "a.b.c": <value>
    }
    it will make d["a"]["b"]["c"] = <value>.

    If any value along the path doesn't exist, create empty dict along the way.
    If any parent node exists but is not a dict, raise InvalidValueType.
    """
    for path, value in dict_to_merge.items():
        relative_path = ""
        _path_nodes = path.split(".")
        while len(_path_nodes) > 1:
            relative_path = (relative_path + f".{_path_nodes[0]}").lstrip(".")
            d = d.setdefault(_path_nodes[0], {})
            if not isinstance(d, dict):
                raise InvalidValueType(relative_path)
            _path_nodes = _path_nodes[1:]
        d[_path_nodes[0]] = value
