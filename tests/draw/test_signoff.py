"""Wing-17 — the review gate.

Four things, in order of importance:
  1. a promoted sheet that nobody reviewed is a finding, not a pass
  2. a signoff whose geometry moved is STALE and must be re-reviewed
  3. a scaffold sheet must not be signed — you cannot confirm absent geometry
  4. every signoff names a reference file that exists
"""
from __future__ import annotations

import json

import pytest

from . import contract, signoff

pytestmark = pytest.mark.draw

SPEC = json.loads((contract.REPO / "tests" / "draw" / "sheets.spec.json").read_text(encoding="utf-8"))
SHEETS = SPEC["sheets"]
PROMOTED = sorted(s for s, v in SHEETS.items() if v["status"] == "promoted")
SIGNOFFS = {so.sheet: so for so in signoff.load_all()}


@pytest.fixture
def project():
    return contract.make_project("simple_12m")


@pytest.mark.parametrize("sheet", PROMOTED)
def test_every_promoted_sheet_is_signed(sheet: str):
    assert sheet in SIGNOFFS, (
        f"{sheet} is promoted but nobody reviewed it — it is consistent, not confirmed"
    )


@pytest.mark.parametrize("sheet", sorted(SIGNOFFS))
def test_signoffs_are_not_stale(sheet: str, project):
    so = SIGNOFFS[sheet]
    assert not signoff.is_stale(project, so), (
        f"{sheet}: geometry changed since {so.reviewed_by} reviewed it on "
        f"{so.reviewed_on} — the review has expired, re-review or revert"
    )


def test_scaffold_sheets_are_not_signed():
    for sheet in SIGNOFFS:
        if sheet in SHEETS and SHEETS[sheet]["status"] == "scaffold":
            pytest.fail(f"{sheet} is signed but still scaffold — un-sign it")


@pytest.mark.parametrize("sheet", sorted(SIGNOFFS))
def test_signoff_references_exist(sheet: str):
    so = SIGNOFFS[sheet]
    path = signoff.REF_DIR / so.against
    assert path.exists(), f"{sheet}: reviewed against {so.against!r}, which is not on disk"


@pytest.mark.parametrize("sheet", sorted(SIGNOFFS))
def test_signoffs_say_what_was_compared(sheet: str):
    so = SIGNOFFS[sheet]
    assert len(so.compared) >= 3
    for item in so.compared:
        assert len(item) > 5 and item[0].isupper() or item[0].isdigit(), (
            f"{sheet}: comparison {item!r} is too thin to check"
        )


def test_reviewer_is_a_person_not_a_placeholder():
    for sheet, so in SIGNOFFS.items():
        assert so.reviewed_by.upper() not in ("REPLACE_ME", "TBC", "TBD", "")


def test_review_has_a_date_and_revision():
    for sheet, so in SIGNOFFS.items():
        assert so.reviewed_on and len(so.reviewed_on) == 10
        assert so.revision.startswith(("P", "C", "A")), (
            f"{sheet}: revision {so.revision!r} is not a P/C/A series code"
        )


def test_stale_signoff_is_detected_when_geometry_moves(project):
    """The mechanism, tested directly: perturb one level, hash must change."""
    so = next(iter(SIGNOFFS.values()))
    before = signoff.is_stale(project, so)
    assert not before
    project.levels.hfl_m += 0.25
    assert signoff.is_stale(project, so), "moving HFL by 250 mm did not expire the review"
