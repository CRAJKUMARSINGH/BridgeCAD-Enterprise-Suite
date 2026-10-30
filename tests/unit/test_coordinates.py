"""Pure-function tests for ``bridgecad_core.geometry.coordinates``."""

from __future__ import annotations

import math

import pytest

from bridgecad_core.geometry import coordinates as coords


def test_sheet_origins_has_one_entry_per_sheet_id():
    origins = coords.sheet_origins([12.0], 0.0)
    assert set(origins) == set(coords.SheetId)
    assert len(origins) == len(list(coords.SheetId))
    assert len(coords.sheet_origins(iter([12.0, 15.0]), 0.0)) == len(list(coords.SheetId))


def test_chainage_zero_sheets_anchor_at_origin():
    origins = coords.sheet_origins([12.0, 15.0], 0.0)
    for sheet_id in (coords.SheetId.PLAN, coords.SheetId.LONG_SECTION, coords.SheetId.BOQ, coords.SheetId.BEARINGS_JOINTS):
        assert (origins[sheet_id].x_m, origins[sheet_id].y_m, origins[sheet_id].rotation_deg) == (
            0.0,
            0.0,
            0.0,
        )


def test_foundation_and_pier_abutment_origins():
    origins = coords.sheet_origins([12.0, 15.0], 0.0)
    assert origins[coords.SheetId.FOUNDATION].x_m == pytest.approx(12.0)
    # Pier/abutment geometry is shifted 5 m below ground.
    assert origins[coords.SheetId.PIER_ABUTMENT].y_m == pytest.approx(-5.0)


def test_cross_section_origin_is_mid_longest_span_with_skew():
    # Longest span is the second (15 m): mid at 12 + 15/2 = 19.5.
    origin = coords.sheet_origins([12.0, 15.0], 20.0)[coords.SheetId.CROSS_SECTION]
    assert origin.x_m == pytest.approx(19.5)
    assert origin.rotation_deg == pytest.approx(20.0)
    # Longest span selection holds for more spans too: [10, 18, 9] -> mid 19.0.
    assert coords.sheet_origins([10.0, 18.0, 9.0], 5.0)[coords.SheetId.CROSS_SECTION].x_m == pytest.approx(19.0)


@pytest.mark.parametrize("skew", [0.0, 30.0])
@pytest.mark.parametrize("point", [(3.5, -2.0), (-7.25, 4.75)])
def test_round_trip_world_sheet_identity(skew, point):
    origin = coords.sheet_origins([12.0, 15.0], skew)[coords.SheetId.CROSS_SECTION]
    back = coords.to_world_coords(origin, coords.to_sheet_coords(origin, point))
    assert back[0] == pytest.approx(point[0], abs=coords.ROUND_TRIP_TOL_M)
    assert back[1] == pytest.approx(point[1], abs=coords.ROUND_TRIP_TOL_M)


def test_to_dxf_mm_multiplies_metres_by_1000():
    assert coords.MM_PER_M == 1000.0
    assert coords.to_dxf_mm((1.0, 2.0)) == pytest.approx((1000.0, 2000.0))
    assert coords.to_dxf_mm((-0.5, 12.345)) == pytest.approx((-500.0, 12345.0))


def test_origin_rotate_quarter_turns():
    expected = {0.0: (1.0, 0.0), 90.0: (0.0, 1.0), 180.0: (-1.0, 0.0), 360.0: (1.0, 0.0)}
    for angle_deg, exp in expected.items():
        origin = coords.SheetOrigin(coords.SheetId.CROSS_SECTION, 0.0, 0.0, angle_deg)
        assert origin.rotate((1.0, 0.0)) == pytest.approx(exp)


def test_skew_rotation_is_deterministic():
    a = coords.sheet_origins([12.0], 30.0)[coords.SheetId.CROSS_SECTION]
    b = coords.sheet_origins([12.0], 30.0)[coords.SheetId.CROSS_SECTION]
    assert a.rotate((1.0, 0.0)) == pytest.approx(b.rotate((1.0, 0.0)))
    assert a.rotate((1.0, 0.0)) == pytest.approx(
        (math.cos(math.radians(30)), math.sin(math.radians(30)))
    )


def test_translation_is_applied_before_rotation():
    origin = coords.sheet_origins([12.0, 15.0], 90.0)[coords.SheetId.CROSS_SECTION]
    # Point below the anchor by 1 m: shifted to (0, -1) then rotated 90 CCW.
    assert coords.to_sheet_coords(origin, (19.5, -1.0)) == pytest.approx((1.0, 0.0))


def test_sheet_origins_rejects_empty_or_non_positive():
    for spans in ([], [0.0], [-5.0], [12.0, 0.0]):
        with pytest.raises(ValueError):
            coords.sheet_origins(spans, 0.0)
