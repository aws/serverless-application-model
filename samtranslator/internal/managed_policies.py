import json
import os
from pathlib import Path
from typing import Dict, Optional

from samtranslator.internal.types import GetManagedPolicyMap
from samtranslator.translator.arn_generator import ArnGenerator

with Path(os.path.dirname(os.path.abspath(__file__)), "data", "managed_policies.json").open(encoding="utf-8") as f:
    _BUNDLED_MANAGED_POLICIES: Dict[str, Dict[str, str]] = json.load(f)


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
      1. Caller-provided managed policy map (can be None, mostly for compatibility)
      2. Managed policy map bundled with the transform code (fast!)
      3. Caller-provided managed policy map (load lazily as last resort)
    """
    # Caller-provided policy map (eager)
    arn = managed_policy_map and managed_policy_map.get(name)
    if arn:
        return arn

    # Bundled policy map
    partition = ArnGenerator.get_partition_name()
    bundled_managed_policies = _BUNDLED_MANAGED_POLICIES.get(partition)
    arn = bundled_managed_policies and bundled_managed_policies.get(name)
    if arn:
        return arn

    # Caller-provided policy map (lazy)
    if callable(get_managed_policy_map):
        fallback_managed_policies = get_managed_policy_map()
        arn = fallback_managed_policies and fallback_managed_policies.get(name)
        if arn:
            return arn

    return None
