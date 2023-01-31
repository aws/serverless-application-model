import json
import os
from typing import Dict

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "managed_policies.json"), encoding="utf-8") as f:
    _MANAGED_POLICIES: Dict[str, Dict[str, str]] = json.load(f)


def get_managed_policy_map(partition: str) -> Dict[str, str]:
    return _MANAGED_POLICIES[partition]
