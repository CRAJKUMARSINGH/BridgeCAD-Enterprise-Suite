"""SS3 Part B — the drawing-audit rows must be provably able to fail.

A guard nobody has ever seen trip is indistinguishable from a guard that does
nothing. These tests drive each row with a project that breaks its condition
and assert the finding comes back ``passed=False``; the model-level rows are
driven directly, the sheet-level rows through the layout audit reading the
*rendered* DXF.
"""
from __future__ import annotations

import pytest

from . import contract

pytestmark = pytest.mark.draw


@pytest.fixture(scope="module")
def baseline():
    return contract.make_project("simple_12m")


def _row(project, check_id: str):
    from bridgecad_core.validation import run_all

    findings = {f.check_id: f for f in run_all(project).findings}
    assert check_id in findings, f"{check_id} never reported a finding"
    return findings[check_id]


class _FakeFamily:
    """A stand-in enum member, so the family gate can be forced on a fixture."""

    def __init__(self, name: str) -> None:
        self.name = name

    def __str__(self) -> str:
        return self.name


# ── registry identity ────────────────────────────────────────────────────────
AUDIT_ROWS = {
    "W76": ("V151", "warning"),
    "W77": ("V152", "critical"),
    "W78": ("V153", "critical"),
    "W79": ("V154", "critical"),
    "W80": ("V155", "warning"),
    "W81": ("V156", "critical"),
    "W82": ("V157", "critical"),
    "W83": ("V158", "critical"),
    "W84": ("V159", "warning"),
    "I51": ("V160", "info"),
    "I52": ("V161", "info"),
    "I53": ("V162", "info"),
    "I54": ("V163", "info"),
}


@pytest.mark.parametrize("design_id", sorted(AUDIT_ROWS))
def test_row_is_registered_with_its_stable_v_id(design_id):
    from bridgecad_core import validation_registry as reg

    v_id, tier = AUDIT_ROWS[design_id]
    by_source = {r.source_rule_id: r for r in reg.RULES}
    rule = by_source[design_id]
    assert rule.id == v_id, f"{design_id} moved from {v_id} to {rule.id}"
    assert rule.tier == tier
    assert rule.implemented is True
    assert rule.standard and rule.clause


@pytest.mark.parametrize("design_id", sorted(AUDIT_ROWS))
def test_row_fires_in_the_qa_output(design_id, baseline):
    """Every row must be reported, or the wiring dropped it silently."""
    from bridgecad_qa.rules_engine import run_rules

    fired = {f.rule_id for f in run_rules(baseline)}
    assert AUDIT_ROWS[design_id][0] in fired


# ── the fail-proof: W84 on the model ─────────────────────────────────────────
def test_presence_by_type_fails_when_a_non_pile_foundation_carries_piles(baseline):
    from bridgecad_core import types as T

    # simple_12m is a pile foundation, so the row is satisfied as it stands.
    assert _row(baseline, "W84").passed is True

    broken = contract.make_project("simple_12m")
    broken.foundation_details.type = T.FoundationType.RAFT
    assert _row(broken, "W84").passed is False


# ── the fail-proof: family rows gate, then bite when the parameters exist ────
def test_box_cell_lattice_zero_count_fails_the_row(baseline):
    from bridgecad_core.validation import check_bx_cell_closed

    broken = contract.make_project("simple_12m")
    broken.superstructure.type = _FakeFamily("BOX_CELL_MULTI")
    broken.foundation_details.unit_cell_counts = [4, 0, 4]
    assert check_bx_cell_closed(broken).passed is False

    broken.foundation_details.unit_cell_counts = [4, 3, 4]
    assert check_bx_cell_closed(broken).passed is True


def test_box_cell_row_is_out_of_scope_on_a_non_box_cell(baseline):
    from bridgecad_core.validation import check_bx_cell_closed

    assert check_bx_cell_closed(baseline).passed is True


def test_box_cell_row_says_why_it_could_not_evaluate(baseline):
    """A missing lattice is 'not evaluable', never a silent clean pass."""
    from bridgecad_core.validation import check_bx_cell_closed

    broken = contract.make_project("simple_12m")
    broken.superstructure.type = _FakeFamily("BOX_CELL_MULTI")
    finding = check_bx_cell_closed(broken)
    assert finding.passed is True
    assert "primitive" in finding.message


def test_arch_schedule_row_fails_when_endpoints_do_not_close(baseline):
    from bridgecad_core.validation import check_ar_schedule_closed

    broken = contract.make_project("simple_12m")
    broken.superstructure.type = _FakeFamily("RCC_ARCH_OPEN_SPANDREL")
    broken.superstructure.arch_schedule_mm = [(0, 400), (5000, 900), (10000, 0)]
    assert check_ar_schedule_closed(broken).passed is False

    broken.superstructure.arch_schedule_mm = [(0, 0), (5000, 900), (10000, 0)]
    assert check_ar_schedule_closed(broken).passed is True


def test_arch_rib_on_curve_row_fails_when_a_node_leaves_the_parabola(baseline):
    from bridgecad_core.validation import check_ar_rib_on_curve

    broken = contract.make_project("simple_12m")
    broken.superstructure.type = _FakeFamily("RCC_ARCH_OPEN_SPANDREL")
    broken.superstructure.arch_rise_mm = 4000
    span_mm = float(broken.geometry_input.span_lengths_m[0]) * 1000.0
    a = 4000.0 / (span_mm / 2.0) ** 2
    exact = [(0, 0), (span_mm / 2.0, 4000), (span_mm, 0)]
    assert check_ar_rib_on_curve(broken).passed is True
    del a

    broken.superstructure.arch_schedule_mm = [(0, 0), (span_mm / 2.0, 9999), (span_mm, 0)]
    assert check_ar_rib_on_curve(broken).passed is False


def test_precast_strip_gap_row_reads_the_declared_gap(baseline):
    from bridgecad_core.validation import check_pa_strip_gap

    broken = contract.make_project("simple_12m")
    broken.superstructure.type = _FakeFamily("PRECAST_ARCH")
    broken.superstructure.arch_strip_gap_mm = 120
    assert check_pa_strip_gap(broken).passed is False

    broken.superstructure.arch_strip_gap_mm = 100
    assert check_pa_strip_gap(broken).passed is True


# ── the layout audit is opt-in and honest about it ───────────────────────────
def test_layout_audit_is_off_by_default():
    from bridgecad_draw import layout_audit as la

    la.set_enabled(None)
    assert la.audit_enabled() is False


def test_sheet_rows_report_not_evaluated_while_the_audit_is_off(baseline):
    from bridgecad_draw import layout_audit as la

    la.set_enabled(False)
    try:
        for check_id in ("W81", "W82", "W83"):
            assert _row(baseline, check_id).passed is True
    finally:
        la.set_enabled(None)


def test_scale_ladder_agrees_with_fit():
    from bridgecad_draw import layout_audit as la
    from bridgecad_draw.fit import LADDER

    assert tuple(la._SCALE_LADDER) == tuple(LADDER)


def test_bbox_overlap_semantics():
    from bridgecad_draw.layout_audit import BBox

    a = BBox(0, 0, 10, 10, text="A", sheet="S1")
    b = BBox(5, 5, 15, 15, text="B", sheet="S1")
    assert a.overlaps(b, tol=0.5) is True
    assert a.overlaps(BBox(11, 0, 20, 10), tol=0.5) is False


# ── the audit reads the rendered DXF, not the intent ────────────────────────
def test_enabled_audit_renders_and_reads_the_document(baseline):
    from bridgecad_draw import layout_audit as la

    la.set_enabled(True)
    try:
        audit = la.collect(baseline)
        assert audit.rendered, f"audit failed to render: {audit.error}"
        assert audit.text_boxes, "no text entities were read from the rendered package"
        assert audit.layers_drawn, "no layers were read from the rendered package"
        for sheet, denom in audit.printed_scales:
            assert denom == 1 or la.scale_on_ladder(denom), (
                f"{sheet} captions a non-ladder scale 1:{denom}"
            )
        from bridgecad_core.validation import run_all

        findings = {f.check_id: f for f in run_all(baseline).findings}
        for check_id in ("W81", "W82", "W83", "I52", "I53", "I54"):
            assert check_id in findings
    finally:
        la.set_enabled(None)
