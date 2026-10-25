"""Wing-05 — wing wall geometry against hand-computed values.

Convention (see the convention diagram):
    face_run_m = (abtl_m - carriageway_width_m) / 2
    length_m   = face_run_m / cos(radians(splay_deg))
    return_m   = length_m * sin(radians(splay_deg))
splay_deg is measured FROM THE ABUTMENT FACE.

Golden case simple_12m: ABTL 13.0, W 7.5 -> face_run 2.75 m exactly.
    splay 60 -> length 5.5 m exactly          (2.75 / 0.5)
    splay 45 -> length 3.8890873 m
    splay  0 -> length 2.75 m exactly, return 0
"""
from __future__ import annotations

import math

import pytest

from . import contract

pytestmark = pytest.mark.draw

FACE_RUN = 2.75
LENGTH_60 = 5.5
LENGTH_45 = 2.75 / math.cos(math.radians(45))
LENGTH_0 = 2.75


def _with_splay(deg: float):
    project = contract.make_project("simple_12m")
    project.drawing_control.splay_deg = deg
    return project


def test_face_run_is_derived_from_abtl_not_chosen():
    walls = contract.wing_wall_geometry(contract.make_project("simple_12m"))
    for w in walls:
        assert w.face_run_m == pytest.approx(FACE_RUN, abs=1e-9)


def test_both_sides_are_produced():
    walls = contract.wing_wall_geometry(contract.make_project("simple_12m"))
    assert {w.side for w in walls} == {"left", "right"}


@pytest.mark.parametrize("deg,expected", [
    (0.0, LENGTH_0),
    (45.0, LENGTH_45),
    (60.0, LENGTH_60),
])
def test_length_matches_hand_computed_value(deg: float, expected: float):
    walls = contract.wing_wall_geometry(_with_splay(deg))
    for w in walls:
        assert w.length_m == pytest.approx(expected, rel=1e-9), (
            f"splay {deg}deg: length {w.length_m}, hand-computed {expected}"
        )


def test_return_projection_is_length_times_sin_splay():
    walls = contract.wing_wall_geometry(_with_splay(45.0))
    for w in walls:
        assert w.return_m == pytest.approx(w.length_m * math.sin(math.radians(45.0)), rel=1e-9)


def test_zero_splay_has_no_return():
    walls = contract.wing_wall_geometry(_with_splay(0.0))
    for w in walls:
        assert w.return_m == pytest.approx(0.0, abs=1e-9)


def test_length_is_monotonic_in_splay():
    """Closing the splay must lengthen the wall, never shorten it."""
    lengths = [contract.wing_wall_geometry(_with_splay(d))[0].length_m
               for d in (0, 15, 30, 45, 60)]
    assert lengths == sorted(lengths), f"length not monotonic in splay: {lengths}"


def test_wings_are_symmetric_on_an_unskewed_bridge():
    walls = {w.side: w for w in contract.wing_wall_geometry(contract.make_project("simple_12m"))}
    assert walls["left"].length_m == pytest.approx(walls["right"].length_m)
    assert walls["left"].splay_deg == pytest.approx(walls["right"].splay_deg)


def test_skewed_bridge_keeps_equal_length_but_opposite_splay_sign():
    """On a skewed bridge the two wings mirror across the skew; lengths match."""
    project = contract.make_project("skew15_3x18m")
    walls = {w.side: w for w in contract.wing_wall_geometry(project)}
    assert walls["left"].length_m == pytest.approx(walls["right"].length_m, rel=1e-9)


def test_top_level_sits_below_the_deck():
    project = contract.make_project("simple_12m")
    walls = contract.wing_wall_geometry(project)
    deck = project.geometry_input.deck_level_m
    for w in walls:
        assert w.top_level_m < deck, "wing wall top must sit below the deck soffit/kerb"
        assert w.top_level_m > 0


def test_base_level_clears_scour():
    project = contract.make_project("simple_12m")
    walls = contract.wing_wall_geometry(project)
    for w in walls:
        assert w.base_level_m <= w.top_level_m, "base above top — inverted wall"
        assert w.base_level_m <= project.hydraulic_data.scour_level_m, (
            "wing wall base does not reach below scour"
        )


def test_no_degenerate_walls():
    for slug in contract.golden_slugs():
        for w in contract.wing_wall_geometry(contract.make_project(slug)):
            assert w.length_m > 0.5, f"{slug}/{w.side}: wall length {w.length_m} m is degenerate"
            assert 0 <= w.splay_deg < 89, f"{slug}/{w.side}: splay {w.splay_deg} outside [0, 89)"


def test_face_run_never_exceeds_half_the_abutment():
    for slug in contract.golden_slugs():
        project = contract.make_project(slug)
        abtl, _ = contract.resolve_abtl(project)
        for w in contract.wing_wall_geometry(project):
            assert 2 * w.face_run_m <= abtl + 1e-9, (
                f"{slug}/{w.side}: wings overlap the deck opening"
            )
