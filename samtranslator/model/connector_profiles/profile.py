import copy
import json
import re
from pathlib import Path
from typing import Any, Dict

ConnectorProfile = Dict[str, Any]

_PROFILE_FILE = Path(__file__).absolute().parent / "profiles.json"
with _PROFILE_FILE.open(encoding="utf-8") as f:
    PROFILE: ConnectorProfile = json.load(f)


def get_profile(source_type: str, dest_type: str):  # type: ignore[no-untyped-def]
    profile = PROFILE["Permissions"].get(source_type, {}).get(dest_type)
    # Ensure not passing a mutable shared variable
    return copy.deepcopy(profile)


def verify_profile_variables_replaced(obj: Any) -> None:
    """
    Verifies all profile variables have been replaced; throws ValueError if not.
    """
    s = json.dumps(obj)
    matches = re.findall(r"%{[\w\.]+}", s)
    if matches:
        raise ValueError(f"The following variables have not been replaced: {matches}")


def profile_replace(obj: Any, replacements: Dict[str, Any]):  # type: ignore[no-untyped-def]
    """
    This function is used to recursively replace all keys in 'replacements' found
    in 'obj' with matching values in 'replacement' dictionary.
    After the replacement, the obj should be in a CloudFormation-compatible format.

    Raises ValueError if a profile variable being replaced is None.
    """
    return _map_nested(obj, lambda v: _profile_replace_str(v, replacements))


def _map_nested(obj: Any, fn):  # type: ignore[no-untyped-def, no-untyped-def]
    if isinstance(obj, dict):
        return {k: _map_nested(v, fn) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_map_nested(v, fn) for v in obj]
    return fn(obj)


def _sanitize(s: str) -> str:
    """Remove everything but alphanumeric characters."""
    return "".join(c for c in s if c.isalnum())


def _profile_replace_str(s: Any, replacements: Dict[str, Any]):  # type: ignore[no-untyped-def]
    if not isinstance(s, str):
        return s
    res = {}
    for k, v in replacements.items():
        pattern = "%{" + k + "}"
        # !Sub doesn't allow special characters in variable names
        sub_var_name = _sanitize(k)
        replaced_pattern = "${" + sub_var_name + "}"
        if pattern in s and v is None:
            raise ValueError(f"{k} is missing.")
        if pattern == s:
            # s and pattern match exactly, simply return replacement string
            return v
        if pattern in s:
            # pattern is substring of s, use Fn::Sub to replace part of s
            s = s.replace(pattern, replaced_pattern)
            res[sub_var_name] = v
    if re.search(r"\${.+}", s):
        # As long as the string has a ${..}, it needs sub.
        if res:
            return {"Fn::Sub": [s, res]}
        return {"Fn::Sub": s}
    return s
