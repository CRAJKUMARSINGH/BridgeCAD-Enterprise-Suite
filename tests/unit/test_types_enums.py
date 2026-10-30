"""Stable enum contracts in ``bridgecad_core.types``."""

from __future__ import annotations

from bridgecad_core.types import (
    ENUM_REGISTRY,
    BridgeCategory,
    ConcreteGrade,
    DrawingScale,
    FoundationType,
    SheetSize,
    SteelGrade,
)

UNIQUE_ENUMS = [ConcreteGrade, SteelGrade, FoundationType, SheetSize, BridgeCategory, DrawingScale]


def test_concrete_grade_value_round_trips():
    assert ConcreteGrade.M30.value == "M30"
    assert ConcreteGrade("M30") is ConcreteGrade.M30


def test_steel_grade_value_round_trips():
    assert SteelGrade.Fe500D.value == "Fe500D"
    assert SteelGrade("Fe500D") is SteelGrade.Fe500D


def test_foundation_type_value_round_trips():
    assert FoundationType.PILE.value == "PILE_FOUNDATION"
    assert FoundationType("PILE_FOUNDATION") is FoundationType.PILE


def test_bridge_category_minor_bridge_membership():
    assert BridgeCategory.MINOR_BRIDGE in set(BridgeCategory)


def test_enums_are_non_empty_and_have_unique_members():
    for enum_cls in UNIQUE_ENUMS:
        values = [m.value for m in enum_cls]
        assert values
        assert len(values) == len(set(values))


def test_drawing_scale_members_are_their_denominators():
    assert DrawingScale.S100.value == 100
    assert int(DrawingScale.S100) == 100
    assert int(DrawingScale.S50) == 50
    assert int(DrawingScale.S1000) == 1000


def test_sheet_size_a1_has_iso_value():
    assert SheetSize.A1.value == "ISO_A1_594x841"


def test_labeled_enum_exposes_human_label():
    assert ConcreteGrade.M30.label == "M30"
    assert FoundationType.PILE.label == "Pile"


def test_enum_registry_contains_the_stable_enums():
    for enum_cls in UNIQUE_ENUMS:
        assert ENUM_REGISTRY[enum_cls.__name__] is enum_cls
