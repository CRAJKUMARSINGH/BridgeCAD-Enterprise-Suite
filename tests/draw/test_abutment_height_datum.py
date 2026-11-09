"""``abutment_height_m`` is the TOTAL height, GL to deck soffit — pin the datum.

The field is documented as "Abutment height (GL to deck soffit), m", but three
views disagreed about it and the drawings drifted a cap depth against each other:

    Sheet 5, transverse   treated it as the SHAFT height and stacked the cap on
                          top, so the abutment (and the dirt-wall / approach-slab
                          / wearing-coat stack above its rear ledge) sat one cap
                          depth too high.
    Sheet 5, longitudinal already treated it as the TOTAL (shaft = total − cap).
    Sheet 8               added bearing + pedestal + cap to the shaft, drawing
                          the shaft one cap depth too tall (the "Venice C1"
                          convention).

These tests read the built DXF, so they fail on either regression instead of
trusting a source comment.  Sheet 5 and Sheet 8 are the build-path modules
(``bridgecad_draw.booklet`` imports them directly), not the ``sheets/`` copies.
"""
from __future__ import annotations

import ezdxf
import pytest

from . import contract

pytestmark = pytest.mark.draw

FIXTURE = "tests/e2e/fixtures/simple_12m.json"


def _project():
    """The canonical 1x12 m minor-bridge fixture, as the sheets consume it."""
    return contract._build_from_fixture(contract._fixture_data(FIXTURE))


def _polylines(doc, layer: str) -> list[list[tuple[float, float]]]:
    out = []
    for e in doc.modelspace():
        if e.dxftype() == "LWPOLYLINE" and e.dxf.get("layer") == layer:
            out.append([(float(x), float(y)) for x, y in e.get_points("xy")])
    return out


def _lines(doc, layer: str) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    out = []
    for e in doc.modelspace():
        if e.dxftype() == "LINE" and e.dxf.get("layer") == layer:
            s = (float(e.dxf.start.x), float(e.dxf.start.y))
            t = (float(e.dxf.end.x), float(e.dxf.end.y))
            out.append((s, t))
    return out


def _horizontal(
    lines: list[tuple[tuple[float, float], tuple[float, float]]]
) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    return [(s, t) for s, t in lines if abs(s[1] - t[1]) < 1e-6]


def test_sheet5_both_views_span_one_abutment_height(tmp_path):
    """Sheet 5's transverse and longitudinal views must agree, and agree with
    ``abutment_height_m`` as the TOTAL (shaft + cap) height.

    The views sit in the upper (transverse) and lower (longitudinal) halves of
    the sheet; nothing else on ``SUB-ABUT`` shares them (the longitudinal return
    wall is a separate ``SUB-ABUT`` ring in the lower half, but above the shaft).
    """
    from bridgecad_draw import sheet5_pier_abutment_details as sheet5

    project = _project()
    sub = project.substructure
    abt_h = float(sub.abutment_height_m)
    abt_len = float(sub.abutment_length_m)

    out = tmp_path / "s5.dxf"
    sheet5.generate(project, out)
    doc = ezdxf.readfile(str(out))

    # The transverse cap-top is drawn as the dashed retained-fill line on the
    # rear of the cap — its run is the full ABTL, which also gives the sheet's
    # mm-per-metre scale without hard-coding the module's layout constants.
    cap_lines = _horizontal(_lines(doc, "ABUT-PROF"))
    assert len(cap_lines) == 1, f"expected one cap-top line on ABUT-PROF, got {len(cap_lines)}"
    (x0, cap_top_t), (x1, _) = cap_lines[0]
    sc = abs(x1 - x0) / abt_len

    # Transverse: lowest SUB-ABUT point is the shaft base.
    trans = [p for p in _polylines(doc, "SUB-ABUT") if min(y for _, y in p) > 200.0]
    assert trans, "no transverse SUB-ABUT geometry — layout moved"
    shaft_base_t = min(y for p in trans for _, y in p)
    total_t = cap_top_t - shaft_base_t

    # Longitudinal: the cap/dirt-wall construction joint is the horizontal
    # SUB-DIRT-WALL line at the cap top; the shaft base is the lowest SUB-ABUT
    # point below the transverse view.
    cj = _horizontal(_lines(doc, "SUB-DIRT-WALL"))
    assert cj, "no dirt-wall construction joint on SUB-DIRT-WALL"
    cap_top_l = cj[0][0][1]
    longi = [p for p in _polylines(doc, "SUB-ABUT") if max(y for _, y in p) < 200.0]
    assert longi, "no longitudinal SUB-ABUT geometry — layout moved"
    shaft_base_l = min(y for p in longi for _, y in p)
    total_l = cap_top_l - shaft_base_l

    assert total_t == pytest.approx(abt_h * sc, rel=1e-6), (
        f"transverse abutment is {total_t / sc:.3f} m tall, expected the TOTAL "
        f"{abt_h:.3f} m — the cap was stacked on a full-height shaft again"
    )
    assert total_l == pytest.approx(abt_h * sc, rel=1e-6), (
        f"longitudinal abutment is {total_l / sc:.3f} m tall, expected {abt_h:.3f} m"
    )
    assert total_t == pytest.approx(total_l, rel=1e-6), "the two views disagree"


def test_sheet8_abutment_spans_one_total_height(tmp_path):
    """Sheet 8's shaft base must sit one ``abutment_height_m`` below the bearing
    seat — the cap, pedestal and bearing live *inside* that span, not on top.

    Measured off the drawing: from the bearing seat (top of the ``SUB-BEARING``
    pads = deck soffit) down to the shaft base (lowest ``SUB-ABUT`` point).
    """
    from bridgecad_draw import sheet8_side_elevations as sheet8

    project = _project()
    sub = project.substructure
    fd = project.foundation_details
    abt_h = float(sub.abutment_height_m)
    pile_len = float(fd.pile_length_m)

    out = tmp_path / "s8.dxf"
    sheet8.generate(project, out)
    doc = ezdxf.readfile(str(out))

    # Sheet 8 scales adaptively, so resolve mm-per-metre from the pile shafts:
    # each FOUND-PILE vertical is exactly one pile length long.
    pile_shafts = [
        (s, t)
        for s, t in _lines(doc, "FOUND-PILE")
        if abs(s[0] - t[0]) < 1e-6 and abs(s[1] - t[1]) > 1.0
    ]
    assert pile_shafts, "no pile shafts on Sheet 8 — cannot resolve the view scale"
    sc = max(abs(t[1] - s[1]) for s, t in pile_shafts) / pile_len

    abt_base_y = max(y for p in _polylines(doc, "SUB-ABUT") for _, y in p)
    bearing_seat_y = min(y for p in _polylines(doc, "SUB-BEARING") for _, y in p)
    total = (abt_base_y - bearing_seat_y) / sc

    assert total == pytest.approx(abt_h, abs=0.02), (
        f"Sheet 8 abutment spans {total:.3f} m from bearing seat to shaft base, "
        f"expected the TOTAL {abt_h:.3f} m — the bearing/pedestal/cap were added "
        "on top of a full-height shaft again"
    )
