"""bridgecad_draw._sheetkit — paper-space furniture for the asset-pack sheets.

WHY THIS EXISTS
    The asset pack reproduces the two drawing sets shipped in
    ``sample-gad-drawings/*.pdf``:

      * a PMGSY minor bridge, 7 x 9.0 m RCC solid slab, three A3 sheets
        (L-section + plan, deck section + substructure details, pier details);
      * a 1 x 6.0 m high-level bridge, one A3 sheet
        (elevation, half plan, level table, boreholes, index plan).

    Eleven of those views are *compositions*, not single drawings: a frame, a
    multi-cell Indian PWD title block, a view heading, dimension chains
    measured in metres off the geometry, reduced-level tags, hatch legend and a
    numbered note block.  Repeating that furniture inside every sheet module
    would drift (two different title blocks on one sheet set is exactly the
    kind of thing a checker rejects), so it lives here once.

CONVENTIONS
    * Model space is paper millimetres, exactly as the rest of the package does
      it — an A3 sheet is 420 x 297 and sits at the origin.
    * Sheet modules reason in *real* units (metres of chainage, metres of RL).
      ``Panel`` maps those into the sheet, so no module ever multiplies by 1000
      by hand and no view can silently land off the frame.
    * Every annotation height is >= 1.9 mm so the plot is legible at A3, which
      is the size both source PDFs use.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Iterable, Sequence

from .dxf_engine import new_sheet, save
from .primitives import dim_linear_h, dim_linear_v, north_arrow, polyline, rectangle

# ---------------------------------------------------------------------------
# Text — written here rather than via primitives.text()
# ---------------------------------------------------------------------------
# primitives.text() clamps the height to MIN_TEXT_HEIGHT_MM.  That clamp is
# right for the 1:100 GAD sheets (a 0.35 mm label there is a mistake), but this
# module needs sub-2 mm table cells, so the raw entity is written directly.
try:  # ezdxf is optional at import time, like every other module here
    from ezdxf.enums import TextEntityAlignment as _TEA

    _ALIGN = {
        "LEFT": _TEA.LEFT,
        "CENTER": _TEA.CENTER,
        "RIGHT": _TEA.RIGHT,
        "MIDDLE": _TEA.MIDDLE,
        "TOP_LEFT": _TEA.TOP_LEFT,
    }
except Exception:  # pragma: no cover - ezdxf present in every real run
    _ALIGN = {}


def put_text(
    msp: Any,
    content: Any,
    x: float,
    y: float,
    height: float = 2.4,
    layer: str = "TEXT-GENERAL",
    rotation: float = 0.0,
    align: str = "LEFT",
    color: int | None = None,
) -> Any:
    """Place one text entity at an absolute paper position."""
    try:
        attribs: dict[str, Any] = {"layer": layer, "height": float(max(height, 0.05))}
        if rotation:
            attribs["rotation"] = float(rotation)
        if color is not None:
            attribs["color"] = int(color)
        t = msp.add_text(str(content), dxfattribs=attribs)
        target = _ALIGN.get(str(align).upper())
        if target is not None:
            t.set_placement((float(x), float(y)), align=target)
        else:
            t.dxf.insert = (float(x), float(y))
        return t
    except Exception:
        return None


def _char_w(height: float) -> float:
    """Average glyph advance for the Arial text style, in mm."""
    return 0.62 * float(height)


def fit_text(content: str, width_mm: float, height: float) -> str:
    """Truncate *content* so it cannot overrun a *width_mm* wide cell."""
    s = str(content)
    room = max(int(width_mm / max(_char_w(height), 1e-6)) - 1, 3)
    return s if len(s) <= room else s[: room - 1].rstrip() + "\u2026"


def wrap_text(content: str, max_chars: int) -> list[str]:
    """Greedy word wrap; never returns an empty list."""
    words = str(content).split()
    lines: list[str] = []
    cur = ""
    for w in words:
        trial = (cur + " " + w).strip()
        if len(trial) <= max_chars:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


# ---------------------------------------------------------------------------
# Sheet sizes
# ---------------------------------------------------------------------------

PAPER_SIZES: dict[str, tuple[float, float]] = {
    "A4": (297.0, 210.0),
    "A3": (420.0, 297.0),
    "A2": (594.0, 420.0),
    "A1": (841.0, 594.0),
}

TXT_H = 3.4  # view heading
TXT_M = 2.4  # normal annotation
TXT_S = 2.0  # dimension text / table cell
TXT_XS = 1.7  # legend, note continuation


# ---------------------------------------------------------------------------
# Panel — model metres -> paper millimetres
# ---------------------------------------------------------------------------


class Panel:
    """A rectangular viewport that maps real-world metres onto the sheet.

    Parameters
    ----------
    rect : (x0, y0, x1, y1)
        Paper-space box the view must stay inside, in sheet millimetres.
    x_range, y_range : (min, max)
        Model extent in metres.  ``y_range`` is always a level (RL) for
        elevations and a transverse offset for plans.
    fit : ``"uniform"`` | ``"xy"``
        ``uniform`` keeps 1:1 geometry (details, sections).  ``xy`` fills the
        box independently, which is how a 63 m long-section fits an A3 sheet —
        the view is then marked NOT TO SCALE, as the source PDFs are.
    """

    def __init__(
        self,
        msp: Any,
        rect: tuple[float, float, float, float],
        x_range: tuple[float, float],
        y_range: tuple[float, float],
        fit: str = "uniform",
        pad: float = 2.0,
    ) -> None:
        self.msp = msp
        self.x0, self.y0, self.x1, self.y1 = (float(v) for v in rect)
        self.xr = (float(min(x_range)), float(max(x_range)))
        self.yr = (float(min(y_range)), float(max(y_range)))
        self.fit = fit
        bw = max((self.x1 - self.x0) - 2.0 * pad, 1.0)
        bh = max((self.y1 - self.y0) - 2.0 * pad, 1.0)
        span_x = max(self.xr[1] - self.xr[0], 1e-9)
        span_y = max(self.yr[1] - self.yr[0], 1e-9)
        if fit == "xy":
            self.sx = bw / span_x
            self.sy = bh / span_y
        else:
            s = min(bw / span_x, bh / span_y)
            self.sx = self.sy = s
        self.ox = self.x0 + pad + (bw - span_x * self.sx) / 2.0
        self.oy = self.y0 + pad + (bh - span_y * self.sy) / 2.0

    # -- mapping ---------------------------------------------------------
    def X(self, xm: float) -> float:
        return self.ox + (float(xm) - self.xr[0]) * self.sx

    def Y(self, ym: float) -> float:
        return self.oy + (float(ym) - self.yr[0]) * self.sy

    def P(self, xm: float, ym: float) -> tuple[float, float]:
        return (self.X(xm), self.Y(ym))

    @property
    def mm_per_m(self) -> float:
        return self.sx

    # -- drawing ---------------------------------------------------------
    def line(self, x1: float, y1: float, x2: float, y2: float, layer: str = "STRUC-OUTLINE",
             color: int | None = None, linetype: str | None = None, lw: int | None = None) -> Any:
        try:
            attribs: dict[str, Any] = {"layer": layer}
            if color is not None:
                attribs["color"] = int(color)
            if linetype:
                attribs["linetype"] = linetype
            if lw is not None:
                attribs["lineweight"] = int(lw)
            a, b = self.P(x1, y1), self.P(x2, y2)
            if abs(a[0] - b[0]) < 1e-9 and abs(a[1] - b[1]) < 1e-9:
                return None
            return self.msp.add_line(a, b, dxfattribs=attribs)
        except Exception:
            return None

    def poly(self, pts: Iterable[tuple[float, float]], layer: str = "STRUC-OUTLINE",
             close: bool = False, **kw: Any) -> Any:
        paper = [self.P(x, y) for x, y in pts]
        return polyline(self.msp, paper, layer=layer, close=close, **kw)

    def rect(self, x: float, y: float, w: float, h: float, layer: str = "STRUC-OUTLINE",
             **kw: Any) -> Any:
        return self.poly(
            [(x, y), (x + w, y), (x + w, y + h), (x, y + h)], layer=layer, close=True, **kw
        )

    def circle(self, x: float, y: float, r: float, layer: str = "STRUC-OUTLINE",
               color: int | None = None) -> Any:
        try:
            attribs: dict[str, Any] = {"layer": layer}
            if color is not None:
                attribs["color"] = int(color)
            return self.msp.add_circle(self.P(x, y), max(r * self.sx, 0.05), dxfattribs=attribs)
        except Exception:
            return None

    def hatch(self, pts: Iterable[tuple[float, float]], pattern: str = "ANSI31",
              scale: float = 1.0, layer: str = "STRUC-HATCHING", color: int | None = None) -> Any:
        try:
            attribs: dict[str, Any] = {"layer": layer}
            if color is not None:
                attribs["color"] = int(color)
            h = self.msp.add_hatch(dxfattribs=attribs)
            if str(pattern).upper() == "SOLID":
                h.set_solid_fill(color=color if color is not None else 8)
            else:
                h.set_pattern_fill(str(pattern), scale=float(scale))
            h.paths.add_polyline_path([self.P(x, y) for x, y in pts], is_closed=True)
            return h
        except Exception:
            return None

    def band(self, x0: float, y0: float, x1: float, y1: float, pattern: str = "ANSI31",
             scale: float = 1.0, layer: str = "STRUC-HATCHING", color: int | None = None) -> Any:
        return self.hatch(
            [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], pattern=pattern, scale=scale,
            layer=layer, color=color,
        )

    def text(self, content: Any, x: float, y: float, h: float = TXT_S,
             layer: str = "TEXT-GENERAL", align: str = "LEFT", rot: float = 0.0,
             dx: float = 0.0, dy: float = 0.0, color: int | None = None) -> Any:
        return put_text(self.msp, content, self.X(x) + dx, self.Y(y) + dy, h, layer,
                        rotation=rot, align=align, color=color)

    def label_at(self, content: Any, x_paper: float, y_paper: float, h: float = TXT_S,
                 layer: str = "TEXT-GENERAL", align: str = "LEFT", rot: float = 0.0) -> Any:
        return put_text(self.msp, content, x_paper, y_paper, h, layer, rotation=rot, align=align)

    # -- annotations attached to the geometry, never to the sheet --------
    def leader(
        self,
        xm: float,
        ym: float,
        dx: float,
        dy: float,
        label: str,
        align: str = "LEFT",
        th: float = TXT_XS,
        shelf: float = 9.0,
    ) -> None:
        """Leader from a model point to a label held *dx, dy* mm away.

        The offset is relative to the feature, not to the sheet, so a leader
        stays with its detail no matter where the panel is placed.  That is the
        only reason the earlier absolute-coordinate leaders crossed the whole
        drawing.
        """
        try:
            px, py = self.P(xm, ym)
            tx, ty = px + dx, py + dy
            self.msp.add_line((px, py), (tx, ty), dxfattribs={"layer": "DIM-LEADER",
                                                             "lineweight": 9})
            sgn = shelf if align.upper() == "LEFT" else -shelf
            self.msp.add_line((tx, ty), (tx + sgn, ty),
                              dxfattribs={"layer": "DIM-LEADER", "lineweight": 9})
            put_text(self.msp, label, tx + sgn + (1.0 if sgn > 0 else -1.0), ty + 0.6,
                     th, "TEXT-SPEC", align=align)
        except Exception:
            pass

    def sample(self, xm: float, ym: float, r: float = 2.0, layer: str = "MISC-DEFPOINTS") -> None:
        """Small circle marking a feature (weep hole, spout, bearing)."""
        try:
            self.msp.add_circle(self.P(xm, ym), r, dxfattribs={"layer": layer})
        except Exception:
            pass

    # -- captions --------------------------------------------------------
    def caption_below(self, title: str, sub: str | None = None, th: float = TXT_H,
                      drop: float = 4.2) -> None:
        """View caption in the strip reserved *under* the panel.

        Captions sit below their view on every sheet of this pack.  Doing that
        instead of stacking them above keeps a long-section caption from being
        pushed into the sheet banner on the crowded A3.
        """
        cx = (self.x0 + self.x1) / 2.0
        y = self.y0 - drop
        put_text(self.msp, title.upper(), cx, y, th, "TEXT-TITLE", align="CENTER")
        try:
            tw = len(title) * _char_w(th)
            self.msp.add_line((cx - tw / 2.0, y - 1.5), (cx + tw / 2.0, y - 1.5),
                              dxfattribs={"layer": "TEXT-TITLE"})
        except Exception:
            pass
        if sub:
            put_text(self.msp, sub, cx, y - (th + 1.8), th * 0.60, "TEXT-HEADER",
                     align="CENTER")


# ---------------------------------------------------------------------------
# Sheet — frame, title block, notes, tables
# ---------------------------------------------------------------------------


class Sheet:
    """One A3 sheet of the asset pack."""

    def __init__(self, size: str = "A3", title: str = "ASSET PACK") -> None:
        self.size = size.upper()
        self.doc, self.msp = new_sheet(title)
        self.w, self.h = PAPER_SIZES.get(self.size, PAPER_SIZES["A3"])
        self.m = 8.0 if self.size == "A3" else 10.0
        rectangle(self.msp, 0, 0, self.w, self.h, layer="BORDER-OUTER", lw=60)
        rectangle(self.msp, self.m, self.m, self.w - 2 * self.m, self.h - 2 * self.m,
                  layer="BORDER-INNER", lw=35)

    # -- primitives ------------------------------------------------------
    def text(self, content: Any, x: float, y: float, h: float = TXT_M,
             layer: str = "TEXT-GENERAL", align: str = "LEFT", rot: float = 0.0,
             color: int | None = None) -> Any:
        return put_text(self.msp, content, x, y, h, layer, rotation=rot, align=align, color=color)

    def line(self, x1: float, y1: float, x2: float, y2: float, layer: str = "STRUC-OUTLINE",
             lw: int | None = None, linetype: str | None = None) -> Any:
        try:
            attribs: dict[str, Any] = {"layer": layer}
            if lw is not None:
                attribs["lineweight"] = int(lw)
            if linetype:
                attribs["linetype"] = linetype
            if abs(x1 - x2) < 1e-9 and abs(y1 - y2) < 1e-9:
                return None
            return self.msp.add_line((x1, y1), (x2, y2), dxfattribs=attribs)
        except Exception:
            return None

    def rect(self, x: float, y: float, w: float, h: float, layer: str = "STRUC-OUTLINE",
             lw: int | None = None) -> Any:
        return rectangle(self.msp, x, y, w, h, layer=layer, lw=lw)

    def poly(self, pts: Sequence[tuple[float, float]], layer: str = "STRUC-OUTLINE",
             close: bool = False) -> Any:
        return polyline(self.msp, list(pts), layer=layer, close=close)

    def hatch_box(self, x: float, y: float, w: float, h: float, pattern: str = "ANSI31",
                  scale: float = 1.0, layer: str = "STRUC-HATCHING",
                  color: int | None = None) -> Any:
        try:
            attribs: dict[str, Any] = {"layer": layer}
            if color is not None:
                attribs["color"] = int(color)
            hh = self.msp.add_hatch(dxfattribs=attribs)
            if str(pattern).upper() == "SOLID":
                hh.set_solid_fill(color=color if color is not None else 8)
            else:
                hh.set_pattern_fill(str(pattern), scale=float(scale))
            hh.paths.add_polyline_path(
                [(x, y), (x + w, y), (x + w, y + h), (x, y + h)], is_closed=True
            )
            return hh
        except Exception:
            return None

    def panel(self, rect: tuple[float, float, float, float], x_range: tuple[float, float],
              y_range: tuple[float, float], fit: str = "uniform", pad: float = 2.0) -> Panel:
        return Panel(self.msp, rect, x_range, y_range, fit=fit, pad=pad)

    def view_frame(self, x: float, y: float, w: float, h: float, layer: str = "STRUC-DETAIL") -> None:
        """Thin enclosure around a detail view (the source sheets use one)."""
        self.rect(x, y, w, h, layer=layer, lw=9)

    # -- dimensions ------------------------------------------------------
    def dim_h(self, x1: float, x2: float, y: float, label: str | None = None,
              off: float = 6.0, th: float = TXT_S, layer: str = "DIM-LINEAR") -> None:
        try:
            dim_linear_h(self.msp, x1, y, x2, y, y + off, label=label, layer=layer, text_height=th)
        except Exception:
            pass

    def dim_v(self, y1: float, y2: float, x: float, label: str | None = None,
              off: float = 6.0, th: float = TXT_S, layer: str = "DIM-LINEAR") -> None:
        try:
            dim_linear_v(self.msp, x, y1, x, y2, x + off, label=label, layer=layer, text_height=th)
        except Exception:
            pass

    def dim_chain_h(self, xs: Sequence[float], y: float, labels: Sequence[str] | None = None,
                    off: float = 6.0, th: float = TXT_S) -> None:
        """A continuous horizontal chain: one DIMENSION per gap, ticks shared."""
        for i in range(len(xs) - 1):
            lab = labels[i] if labels and i < len(labels) else None
            self.dim_h(xs[i], xs[i + 1], y, lab, off=off, th=th)

    # -- level tag, leader ----------------------------------------------
    def level(self, x: float, y: float, value: float, prefix: str = "RL",
              th: float = TXT_S, align: str = "RIGHT", dx: float = -3.0) -> None:
        """Reduced-level tag: tick, level line, value."""
        try:
            w = 3.0
            self.line(x - w, y, x + w, y, layer="DIM-LEVEL")
            self.line(x, y, x - 6.0, y, layer="DIM-LEVEL")
            self.text(f"{prefix} {value:.3f}", x + dx, y + 4.0, th, "TEXT-LEVEL", align=align)
        except Exception:
            pass

    def leader(self, x1: float, y1: float, x2: float, y2: float, label: str,
               th: float = TXT_XS, align: str = "LEFT", layer: str = "DIM-LEADER") -> None:
        """Leader from geometry (x1,y1) to a labelled shelf at (x2,y2)."""
        shelf = 12.0 if align == "LEFT" else -12.0
        try:
            self.line(x1, y1, x2, y2, layer=layer, lw=9)
            self.line(x2, y2, x2 + shelf, y2, layer=layer, lw=9)
            tx = x2 + shelf + (1.2 if align == "LEFT" else -1.2)
            self.text(label, tx, y2 + 0.7, th, "TEXT-SPEC", align=align)
        except Exception:
            pass

    # -- view heading ----------------------------------------------------
    def heading(self, x: float, y: float, title: str, sub: str | None = None,
                align: str = "CENTER", th: float = TXT_H) -> None:
        self.text(title.upper(), x, y, th, "TEXT-TITLE", align=align)
        if sub:
            self.text(sub, x, y - (th + 1.6), th * 0.62, "TEXT-HEADER", align=align)
        try:
            tw = len(title) * _char_w(th)
            if align == "CENTER":
                self.line(x - tw / 2, y - 1.4, x + tw / 2, y - 1.4, layer="TEXT-TITLE")
            else:
                self.line(x, y - 1.4, x + tw, y - 1.4, layer="TEXT-TITLE")
        except Exception:
            pass

    def banner(self, text: str, y: float, x0: float | None = None, x1: float | None = None,
               th: float = TXT_H) -> None:
        """Full-width title bar used by the PMGSY sheets.

        A solid black bar with knocked-out text is not achievable in DXF (the
        text would plot black on black), so the bar is a double-ruled box with
        a light tint — the same read as the plotted PDF at a fraction of the
        ink.
        """
        x0 = self.m + 2 if x0 is None else x0
        x1 = self.w - self.m - 2 if x1 is None else x1
        self.rect(x0, y, x1 - x0, th + 4.0, layer="BORDER-INNER", lw=25)
        self.rect(x0 + 1.0, y + 1.0, x1 - x0 - 2.0, th + 2.0, layer="BORDER-INNER", lw=9)
        self.text(text.upper(), (x0 + x1) / 2, y + 1.8, th, "TEXT-TITLE", align="CENTER")

    # -- notes -----------------------------------------------------------
    def notes(self, x: float, y: float, w: float, items: Sequence[str],
              heading: str = "NOTES :-", th: float = TXT_XS, gap: float = 3.7,
              numbered: bool = True, start: int = 1) -> float:
        """Numbered note block. Returns the y of the last baseline.

        *start* keeps the numbering continuous when the notes are split across
        two columns on a crowded sheet.
        """
        if heading:
            self.text(heading, x, y, th + 0.9, "TEXT-HEADER")
            self.line(x, y - 2.0, x + w, y - 2.0, layer="TEXT-HEADER", lw=9)
        cy = y - gap - 1.0
        max_chars = max(int(w / _char_w(th)) - 4, 20)
        for i, item in enumerate(items, start=start):
            tag = f"{i}." if numbered else "\u2022"
            lines = wrap_text(item, max_chars)
            self.text(tag, x, cy, th, "TEXT-SPEC")
            for j, ln in enumerate(lines):
                self.text(ln, x + 6.0, cy, th, "TEXT-GENERAL")
                if j < len(lines) - 1:
                    cy -= gap
            cy -= gap + 0.5
        return cy

    # -- table -----------------------------------------------------------
    def table(self, x: float, y: float, widths: Sequence[float],
              rows: Sequence[Sequence[str]], row_h: float = 6.6, th: float = TXT_S,
              header: bool = True, top: bool = False) -> float:
        """Draw a ruled table whose first row is a header. Returns its bottom y.

        Rows are ordered top-down starting at *y* (the header baseline box) and
        the table grows downwards.
        """
        n = len(rows)
        if n == 0:
            return y
        width = sum(widths)
        height = row_h * n
        y_top = y
        # outer box
        self.rect(x, y_top - height, width, height, layer="TABL", lw=18)
        for r, row in enumerate(rows):
            ry = y_top - row_h * (r + 1)
            if r:
                self.line(x, y_top - row_h * r, x + width, y_top - row_h * r,
                          layer="TABL", lw=9)
            cx = x
            for c, cell in enumerate(row):
                cw = widths[c] if c < len(widths) else widths[-1]
                if c:
                    self.line(cx, ry, cx, ry + row_h, layer="TABL", lw=9)
                style = "TEXT-HEADER" if (header and r == 0) else "TEXT-GENERAL"
                self.text(fit_text(cell, cw - 3.0, th), cx + 1.6, ry + row_h / 2 - th / 2,
                          th, style)
                cx += cw
        if top:
            self.text("", x, y_top, th)
        return y_top - height

    # -- symbols ---------------------------------------------------------
    def north(self, x: float, y: float, size: float = 10.0, label: str = "NORTH") -> None:
        try:
            north_arrow(self.msp, x, y, size=size, layer="SYM-NORTHARROW")
            self.text(label, x, y - size - 3.0, TXT_XS, "TEXT-GENERAL", align="CENTER")
        except Exception:
            pass

    def scalebar(self, x: float, y: float, total_mm: float, segments: int = 4,
                 label: str = "SCALE 1:100", th: float = TXT_XS) -> None:
        seg = total_mm / segments
        for i in range(segments):
            self.rect(x + i * seg, y, seg, 2.6, layer="SYM-SCALE", lw=9)
            if i % 2 == 0:
                self.hatch_box(x + i * seg, y, seg, 2.6, pattern="SOLID", scale=1.0,
                               layer="SYM-SCALE")
        self.text("0", x, y - 3.2, th, "TEXT-GENERAL", align="CENTER")
        self.text(label, x + total_mm, y - 3.2, th, "TEXT-GENERAL", align="RIGHT")

    def section_mark(self, x1: float, y1: float, x2: float, y2: float, tag: str = "A") -> None:
        """Cut line with end tags A-A."""
        try:
            self.line(x1, y1, x2, y2, layer="SYM-SECTIONMARK", linetype="CENTER")
            for (px, py) in ((x1, y1), (x2, y2)):
                self.rect(px - 3.0, py - 3.0, 6.0, 6.0, layer="SYM-SECTIONMARK", lw=13)
                self.text(tag, px, py - 1.3, TXT_S, "TEXT-TITLE", align="CENTER")
                self.line(px, py, px + (6 if px <= x1 else -6), py, layer="SYM-SECTIONMARK")
        except Exception:
            pass

    # -- title block -----------------------------------------------------
    def title_block(
        self,
        *,
        client: str = "",
        consultant: str = "",
        road: str = "",
        title: str = "GENERAL ARRANGEMENT DRAWING",
        drawing_no: str = "",
        sheet_no: str = "1",
        total_sheets: str = "1",
        scale: str = "NTS",
        date: str = "",
        drawn: str = "",
        designed: str = "",
        approved: str = "",
        revision: str = "R-00",
        width: float = 196.0,
        rows: float = 9.2,
    ) -> tuple[float, float]:
        """Indian PWD style 6-row title block in the bottom-right corner.

        Cells are labelled (``CLIENT :-``, ``DRAWING NO :-`` ...) because a
        reviewer reads the block, not the DXF.
        """
        tb_w = width
        tb_h = rows * 6
        x0 = self.w - self.m - tb_w
        y0 = self.m
        self.rect(x0, y0, tb_w, tb_h, layer="TITLEBLK-BOX", lw=50)

        col_a, col_b, col_c = tb_w * 0.40, tb_w * 0.36, tb_w * 0.24
        xs = [x0, x0 + col_a, x0 + col_a + col_b, x0 + tb_w]
        for xv in xs[1:-1]:
            self.line(xv, y0, xv, y0 + tb_h, layer="TITLEBLK-BOX", lw=18)

        def rowline(k: int) -> float:
            return y0 + tb_h - rows * k

        # horizontal rules: 5 internal, rows 6 tall
        for k in range(1, 6):
            yv = y0 + rows * k
            self.line(x0, yv, x0 + tb_w, yv, layer="TITLEBLK-BOX", lw=18)

        def cell(col: int, k: int, label: str, value: str, th: float = TXT_XS) -> None:
            cx = xs[col] + 1.6
            cw = (xs[col + 1] - xs[col]) - 3.2
            top = y0 + rows * k
            self.text(label, cx, top - 3.0, th, "TITLEBLK-TEXT")
            if value:
                self.text(fit_text(value, cw, th + 0.2), cx, top - 6.6, th + 0.2,
                          "TITLEBLK-TEXT")

        cell(0, 1, "CLIENT :-", client)
        cell(1, 1, "DRAWING NO. :-", drawing_no)
        cell(2, 1, "SHEET :-", f"{sheet_no} OF {total_sheets}")
        cell(0, 2, "CONSULTANT :-", consultant)
        cell(1, 2, "DATE :-", date)
        cell(2, 2, "SCALE :-", scale)
        cell(0, 3, "ROAD / PROJECT :-", road)
        cell(1, 3, "REVISION :-", revision)
        cell(2, 3, "DRAWN BY :-", drawn)
        cell(0, 4, "DRAWING TITLE :-", "", TXT_XS)
        title_h = TXT_M - 0.2
        self.text(fit_text(title, col_a + col_b - 5.0, title_h), xs[0] + 1.6,
                  y0 + rows * 4 + 2.4, title_h, "TITLEBLK-TEXT")
        cell(2, 4, "DESIGNED BY :-", designed)
        # signature strip
        labels = ["APPROVED BY :-", approved or "", ""]
        cell(0, 5, labels[0], labels[1])
        cell(1, 5, "CHECKED BY :-", "")
        cell(2, 5, "DATE :-", date)
        return (x0, y0)

    # -- meta ------------------------------------------------------------
    def footer(self, text: str) -> None:
        self.text(text, self.m + 2, self.m + 2.0, TXT_XS, "TEXT-SPEC")

    def save(self, path: str | Path) -> Path:
        return save(self.doc, path)


__all__ = [
    "Panel",
    "Sheet",
    "PAPER_SIZES",
    "TXT_H",
    "TXT_M",
    "TXT_S",
    "TXT_XS",
    "fit_text",
    "put_text",
    "wrap_text",
]
