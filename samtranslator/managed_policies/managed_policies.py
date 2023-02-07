import json
import os
from typing import Dict

from samtranslator.translator.arn_generator import ArnGenerator


# TODO: Adding cache breaks tests as partition is reused
# @lru_cache(maxsize=1)
def get_managed_policy_map() -> Dict[str, str]:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "managed_policies.json")
    with open(path, encoding="utf-8") as f:
        policies: Dict[str, str] = json.load(f)
        partition = ArnGenerator.get_partition_name()
        return policies[partition]
