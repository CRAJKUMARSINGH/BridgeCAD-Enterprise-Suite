"""tests/core/test_superstructure_profiles.py — geometry tests for the
accurate component profiles (slab / T-beam / PSC I-girder).

    python -m pytest tests/core -q
"""
from __future__ import annotations

import math

from bridgecad_core.geometry.superstructure_profiles import (
    bearing_positions,
    derive_defaults,
    diaphragm_stations,
    igirder_profile,
    section_profile,
    skew_adjusted_support_chainage,
    solid_slab_profile,
    tbeam_profile,
)


def _polygon_ok(pts, depth_mm, tol=1e-6):
    assert len(pts) >= 4
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    assert min(xs) < max(xs)
    # Y positive down: max Y == section depth
    assert abs(max(ys) - depth_mm) < 1.0, (max(ys), depth_mm)
    assert min(ys) >= -tol


def test_slab_thickness_derives_from_span():
    d = derive_defaults("SLAB", 12.0)
    assert d.deck_slab_thickness_mm == 480  # 12000/25 = 480
    assert d.girder_depth_mm is None        # no girders on a slab bridge


def test_tbeam_defaults():
    d = derive_defaults("T_BEAM", 15.0, carriageway_width_m=7.5)
    assert d.girder_depth_mm == 1250        # 15000/12 = 1250
    assert d.girder_spacing_m == 2.0
    assert d.girders_per_deck == 4          # 7.5/2 -> 4 (>=2, +1 rule)
    assert d.stem_width_mm == 250
    pts = tbeam_profile(d)
    _polygon_ok(pts, d.girder_depth_mm)  # local origin at slab top; stem soffit at girder depth
    # stem symmetric
    xs = [p[0] for p in pts]
    assert abs(max(xs) - min(xs)) > 0       # flange wider than stem


def test_igirder_defaults_and_profile():
    d = derive_defaults("PSC_I_GIRDER", 30.0, carriageway_width_m=7.5)
    assert d.girder_depth_mm == 1900        # 30000/16 = 1875, rounded to 50 mm
    pts = igirder_profile(d)
    _polygon_ok(pts, d.girder_depth_mm)
    # bottom flange narrower than top flange
    xs = [p[0] for p in pts]
    half_tf = d.top_flange_width_mm / 2.0
    half_bf = d.bottom_flange_width_mm / 2.0
    assert max(xs) - min(xs) >= 2 * half_tf - 1e-6
    # bottom flange points present
    assert any(abs(abs(x) - half_bf) < 1e-6 for x in xs)


def test_section_profile_dispatch():
    assert section_profile(derive_defaults("SLAB", 10.0)) == solid_slab_profile(
        derive_defaults("SLAB", 10.0))
    assert len(section_profile(derive_defaults("T_BEAM", 15.0))) > 0
    assert len(section_profile(derive_defaults("PSC", 30.0))) > 0


def test_diaphragm_stations_end_and_intermediate():
    st = diaphragm_stations(30.0, max_spacing_m=6.0)
    assert st[0] == 0.0 and st[-1] == 30.0  # end diaphragms over bearings
    steps = [b - a for a, b in zip(st, st[1:])]
    assert all(s <= 6.0 + 1e-9 for s in steps)


def test_bearing_positions_symmetric_one_per_girder():
    b = bearing_positions(4, 2.0)
    assert len(b) == 4
    assert abs(sum(b)) < 1e-9               # symmetric about CL
    assert b[1] - b[0] == 2.0


def test_skew_support_shift():
    up, down = skew_adjusted_support_chainage(100.0, skew_deg=30.0, deck_width_m=10.0)
    shift = 5.0 * math.tan(math.radians(30.0))
    assert abs((down - up) - 2 * shift) < 1e-9
    assert abs(up + down - 200.0) < 1e-9