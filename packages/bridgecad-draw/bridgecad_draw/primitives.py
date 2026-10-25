"""
bridgecad_draw.primitives — High-level DXF drawing helpers built on ezdxf.

All helpers accept an ``msp`` (modelspace) object and return the entity or None.
Coordinates are in real-world metres unless noted (ezdxf draws in model units).

Design notes
------------
- Every helper is a standalone function; no class state.
- Layer names reference LAYER_REGISTRY keys defined in layers.py.
- All functions guard against invalid inputs and return None on failure.
- Scale-aware helpers accept ``scale`` (denominator, e.g. 100 for 1:100).
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
Pt2 = tuple[float, float]
Pts = Sequence[Pt2]


# ---------------------------------------------------------------------------
# Low-level attribute builder
# ---------------------------------------------------------------------------

def _attribs(layer: str, color: int | None = None,
             linetype: str | None = None, lw: int | None = None) -> dict:
    d: dict[str, Any] = {"layer": layer}
    if color is not None:
        d["color"] = color
    if linetype is not None:
        d["linetype"] = linetype
    if lw is not None:
        d["lineweight"] = lw
    return d


# ---------------------------------------------------------------------------
# Basic geometry
# ---------------------------------------------------------------------------

def line(msp, p1: Pt2, p2: Pt2, layer: str = "STRUC-OUTLINE",
         color: int | None = None, linetype: str | None = None,
         lw: int | None = None) -> Any:
    """Draw a single line from *p1* to *p2*."""
    try:
        return msp.add_line(p1, p2, dxfattribs=_attribs(layer, color, linetype=linetype, lw=lw))
    except Exception:
        return None


def polyline(msp, points: Pts, layer: str = "STRUC-OUTLINE",
             close: bool = False, color: int | None = None,
             linetype: str | None = None,
             lw: int | None = None) -> Any:
    """Draw a lightweight polyline through *points*."""
    try:
        pts = [(float(x), float(y)) for x, y in points]
        if close and pts and pts[0] != pts[-1]:
            pts.append(pts[0])
        return msp.add_lwpolyline(pts, dxfattribs=_attribs(layer, color, linetype=linetype, lw=lw))
    except Exception:
        return None


def rectangle(msp, x: float, y: float, w: float, h: float,
              layer: str = "STRUC-OUTLINE",
              color: int | None = None, lw: int | None = None) -> Any:
    """Draw a closed rectangle with bottom-left corner at (x, y)."""
    pts = [(x, y), (x+w, y), (x+w, y+h), (x, y+h), (x, y)]
    return polyline(msp, pts, layer=layer, color=color, lw=lw)


def circle(msp, cx: float, cy: float, r: float,
           layer: str = "STRUC-OUTLINE", color: int | None = None) -> Any:
    """Draw a circle centred at (cx, cy) with radius r."""
    try:
        return msp.add_circle((cx, cy), r, dxfattribs=_attribs(layer, color))
    except Exception:
        return None


def arc(msp, cx: float, cy: float, r: float,
        start_deg: float, end_deg: float,
        layer: str = "STRUC-OUTLINE", color: int | None = None) -> Any:
    """Draw an arc centred at (cx, cy)."""
    try:
        return msp.add_arc((cx, cy), r, start_deg, end_deg,
                           dxfattribs=_attribs(layer, color))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------

def text(msp, content: str, x: float, y: float, height: float = 0.5,
         layer: str = "TEXT-GENERAL", rotation: float = 0.0,
         color: int | None = None, halign: str = "LEFT") -> Any:
    """Add a simple text entity."""
    try:
        align_map = {"LEFT": 0, "CENTER": 4, "RIGHT": 2,
                     "MIDDLE": 5, "TOP_LEFT": 1}
        ha = align_map.get(halign.upper(), 0)
        attribs = _attribs(layer, color)
        attribs.update({"height": float(height)})
        if rotation:
            attribs["rotation"] = float(rotation)
        t = msp.add_text(str(content), dxfattribs=attribs)
        if ha:
            t.set_placement((x, y), align=ha)
        else:
            t.dxf.insert = (float(x), float(y))
        return t
    except Exception:
        return None


def mtext(msp, content: str, x: float, y: float, width: float,
          height: float = 0.5, layer: str = "TEXT-GENERAL",
          color: int | None = None) -> Any:
    """Add an MTEXT (multi-line text) entity."""
    try:
        attribs = _attribs(layer, color)
        attribs["char_height"] = float(height)
        attribs["width"] = float(width)
        attribs["insert"] = (float(x), float(y))
        return msp.add_mtext(str(content), dxfattribs=attribs)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Hatching
# ---------------------------------------------------------------------------

def hatch_rect(msp, x: float, y: float, w: float, h: float,
               pattern: str = "ANSI31", scale: float = 1.0,
               layer: str = "STRUC-HATCHING", color: int | None = None) -> Any:
    """Fill a rectangle with a hatch pattern (concrete = ANSI31, earth = ANSI37)."""
    try:
        hatch = msp.add_hatch(dxfattribs=_attribs(layer, color))
        hatch.set_pattern_fill(pattern, scale=scale)
        pts = [(x, y), (x+w, y), (x+w, y+h), (x, y+h)]
        hatch.paths.add_polyline_path(pts, is_closed=True)
        return hatch
    except Exception:
        return None


def hatch_poly(msp, points: Pts, pattern: str = "ANSI31",
               scale: float = 1.0, layer: str = "STRUC-HATCHING",
               color: int | None = None) -> Any:
    """Fill an arbitrary polygon with a hatch pattern."""
    try:
        hatch = msp.add_hatch(dxfattribs=_attribs(layer, color))
        hatch.set_pattern_fill(pattern, scale=scale)
        pts = [(float(x), float(y)) for x, y in points]
        hatch.paths.add_polyline_path(pts, is_closed=True)
        return hatch
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Dimension helpers
# ---------------------------------------------------------------------------

def dim_linear_h(msp, x1: float, y1: float, x2: float, y2: float,
                 dim_y: float, label: str | None = None,
                 layer: str = "DIM-LINEAR",
                 text_height: float = 0.35) -> Any:
    """Horizontal linear dimension between (x1,y1) and (x2,y2).

    *dim_y* is the y-position of the dimension line.
    """
    try:
        # Extension lines
        line(msp, (x1, y1), (x1, dim_y), layer=layer)
        line(msp, (x2, y2), (x2, dim_y), layer=layer)
        # Dimension line with arrowheads (simple tick)
        line(msp, (x1, dim_y), (x2, dim_y), layer=layer)
        # Arrowhead ticks
        tick = text_height * 0.8
        line(msp, (x1, dim_y - tick), (x1, dim_y + tick), layer=layer)
        line(msp, (x2, dim_y - tick), (x2, dim_y + tick), layer=layer)
        # Label
        display = label if label else f"{abs(x2 - x1):.3f}"
        cx = (x1 + x2) / 2
        text(msp, display, cx, dim_y + text_height * 0.3,
             height=text_height, layer="DIM-LINEAR", halign="CENTER")
    except Exception:
        return None


def dim_linear_v(msp, x1: float, y1: float, x2: float, y2: float,
                 dim_x: float, label: str | None = None,
                 layer: str = "DIM-LINEAR",
                 text_height: float = 0.35) -> Any:
    """Vertical linear dimension between (x1,y1) and (x2,y2).

    *dim_x* is the x-position of the dimension line.
    """
    try:
        line(msp, (x1, y1), (dim_x, y1), layer=layer)
        line(msp, (x2, y2), (dim_x, y2), layer=layer)
        line(msp, (dim_x, y1), (dim_x, y2), layer=layer)
        tick = text_height * 0.8
        line(msp, (dim_x - tick, y1), (dim_x + tick, y1), layer=layer)
        line(msp, (dim_x - tick, y2), (dim_x + tick, y2), layer=layer)
        display = label if label else f"{abs(y2 - y1):.3f}"
        cy = (y1 + y2) / 2
        text(msp, display, dim_x + text_height * 0.5, cy,
             height=text_height, layer="DIM-LINEAR", rotation=90)
    except Exception:
        return None


def level_tag(msp, x: float, y: float, rl: float,
              text_height: float = 0.35, layer: str = "DIM-LEVEL") -> None:
    """Draw a reduced-level (RL) tag: horizontal tick + RL value."""
    try:
        w = text_height * 3
        line(msp, (x - w, y), (x + w, y), layer=layer)
        line(msp, (x, y), (x, y - text_height * 0.5), layer=layer)
        label = f"RL {rl:.3f}"
        text(msp, label, x + w * 1.1, y, height=text_height,
             layer="TEXT-LEVEL")
    except Exception:
        pass


def chainage_tag(msp, x: float, y: float, ch_km: float,
                 text_height: float = 0.35, layer: str = "CIVIL-CHAINAGE") -> None:
    """Draw a chainage marker: vertical tick + CH label."""
    try:
        tick_h = text_height * 1.5
        line(msp, (x, y), (x, y - tick_h), layer=layer)
        label = f"CH {ch_km:.3f}"
        text(msp, label, x, y - tick_h - text_height * 0.3,
             height=text_height, layer="DIM-CHAINAGE", rotation=90)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Symbol helpers
# ---------------------------------------------------------------------------

def north_arrow(msp, cx: float, cy: float, size: float = 2.0,
                layer: str = "SYM-NORTHARROW") -> None:
    """Draw a simple north arrow centred at (cx, cy)."""
    try:
        tip   = (cx, cy + size)
        left  = (cx - size * 0.35, cy - size * 0.5)
        right = (cx + size * 0.35, cy - size * 0.5)
        base  = (cx, cy - size * 0.2)
        # Left half filled (dark)
        hatch_poly(msp, [tip, left, base], pattern="SOLID",
                   scale=1.0, layer=layer, color=7)
        # Outline
        polyline(msp, [tip, left, base, right, tip],
                 layer=layer, close=False)
        text(msp, "N", cx, cy + size + size * 0.3,
             height=size * 0.45, layer=layer, halign="CENTER")
    except Exception:
        pass


def section_mark(msp, x: float, y: float, label: str = "A",
                 size: float = 1.0, layer: str = "SYM-SECTIONMARK") -> None:
    """Draw a section-cut marker: circle + label."""
    try:
        circle(msp, x, y, size * 0.6, layer=layer, color=1)
        text(msp, label, x, y - size * 0.2,
             height=size * 0.6, layer=layer, halign="CENTER")
    except Exception:
        pass


def section_arrow(msp, x_line: float, y1: float, y2: float, label: str = "A-A",
                  size: float = 2.0, text_height: float = 0.35,
                  layer: str = "STRUC-SECTION") -> None:
    """IRC SP:55 Clause 11.4 section cut indicator.

    Draws a vertical cut line from (x_line, y1) to (x_line, y2) with thickened
    heavy end-ticks (per IRC Clause 11.4.3), arrowheads pointing in the
    viewing direction (both ends), and the cut label ``A-A`` / ``B-B`` etc.
    centred above the cut line on the STRUC-SECTION layer.
    """
    try:
        # Vertical cut line (dash-long-short on section layer)
        line(msp, (x_line, y1), (x_line, y2), layer=layer, lw=50,
             linetype="DASHED", color=1)

        # Heavy end-tick rectangles at y1 and y2 (IRC 11.4 — 3 mm × 3 mm plot)
        tick_w = size * 0.15
        tick_h = size * 0.15
        for yy in (y1, y2):
            rectangle(msp, x_line - tick_w/2, yy - tick_h/2, tick_w, tick_h,
                      layer=layer, color=1)

        # Arrowheads (simple filled triangle hatches) pointing outward from
        # the cut (direction the viewer is looking from).
        arrow_L = size * 0.8
        arrow_W = size * 0.35
        # Top arrow (pointing up)
        tri_top = [(x_line - arrow_W/2, y1 + tick_h/2),
                   (x_line + arrow_W/2, y1 + tick_h/2),
                   (x_line,            y1 + tick_h/2 + arrow_L)]
        hatch_poly(msp, tri_top, pattern="SOLID", scale=1.0,
                   layer=layer, color=1)
        # Bottom arrow (pointing down)
        tri_bot = [(x_line - arrow_W/2, y2 - tick_h/2),
                   (x_line + arrow_W/2, y2 - tick_h/2),
                   (x_line,            y2 - tick_h/2 - arrow_L)]
        hatch_poly(msp, tri_bot, pattern="SOLID", scale=1.0,
                   layer=layer, color=1)

        # Cut label (e.g. "A-A") centered above top arrow, 1 size spacing
        text(msp, label, x_line, y1 + tick_h/2 + arrow_L + size * 0.35,
             height=text_height * 1.2, layer="TEXT-HEADER",
             halign="CENTER", color=1)
    except Exception:
        pass


def scale_bar(msp, x: float, y: float, scale_denom: int,
              segments: int = 5, seg_len_m: float = 5.0,
              layer: str = "SYM-SCALE", text_height: float = 0.35) -> None:
    """Draw a graphic scale bar."""
    try:
        total = segments * seg_len_m
        rectangle(msp, x, y, total, text_height * 0.8, layer=layer)
        # Alternating fill
        for i in range(segments):
            sx = x + i * seg_len_m
            if i % 2 == 0:
                hatch_rect(msp, sx, y, seg_len_m, text_height * 0.8,
                           pattern="SOLID", scale=1.0, layer=layer, color=7)
        # Labels
        for i in range(segments + 1):
            val = i * seg_len_m
            text(msp, f"{val:.0f}m", x + i * seg_len_m,
                 y - text_height * 1.2, height=text_height,
                 layer="TEXT-GENERAL", halign="CENTER")
        text(msp, f"1 : {scale_denom}", x + total / 2,
             y + text_height * 1.5, height=text_height,
             layer="TEXT-GENERAL", halign="CENTER")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Layout cursor — relative-coordinate tracking
# ---------------------------------------------------------------------------

class LayoutCursor:
    """Mutable (x, y) "drawing pen" with stack and convenience draw calls.

    Rationale
    ---------
    Replaces brittle, hard-coded absolute coordinate lists in drawing sheet
    modules with relative ``advance`` / ``push`` / ``pop`` sequences so that
    a single spacing change (e.g. label height, row pitch) propagates to every
    affected position automatically — eliminating the regression risk of
    editing many scattered ``(x, y)`` literals by hand.

    All mutable methods return ``self`` so callers can chain::

        c = LayoutCursor(10.0, 5.0)
        c.advance_y(2.0).rect(msp, 3.0, 1.5).advance_y(1.0)
    """

    __slots__ = ("_x", "_y", "_stack")

    def __init__(self, x: float = 0.0, y: float = 0.0) -> None:
        self._x = float(x)
        self._y = float(y)
        self._stack: list[tuple[float, float]] = []

    # ------------------------------------------------------------------
    # Position introspection
    # ------------------------------------------------------------------
    @property
    def x(self) -> float:
        return self._x

    @property
    def y(self) -> float:
        return self._y

    @property
    def pos(self) -> Pt2:
        return (self._x, self._y)

    # ------------------------------------------------------------------
    # Absolute movement
    # ------------------------------------------------------------------
    def move_to(self, x: float, y: float) -> LayoutCursor:
        self._x = float(x)
        self._y = float(y)
        return self

    # ------------------------------------------------------------------
    # Relative movement
    # ------------------------------------------------------------------
    def move(self, dx: float = 0.0, dy: float = 0.0) -> LayoutCursor:
        self._x += float(dx)
        self._y += float(dy)
        return self

    def advance_x(self, dx: float) -> LayoutCursor:
        self._x += float(dx)
        return self

    def advance_y(self, dy: float) -> LayoutCursor:
        self._y += float(dy)
        return self

    # ------------------------------------------------------------------
    # Stack — save / restore cursor for nested sub-layouts
    # ------------------------------------------------------------------
    def push(self) -> LayoutCursor:
        self._stack.append((self._x, self._y))
        return self

    def pop(self) -> LayoutCursor:
        if not self._stack:
            raise IndexError("LayoutCursor.pop() on empty push/pop stack")
        self._x, self._y = self._stack.pop()
        return self

    # ------------------------------------------------------------------
    # Cursor-aware primitive shortcuts (draw + advance in one call)
    # ------------------------------------------------------------------
    def rect(self, msp, w: float, h: float,
             layer: str = "STRUC-OUTLINE",
             color: int | None = None,
             lw: int | None = None) -> LayoutCursor:
        """Draw a rectangle with its BL corner at the current cursor position.

        The cursor is **not** advanced — callers explicitly chain
        ``advance_x(w)`` / ``advance_y(h)`` when needed.
        """
        rectangle(msp, self._x, self._y, w, h,
                  layer=layer, color=color, lw=lw)
        return self

    def hatch(self, msp, w: float, h: float,
              pattern: str = "ANSI31", scale: float = 1.0,
              layer: str = "STRUC-HATCHING",
              color: int | None = None) -> LayoutCursor:
        hatch_rect(msp, self._x, self._y, w, h, pattern=pattern,
                   scale=scale, layer=layer, color=color)
        return self

    def label(self, msp, content: str,
              height: float = 0.35,
              layer: str = "TEXT-GENERAL",
              halign: str = "LEFT",
              color: int | None = None,
              dx: float = 0.0, dy: float = 0.0) -> LayoutCursor:
        """Place text at cursor + (dx, dy) offset.  Cursor does not move."""
        text(msp, str(content), self._x + dx, self._y + dy,
             height=height, layer=layer, halign=halign, color=color)
        return self

    def line_to(self, msp, dx: float, dy: float,
                layer: str = "STRUC-OUTLINE",
                color: int | None = None,
                lw: int | None = None) -> LayoutCursor:
        """Draw a line from current cursor position to ``cursor + (dx, dy)``.

        Leaves the cursor at the **end** of the drawn line.
        """
        end = (self._x + dx, self._y + dy)
        line(msp, self.pos, end, layer=layer, color=color, lw=lw)
        self._x, self._y = end
        return self


__all__ = [
    "line", "polyline", "rectangle", "circle", "arc",
    "text", "mtext",
    "hatch_rect", "hatch_poly",
    "dim_linear_h", "dim_linear_v", "level_tag", "chainage_tag",
    "north_arrow", "section_mark", "section_arrow", "scale_bar",
    "LayoutCursor",
]
