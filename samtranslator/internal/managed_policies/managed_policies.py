import json
import os
from pathlib import Path
from typing import Dict, Optional

from samtranslator.internal.types import GetManagedPolicyMap
from samtranslator.translator.arn_generator import ArnGenerator

with Path(os.path.dirname(os.path.abspath(__file__)), "managed_policies.json").open(encoding="utf-8") as f:
    _BUNDLED_MANAGED_POLICIES: Dict[str, Dict[str, str]] = json.load(f)


def _dict_get(d: Optional[Dict[str, str]], k: str) -> Optional[str]:
    if isinstance(d, dict) and k in d:
        return d[k]
    return None


# Not designed for efficiency
def get_managed_policy_arn(
    name: str,
    managed_policy_map: Optional[Dict[str, str]],
    get_managed_policy_map: Optional[GetManagedPolicyMap],
) -> Optional[str]:
    arn = _dict_get(managed_policy_map, name)
    if arn:
        return arn

    partition = ArnGenerator.get_partition_name()
    bundled_managed_policies = _BUNDLED_MANAGED_POLICIES.get(partition)
    arn = _dict_get(bundled_managed_policies, name)
    if arn:
        return arn

    if callable(get_managed_policy_map):
        # TODO: Error handling?
        fallback_managed_policies = get_managed_policy_map()
        arn = _dict_get(fallback_managed_policies, name)
        if arn:
            return arn

    return None
