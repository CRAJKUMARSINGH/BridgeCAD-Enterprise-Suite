"""bridgecad_core.revisions — per-project append-only revision register.

``freeze`` stores every sheet fingerprint under a revision tag; ``issue`` is
immutable — re-issuing an existing tag is rejected.  ``compare_to_issued``
diffs the live project's sheets against the last issued fingerprints.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class RevisionRecord:
    tag: str
    issued_at: str
    author: str
    fingerprints: dict[str, dict[str, str]] = field(default_factory=dict)
    quantum_mm: float = 1.0


class RevisionError(RuntimeError):
    pass


_STORE_DIR = Path(".bridgecad_revisions")


def _store_path(project: Any) -> Path:
    name = getattr(getattr(project, "project_master", None), "project_code", None) or "project"
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(name))
    return _STORE_DIR / f"{safe}.json"


def _load(path: Path) -> dict[str, RevisionRecord]:
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    out: dict[str, RevisionRecord] = {}
    for tag, rec in (raw.get("revisions") or {}).items():
        out[tag] = RevisionRecord(
            tag=tag,
            issued_at=rec.get("issued_at", ""),
            author=rec.get("author", ""),
            fingerprints=rec.get("fingerprints", {}),
            quantum_mm=float(rec.get("quantum_mm", 1.0)),
        )
    return out


def _save(path: Path, records: dict[str, RevisionRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "revisions": {
            tag: {
                "tag": r.tag,
                "issued_at": r.issued_at,
                "author": r.author,
                "quantum_mm": r.quantum_mm,
                "fingerprints": r.fingerprints,
            }
            for tag, r in records.items()
        }
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _sheet_fps(project: Any, quantum_mm: float = 1.0) -> dict[str, dict[str, str]]:
    """Render-free fingerprints are impossible — sheets must be generated.

    For the register we fingerprint the *model* instead: a canonical JSON dump
    of every section.  That is coarser than entity fingerprints but stable,
    cheap, and sufficient for issue/compare gating.  Entity-level diff is the
    draw package's job at render time.
    """
    try:
        data = project.model_dump(mode="json")
    except Exception:
        data = str(project)
    import hashlib

    blob = json.dumps(data, sort_keys=True, default=str)
    return {"__model__": {"fp": hashlib.sha256(blob.encode()).hexdigest()[:16]}}


def freeze(
    project: Any,
    revision_tag: str,
    author: str = "",
    quantum_mm: float = 1.0,
) -> RevisionRecord:
    """Store fingerprints for *project* under *revision_tag* (immutable)."""
    path = _store_path(project)
    records = _load(path)
    if revision_tag in records:
        raise RevisionError(f"revision '{revision_tag}' already issued — revisions are immutable")
    rec = RevisionRecord(
        tag=revision_tag,
        issued_at=datetime.now(UTC).isoformat(timespec="seconds"),
        author=author,
        fingerprints=_sheet_fps(project, quantum_mm),
        quantum_mm=quantum_mm,
    )
    records[revision_tag] = rec
    _save(path, records)
    return rec


def last_issued(project: Any) -> RevisionRecord | None:
    records = _load(_store_path(project))
    if not records:
        return None
    return max(records.values(), key=lambda r: r.issued_at)


def compare_to_issued(project: Any) -> list[str]:
    """Fingerprints differing from the last issued revision (empty = clean)."""
    last = last_issued(project)
    if last is None:
        return ["__no_issued_revision__"]
    current = _sheet_fps(project, last.quantum_mm)
    changes: list[str] = []
    for sheet, fps in current.items():
        old = last.fingerprints.get(sheet, {})
        for key, fp in fps.items():
            if old.get(key) != fp:
                changes.append(f"{sheet}:{key}")
    return changes


def issued_tags(project: Any) -> list[str]:
    return sorted(_load(_store_path(project)).keys())


__all__ = [
    "RevisionRecord",
    "RevisionError",
    "freeze",
    "last_issued",
    "compare_to_issued",
    "issued_tags",
]
