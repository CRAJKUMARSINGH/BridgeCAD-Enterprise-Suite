"""Shared drafting kit for the in-memory sheet builders.

Wing-16 set the pattern in ``sheet2_long_section``: take the sheet's declared
frame from ``draw_sheet_frame``, draw through a layer-stamping modelspace so no
entity is left on layer "0", and resolve every position through the Wing-11
coordinate contract so a chainage lands on the same model x on every sheet.
Sheets 1 and 3-7 need exactly that, so it lives here once rather than six times.

Nothing here knows what a bridge is. Each sheet module supplies the geometry;
this module supplies the frame, the pen and the paper sizes.
"""

from __future__ import annotations

from contextlib import contextmanager

from bridgecad_draw.coordinates import (
    check_declared,
    m,
    model_text_height_mm,
    to_model_space,
)
from bridgecad_draw.dxf_engine import new_sheet
from bridgecad_draw.primitives import (
    hatch_rect,
    polyline,
    rectangle,
)
from bridgecad_draw.primitives import (
    text as _text,
)
from bridgecad_draw.titleblocks import draw_sheet_frame

#: Text is sized on paper and scaled to model space once, here.
PAPER_TEXT_MM = 2.5
#: The set is seven sheets; every frame states its own index out of this.
TOTAL_SHEETS = 7
#: ezdxf creates this dimstyle on first use; naming it keeps the choice visible.
DIM_DIMSTYLE = "EZDXF"


class _Layered:
    """A modelspace that stamps the enclosing block's layer on new entities.

    ezdxf gives every new graphic entity layer "0" (``DEFAULT_ATTRIBS``) and
    consults no "current layer", so an entity drawn without an explicit layer is
    a defect the contract tests reject.
    """

    __slots__ = ("_msp", "layer_name")

    def __init__(self, msp, layer_name: str = "TEXT"):
        self._msp = msp
        self.layer_name = layer_name

    def _stamp(self, dxfattribs):
        attribs = dict(dxfattribs or {})
        attribs["layer"] = self.layer_name  # forced: the enclosing block wins
        return attribs

    def add_line(self, start, end, dxfattribs=None, **kwargs):
        return self._msp.add_line(start, end, dxfattribs=self._stamp(dxfattribs), **kwargs)

    def add_text(self, content, dxfattribs=None, **kwargs):
        return self._msp.add_text(content, dxfattribs=self._stamp(dxfattribs), **kwargs)

    def __getattr__(self, name):
        return getattr(self._msp, name)


@contextmanager
def layer(ms: _Layered, layer_name: str):
    """Draw the enclosed entities on *layer_name*."""
    previous = ms.layer_name
    ms.layer_name = layer_name
    try:
        yield ms
    finally:
        ms.layer_name = previous


def field(obj, name: str, default=None):
    """Read *name* off a model object or a plain dict, without raising."""
    value = getattr(obj, name, None)
    if value is None and isinstance(obj, dict):
        value = obj.get(name)
    if value is None:
        return default
    return value


class Canvas:
    """One sheet under construction: its frame, its pen, its paper size."""

    def __init__(
        self,
        sheet: str,
        title: str,
        index: int,
        *,
        total: int = TOTAL_SHEETS,
        text_mm: float = PAPER_TEXT_MM,
    ):
        frame = check_declared(sheet)
        self.sheet = sheet
        self.index = index
        self.text_mm = text_mm
        self.scale = frame.plot_scale
        self.doc, raw = new_sheet(title)
        self.frame_w, self.frame_h = draw_sheet_frame(
            raw, sheet, sheet_index=index, total_sheets=total
        )
        self.ms = _Layered(raw)
        #: Model height that plots at ``text_mm`` on paper: 2.5 mm at 1:100 is
        #: 250 mm of model, not 2.5 — see ``coordinates.model_text_height_mm``.
        self.height = model_text_height_mm(sheet, text_mm)

    # ── coordinate contract ─────────────────────────────────────────────
    def x(self, chainage_m: float) -> float:
        """Chainage (m, project space) -> model x (mm)."""
        return to_model_space(self.sheet, chainage_m, 0.0)[0]

    def y(self, level_m: float) -> float:
        """Level (m) -> model y (mm).

        On a plan the second axis is a transverse offset in metres rather than a
        level, and the mapping is the same one: a metre is a thousand model mm.
        """
        return to_model_space(self.sheet, 0.0, level_m)[1]

    def mm(self, metres: float) -> float:
        return m(metres)

    # ── pen ─────────────────────────────────────────────────────────────
    @contextmanager
    def on(self, layer_name: str):
        with layer(self.ms, layer_name) as ms:
            yield ms

    def line(self, p1, p2, **attribs):
        return self.ms.add_line(p1, p2, dxfattribs=attribs or None)

    def dash(self, p1, p2, linetype: str = "DASHED"):
        return self.line(p1, p2, linetype=linetype)

    def rect(self, x, y, w, h, *, lw=None):
        return rectangle(self.ms, x, y, w, h, layer=self.ms.layer_name, lw=lw)

    def poly(self, points, *, close: bool = True):
        return polyline(self.ms, points, close=close, layer=self.ms.layer_name)

    def hatch(self, x, y, w, h, *, pattern: str = "ANSI31", scale: float = 6.0):
        return hatch_rect(
            self.ms, x, y, w, h, pattern=pattern, scale=scale, layer=self.ms.layer_name
        )

    def text(self, content, x, y, *, height: float | None = None, halign: str = "LEFT"):
        return _text(
            self.ms,
            str(content),
            x,
            y,
            height=self.height if height is None else height,
            halign=halign,
        )

    def dimension(self, p1, p2, *, base, angle: float = 0.0, text=None, layer_name: str = "DIM"):
        """A real DXF DIMENSION entity — the type the contract counts.

        ``primitives.dim_linear_*`` draws a line and a text label; those are not
        DIMENSION entities and ``assert_min_dimensions`` does not see them.

        ``angle`` is 0 for a horizontal dimension line and 90 for a vertical one,
        which is what decides whether the measured distance is taken along x or
        along y.
        """
        dim = self.ms.add_linear_dim(
            base=base,
            p1=p1,
            p2=p2,
            angle=angle,
            dimstyle=DIM_DIMSTYLE,
            dxfattribs={"layer": layer_name},
            override={"dimtxt": self.height * 0.6, "dimtxsty": "BRIDGE_STD"},
        )
        if text is not None:
            dim.set_text(text)
        dim.render()
        return dim

    def note(self, lines, x, y, *, leading: float | None = None, layer_name: str = "TEXT-SPEC"):
        """A notes block, first line at *y*, each line below the last."""
        step = leading if leading is not None else self.height * 1.6
        with layer(self.ms, layer_name):
            for i, line in enumerate(lines):
                self.text(line, x, y - i * step)
        return y - (len(lines) - 1) * step

    def table(
        self, x, y_top, col_widths, rows, *, row_h: float | None = None, layer_name: str = "TABL"
    ):
        """A ruled schedule. ``rows[0]`` is the header; returns the bottom y."""
        step = row_h if row_h is not None else self.height * 2.2
        width = sum(col_widths)
        edges = [x]
        for w in col_widths:
            edges.append(edges[-1] + w)
        with layer(self.ms, layer_name):
            for i in range(len(rows) + 1):
                yy = y_top - i * step
                self.line((x, yy), (x + width, yy))
            for ex in edges:
                self.line((ex, y_top), (ex, y_top - len(rows) * step))
            for i, row in enumerate(rows):
                yy = y_top - (i + 1) * step + (step - self.height) * 0.5
                for j, cell in enumerate(row):
                    self.text(cell, edges[j] + self.height * 0.3, yy, height=self.height * 0.85)
        return y_top - len(rows) * step

    def level_staff(self, x, pairs, *, tick: float | None = None, layer_name: str = "DIM-LEVEL"):
        """A stack of RL tags at *x*: ``pairs`` is [(name, level_m), ...]."""
        span = tick if tick is not None else self.height * 0.5
        with layer(self.ms, layer_name):
            self.line(
                (x, self.y(min(p[1] for p in pairs)) - span),
                (x, self.y(max(p[1] for p in pairs)) + span),
            )
            for name, lv in pairs:
                yy = self.y(lv)
                self.line((x - span, yy), (x + span, yy))
                self.text(f"{name} RL {lv:.3f}", x + span * 1.4, yy, halign="LEFT")


__all__ = ["Canvas", "layer", "field", "PAPER_TEXT_MM", "TOTAL_SHEETS", "DIM_DIMSTYLE"]
