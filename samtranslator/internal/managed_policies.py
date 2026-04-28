import json
from pathlib import Path

with (Path(__file__).absolute().parent / "data" / "aws_managed_policies.json").open(encoding="utf-8") as f:
    _BUNDLED_MANAGED_POLICIES: dict[str, dict[str, str]] = json.load(f)


def get_bundled_managed_policy_map(partition: str) -> dict[str, str] | None:
    return _BUNDLED_MANAGED_POLICIES.get(partition)
