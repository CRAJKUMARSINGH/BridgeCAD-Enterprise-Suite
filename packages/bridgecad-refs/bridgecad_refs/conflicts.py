"""A conflict is a finding, not a failure.

Either the code is wrong, the reference is wrong, or the reference is a different
bridge. All three are worth knowing, and none of them is resolved by widening a
tolerance. Open conflicts are counted and printed; a conflict closed without a
note is a conflict nobody learned from.
"""

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

LOG = Path(__file__).resolve().parents[3] / "references" / "conflicts.jsonl"


@dataclass
class Conflict:
    key: str
    generated: str
    stated: str
    citation_ref: str
    resolved_as: str | None = None  # code_wrong | ref_wrong | different_bridge | tolerance
    note: str | None = None
    raised_on: str = field(default_factory=lambda: date.today().isoformat())


def open_conflicts() -> list[Conflict]:
    if not LOG.exists():
        return []
    seen: dict[str, Conflict] = {}
    for line in LOG.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        c = Conflict(**json.loads(line))
        seen[c.key] = c  # later line wins, so a resolution appends
    return [c for c in seen.values() if c.resolved_as is None]
