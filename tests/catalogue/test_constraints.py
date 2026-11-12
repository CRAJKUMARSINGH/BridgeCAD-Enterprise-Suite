"""Cross-constraint behaviour of the catalogue resolver and sweep."""
from __future__ import annotations

from decimal import Decimal

import pytest

from bridgecad_catalogue import registry, sweep
from bridgecad_catalogue.resolve import resolve
from bridgecad_catalogue.schema import Violation


@pytest.fixture
def card_001() -> dict:
    return registry.by_id("BR-I-2022-001")


@pytest.fixture
def card_004() -> dict:
    return registry.by_id("BR-I-2022-004")


@pytest.fixture
def card_006() -> dict:
    return registry.by_id("BR-I-2022-006")


@pytest.fixture
def card_009() -> dict:
    return registry.by_id("BR-I-2022-009")


@pytest.fixture
def card_014() -> dict:
    return registry.by_id("BR-I-2022-014")


# ── derivations ──────────────────────────────────────────────────────────────


def test_total_length_tracks_spans(card_006: dict) -> None:
    p = resolve(card_006, {"span_length_m": 12})
    assert p["total_length_m"] == 60 and len(p["span_lengths"]) == 5


def test_soffit_moves_with_deck(card_001: dict) -> None:
    a = resolve(card_001, {})["soffit_level"]
    b = resolve(card_001, {"deck_thickness_mm": 700})["soffit_level"]
    assert b == a - Decimal("0.200")


def test_girder_count_grows_with_width(card_009: dict) -> None:
    wide = resolve(card_009, {"carriageway_width": 11.0})["girders_per_deck"]
    base = resolve(card_009, {})["girders_per_deck"]
    assert wide > base


# ── rejections ───────────────────────────────────────────────────────────────


def test_freeboard_breach_rejected(card_001: dict) -> None:
    with pytest.raises(Violation, match="freeboard"):
        resolve(card_001, {"hfl_m": 103.0})


def test_open_foundation_on_weak_soil_rejected(card_001: dict) -> None:
    with pytest.raises(Violation, match="SBC"):
        resolve(card_001, {"sbc_t_per_m2": 15})


def test_locked_needs_force(card_014: dict) -> None:
    # ``superstructure_type`` is booklet identity — changing it needs --force.
    with pytest.raises(Violation, match="locked"):
        resolve(card_014, {"superstructure_type": "RCC_SOLID_SLAB"})
    forced = resolve(card_014, {"superstructure_type": "RCC_SOLID_SLAB"}, force=True)
    assert forced["superstructure_type"] == "RCC_SOLID_SLAB"


def test_unknown_variable_rejected(card_001: dict) -> None:
    with pytest.raises(Violation, match="unknown variable"):
        resolve(card_001, {"wibble_m": 1})


def test_out_of_range_rejected(card_001: dict) -> None:
    with pytest.raises(Violation, match="not a multiple"):
        resolve(card_001, {"span_length_m": 10.3})


# ── the model must stop lying (box cell / arch) ──────────────────────────────


def test_box_cell_has_no_piers(card_004: dict) -> None:
    p = resolve(card_004, {})
    assert p["pier_count"] == 0
    assert p["bearing_type"] == "NONE"


def test_box_cell_soffit_is_rtl_minus_deck(card_004: dict) -> None:
    p = resolve(card_004, {})
    assert p["soffit_level"] == Decimal(str(p["road_level"])) - Decimal("0.500")


def test_approximation_is_reported(card_004: dict) -> None:
    p = resolve(card_004, {})
    assert p.get("approximation") is True
    assert any("approximation" in w for w in p.warnings)


# ── the trace ────────────────────────────────────────────────────────────────


def test_trace_records_derivations(card_006: dict) -> None:
    p = resolve(card_006, {"span_length_m": 12})
    fields = {row["field"] for row in p.trace}
    assert {"total_length_m", "soffit_level", "foundation_level"} <= fields


# ── sweep ────────────────────────────────────────────────────────────────────


def test_sweep_expands_a_range() -> None:
    matrix = sweep.matrix(["span_length_m=10:20:5"])
    assert [m["span_length_m"] for m in matrix] == [Decimal(x) for x in ("10", "15", "20")]


def test_sweep_rejects_a_choice_field() -> None:
    with pytest.raises(Violation, match="not sweepable"):
        sweep.parse("carriageway_width=3.5:11:3.5")


def test_sweep_rejects_a_bad_step() -> None:
    with pytest.raises(Violation, match="positive"):
        sweep.parse("span_length_m=10:20:0")
