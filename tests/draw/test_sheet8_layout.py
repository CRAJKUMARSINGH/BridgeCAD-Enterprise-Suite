"""Sheet 5/8 guards — the checks table clears the views, and Sheet 8's printed
scale tells the truth (SS3 §A1/§A6)."""

from __future__ import annotations

import json
from pathlib import Path

import ezdxf
import pytest

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "tests" / "e2e" / "fixtures" / "simple_12m.json"

pytestmark = pytest.mark.draw


@pytest.fixture(scope="module")
def project():
    from . import contract

    return contract._build_from_fixture(
        contract._fixture_data("tests/e2e/fixtures/simple_12m.json")
    )


def test_sheet8_checks_table_clears_views():
    from bridgecad_draw import sheet8_side_elevations as s8

    assert s8._CHECKS_Y + s8._CHECKS_ROWS_H < s8._VIEW_Y0


def test_sheet5_checks_table_clears_pier_dims(project):
    """Table top (origin y=80 + 7 mm/row + header) must stay below the pier
    elevation dimension band (~237 mm)."""
    from bridgecad_draw.checks_table import build_abutment_rows

    n = len(build_abutment_rows(project))
    table_top = 80.0 + 7.0 * (n + 1)
    assert table_top < 237.0, f"checks table top {table_top:.0f} collides with pier dims"


# ── SS3 §A1/§A6 — Sheet 8 printed-scale honesty and presence gates ───────────
def _s8_render(tmp_path, **overrides):
    from bridgecad_draw import sheet8_side_elevations as s8

    from . import contract

    proj = contract.make_project("blank", **overrides)
    out = tmp_path / "Sheet8.dxf"
    s8.generate(proj, out)
    return ezdxf.readfile(str(out)), proj


def _s8_overall_w(proj) -> float:
    """The end-face deck width, spelled the way the sheet spells it."""
    gi = proj.geometry_input
    return (
        float(gi.carriageway_width_m)
        + float(gi.kerb_width_left_m or 0.25)
        + float(gi.kerb_width_right_m or 0.25)
        + float(gi.footpath_left_m or 0.0)
        + float(gi.footpath_right_m or 0.0)
        + float(gi.crash_barrier_width_left_m or 0.0)
        + float(gi.crash_barrier_width_right_m or 0.0)
    )


def _s8_printed_denom(doc) -> int:
    import re

    for e in doc.modelspace():
        if e.dxftype() == "TEXT":
            m = re.search(r"SCALE 1:(\d+)", e.dxf.text)
            if m:
                return int(m.group(1))
    raise AssertionError("no 'SCALE 1:N' line on Sheet 8")


def _s8_deck_widths(doc) -> list[float]:
    """Paper widths of the SUPER-DECK rectangles (one per transverse view)."""
    widths = []
    for e in doc.modelspace():
        if e.dxftype() == "LWPOLYLINE" and e.dxf.layer == "SUPER-DECK":
            xs = [p[0] for p in e.get_points("xy")]
            widths.append(max(xs) - min(xs))
    return widths


def test_sheet8_printed_scale_is_a_ladder_rung(tmp_path):
    from bridgecad_draw.fit import LADDER

    doc, _ = _s8_render(tmp_path)
    denom = _s8_printed_denom(doc)
    assert denom in LADDER, f"printed 1:{denom} is not a ladder rung"


def test_sheet8_printed_scale_matches_the_geometry(tmp_path):
    """The end-face deck is drawn at exactly 1000/denom mm per metre."""
    doc, proj = _s8_render(tmp_path)
    denom = _s8_printed_denom(doc)
    widths = _s8_deck_widths(doc)
    assert widths, "no SUPER-DECK rectangle — the end-face did not draw a deck"
    drawn_mm_per_m = max(widths) / _s8_overall_w(proj)
    assert drawn_mm_per_m == pytest.approx(1000.0 / denom, rel=1e-6), (
        f"deck drawn at {drawn_mm_per_m:.4f} mm/m but captioned 1:{denom}"
    )


def test_sheet8_text_clears_the_legibility_floor(tmp_path):
    from bridgecad_draw.fit import MIN_TEXT_MM
    from bridgecad_draw.primitives import MIN_TEXT_HEIGHT_MM as FLOOR

    doc, _ = _s8_render(tmp_path)
    heights = [
        e.dxf.height
        for e in doc.modelspace()
        if e.dxftype() == "TEXT" and e.dxf.get("height")
    ]
    assert heights, "no text on Sheet 8"
    assert min(heights) >= FLOOR - 1e-9, f"text height {min(heights)} below IRC floor {FLOOR}"
    assert max(heights) >= MIN_TEXT_MM - 1e-9, (
        f"the sheet's largest text {max(heights)} is under the {MIN_TEXT_MM} target"
    )


def test_sheet8_raft_foundation_draws_no_piles(tmp_path):
    """SS3 §A4 — piles are drawn only for a PILE foundation."""
    from bridgecad_core import types as T

    doc, proj = _s8_render(tmp_path)
    assert proj.foundation_details.type == T.FoundationType.PILE, "fixture premise"
    assert any(e.dxf.layer == "FOUND-PILE" for e in doc.modelspace()), (
        "a pile job drew no piles — cannot prove the gate"
    )

    proj.foundation_details.type = T.FoundationType.RAFT
    out = tmp_path / "raft.dxf"
    from bridgecad_draw import sheet8_side_elevations as s8

    s8.generate(proj, out)
    doc2 = ezdxf.readfile(str(out))
    assert not [e for e in doc2.modelspace() if e.dxf.layer == "FOUND-PILE"], (
        "a raft foundation drew a pile group — SS3 §A4 gate is not wired"
    )
