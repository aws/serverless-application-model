"""Per-property merge strategy types for the Globals merge engine."""

from dataclasses import dataclass
from enum import Enum


class MergeOp(Enum):
    # -- Defaults (implicit when no CUSTOM_STRATEGIES entry matches) --
    DEEP_MERGE = "deep_merge"  # dict: recursive key union, local wins scalars, nested lists concatenate
    CONCATENATE = "concatenate"  # list: global_list + local_list

    # -- Custom strategies (registered per-property in CUSTOM_STRATEGIES) --
    REPLACE = "replace"  # local wins entirely, global discarded
    PRUNE_AND_MERGE = "prune_and_merge"  # dict: drop global keys not declared in local, then deep-merge shared keys


@dataclass(frozen=True)
class MergeRule:
    op: MergeOp


# Convenience constants for use in CUSTOM_STRATEGIES registry.
# DEEP_MERGE and CONCATENATE are the implicit defaults -- registering them is a no-op
# but allowed for explicitness.
DEEP_MERGE = MergeRule(MergeOp.DEEP_MERGE)
CONCATENATE = MergeRule(MergeOp.CONCATENATE)
REPLACE = MergeRule(MergeOp.REPLACE)
PRUNE_AND_MERGE = MergeRule(MergeOp.PRUNE_AND_MERGE)
