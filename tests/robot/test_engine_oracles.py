"""Engineering-domain oracles bound to the live ``bridgecad_core`` contract.

These catch "it ran but it's wrong": a QA run that never scores, a plan with the
wrong corner count, a cross-section whose width disagrees with its own input, a
long section whose deck sits below its soffit, a takeoff that shrinks as the
span grows. Software-green over an engineering-wrong number is still a FAIL.

Contract source: ``packages/bridgecad-core/bridgecad_core/__init__.py``.
"""

from __future__ import annotations

import pytest

from bridgecad_core import (
    compute_cross_section_geometry,
    compute_long_section_geometry,
    compute_plan_geometry,
    irc6_combinations,
)
from bridgecad_core.quantities import extract_quantities
from bridgecad_core.types import ValidationSeverity
from bridgecad_core.validation import run_all

pytestmark = pytest.mark.robot


# ---------------------------------------------------------------------------
# Validation oracle
# ---------------------------------------------------------------------------
def test_validation_report_is_well_formed(project):
    report = run_all(project)
    assert report.findings, "no QA checks ran against a valid project"
    for finding in report.findings:
        assert finding.check_id
        assert finding.description
        assert isinstance(finding.severity, ValidationSeverity)
    assert 0 <= report.score <= 100
    assert report.overall_status in {"PASS", "WARN", "FAIL"}
    # The status must agree with the findings, not be a constant.
    failed_critical = any(
        not f.passed and f.severity is ValidationSeverity.CRITICAL for f in report.findings
    )
    assert (report.overall_status == "FAIL") == failed_critical


# ---------------------------------------------------------------------------
# Geometry oracles
# ---------------------------------------------------------------------------
def test_plan_geometry_matches_project(project):
    geo = compute_plan_geometry(project)
    gi = project.geometry_input
    assert len(geo.deck_corners) == 4, "a rectangular deck has exactly four corners"
    assert geo.total_length_m == pytest.approx(float(gi.total_length_m), rel=1e-9)
    assert geo.overall_width_m == pytest.approx(float(gi.overall_width_m), rel=1e-9)
    assert len(geo.span_lengths_m) == int(gi.span_count)


def test_cross_section_width_matches_input(project):
    geo = compute_cross_section_geometry(project)
    gi = project.geometry_input
    assert geo.overall_width_m == pytest.approx(float(gi.overall_width_m), rel=1e-6)
    assert geo.carriageway_width_m > 0
    assert geo.half_width_offsets == sorted(geo.half_width_offsets), (
        "zone offsets must march outward from the centreline"
    )


def test_long_section_levels_are_ordered(project):
    geo = compute_long_section_geometry(project)
    assert geo.top_of_deck_rl > geo.soffit_rl, "deck surface sits below the girder soffit"
    assert geo.chainage_end_m > geo.chainage_start_m


# ---------------------------------------------------------------------------
# Quantity oracles
# ---------------------------------------------------------------------------
def _concrete_cum(project) -> float:
    """Total concrete (m³) across every item the takeoff reports."""
    return sum(item.qty for item in extract_quantities(project).items if item.unit == "cum")


def test_quantities_are_non_negative(project):
    boq = extract_quantities(project)
    assert boq.items, "no BOQ items extracted from a valid project"
    for item in boq.items:
        assert item.qty >= 0, f"{item.code} has negative quantity {item.qty}"


def test_concrete_grows_with_total_length(project, span_variant):
    short = _concrete_cum(project)
    long = _concrete_cum(span_variant([24.0, 24.0]))
    assert short > 0
    assert long > short, f"48 m span ({long:.1f} m³) is not heavier than 12 m ({short:.1f} m³)"


# ---------------------------------------------------------------------------
# Standards oracle
# ---------------------------------------------------------------------------
def test_irc6_combinations_are_complete():
    combos = irc6_combinations()
    assert combos, "no IRC:6 combinations registered"
    ids = [c.id for c in combos]
    assert len(ids) == len(set(ids)), "duplicate combination id"
    for combo in combos:
        assert "IRC" in combo.standard
        assert combo.limit_state in {"ULS", "SLS", "SEISMIC"}
        assert combo.terms, f"{combo.id} references no load cases"
    assert any(c.limit_state == "ULS" for c in combos), "no ultimate limit state combination"
