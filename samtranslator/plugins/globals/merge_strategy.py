"""Per-property merge strategy types for the Globals merge engine."""

from dataclasses import dataclass
from enum import Enum


class MergeOp(Enum):
    CONCATENATE = "concatenate"
    REPLACE = "replace"
    MERGE_BY_KEY = "merge_by_key"
    REPLACE_KEYS_MERGE_VALUES = "replace_keys_merge_values"


@dataclass(frozen=True)
class MergeRule:
    op: MergeOp
    key: str | None = None

    def __post_init__(self) -> None:
        if self.op == MergeOp.MERGE_BY_KEY and not self.key:
            raise ValueError("MERGE_BY_KEY requires a 'key' field")
        if self.op not in (MergeOp.MERGE_BY_KEY,) and self.key is not None:
            raise ValueError(f"'key' is only valid with MERGE_BY_KEY, not {self.op.value}")


# Explicit default; not needed in CUSTOM_STRATEGIES (unlisted paths already concatenate).
CONCATENATE = MergeRule(MergeOp.CONCATENATE)
REPLACE = MergeRule(MergeOp.REPLACE)
REPLACE_KEYS_MERGE_VALUES = MergeRule(MergeOp.REPLACE_KEYS_MERGE_VALUES)


def merge_by_key(key: str) -> MergeRule:
    """Factory for MERGE_BY_KEY rules. Merges list-of-dicts by the named key field."""
    return MergeRule(MergeOp.MERGE_BY_KEY, key=key)
