"""The abutment is two battered shapes, not one rectangle.

The original LISP draws the abutment as a 14-vertex battered polygon — ``abt1()``
for A1 (the AL* parameter family) and its mirror for A2 (AR*). Sheet 5 panel C
used to draw a single flat rectangle the full ABTL width, which is not the shape
the structure has.

This reads the built DXF, so it fails if the rectangle comes back, if only one
profile is emitted, or if the profile loses its batter (footing no wider than the
cap). It pins the drawn shape, not a source comment.
"""
from __future__ import annotations

import pytest

from . import contract, dxf_assert

pytestmark = pytest.mark.draw

SHEET = "sheet5_pier_abutment_details"
PROFILE_LAYER = "ABUT-PROF"
MM_PER_M = 1000.0  # the Canvas draws the sheet at 1:1 in mm

#: The LISP abt1() polygon has fourteen vertices; a rectangle has four.
ABT1_VERTICES = 14


def _polys(doc, layer: str) -> list[list[tuple[float, float]]]:
    """Every polyline on *layer*, as [(x, y), ...] with the closing vertex kept."""
    out = []
    for e in dxf_assert.entities(doc, layer=layer):
        if e.dxftype() == "LWPOLYLINE":
            out.append([(float(x), float(y)) for x, y in e.get_points("xy")])
    return out


def _lines(doc, layer: str) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """Every LINE on *layer*, as ((x0, y0), (x1, y1))."""
    out = []
    for e in dxf_assert.entities(doc, layer=layer):
        if e.dxftype() == "LINE":
            s = (float(e.dxf.start.x), float(e.dxf.start.y))
            t = (float(e.dxf.end.x), float(e.dxf.end.y))
            out.append((s, t))
    return out


def _open_ring(pts: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Drop the duplicated closing vertex a closed polyline carries."""
    if len(pts) > 1 and pts[0] == pts[-1]:
        return pts[:-1]
    return pts


def _span_at(pts: list[tuple[float, float]]) -> dict[float, float]:
    """Horizontal span of the vertices at each distinct y level."""
    levels: dict[float, list[float]] = {}
    for x, y in pts:
        levels.setdefault(round(y, 6), []).append(x)
    return {y: max(xs) - min(xs) for y, xs in levels.items()}


@pytest.fixture()
def sheet5():
    project = contract.make_project("simple_12m")
    return project, contract.build_sheet(project, SHEET)


def test_profile_layer_is_registered():
    assert PROFILE_LAYER in contract.layer_registry(), (
        f"{PROFILE_LAYER} is not in the layer registry — the audit will reject it"
    )


def test_two_battered_profiles_are_drawn(sheet5):
    """A1 and A2, both present, both the 14-vertex LISP polygon."""
    _, doc = sheet5
    profiles = _polys(doc, PROFILE_LAYER)
    assert len(profiles) == 2, f"expected A1 and A2 profiles, got {len(profiles)}"
    for pts in profiles:
        ring = _open_ring(pts)
        assert len(ring) == ABT1_VERTICES, (
            f"abt1() has {ABT1_VERTICES} vertices; drawn poly has {len(ring)} — "
            "the flat rectangle is back"
        )


def test_profiles_are_battered_not_rectangular(sheet5):
    """The footing must be wider than the cap, or there is no batter.

    A rectangle's top and bottom runs are equal; a battered profile's top run
    (the DWTH-thin cap) is much narrower than its footing.
    """
    _, doc = sheet5
    for pts in _polys(doc, PROFILE_LAYER):
        spans = _span_at(_open_ring(pts))
        assert len(spans) > 2, "profile has no batter — it is axis-aligned"
        top = spans[max(spans)]      # highest y — the cap / dirt wall
        bottom = spans[min(spans)]   # lowest y — the footing toe
        assert top < bottom, (
            f"top run {top:.1f} mm is not narrower than the footing {bottom:.1f} mm "
            "— no toe/footing batter"
        )


def test_a1_is_left_of_a2(sheet5):
    """A1 (AL*) anchors at the left end of the face, A2 (AR*) at the right."""
    _, doc = sheet5
    a1, a2 = sorted(_polys(doc, PROFILE_LAYER), key=lambda p: min(x for x, _ in p))
    assert max(x for x, _ in a1) < min(x for x, _ in a2), "A1 and A2 overlap"


def test_no_flat_abutment_rectangle_remains(sheet5):
    """No SUB-ABUT polyline may span the abutment face — that is the old block.

    The return-wall stubs and the wing walls are short; only the removed flat
    rectangle was as wide as the ABTL face.
    """
    project, doc = sheet5
    abtl_m, _ = contract.resolve_abtl(project)
    face_mm = abtl_m * MM_PER_M
    for pts in _polys(doc, "SUB-ABUT"):
        xs = [x for x, _ in pts]
        extent = max(xs) - min(xs)
        assert extent < face_mm * 0.9, (
            f"a SUB-ABUT polyline spans {extent:.1f} mm of the {face_mm:.1f} mm "
            "abutment face — the flat rectangle is back"
        )


def test_profile_labels_reach_the_sheet(sheet5):
    _, doc = sheet5
    blob = " ".join(dxf_assert.text_of(doc)).upper()
    assert "BATTERED PROFILE" in blob
    assert "ABUTMENT A1" in blob and "ABUTMENT A2" in blob
    assert "DWTH 0.30" in blob, "the dirt-wall thickness must be stated on the profile"


#: abt1() draws four internal lines per profile: the cap soffit, the toe/footing
#: top, the back batter up to road level and the wall top across to the outer
#: face. Panel C holds two profiles.
ABT1_LINES_PER_PROFILE = 4
ABT1_LINES_TOTAL = ABT1_LINES_PER_PROFILE * 2


def test_abt1_outlines_the_dirt_wall(sheet5):
    """Panel C must draw abt1()'s four internal lines per profile.

    Defect report: the dirt wall read as a taller abutment because the elevation
    drew only the fill polygon plus two construction lines — the thin DWTH wall
    was never outlined. The original abt1() (enhanced_lisp_functions.py) also
    draws ``(x12, albbl)→(x12, RTL)`` and ``(x12, RTL)→(x14, RTL)``; the last
    closes the wall off from the fill so it reads as a wall.
    """
    _, doc = sheet5
    lines = _lines(doc, PROFILE_LAYER)
    assert len(lines) == ABT1_LINES_TOTAL, (
        f"abt1() emits {ABT1_LINES_PER_PROFILE} internal lines per profile; "
        f"panel C needs {ABT1_LINES_TOTAL}, got {len(lines)} — the dirt wall is "
        "no longer outlined"
    )

    for pts in _polys(doc, PROFILE_LAYER):
        ring = _open_ring(pts)
        rtl = max(y for _, y in ring)
        lo, hi = min(x for x, _ in ring) - 1.0, max(x for x, _ in ring) + 1.0
        mine = [(a, b) for a, b in lines if lo <= a[0] <= hi and lo <= b[0] <= hi]
        assert len(mine) == ABT1_LINES_PER_PROFILE, (
            f"this profile carries {len(mine)} of abt1()'s "
            f"{ABT1_LINES_PER_PROFILE} internal lines"
        )
        tops = [
            (a, b)
            for a, b in mine
            if abs(a[1] - rtl) < 1e-6 and abs(b[1] - rtl) < 1e-6
        ]
        assert len(tops) == 1, (
            "the dirt-wall top line (x12, RTL)→(x14, RTL) is missing — the DWTH "
            "wall merges into the abutment fill"
        )
