"""Wing-02 — golden cases exist, are complete, and match the model.

A golden case with no reviewer is honest: it says the numbers are internally
consistent, not that an engineer approved them. `reviewed_by` flips only after
Wing-08 sign-off.
"""
from __future__ import annotations

import pytest

from . import contract

pytestmark = pytest.mark.draw

REQUIRED_KEYS = {
    "slug", "fixture", "source_drawing", "class", "expected", "provenance",
}
REQUIRED_EXPECTED = {
    "span_count", "total_length_m", "overall_width_m", "intermediate_piers",
    "abtl_m", "abtl_source", "splay_deg",
    "wing_face_run_m", "wing_length_m", "wing_return_m",   # NEW
}


@pytest.mark.parametrize("slug", contract.golden_slugs())
def test_golden_case_is_well_formed(slug: str):
    g = contract.load_golden(slug)
    assert REQUIRED_KEYS <= set(g), f"{slug} missing keys: {REQUIRED_KEYS - set(g)}"
    assert REQUIRED_EXPECTED <= set(g["expected"]), (
        f"{slug} expected-block missing: {REQUIRED_EXPECTED - set(g['expected'])}"
    )
    assert (contract.REPO / g["fixture"]).exists(), f"{slug} fixture missing"


@pytest.mark.parametrize("slug", contract.golden_slugs())
def test_golden_case_matches_the_model(slug: str):
    """The pinned summary must match what the model actually produces."""
    g = contract.load_golden(slug)
    project = contract.make_project(slug)
    exp = g["expected"]

    assert len(project.spans) == exp["span_count"]
    assert sum(s.length_m for s in project.spans) == pytest.approx(exp["total_length_m"], abs=1e-6)
    assert len(contract.pier_positions(project)) == exp["intermediate_piers"]

    abtl, source = contract.resolve_abtl(project)
    assert abtl == pytest.approx(exp["abtl_m"], abs=1e-6)
    assert source == exp["abtl_source"], (
        f"{slug}: ABTL resolved from {source!r}, golden pins {exp['abtl_source']!r} — "
        "a workbook field was added or the ladder reordered"
    )

    # NEW: the wing geometry the golden case pins must match the model.
    # Without this, a drifted splay default is invisible to the suite.
    if "wing_length_m" in exp:
        walls = contract.wing_wall_geometry(project)
        assert len(walls) == 2, f"{slug}: expected a left and right wing"
        for w in walls:
            assert w.splay_deg == pytest.approx(exp["splay_deg"], abs=1e-9), (
                f"{slug}/{w.side}: splay {w.splay_deg}, golden pins {exp['splay_deg']}"
            )
            assert w.face_run_m == pytest.approx(exp["wing_face_run_m"], abs=1e-6)
            assert w.length_m == pytest.approx(exp["wing_length_m"], rel=1e-9)
            assert w.return_m == pytest.approx(exp["wing_return_m"], abs=1e-6)


def test_the_five_cases_are_all_present():
    slugs = set(contract.golden_slugs())
    assert {"simple_12m", "continuous_3x12m", "skew15_3x18m",
            "well_0_600", "pp05_30m_psc"} <= slugs
