import json
import os
from pathlib import Path
from typing import Dict

with Path(os.path.dirname(os.path.abspath(__file__)), "managed_policies.json").open(encoding="utf-8") as f:
    _BUNDLED_MANAGED_POLICIES: Dict[str, Dict[str, str]] = json.load(f)


def get_bundled_managed_policies(partition: str) -> Dict[str, str]:
    return _BUNDLED_MANAGED_POLICIES[partition]
