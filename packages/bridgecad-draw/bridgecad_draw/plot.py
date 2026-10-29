"""Page setup and paper-space layouts.

Model space stays 1:1 mm. Paper scale lives only here, in a locked viewport, so
the same DXF plots identically twice. Week 39.
"""

from __future__ import annotations

from typing import Any

from .coordinates import FRAMES, TITLE_BLOCK, check_declared

PLOT_STYLE = "BRG-MONO.ctb"
MARGIN_MM = 10.0


def setup_layout(doc: Any, sheet: str) -> str:
    """Create the sheet's paper-space layout, page setup and locked viewport.

    Returns the layout name.
    """
    frame = check_declared(sheet)
    name = sheet
    layout = doc.layouts.new(name)

    layout.page_setup(
        size=(frame.width_mm, frame.height_mm),
        margins=(0.0, 0.0, 0.0, 0.0),
        units="mm",
        offset=(0.0, 0.0),
        rotation=0.0,
        scale=1.0,
        name=f"A1 {'landscape'}",
        device="DWG To PDF.pc3",
    )
    layout.dxf.plot_style_sheet = PLOT_STYLE
    layout.dxf.plot_orientation = 1  # landscape

    # Viewport covers the drawing region only, never the title block corner.
    tb_h = TITLE_BLOCK["height_mm"]
    vp_w = frame.width_mm - 2 * MARGIN_MM
    vp_h = frame.height_mm - 2 * MARGIN_MM - tb_h

    centre = (
        MARGIN_MM + vp_w / 2.0,
        MARGIN_MM + tb_h + vp_h / 2.0,
    )
    # view_height is the model-space height shown; paper height x scale.
    layout.add_viewport(
        center=centre,
        size=(vp_w, vp_h),
        view_center_point=(
            (MARGIN_MM + vp_w / 2.0) * frame.plot_scale,
            (MARGIN_MM + tb_h + vp_h / 2.0) * frame.plot_scale,
        ),
        view_height=vp_h * frame.plot_scale,
    )

    vp = [e for e in layout if e.dxftype() == "VIEWPORT"][-1]
    vp.dxf.status = 2  # active
    vp.dxf.layer = "MISC-DEFPOINTS"
    vp.dxf.frozen_layers = "MISC-DEFPOINTS"
    return name


def setup_all(doc: Any) -> list[str]:
    return [setup_layout(doc, sheet) for sheet in FRAMES if _is_paper_sheet(sheet)]


def _is_paper_sheet(sheet: str) -> bool:
    """Sheet 7 is a table at 1:1 and needs no viewport scaling."""
    return sheet != "sheet7_bill_of_quantities"


def measured_scale(layout: Any) -> float:
    """Scale denominator implied by the layout's viewport, for assertions."""
    vps = [e for e in layout if e.dxftype() == "VIEWPORT" and e.dxf.id != 1]
    if not vps:
        raise ValueError("layout has no viewport")
    vp = vps[0]
    return vp.dxf.view_height / vp.dxf.height


__all__ = ["setup_layout", "setup_all", "measured_scale", "PLOT_STYLE"]
