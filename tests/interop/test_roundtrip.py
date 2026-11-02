"""W08 · export → import → compare for every format.

Each test writes a pinned project to a format, reads it back with the same
adapter family and compares the two ``BridgeProject`` dumps.

The comparison is *numeric*, not textual. ``Decimal("350")`` and
``Decimal("350.0")`` are the same quantity written two ways, and JSON, CSV and
Excel each pick their own spelling of it. Comparing the numbers — not the
strings — is what makes the budget in ``docs/interop.md`` a real claim rather
than a formatting coincidence.

Every listed comparison must be empty: the formats below are round-trippable
and their budget is zero loss. IFC and DWG are export-only (see
``test_ifc.py``) because their readers live in other vendors' tools.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]

pytestmark = pytest.mark.interop


def _norm(value):
    """Coerce a dumped value so 350, 350.0 and "350" compare equal."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, Decimal)):
        try:
            return Decimal(str(value))
        except InvalidOperation:
            return value
    if isinstance(value, str):
        try:
            return Decimal(value)
        except InvalidOperation:
            return value
    if isinstance(value, list):
        return [_norm(v) for v in value]
    if isinstance(value, dict):
        return {k: _norm(v) for k, v in value.items()}
    return value


def _diff(left, right, path: str = "") -> list[str]:
    """Return every path at which two dumps disagree, as human-readable text."""
    if isinstance(left, dict) and isinstance(right, dict):
        out: list[str] = []
        for key in sorted(set(left) | set(right)):
            if key not in left:
                out.append(f"{path}.{key}: <missing> != {right[key]!r}")
            elif key not in right:
                out.append(f"{path}.{key}: {left[key]!r} != <missing>")
            else:
                out += _diff(left[key], right[key], f"{path}.{key}")
        return out
    if isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            return [f"{path}: length {len(left)} != {len(right)}"]
        out = []
        for i, (a, b) in enumerate(zip(left, right, strict=True)):
            out += _diff(a, b, f"{path}[{i}]")
        return out
    if _norm(left) != _norm(right):
        return [f"{path}: {left!r} != {right!r}"]
    return []


def _dump(project) -> dict:
    from bridgecad_io.json_adapter import project_to_dict

    return project_to_dict(project)


# ── JSON ─────────────────────────────────────────────────────────────────────
def test_json_round_trip_is_lossless(tmp_path, pinned):
    """`.bridgecad.json` is the transport format: it must lose nothing."""
    from bridgecad_io import from_json, to_json

    target = tmp_path / "project.bridgecad.json"
    to_json(pinned, path=target)
    assert _diff(_dump(pinned), _dump(from_json(target))) == []


# ── CSV ──────────────────────────────────────────────────────────────────────
def test_csv_round_trip_is_lossless(tmp_path, pinned):
    """The sub-model CSV roster is a second lossless view of the same project."""
    from bridgecad_io import from_csv, to_csv

    written = to_csv(pinned, tmp_path / "csv")
    assert len(written) == 16, "14 sub-model CSVs + 2 schedules"
    assert _diff(_dump(pinned), _dump(from_csv(tmp_path / "csv"))) == []


# ── Excel ────────────────────────────────────────────────────────────────────
def test_excel_round_trip_is_lossless(tmp_path, pinned):
    """The 14-sheet workbook is the primary input contract.

    ``write_excel`` and ``read_excel`` both derive their field set from the
    Pydantic model, so the round-trip is lossless by construction rather than
    by a hand-maintained column list that can drift.
    """
    pytest.importorskip("openpyxl")
    from bridgecad_io import read_excel, write_excel

    target = tmp_path / "project.xlsx"
    write_excel(pinned, target)
    assert _diff(_dump(pinned), _dump(read_excel(target))) == []


# ── the budget itself ────────────────────────────────────────────────────────
def test_loss_budget_is_published_for_every_format():
    """DoD: 'loss budget defined' — every format this suite writes is listed."""
    body = (REPO / "docs" / "interop.md").read_text(encoding="utf-8")
    assert "## Loss budget" in body
    for fmt in ("JSON", "CSV", "Excel", "IFC", "DWG"):
        assert fmt in body, f"{fmt} is not covered by docs/interop.md"
