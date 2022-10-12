from typing import Any


def dictfind(obj: Any, path: str, separator: str = ".") -> Any:
    if not isinstance(obj, dict):
        return None
    keys = path.split(separator)
    v = obj
    for k in keys:
        if k not in v:
            return None
        v = v[k]
    return v
