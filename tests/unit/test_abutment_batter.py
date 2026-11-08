"""Unit tests for the LISP abt1() battered side profile.

The riverside (face) and earthside (back, dirt-wall side) batters are
DIFFERENT parameters — the whole point of the abt1() profile.
"""

from __future__ import annotations

import pytest

from bridgecad_core.geometry.abutment_profiles import (
    GRAVITY,
    battered_side_outline,
    family_for,
)

STEM_H = 3.0


def _runs(pts):
    """(face_run, back_run) horizontal batter runs in metres."""
    face_run = pts[4][0] - pts[2][0]  # x5 - x3, gentle riverside face
    back_run = pts[12][0] - pts[10][0]  # x14 - x12, steep earthside face
    return face_run, back_run


def test_face_and_back_batters_differ():
    """Default 1:10 face vs 1:3 back — the back batter must be steeper."""
    prof = battered_side_outline(STEM_H)
    face_run, back_run = _runs(prof.points)
    assert face_run == pytest.approx(STEM_H / 10.0)
    assert back_run == pytest.approx(STEM_H / 3.0)
    assert back_run > face_run  # earthside steeper than riverside


def test_batter_is_parametric():
    """Changing the 1:n values changes the runs — nothing is hard-coded."""
    gentle = battered_side_outline(STEM_H, face_batter_1n=20, back_batter_1n=20)
    steep = battered_side_outline(STEM_H, face_batter_1n=5, back_batter_1n=5)
    f_g, b_g = _runs(gentle.points)
    f_s, b_s = _runs(steep.points)
    assert f_g < f_s and b_g < b_s
    # equal n → equal runs (symmetric batter allowed when user asks for it)
    assert f_g == pytest.approx(b_g) and f_s == pytest.approx(b_s)


def test_dirt_wall_on_earthside():
    """dirt_wall_x sits at −x (earthside) of the riverside face anchor x=0."""
    prof = battered_side_outline(STEM_H, dirt_w_m=0.3)
    assert prof.dirt_wall_x == -0.3
    xs = [p[0] for p in prof.points]
    assert min(xs) < prof.dirt_wall_x  # stem mass extends earthside of the wall


def test_vertical_datums():
    """foot_bot < stem_bot < cap_bot < cap_top < rtl, all from one ladder."""
    prof = battered_side_outline(STEM_H, foot_d_m=1.0, cap_d_m=0.6, above_m=0.25)
    assert prof.foot_bot_y == 0.0
    assert prof.stem_bot_y == 1.0
    assert prof.cap_bot_y == 1.0 + STEM_H
    assert prof.cap_top_y == 1.0 + STEM_H + 0.6
    assert prof.cap_top_y + 0.25 == prof.points[0][1]  # rtl


def test_mirror_for_a1_a2():
    """The profile is drawn once; A1/A2 mirror by negating x (sheet's job)."""
    prof = battered_side_outline(STEM_H)
    mirrored = [(-x, y) for x, y in prof.points]
    # mirrored dirt wall lands at +x — the opposite abutment's earthside
    assert -prof.dirt_wall_x == 0.3
    assert all(isinstance(x, float) for x, _ in mirrored)


def test_family_mapping():
    assert family_for("GRAVITY") == GRAVITY
    assert family_for("SEMI_GRAVITY") == GRAVITY
    assert family_for("CANTILEVER") == "cantilever"
