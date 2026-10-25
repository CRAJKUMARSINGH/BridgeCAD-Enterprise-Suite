"""bridgecad_draw.sheets.sheet2_long_section — the longitudinal section, in memory.

Wing-16. The body below is the drawing: it reads the project and never restates
the project's numbers — move a level and the line moves with it.

Everything the body names is supplied by this header. Two of those names are
worth stating out loud:

* ``h_text`` is the MODEL height that plots to 2.5 mm on paper. At 1:100 that is
  250 mm of model text, not 2.5 — see ``coordinates.model_text_height_mm``.
* ``layer()`` mutates the layer-aware modelspace it is handed. ezdxf stamps
  layer "0" on every new entity (``DEFAULT_ATTRIBS``) and consults no "current
  layer", so an entity drawn without an explicit layer is a defect the contract
  tests reject.

TWO RE-BASINGS AGAINST THE WING-11 COORDINATE CONTRACT
    The spec's body was written against absolute chainage/level coordinates. The
    repo's contract (``coordinates.py``) re-bases every sheet on its own declared
    datum and draws the frame corner at (0, 0), so two of the body's anchors have
    to be re-based or they leave the sheet:

    1. The vertical level dimensions run from the FOUNDING level up, not from RL
       0. Sheet 2's datum is RL 90, so RL 0 is 90 m below the frame: a dimension
       to it is not a dimension, it is the whole vertical scale.
    2. The same staff sits just INSIDE the datum, not in a gutter to its left.
       Chainage 0 is the paper's left edge, so a left gutter is off the sheet and
       clause 7 of the contract rejects it.

    Both are the same correction: an anchor written for absolute space is re-based
    onto the shared frame. Nothing else in the body is altered.
"""
from __future__ import annotations

import itertools
from contextlib import contextmanager

from bridgecad_draw.coordinates import model_text_height_mm, to_model_space
from bridgecad_draw.dxf_engine import new_sheet
from bridgecad_draw.primitives import text as _text
from bridgecad_draw.titleblocks import draw_sheet_frame

SHEET = "sheet2_long_section"
LABEL_FORMAT = "{:.3f}"
TICK_PITCH_M = 5.0
PAPER_TEXT_MM = 2.5


class _Layered:
    """A modelspace that knows which layer the current block is drawing on."""

    __slots__ = ("_msp", "layer_name")

    def __init__(self, msp, layer_name: str = "TEXT"):
        self._msp = msp
        self.layer_name = layer_name

    def _stamp(self, dxfattribs):
        attribs = dict(dxfattribs or {})
        attribs["layer"] = self.layer_name      # forced: the enclosing block wins
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


# ── coordinate contract ──────────────────────────────────────────────────────
def X(chainage_m: float) -> float:
    """Chainage (m, from A1) -> model x, in millimetres."""
    return to_model_space(SHEET, chainage_m, 0.0)[0]


def Y(level_m: float) -> float:
    """Reduced level (m) -> model y, in millimetres."""
    return to_model_space(SHEET, 0.0, level_m)[1]


# ── annotation primitives the body draws with ────────────────────────────────
def level_line(ms, x0: float, x1: float, y: float) -> None:
    ms.add_line((x0, y), (x1, y))


def label(ms, position, content: str, *, height: float) -> None:
    _text(ms, content, position[0], position[1], height=height, halign="LEFT")


def chainage_tick(ms, x: float, y0: float, y1: float) -> None:
    ms.add_line((x, y0), (x, y1))


def dim_linear(ms, p1, p2, *, text: str, height: float) -> None:
    """A linear dimension drawn between two points, on the enclosing layer."""
    (x1, y1), (x2, y2) = (float(p1[0]), float(p1[1])), (float(p2[0]), float(p2[1]))
    ms.add_line((x1, y1), (x2, y2))
    tick = height * 0.3
    if abs(x2 - x1) >= abs(y2 - y1):                    # horizontal
        ms.add_line((x1, y1 - tick), (x1, y1 + tick))
        ms.add_line((x2, y2 - tick), (x2, y2 + tick))
        anchor = ((x1 + x2) / 2.0, y1 + height * 0.25)
    else:                                               # vertical
        ms.add_line((x1 - tick, y1), (x1 + tick, y1))
        ms.add_line((x2 - tick, y2), (x2 + tick, y2))
        anchor = (x1 + height * 0.25, (y1 + y2) / 2.0)
    label(ms, anchor, text, height=height)


def build(project):
    """Build the longitudinal section for *project*; returns the DXF document."""
    doc, msp = new_sheet("S2 Long Section")
    draw_sheet_frame(msp, SHEET, sheet_index=2)

    ms = _Layered(msp)
    total = float(project.geometry.total_length_m)
    h_text = model_text_height_mm(SHEET, PAPER_TEXT_MM)

    # ── deck line ────────────────────────────────────────────────────────────
    with layer(ms, "DECK"):
        ms.add_line((X(0.0), Y(project.levels.deck_level_m)),
                    (X(total), Y(project.levels.deck_level_m)))

    # ── water levels: line on GRID, label on TEXT ────────────────────────────
    # Label format is 3 dp. "HFL 104.5" is ambiguous on a section where 50 mm of
    # level is a real difference and 3 dp is what the GAD sheets use.
    for name, lv in (("HFL", project.levels.hfl_m), ("LWL", project.levels.lwl_m)):
        with layer(ms, "GRID"):
            level_line(ms, X(0.0), X(total), Y(lv))
        with layer(ms, "TEXT"):
            label(ms, (X(total) + h_text * 0.5, Y(lv) - h_text * 0.5),
                  f"{name} {LABEL_FORMAT.format(lv)}", height=h_text)

    # ── founding level, hidden because it is below the section plane ─────────
    with layer(ms, "HIDD"):
        ms.add_line((X(0.0), Y(project.levels.founding_level_m)),
                    (X(total), Y(project.levels.founding_level_m)))

    # ── natural ground, dashed ───────────────────────────────────────────────
    with layer(ms, "GRND"):
        ground = project.ground_profile  # [(chainage_m, level_m), ...]
        for (x0, y0), (x1, y1) in itertools.pairwise(ground):
            ms.add_line((X(x0), Y(y0)), (X(x1), Y(y1)), dxfattribs={"linetype": "DASHED"})

    # ── pier centrelines, one per pier ───────────────────────────────────────
    # Count is nspan - 1. This is the documented NSPAN bug's home.
    piers = project.geometry.pier_positions()
    for idx, ch in enumerate(piers, start=1):
        with layer(ms, "CL"):
            ms.add_line((X(ch), Y(project.levels.founding_level_m) - h_text * 2),
                        (X(ch), Y(project.levels.deck_level_m) + h_text * 2))
        with layer(ms, "TEXT"):
            label(ms, (X(ch) - h_text * 0.5, Y(project.levels.deck_level_m) + h_text * 2.5),
                  f"P{idx}", height=h_text)

    # ── chainage ticks along the deck ────────────────────────────────────────
    n_ticks = int(total // TICK_PITCH_M) + 1
    for i in range(n_ticks):
        ch = i * TICK_PITCH_M
        with layer(ms, "GRID"):
            chainage_tick(ms, X(ch), Y(project.levels.deck_level_m),
                          Y(project.levels.deck_level_m) + h_text * 1.5)
        with layer(ms, "TEXT"):
            label(ms, (X(ch), Y(project.levels.deck_level_m) + h_text * 2.0),
                  f"{LABEL_FORMAT.format(ch)}", height=h_text)

    # ── dimensions: overall, per span, and the three levels ──────────────────
    with layer(ms, "DIM"):
        dim_linear(ms, (X(0.0), Y(project.levels.founding_level_m) - h_text * 5),
                   (X(total), Y(project.levels.founding_level_m) - h_text * 5),
                   text=f"{total:.3f} m", height=h_text)
        bounds = [0.0, *piers, total]
        for a, b in itertools.pairwise(bounds):
            dim_linear(ms, (X(a), Y(project.levels.founding_level_m) - h_text * 3.5),
                       (X(b), Y(project.levels.founding_level_m) - h_text * 3.5),
                       text=f"{b - a:.3f}", height=h_text)
        # The level staff sits just INSIDE the datum, not outside it. Under the
        # shared coordinate contract the datum is the frame corner (chainage 0 is
        # the paper's left edge), so a gutter to its left is off the sheet, and
        # clause 7 rejects it. The spec's `X(0.0) - h_text * 3` predates that
        # contract — see the module docstring.
        staff_x = X(0.0) + h_text * 0.5
        for name, lv in (("DECK", project.levels.deck_level_m),
                         ("HFL", project.levels.hfl_m),
                         ("LWL", project.levels.lwl_m)):
            dim_linear(ms, (staff_x, Y(project.levels.founding_level_m)),
                       (staff_x, Y(lv)),
                       text=f"{name} {LABEL_FORMAT.format(lv)}", height=h_text)

    return doc
