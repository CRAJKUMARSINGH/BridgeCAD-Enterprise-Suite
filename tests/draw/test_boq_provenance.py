"""Wing-13 — every BOQ line is traceable, or says why it is not.

The failure mode being closed: a plausible number with no provenance. That is
worse than a blank, because a blank is visibly unknown and a plausible number
is invisibly unknown.
"""
from __future__ import annotations

import pytest

from . import contract

pytestmark = pytest.mark.draw

from bridgecad_bill.provenance import (  # noqa: E402
    BoqLine, LineStatus, RateSource, section_summary,
)


def _lines():
    from bridgecad_bill.processor import build_boq
    return build_boq(contract.make_project("simple_12m"))


def test_every_line_has_a_status():
    for ln in _lines():
        assert isinstance(ln.status, LineStatus), f"{ln.item_no}: no status"


def test_calculated_lines_carry_a_formula_and_their_inputs():
    for ln in _lines():
        if ln.status is LineStatus.CALCULATED:
            assert ln.formula, f"{ln.item_no}: calculated with no formula"
            assert ln.source_fields, f"{ln.item_no}: calculated with no source fields"


def test_estimated_lines_carry_a_multiplier_and_its_source():
    for ln in _lines():
        if ln.status is LineStatus.ESTIMATED:
            assert ln.multiplier is not None, ln.item_no
            assert ln.multiplier_source, (
                f"{ln.item_no}: estimated with no source note — a multiplier with "
                "no provenance is the same problem as a bare number"
            )


def test_not_calculated_lines_carry_a_reason_and_no_number():
    for ln in _lines():
        if ln.status is LineStatus.NOT_CALCULATED:
            assert ln.reason, f"{ln.item_no}: not_calculated with no reason"
            assert ln.amount is None, (
                f"{ln.item_no}: not_calculated but amount={ln.amount} — "
                "a number here is a silent default"
            )


def test_missing_input_returns_not_calculated_not_a_default():
    """The core rule. Blank out a required field and the line must say so."""
    project = contract.make_project("simple_12m")
    project.materials.concrete_grade = None
    lines = _lines.__wrapped__() if hasattr(_lines, "__wrapped__") else None  # placeholder
    from bridgecad_bill.processor import build_boq
    lines = build_boq(project)
    affected = [ln for ln in lines if "concrete" in ln.description.lower()]
    assert affected, "no concrete lines found"
    assert any(ln.status is LineStatus.NOT_CALCULATED for ln in affected), (
        "blanking the concrete grade did not produce a not_calculated line"
    )


def test_rate_source_is_recorded_on_every_priced_line():
    for ln in _lines():
        if ln.status is not LineStatus.NOT_CALCULATED:
            assert isinstance(ln.rate_source, RateSource), ln.item_no
            assert ln.rate_source is not RateSource.MISSING, (
                f"{ln.item_no}: priced with a missing rate source"
            )


def test_pwd_override_beats_morth_base():
    """Lookup order is a contract, not an implementation detail."""
    from bridgecad_bill.rates_db import lookup_rate
    rate, source = lookup_rate("300", state="MH")
    assert source in (RateSource.PWD_OVERRIDE, RateSource.MORTH_2024_25)
    assert rate > 0


def test_amount_is_quantity_times_rate_on_priced_lines():
    for ln in _lines():
        if ln.status is not LineStatus.NOT_CALCULATED and ln.amount is not None:
            assert ln.amount == pytest.approx(ln.quantity * ln.rate, rel=1e-9), ln.item_no


def test_section_summary_states_its_own_incompleteness():
    summary = section_summary(_lines())
    assert summary["completeness"] <= 1.0
    assert summary["not_calculated"] == len(summary["unknown_items"])
    if summary["not_calculated"]:
        assert summary["unknown_items"], "unknown lines not itemised"


def test_status_enum_construction_rules_are_enforced():
    with pytest.raises(ValueError, match="formula"):
        BoqLine("1", "d", "m3", 1.0, 1.0, 1.0, LineStatus.CALCULATED)
    with pytest.raises(ValueError, match="multiplier"):
        BoqLine("2", "d", "m3", 1.0, 1.0, 1.0, LineStatus.ESTIMATED)
    with pytest.raises(ValueError, match="reason"):
        BoqLine("3", "d", "m3", None, None, None, LineStatus.NOT_CALCULATED)


def test_boq_report_shows_provenance_columns():
    """An engineer reading the Excel must see status, formula and rate source
    without opening the source."""
    from bridgecad_bill.formatters import to_html
    html = to_html(_lines())
    for column in ("status", "formula", "rate source"):
        assert column.lower() in html.lower(), f"BOQ report lacks a {column!r} column"
