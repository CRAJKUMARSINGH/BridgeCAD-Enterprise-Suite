"""Abutment elevation shape families — CANTILEVER and GRAVITY must differ."""

from __future__ import annotations

import sys
from pathlib import Path

# bootstrap so pytest can find the package without install
_SUITE = Path(__file__).parents[2]
for _pkg in ["bridgecad-core"]:
    _p = _SUITE / "packages" / _pkg
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from bridgecad_core.geometry.abutment_profiles import (
    BATTERED,
    CANTILEVER,
    GRAVITY,
    elevation_outline,
    family_for,
)


def test_gravity_maps_to_gravity_family():
    assert family_for("GRAVITY") == GRAVITY
    assert family_for("SEMI_GRAVITY") == GRAVITY
    assert family_for("GRAVITY_STONE_MASONRY") == GRAVITY


def test_cantilever_family_includes_counterfort_and_buttress():
    for name in ("CANTILEVER", "COUNTERFORT", "BUTTRESSED", "STUB_ABUTMENT"):
        assert family_for(name) == CANTILEVER, name


def test_unknown_type_is_battered_and_never_crashes():
    assert family_for("SOMETHING_NEW") == BATTERED
    assert family_for(None) == BATTERED


def test_gravity_is_a_trapezoid():
    pts = elevation_outline(GRAVITY)
    assert len(pts) == 4
    top_xs = [x for x, y in pts if y == 1.0]
    assert top_xs[0] > 0.0 and top_xs[1] < 1.0


def test_cantilever_is_an_inverted_t():
    pts = elevation_outline(CANTILEVER)
    assert len(pts) == 8
    xs = [x for x, _ in pts]
    assert min(xs) == 0.0 and max(xs) == 1.0


def test_shapes_are_materially_different():
    assert elevation_outline(GRAVITY) != elevation_outline(CANTILEVER)
