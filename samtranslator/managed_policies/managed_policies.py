import json
import os
from functools import lru_cache
from typing import Dict

from samtranslator.translator.arn_generator import ArnGenerator


@lru_cache(maxsize=1)
def get_managed_policy_map() -> Dict[str, str]:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "managed_policies.json")
    with open(path, encoding="utf-8") as f:
        policies: Dict[str, str] = json.load(f)
        partition = ArnGenerator.get_partition_name()
        return {k: v.replace("<partition>", partition) for k, v in policies.items()}
