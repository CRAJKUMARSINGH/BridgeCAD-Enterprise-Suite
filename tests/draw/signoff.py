"""Review records, bound to the geometry they were made against.

THE RULE
    A signoff records the geometry hash it was made on. If the geometry changes,
    the signoff is STALE — not deleted, not silently trusted. Stale signoffs are
    reported, because a reviewer needs to know what changed since they looked.

WHAT A SIGNOFF IS NOT
    It is not a claim the drawing is correct. It is a claim that a named human
    looked at this drawing next to a named reference and wrote down what they
    compared. The `compared` list is what makes the claim checkable later.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SIGNOFF_DIR = REPO / "tests" / "draw" / "signoff"
REF_DIR = REPO / "references"


@dataclass
class Signoff:
    sheet: str
    revision: str
    reviewed_by: str
    reviewed_on: str
    against: str                      # reference file, relative to references/
    compared: list[str]               # what was actually compared, item by item
    geometry_sha: str
    outcome: str = "confirmed"        # confirmed | confirmed_with_exceptions
    exceptions: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.outcome not in ("confirmed", "confirmed_with_exceptions"):
            raise ValueError(f"{self.sheet}: bad outcome {self.outcome!r}")
        if self.outcome == "confirmed_with_exceptions" and not self.exceptions:
            raise ValueError(f"{self.sheet}: exceptions outcome with no exceptions")
        if self.reviewed_by.strip().upper() in ("", "REPLACE_ME", "TBC", "TBD"):
            raise ValueError(f"{self.sheet}: placeholder reviewer {self.reviewed_by!r}")
        if len(self.compared) < 3:
            raise ValueError(f"{self.sheet}: compared only {len(self.compared)} items")


def record(project, sheet: str, **kw) -> Path:
    from bridgecad_draw.contract import geometry_hash
    so = Signoff(sheet=sheet, geometry_sha=geometry_hash(project, sheet), **kw)
    SIGNOFF_DIR.mkdir(parents=True, exist_ok=True)
    path = SIGNOFF_DIR / f"{sheet}.json"
    path.write_text(json.dumps(asdict(so), indent=2) + "\n", encoding="utf-8")
    return path


def load_all() -> list[Signoff]:
    out = []
    for p in sorted(SIGNOFF_DIR.glob("*.json")):
        if p.name.startswith("_"):
            continue
        out.append(Signoff(**json.loads(p.read_text(encoding="utf-8"))))
    return out


def is_stale(project, so: Signoff) -> bool:
    from bridgecad_draw.contract import geometry_hash
    return geometry_hash(project, so.sheet) != so.geometry_sha
