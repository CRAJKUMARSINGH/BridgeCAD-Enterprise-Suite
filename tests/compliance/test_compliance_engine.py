"""W06 · compliance engine, calc sheet and traceability gate.

Runs the clause-mapped report over the canonical project, checks every
utilisation is ``demand / capacity``, renders the calc sheet, and enforces the
DoD: **no gap in the traceability matrix** — every registered check id has a row
in ``docs/verification/TRACEABILITY.md`` naming an existing test node and an
existing V&V benchmark.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

from bridgecad_core.types import ValidationSeverity
from bridgecad_core.validation import ValidationFinding, ValidationReport
from bridgecad_qa.compliance import grade_from_score
from bridgecad_qa.compliance import score as compliance_score
from bridgecad_qa.compliance_engine import (
    CHECK_IDS,
    ComplianceCheck,
    ClauseRef,
    build_compliance_report,
    calc_sheet_markdown,
)

REPO = Path(__file__).resolve().parents[2]
TRACEABILITY = REPO / "docs" / "verification" / "TRACEABILITY.md"
VERIFICATION_CASES = REPO / "tests" / "verification" / "cases.py"

_ROW_RE = re.compile(r"^\|\s*`?(CC-\d{3})`?\s*\|(.+)\|\s*$", re.M)


def _benchmark_ids() -> set[str]:
    name = "bridgecad_vv_cases_for_compliance"
    spec = importlib.util.spec_from_file_location(name, VERIFICATION_CASES)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # dataclass resolution needs the module registered
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return {case.id for case in module.REGISTRY}


def _traceability_rows() -> dict[str, list[str]]:
    rows: dict[str, list[str]] = {}
    for match in _ROW_RE.finditer(TRACEABILITY.read_text(encoding="utf-8")):
        cells = [cell.strip().strip("`") for cell in match.group(2).split("|")]
        rows[match.group(1)] = cells
    return rows


# ---------------------------------------------------------------------------
# Object model and utilisation
# ---------------------------------------------------------------------------


def test_utilsation_is_always_demand_over_capacity():
    check = ComplianceCheck(
        check_id="CC-X",
        title="t",
        clause=ClauseRef("IRC:21", "2000", "Clause 1"),
        demand=3.0,
        capacity=2.0,
        unit="m",
    )
    assert check.utilisation == 1.5
    assert check.passed is False
    assert check.verdict == "FAIL"


def test_zero_capacity_is_infinite_utilisation_but_zero_demand_passes():
    base = dict(
        check_id="CC-X",
        title="t",
        clause=ClauseRef("IRC:21", "2000", "Clause 1"),
        capacity=0.0,
        unit="m",
    )
    assert ComplianceCheck(demand=1.0, **base).utilisation == float("inf")
    assert ComplianceCheck(demand=0.0, **base).utilisation == 0.0


def test_citation_renders_standard_edition_and_clause():
    ref = ClauseRef("IRC:112", "2020", "Clause 6.1")
    assert ref.citation == "IRC:112-2020 Clause 6.1"


# ---------------------------------------------------------------------------
# Report over the canonical project
# ---------------------------------------------------------------------------


def test_report_emits_every_registered_check(project):
    report = build_compliance_report(project)
    assert [check.check_id for check in report.checks] == list(CHECK_IDS)


def test_every_check_carries_a_clause_edition_demand_and_capacity(project):
    report = build_compliance_report(project)
    for check in report.checks:
        assert check.clause.standard and check.clause.edition and check.clause.clause
        assert check.unit
        assert check.capacity > 0
        assert check.utilisation == check.demand / check.capacity


def test_report_aggregates_consistently(project):
    report = build_compliance_report(project)
    assert report.n_checks == len(CHECK_IDS)
    assert report.n_passed + report.n_failed == report.n_checks
    assert report.pass_rate == report.n_passed / report.n_checks
    governing = report.governing
    assert governing is not None
    assert report.max_utilisation == governing.utilisation
    assert all(check.utilisation <= report.max_utilisation for check in report.checks)


def test_all_checks_pass_on_the_canonical_project(project):
    report = build_compliance_report(project)
    assert report.n_failed == 0, [c.check_id for c in report.failed()]


# ---------------------------------------------------------------------------
# Per-check identities (also exercised as VV-CMP-* benchmarks)
# ---------------------------------------------------------------------------


def _by_id(project):
    return {check.check_id: check for check in build_compliance_report(project).checks}


def test_cc001_span_depth_uses_the_registered_band(project):
    check = _by_id(project)["CC-001"]
    span = float(project.geometry_input.span_lengths_m[0])
    depth = float(project.superstructure.girder_depth_mm) / 1000.0
    assert check.demand == round(span / depth, 1)
    assert check.utilisation == check.demand / check.capacity


def test_cc002_slab_thickness_is_required_over_provided(project):
    check = _by_id(project)["CC-002"]
    assert check.capacity == float(project.superstructure.deck_thickness_mm)
    assert check.demand == 200.0  # IRC:21 Clause 304.7 for an RCC T-beam deck


def test_cc003_impact_factor_within_irc_ceiling(project):
    check = _by_id(project)["CC-003"]
    span = float(project.geometry_input.span_lengths_m[0])
    assert check.demand == 4.5 / (6.0 + span)
    assert check.capacity == 0.50


def test_cc004_expansion_joint_gap_rounds_to_five_mm(project):
    check = _by_id(project)["CC-004"]
    assert check.demand % 5.0 == 0.0
    assert check.capacity == 100.0


def test_cc005_freeboard_uses_soffit_minus_hfl(project):
    from bridgecad_core.geometry import long_section as ls

    check = _by_id(project)["CC-005"]
    geo = ls.compute_long_section_geometry(project)
    assert check.capacity == round(float(geo.freeboard_m), 3)
    assert check.demand == round(float(project.hydraulic_data.freeboard_m), 3)


def test_cc006_deck_grade_meets_irc112_minimum(project):
    check = _by_id(project)["CC-006"]
    assert check.demand == 30.0
    assert check.capacity == 30.0


def test_mutation_thin_slab_fails_cc002(blank_project):
    blank_project.superstructure.deck_thickness_mm = 100
    check = _by_id(blank_project)["CC-002"]
    assert check.utilisation == 2.0
    assert check.passed is False
    assert check.verdict == "FAIL"


# ---------------------------------------------------------------------------
# Calc sheet
# ---------------------------------------------------------------------------


def test_calc_sheet_is_deterministic_and_complete(project):
    first = calc_sheet_markdown(project)
    second = calc_sheet_markdown(project)
    assert first == second
    for check_id in CHECK_IDS:
        assert f"`{check_id}`" in first
    assert "IRC:6-2017" in first and "EN 1990:2002" in first
    assert "IRC:112-2020 Clause 6.1" in first
    assert "## 3. Summary" in first


def test_calc_sheet_reports_the_governing_check(project):
    markdown = calc_sheet_markdown(project)
    report = build_compliance_report(project)
    governing = report.governing
    assert governing is not None
    assert f"`{governing.check_id}` @" in markdown


# ---------------------------------------------------------------------------
# Traceability — the DoD gate: no gap in the matrix
# ---------------------------------------------------------------------------


def test_traceability_covers_every_check_id():
    rows = _traceability_rows()
    missing = [check_id for check_id in CHECK_IDS if check_id not in rows]
    assert not missing, f"checks absent from TRACEABILITY.md: {missing}"


def test_traceability_rows_name_a_clause_test_and_benchmark():
    rows = _traceability_rows()
    for check_id, cells in rows.items():
        assert len(cells) >= 5, f"{check_id} row is under-specified: {cells}"
        clause, test_ref, benchmark = cells[2], cells[3], cells[4]
        assert clause, f"{check_id} has no clause"
        assert "::" in test_ref, f"{check_id} has no test node: {test_ref!r}"
        assert benchmark.startswith("VV-"), f"{check_id} has no benchmark id: {benchmark!r}"


def test_traceability_benchmarks_exist_in_the_vv_registry():
    rows = _traceability_rows()
    known = _benchmark_ids()
    for check_id, cells in rows.items():
        assert cells[4] in known, f"{check_id} names an unknown benchmark {cells[4]!r}"


def test_traceability_tests_exist_on_disk():
    rows = _traceability_rows()
    for check_id, cells in rows.items():
        file_part, _, func = cells[3].partition("::")
        target = REPO / file_part
        assert target.is_file(), f"{check_id} names a missing test file {file_part!r}"
        assert f"def {func}(" in target.read_text(encoding="utf-8"), (
            f"{check_id} names a missing test {cells[3]!r}"
        )


# ---------------------------------------------------------------------------
# Grade reconciliation
# ---------------------------------------------------------------------------


def test_grade_from_score_caps_a_plus_when_a_critical_is_outstanding():
    assert grade_from_score(96, 0) == "A+"
    assert grade_from_score(96, 1) == "A"
    assert grade_from_score(50, 3) == "F"


def test_compliance_score_uses_the_shared_grade_function():
    findings = [
        ValidationFinding("C01", "d", ValidationSeverity.CRITICAL, True, ""),
        ValidationFinding("W01", "d", ValidationSeverity.WARNING, True, ""),
    ]
    report = ValidationReport(findings)
    comp = compliance_score(report)
    assert comp.grade == grade_from_score(report.score, report.critical_fail_count)
    assert comp.grade == "A+"
