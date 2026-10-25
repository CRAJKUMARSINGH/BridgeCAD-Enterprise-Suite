"""Wing-11 — the coordinate contract, asserted.

Every clause in coordinates.py has a test here. A clause without a test is a
comment; this file is what makes it a contract.
"""
from __future__ import annotations

import pytest
from ezdxf import bbox

from . import contract, dxf_assert

pytestmark = pytest.mark.draw

from bridgecad_draw.coordinates import (  # noqa: E402
    FRAMES, PLOT_SCALES, TITLE_BLOCK, check_declared, m, to_model_space,
)

SHEETS = tuple(FRAMES)


def test_every_sheet_declares_a_frame():
    """Clause 3 — declared, not implied."""
    for sheet in SHEETS:
        check_declared(sheet)   # raises if undeclared or malformed


def test_no_sheet_uses_a_nonstandard_scale():
    for sheet in SHEETS:
        assert FRAMES[sheet].plot_scale in PLOT_SCALES, sheet


def test_frame_sizes_are_a_series_landscape():
    for sheet in SHEETS:
        w, h = FRAMES[sheet].width_mm, FRAMES[sheet].height_mm
        assert w > h, f"{sheet}: {w}x{h} is portrait — the contract is landscape"


def test_model_space_is_millimetres():
    """Clause 1 — conversion happens once, and only here."""
    assert m(1.0) == 1000.0
    assert m(0.0) == 0.0


def test_same_chainage_resolves_to_the_same_x_across_sheets():
    """Clause 4 — the actual point of a shared contract."""
    pairs = [("sheet1_plan", "sheet2_long_section"), ("sheet1_plan", "sheet4_foundation")]
    for a, b in pairs:
        xa, _ = to_model_space(a, 12.0, 0.0)
        xb, _ = to_model_space(b, 12.0, 0.0)
        assert xa == pytest.approx(xb), (
            f"chainage 12 m maps to x={xa} on {a} but x={xb} on {b}"
        )


def test_level_is_monotonic_in_the_y_axis():
    """Clause 2 — Y is up, so a higher level is a larger Y."""
    y_low = to_model_space("sheet2_long_section", 0.0, 100.0)[1]
    y_high = to_model_space("sheet2_long_section", 0.0, 105.0)[1]
    assert y_high > y_low


@pytest.mark.parametrize("sheet", SHEETS)
def test_geometry_stays_inside_the_declared_frame(sheet: str):
    """Clause 7 — nothing outside the frame, and no accidental (0,0) anchor.

    LIKE UNITS. Model space is millimetres at 1:1, so a paper length is a model
    length MULTIPLIED by the plot scale — a 1:100 sheet carries 100 mm of model
    per paper millimetre. Dividing here compares model mm against paper mm and
    is unpassable for any real sheet.
    """
    project = contract.make_project("simple_12m")
    doc = contract.build_sheet(project, sheet)
    ext = bbox.extents(doc.modelspace(), fast=True)
    assert ext.has_data, f"{sheet}: no geometry"

    frame = check_declared(sheet)
    x0, y0, x1, y1 = frame.drawing_region_mm
    scale = frame.plot_scale

    # Model-space frame: paper millimetres times the declared plot scale.
    assert ext.extmin.x >= -1.0, f"{sheet}: geometry at x={ext.extmin.x} is left of the datum"
    assert ext.extmax.x <= (x1 - x0) * scale + 1.0, (
        f"{sheet}: geometry runs {ext.extmax.x:.1f} mm, frame allows {(x1 - x0) * scale:.1f}"
    )
    assert ext.extmax.y <= (y1 - y0) * scale + 1.0, (
        f"{sheet}: geometry overruns the top of the frame"
    )


@pytest.mark.parametrize("sheet", SHEETS)
def test_title_block_is_inside_its_declared_region(sheet: str):
    """Clause 6 — the title block corner is reserved, and the text is in it."""
    from .dxf_assert import entities
    project = contract.make_project("simple_12m")
    doc = contract.build_sheet(project, sheet)
    frame = check_declared(sheet)
    tb_h = TITLE_BLOCK["height_mm"] * frame.plot_scale

    tb_text = [e for e in entities(doc)
               if e.dxftype() in ("TEXT", "MTEXT")
               and e.dxf.insert.y <= tb_h + 1.0]
    assert tb_text, f"{sheet}: no title block text in the reserved {TITLE_BLOCK['corner']} corner"


def test_title_block_and_drawing_regions_do_not_overlap():
    for sheet in SHEETS:
        x0, y0, x1, y1 = check_declared(sheet).drawing_region_mm
        assert y0 >= TITLE_BLOCK["height_mm"], f"{sheet}: drawing region overlaps the title block"


def test_undeclared_sheet_raises_rather_than_defaulting():
    """A new sheet that forgets its frame must fail loudly."""
    with pytest.raises(KeyError, match="no declared frame"):
        check_declared("sheet8_does_not_exist")


def test_sheet_one_is_the_reference_datum():
    """Every other sheet's datum is stated relative to sheet 1's."""
    from bridgecad_draw.coordinates import origin_xy
    assert origin_xy("sheet1_plan") == (0.0, 0.0)
