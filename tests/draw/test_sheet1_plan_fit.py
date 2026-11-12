"""SS3 §A1/§A6 — Sheet 1 plan scale honesty and presence gates.

These drive the *production* plan sheet (``bridgecad_draw.sheet1_plan``), not a
scaffold, because the caption lie this file exists to prevent lived in the
production path: the sheet used to fit itself to the box with an invented
denominator (``min(scale_h, scale_v) * 0.93``) and then print a constant
"1:100" beside it — a 24 m arch came out near 1:15 under a "1:100" title.

Every assertion here is measured from the generated DXF, so it cannot pass if
the printed scale and the drawn geometry disagree.
"""
from __future__ import annotations

import ezdxf
import pytest

from bridgecad_draw import sheet1_plan as S1
from bridgecad_draw.fit import LADDER

from . import contract

pytestmark = pytest.mark.draw

# The booklet type 010 shape: nine 30 m spans (270 m).
NSPAN, SPAN_M = 9, 30.0
TOTAL_M = NSPAN * SPAN_M


def _render(tmp_path, *, scale_denom=None, nspan=NSPAN, span_m=SPAN_M, **overrides):
    """Generate Sheet 1 from a blank model with *overrides*, return (doc, project)."""
    project = contract.make_project("blank", nspan=nspan, span_m=span_m, **overrides)
    out = tmp_path / "Sheet1_Plan.dxf"
    S1.generate(project, out, scale_denom=scale_denom)
    return ezdxf.readfile(str(out)), project


def _texts(doc) -> list[str]:
    out = []
    for e in doc.modelspace():
        if e.dxftype() == "TEXT":
            out.append(e.dxf.text)
        elif e.dxftype() == "MTEXT":
            out.append(e.text)
    return out


def _printed_denom(doc) -> int:
    """The denominator the sheet states on its own face."""
    import re

    for t in _texts(doc):
        m = re.search(r"SCALE 1:(\d+)", t)
        if m:
            return int(m.group(1))
    raise AssertionError(f"no 'SCALE 1:N' line on the sheet: {_texts(doc)[:20]}")


def _deck_extent(doc) -> float:
    """The deck outline's span along chainage, in paper mm.

    The outline is drawn as a closed LWPOLYLINE from ``hpos(0)`` to
    ``hpos(total_len)``, so its x-extent is ``total_len * mm_per_m`` exactly on
    an unsheared (skew 0) bridge.
    """
    extents = []
    for e in doc.modelspace():
        if e.dxftype() == "LWPOLYLINE" and e.dxf.layer == "STRUC-OUTLINE":
            xs = [p[0] for p in e.get_points("xy")]
            extents.append(max(xs) - min(xs))
    assert extents, "no STRUC-OUTLINE polyline — the plan did not draw a deck"
    return max(extents)


def _layers(doc) -> set[str]:
    return {e.dxf.layer for e in doc.modelspace()}


def test_printed_scale_is_a_ladder_rung(tmp_path):
    doc, _ = _render(tmp_path)
    denom = _printed_denom(doc)
    assert denom in LADDER, f"printed 1:{denom} is not a ladder rung"


def test_printed_scale_matches_the_geometry(tmp_path):
    """The deck is drawn at exactly 1000/denom mm per metre — no drift."""
    doc, _ = _render(tmp_path)
    denom = _printed_denom(doc)
    drawn_mm_per_m = _deck_extent(doc) / TOTAL_M
    assert drawn_mm_per_m == pytest.approx(1000.0 / denom, rel=1e-6), (
        f"deck drawn at {drawn_mm_per_m:.4f} mm/m but captioned 1:{denom}"
    )


def test_scale_denom_override_agrees_with_the_geometry(tmp_path):
    """``scale_denom`` is honoured and the printed caption follows the geometry."""
    doc, project = _render(tmp_path, scale_denom=50, nspan=1, span_m=12.0)
    denom = _printed_denom(doc)
    assert denom == 50, f"requested 1:50 but the sheet printed 1:{denom}"
    total = float(project.geometry_input.total_length_m)
    assert _deck_extent(doc) / total == pytest.approx(1000.0 / 50, rel=1e-6)


def test_text_clears_the_irc_floor(tmp_path):
    """Every glyph clears the hard IRC SP:55 floor (``MIN_TEXT_HEIGHT_MM``)."""
    from bridgecad_draw.primitives import MIN_TEXT_HEIGHT_MM as FLOOR

    doc, _ = _render(tmp_path)
    heights = [
        e.dxf.height
        for e in doc.modelspace()
        if e.dxftype() == "TEXT" and e.dxf.get("height")
    ]
    assert heights, "no text on the sheet"
    assert min(heights) >= FLOOR - 1e-9, f"text height {min(heights)} below IRC floor {FLOOR}"


def test_a_single_span_plan_draws_no_pier_caps(tmp_path):
    """No internal pier ⇒ no pier cap footprint."""
    doc, _ = _render(tmp_path, nspan=1, span_m=12.0)
    assert "SUB-PIER" not in _layers(doc), "a single-span bridge drew a pier cap"


def test_box_cell_draws_no_pier_caps_and_flags_b_b(tmp_path):
    """SS3 §A6 — a box cell is monolithic: no pier cap, and B-B is not applicable."""
    from bridgecad_core import types as T

    project = contract.make_project("blank", nspan=NSPAN, span_m=SPAN_M)
    project.superstructure.type = T.SuperstructureType.BOX_CELL_MULTI

    out = tmp_path / "box.dxf"
    S1.generate(project, out)
    doc = ezdxf.readfile(str(out))

    assert "SUB-PIER" not in _layers(doc), (
        "a box-cell superstructure drew a pier cap — SS3 §A6 gate is not wired"
    )
    assert any("B-B NOT APPLICABLE" in t for t in _texts(doc)), (
        "no 'SECTION B-B NOT APPLICABLE' note on a pierless plan"
    )


def test_bearing_symbols_follow_the_model(tmp_path):
    """The plan draws a bearing symbol only when the model declares a bearing.

    The blank fixture leaves ``bearings_joints.bearing_type`` unset (the model
    encodes "no bearing" as ``None``), so the default sheet must be symbol-free;
    declaring a bearing must then produce symbols — proving the absence is a
    gate and not a broken symbol routine.
    """
    from bridgecad_core import types as T

    doc, project = _render(tmp_path)
    assert "SUB-BEARING" not in _layers(doc), "bearingless model drew a bearing symbol"

    project.bearings_joints.bearing_type = T.BearingType.ELASTOMERIC_NEOPRENE
    out = tmp_path / "bearings.dxf"
    S1.generate(project, out)
    doc2 = ezdxf.readfile(str(out))
    assert "SUB-BEARING" in _layers(doc2), "a bearing model drew no bearing symbol"
