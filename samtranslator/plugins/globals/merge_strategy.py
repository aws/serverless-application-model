"""Per-property merge strategy types for the Globals merge engine."""

from enum import Enum


class MergeOp(Enum):
    # -- Defaults (implicit when no CUSTOM_STRATEGIES entry matches) --
    DEEP_MERGE = "deep_merge"  # dict: recursive key union, local wins scalars, nested lists concatenate
    CONCATENATE = "concatenate"  # list: global_list + local_list

    # -- Custom strategies (registered per-property in CUSTOM_STRATEGIES) --
    REPLACE = "replace"  # local wins entirely, global discarded
    PRUNE_AND_MERGE = "prune_and_merge"  # dict: drop global keys not declared in local, then deep-merge shared keys
