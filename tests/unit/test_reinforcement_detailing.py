"""Unit tests for reinforcement items, utilisation and the detailing store."""

from __future__ import annotations

from decimal import Decimal

from bridgecad_core import detailing
from bridgecad_core.reinforcement import RebarItem, as_required_for, default_items


def _item(dia: int, spacing: int, as_req: str = "1000") -> RebarItem:
    return RebarItem(
        mark="T1",
        element="ABUTMENT_CAP",
        face="TEST",
        section_depth_mm=600,
        as_required_mm2_per_m=Decimal(as_req),
        design_dia_mm=dia,
        design_spacing_mm=spacing,
    )


def test_as_provided_three_pairs():
    # 16@150 → 1000/150 * pi * 8^2 ≈ 1340.41 mm2/m
    assert abs(float(_item(16, 150).as_provided_mm2_per_m) - 1340.41) < 0.5
    # 20@150 → ≈ 2094.40
    assert abs(float(_item(20, 150).as_provided_mm2_per_m) - 2094.40) < 0.5
    # 25@100 → ≈ 4908.74
    assert abs(float(_item(25, 100).as_provided_mm2_per_m) - 4908.74) < 0.5


def test_utilisation_direction():
    # As,prov > As,req → utilisation < 1 (adequate); never inverted.
    item = _item(16, 150, as_req="1000")
    assert item.utilisation < Decimal("1")
    tight = _item(12, 300, as_req="1000")  # 12@300 ≈ 377 < 1000
    assert tight.utilisation > Decimal("1")


def test_user_override_changes_utilisation(project):
    store = detailing.store_for(project)
    before = store.get("C1").utilisation
    store.set_bar("C1", 32, 75)  # much heavier than any design → utilisation drops
    after = store.get("C1").utilisation
    assert after < before
    assert store.get("C1").user_defined is True


def test_reset_restores_design(project):
    store = detailing.store_for(project)
    store.set_bar("C1", 32, 75)
    store.reset_all()
    led = store.ledger()
    assert led.delta_kg == 0.0
    assert led.user_defined_count == 0


def test_failing_count_and_ledger(project):
    led = detailing.ledger(project)
    assert led.total_kg > 0
    assert led.failing_count >= 0
    assert led.kg_per_m3 > 0


def test_minima_table_source():
    as_req, src = as_required_for("ABUTMENT_CAP", 600)
    assert as_req > 0
    assert "IRC" in src or "minima" in src


def test_default_items_cover_elements(project):
    elements = {i.element for i in default_items(project)}
    assert {"ABUTMENT_CAP", "DIRT_WALL", "ABUTMENT_SHAFT"} <= elements
    for item in default_items(project):
        assert item.as_required_mm2_per_m > 0
        assert item.source == "minima_table_v1"
