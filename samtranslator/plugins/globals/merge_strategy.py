"""Per-property merge strategy types for the Globals merge engine."""

from dataclasses import dataclass
from enum import Enum


class MergeOp(Enum):
    CONCATENATE = "concatenate"
    REPLACE = "replace"
    MERGE_BY_KEY = "merge_by_key"


@dataclass(frozen=True)
class MergeRule:
    op: MergeOp
    key: str | None = None

    def __post_init__(self) -> None:
        if self.op == MergeOp.MERGE_BY_KEY and not self.key:
            raise ValueError("MERGE_BY_KEY requires a 'key' field")
        if self.op != MergeOp.MERGE_BY_KEY and self.key is not None:
            raise ValueError(f"'key' is only valid with MERGE_BY_KEY, not {self.op.value}")


# Explicit default; not needed in CUSTOM_STRATEGIES (unlisted paths already concatenate).
CONCATENATE = MergeRule(MergeOp.CONCATENATE)
REPLACE = MergeRule(MergeOp.REPLACE)


def merge_by_key(key: str) -> MergeRule:
    """Factory for MERGE_BY_KEY rules. Merges list-of-dicts by the named key field."""
    return MergeRule(MergeOp.MERGE_BY_KEY, key=key)
