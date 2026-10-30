"""Pure-function tests for ``bridgecad_core.quantities``."""

from __future__ import annotations

from decimal import Decimal

import pytest

from bridgecad_core.quantities import (
    BillItem,
    BillOfQuantities,
    _deck_slab_cum,
    _f,
    _name,
    _pier_count,
    _rebar_kg,
    _wearing_coat_cum,
    extract_quantities,
)
from bridgecad_core.types import FoundationType

# ---------------------------------------------------------------------------
# _f coercion
# ---------------------------------------------------------------------------


def test_f_none_returns_default():
    assert _f(None, 7.5) == 7.5
    assert _f(None) == 0.0


def test_f_parses_numeric_string_and_decimal():
    assert _f("3.5", 0.0) == pytest.approx(3.5)
    assert _f(Decimal("2.25"), 0.0) == pytest.approx(2.25)


def test_f_passes_through_numbers():
    for value, expected in [(4, 4.0), (-3, -3.0), (1.5, 1.5)]:
        assert _f(value, 0.0) == pytest.approx(expected)


def test_f_non_numeric_string_falls_back_to_default():
    assert _f("not-a-number", 9.0) == 9.0


# ---------------------------------------------------------------------------
# _name
# ---------------------------------------------------------------------------


def test_name_uses_enum_member_name_and_uppercases_strings():
    assert _name(FoundationType.PILE) == "PILE"
    assert _name("wall/rectangular") == "WALL/RECTANGULAR"


# ---------------------------------------------------------------------------
# _rebar_kg
# ---------------------------------------------------------------------------


def test_rebar_kg_is_linear_in_volume():
    assert _rebar_kg(20.0, "deck_slab") == pytest.approx(2.0 * _rebar_kg(10.0, "deck_slab"))


def test_rebar_kg_zero_volume_is_zero():
    assert _rebar_kg(0.0, "piles") == 0.0


def test_rebar_kg_unknown_key_uses_half_percent_fallback():
    # Fallback pct = 0.5% -> 100 m3 * 0.005 * 7.85 t/m3 * 1000.
    assert _rebar_kg(100.0, "no_such_component") == pytest.approx(100.0 * 0.005 * 7.85 * 1000.0)


# ---------------------------------------------------------------------------
# component volume helpers
# ---------------------------------------------------------------------------


def test_deck_slab_cum_matches_length_width_thickness(project):
    gi = project.geometry_input
    t = float(project.superstructure.deck_thickness_mm) / 1000.0
    expected = float(gi.total_length_m) * float(gi.overall_width_m) * t
    assert _deck_slab_cum(project) == pytest.approx(expected)


def test_wearing_coat_cum_uses_carriageway_width(project):
    gi = project.geometry_input
    t = float(project.superstructure.wearing_coat_thickness_mm) / 1000.0
    expected = float(gi.total_length_m) * float(gi.carriageway_width_m) * t
    assert _wearing_coat_cum(project) == pytest.approx(expected)


def test_pier_count_is_nspan_minus_one_and_non_negative(project):
    assert _pier_count(project) == max(int(project.geometry_input.span_count) - 1, 0)
    assert _pier_count(project) >= 0


# ---------------------------------------------------------------------------
# BillOfQuantities data shape
# ---------------------------------------------------------------------------


def test_bill_item_defaults_rate_and_amount_to_none():
    item = BillItem(code="X", description="d", unit="cum", qty=1.0)
    assert item.rate is None
    assert item.amount is None


def test_bill_of_quantities_add_appends():
    boq = BillOfQuantities()
    boq.add(BillItem(code="X", description="d", unit="cum", qty=1.0))
    boq.add(BillItem(code="Y", description="e", unit="kg", qty=2.0))
    assert [it.code for it in boq.items] == ["X", "Y"]
    assert boq.total_cost == 0.0


# ---------------------------------------------------------------------------
# extract_quantities
# ---------------------------------------------------------------------------


def test_extract_quantities_returns_well_formed_boq(project):
    boq = extract_quantities(project)
    assert isinstance(boq, BillOfQuantities)
    assert len(boq.items) > 0
    assert all(it.code and it.description and it.unit for it in boq.items)
    assert all(it.qty >= 0 for it in boq.items)


def test_extract_quantities_codes_are_unique(project):
    codes = [it.code for it in extract_quantities(project).items]
    assert len(codes) == len(set(codes))


def test_extract_quantities_is_unpriced_before_costing(project):
    boq = extract_quantities(project)
    assert boq.total_cost == 0.0
    assert all(it.rate is None for it in boq.items)
