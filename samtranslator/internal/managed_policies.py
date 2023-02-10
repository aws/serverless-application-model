import json
import os
from pathlib import Path
from typing import Dict, Optional

from samtranslator.internal.types import GetManagedPolicyMap
from samtranslator.translator.arn_generator import ArnGenerator

with Path(os.path.dirname(os.path.abspath(__file__)), "data", "managed_policies.json").open(encoding="utf-8") as f:
    _BUNDLED_MANAGED_POLICIES: Dict[str, Dict[str, str]] = json.load(f)


def _dict_get(d: Optional[Dict[str, str]], k: str) -> Optional[str]:
    if isinstance(d, dict) and k in d:
        return d[k]
    return None


def get_managed_policy_arn(
    name: str,
    managed_policy_map: Optional[Dict[str, str]],
    get_managed_policy_map: Optional[GetManagedPolicyMap],
) -> Optional[str]:
    """
    Get the ARN of a AWS managed policy name. Used in Policies property of
    AWS::Serverless::Function and AWS::Serverless::StateMachine.

    The intention is that the bundled managed policy map is used in the majority
    of cases, avoiding the extra IAM calls (IAM is partition-global; AWS managed
    policies are the same for any region within a partition).

    Determined in this order:
      1. Caller-provided managed policy map (can be omitted)
      2. Managed policy map bundled with the transform code (i.e. fast)
      3. Caller-provided managed policy map (as function for lazy loading)
    """
    # Caller-provided policy map (eager)
    arn = _dict_get(managed_policy_map, name)
    if arn:
        return arn

    # Bundled policy map
    partition = ArnGenerator.get_partition_name()
    bundled_managed_policies = _BUNDLED_MANAGED_POLICIES.get(partition)
    arn = _dict_get(bundled_managed_policies, name)
    if arn:
        return arn

    # Caller-provided policy map (lazy)
    if callable(get_managed_policy_map):
        fallback_managed_policies = get_managed_policy_map()
        arn = _dict_get(fallback_managed_policies, name)
        if arn:
            return arn

    return None
