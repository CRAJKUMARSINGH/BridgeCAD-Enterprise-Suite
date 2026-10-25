"""Wing-16 — sheet 2 against hand-computed positions.

Every expected value here is arithmetic done on paper first, then typed. If the
implementation and this file agree, they agree on the formula, not on each other.
"""
from __future__ import annotations

import pytest

from . import contract, dxf_assert

pytestmark = pytest.mark.draw

SHEET = "sheet2_long_section"
SCALE = 100          # declared in coordinates.FRAMES — asserted, not assumed
LEVEL_DATUM = 90.0   # declared in coordinates.FRAMES
PITCH = 5.0

from bridgecad_draw.coordinates import check_declared, m, model_text_height_mm, to_model_space  # noqa: E402


@pytest.fixture
def project():
    return contract.make_project("continuous_3x12m")   # 36 m, piers at 12 and 24


@pytest.fixture
def doc(project):
    return contract.build_sheet(project, SHEET)


def _X(ch): return to_model_space(SHEET, ch, 0.0)[0]
def _Y(lv): return to_model_space(SHEET, 0.0, lv)[1]


def test_declared_scale_and_datum_are_what_the_sheet_assumes():
    """The sheet's arithmetic assumes 1:100 from a 90 m datum. Pin both."""
    frame = check_declared(SHEET)
    assert frame.plot_scale == SCALE
    assert frame.origin_level_m == LEVEL_DATUM


def test_origin_is_chainage_zero(doc):
    assert _X(0.0) == 0.0


def test_pier_centrelines_are_at_exactly_the_pier_positions(doc, project):
    """nspan - 1 centrelines, at the model positions, not near them."""
    centrelines = [e for e in dxf_assert.entities(doc, layer="CL") if e.dxftype() == "LINE"]
    assert len(centrelines) == len(project.geometry.pier_positions()) == 2

    xs = sorted(e.dxf.start.x for e in centrelines)
    assert xs[0] == pytest.approx(_X(12.0), abs=1e-6)
    assert xs[1] == pytest.approx(_X(24.0), abs=1e-6)


def test_levels_are_read_from_the_project_not_restated(doc, project):
    """The whole point of the sheet taking a project. Move the level, move the line."""
    hfl_y = _Y(project.levels.hfl_m)
    on_hfl = [e for e in dxf_assert.entities(doc, layer="GRID")
              if e.dxftype() == "LINE" and abs(e.dxf.start.y - hfl_y) < 1e-6]
    assert on_hfl, f"no GRID line at the project HFL {project.levels.hfl_m}"


def test_levels_are_ordered_high_to_low(doc, project):
    ys = {k: _Y(getattr(project.levels, k)) for k in
          ("deck_level_m", "hfl_m", "lwl_m", "founding_level_m")}
    assert ys["deck_level_m"] > ys["hfl_m"] > ys["lwl_m"] > ys["founding_level_m"]


def test_chainage_tick_count_and_pitch(doc, project):
    ticks = [e for e in dxf_assert.entities(doc, layer="GRID") if e.dxftype() == "LINE"]
    total = project.geometry.total_length_m
    expected = int(total // PITCH) + 1
    assert expected == 8, "hand count: 0,5,...,35 is 8 ticks"

    xs = sorted({round(e.dxf.start.x, 6) for e in ticks if e.dxf.start.x == e.dxf.end.x})
    assert len(xs) >= expected
    pitches = {round(b - a, 6) for a, b in zip(xs, xs[1:])}
    assert pitches == {m(PITCH)}, f"tick pitch {pitches} is not a uniform {m(PITCH)} mm"


def test_level_labels_use_three_decimal_places(doc):
    """"104.5" on a section is ambiguous. The GAD sheets use 3 dp."""
    blob = " ".join(dxf_assert.text_of(doc))
    assert "HFL 104.500" in blob
    assert "LWL 99.200" in blob
    assert "HFL 104.5 " not in blob


def test_text_height_plots_to_the_paper_floor(doc):
    """2.5 mm on paper at 1:100 is 250 mm of model geometry."""
    heights = {round(e.dxf.height, 6) for e in dxf_assert.entities(doc)
               if e.dxftype() == "TEXT"}
    assert heights == {model_text_height_mm(SHEET, 2.5)} == {250.0}, heights


def test_pier_labels_are_sequential_from_one(doc):
    blob = " ".join(dxf_assert.text_of(doc))
    assert "P1" in blob and "P2" in blob and "P3" not in blob


def test_dimensions_cover_each_span_and_the_overall(doc, project):
    dims = dxf_assert.text_of(doc, layer="DIM")
    assert any("36.000" in d for d in dims), "no overall dimension"
    for span in ("12.000",):
        assert sum(1 for d in dims if span in d) >= 3, f"span {span} not dimensioned per span"


def test_nothing_leaves_the_frame(doc):
    from ezdxf import bbox
    ext = bbox.extents(doc.modelspace(), fast=True)
    from bridgecad_draw.coordinates import paper_size_mm
    w, h = paper_size_mm(SHEET, (ext.extmax.x - ext.extmin.x, ext.extmax.y - ext.extmin.y))
    assert w <= 841 and h <= 534, f"{w:.0f}x{h:.0f} mm of paper does not fit an A1"


def test_sheet_fill_is_acceptable(doc):
    """~43% of an A1 is normal for a 36 m long section at 1:100. Below 35% means
    the scale is wrong and the drawing is unreadable in print."""
    from ezdxf import bbox
    from bridgecad_draw.coordinates import paper_size_mm
    ext = bbox.extents(doc.modelspace(), fast=True)
    w, _ = paper_size_mm(SHEET, (ext.extmax.x - ext.extmin.x, 0.0))
    assert w / 841 >= 0.35, f"only {w / 841:.0%} of the frame used — check the scale"


def test_rendering_is_deterministic(project):
    a = contract.serialise(contract.build_sheet(project, SHEET))
    b = contract.serialise(contract.build_sheet(project, SHEET))
    assert a == b
