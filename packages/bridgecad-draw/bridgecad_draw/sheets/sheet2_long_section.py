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

from bridgecad_draw.coordinates import m, model_text_height_mm, to_model_space
from bridgecad_draw.dxf_engine import new_sheet
from bridgecad_draw.primitives import text as _text
from bridgecad_draw.titleblocks import draw_sheet_frame

SHEET = "sheet2_long_section"
LABEL_FORMAT = "{:.3f}"
TICK_PITCH_M = 5.0
PAPER_TEXT_MM = 2.5
DIM_DIMSTYLE = "EZDXF"  # the style ezdxf's drafting setup defines


class _Layered:
    """A modelspace that knows which layer the current block is drawing on."""

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
    if abs(x2 - x1) >= abs(y2 - y1):  # horizontal
        ms.add_line((x1, y1 - tick), (x1, y1 + tick))
        ms.add_line((x2, y2 - tick), (x2, y2 + tick))
        anchor = ((x1 + x2) / 2.0, y1 + height * 0.25)
    else:  # vertical
        ms.add_line((x1 - tick, y1), (x1 + tick, y1))
        ms.add_line((x2 - tick, y2), (x2 + tick, y2))
        anchor = (x1 + height * 0.25, (y1 + y2) / 2.0)
    label(ms, anchor, text, height=height)


def segment(ms, p1, p2) -> None:
    """A line, unless it would be zero-length — which the contract rejects."""
    (x1, y1), (x2, y2) = (float(p1[0]), float(p1[1])), (float(p2[0]), float(p2[1]))
    if abs(x2 - x1) < 1e-6 and abs(y2 - y1) < 1e-6:
        return
    ms.add_line((x1, y1), (x2, y2))


def box(ms, x: float, y: float, w: float, h: float) -> None:
    """A closed rectangle as four lines, degenerate edges dropped."""
    segment(ms, (x, y), (x + w, y))
    segment(ms, (x + w, y), (x + w, y + h))
    segment(ms, (x + w, y + h), (x, y + h))
    segment(ms, (x, y + h), (x, y))


def real_dim(ms, p1, p2, *, base, angle: float, height: float, text: str | None = None) -> None:
    """A real DXF ``DIMENSION`` entity, on the DIM layer.

    ``dim_linear`` above draws a line and a text label; the DXF contract counts
    ``DIMENSION`` entities, which only ``add_linear_dim(...).render()`` emits.
    Both are kept: the labels read on the drawing, the entities satisfy the
    contract. ``angle`` is 0 for a horizontal dimension line and 90 for a
    vertical one.
    """
    dim = ms.add_linear_dim(
        base=base,
        p1=p1,
        p2=p2,
        angle=angle,
        dimstyle=DIM_DIMSTYLE,
        dxfattribs={"layer": "DIM"},
        override={"dimtxt": height * 0.6, "dimtxsty": "BRIDGE_STD"},
    )
    if text is not None:
        dim.set_text(text)
    dim.render()


def build(project):
    """Build the longitudinal section for *project*; returns the DXF document."""
    doc, msp = new_sheet("S2 Long Section")
    frame_w, _frame_h = draw_sheet_frame(msp, SHEET, sheet_index=2)

    ms = _Layered(msp)
    total = float(project.geometry.total_length_m)
    h_text = model_text_height_mm(SHEET, PAPER_TEXT_MM)

    # ── deck line ────────────────────────────────────────────────────────────
    with layer(ms, "DECK"):
        ms.add_line(
            (X(0.0), Y(project.levels.deck_level_m)), (X(total), Y(project.levels.deck_level_m))
        )

    # ── water levels: line on GRID, label on TEXT ────────────────────────────
    # Label format is 3 dp. "HFL 104.5" is ambiguous on a section where 50 mm of
    # level is a real difference and 3 dp is what the GAD sheets use.
    for name, lv in (("HFL", project.levels.hfl_m), ("LWL", project.levels.lwl_m)):
        with layer(ms, "GRID"):
            level_line(ms, X(0.0), X(total), Y(lv))
        with layer(ms, "TEXT"):
            label(
                ms,
                (X(total) + h_text * 0.5, Y(lv) - h_text * 0.5),
                f"{name} {LABEL_FORMAT.format(lv)}",
                height=h_text,
            )

    # ── founding level, hidden because it is below the section plane ─────────
    with layer(ms, "HIDD"):
        ms.add_line(
            (X(0.0), Y(project.levels.founding_level_m)),
            (X(total), Y(project.levels.founding_level_m)),
        )

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
            ms.add_line(
                (X(ch), Y(project.levels.founding_level_m) - h_text * 2),
                (X(ch), Y(project.levels.deck_level_m) + h_text * 2),
            )
        with layer(ms, "TEXT"):
            label(
                ms,
                (X(ch) - h_text * 0.5, Y(project.levels.deck_level_m) + h_text * 2.5),
                f"P{idx}",
                height=h_text,
            )

    # ── chainage ticks along the deck ────────────────────────────────────────
    n_ticks = int(total // TICK_PITCH_M) + 1
    for i in range(n_ticks):
        ch = i * TICK_PITCH_M
        with layer(ms, "GRID"):
            chainage_tick(
                ms,
                X(ch),
                Y(project.levels.deck_level_m),
                Y(project.levels.deck_level_m) + h_text * 1.5,
            )
        with layer(ms, "TEXT"):
            label(
                ms,
                (X(ch), Y(project.levels.deck_level_m) + h_text * 2.0),
                f"{LABEL_FORMAT.format(ch)}",
                height=h_text,
            )

    # ── dimensions: overall, per span, and the three levels ──────────────────
    with layer(ms, "DIM"):
        dim_linear(
            ms,
            (X(0.0), Y(project.levels.founding_level_m) - h_text * 5),
            (X(total), Y(project.levels.founding_level_m) - h_text * 5),
            text=f"{total:.3f} m",
            height=h_text,
        )
        bounds = [0.0, *piers, total]
        for a, b in itertools.pairwise(bounds):
            dim_linear(
                ms,
                (X(a), Y(project.levels.founding_level_m) - h_text * 3.5),
                (X(b), Y(project.levels.founding_level_m) - h_text * 3.5),
                text=f"{b - a:.3f}",
                height=h_text,
            )
        # The level staff sits just INSIDE the datum, not outside it. Under the
        # shared coordinate contract the datum is the frame corner (chainage 0 is
        # the paper's left edge), so a gutter to its left is off the sheet, and
        # clause 7 rejects it. The spec's `X(0.0) - h_text * 3` predates that
        # contract — see the module docstring.
        staff_x = X(0.0) + h_text * 0.5
        for name, lv in (
            ("DECK", project.levels.deck_level_m),
            ("HFL", project.levels.hfl_m),
            ("LWL", project.levels.lwl_m),
        ):
            dim_linear(
                ms,
                (staff_x, Y(project.levels.founding_level_m)),
                (staff_x, Y(lv)),
                text=f"{name} {LABEL_FORMAT.format(lv)}",
                height=h_text,
            )

    # ── superstructure build-up: wearing coat, deck slab, parapet ───────────
    # Everything is read off the project, so a thicker slab or a taller parapet
    # moves the lines rather than restating a number in the sheet.
    sup = project.superstructure
    deck = project.levels.deck_level_m
    hfl = project.levels.hfl_m
    lwl = project.levels.lwl_m
    founding = project.levels.founding_level_m
    slab_m = float(sup.deck_thickness_mm) / 1000.0
    wc_m = float(sup.wearing_coat_thickness_mm or 0) / 1000.0
    parapet_m = float(sup.parapet_height_mm or 0) / 1000.0
    wc_under = deck - wc_m  # underside of the wearing coat
    soffit = deck - wc_m - slab_m  # deck slab soffit

    with layer(ms, "SUPER-DECK"):
        segment(ms, (X(0.0), Y(soffit)), (X(total), Y(soffit)))
        segment(ms, (X(0.0), Y(soffit)), (X(0.0), Y(deck)))
        segment(ms, (X(total), Y(soffit)), (X(total), Y(deck)))
    with layer(ms, "SUPER-WEARING"):
        segment(ms, (X(0.0), Y(wc_under)), (X(total), Y(wc_under)))
    if parapet_m > 0:
        parapet_w = h_text * 1.2
        with layer(ms, "SUPER-PARAPET"):
            box(ms, X(0.0), Y(deck), parapet_w, m(parapet_m))
            box(ms, X(total) - parapet_w, Y(deck), parapet_w, m(parapet_m))

    # ── abutments, pile caps and piles below the founding level ─────────────
    ground_levels = [lv for _, lv in project.ground_profile]
    ground_min = min(ground_levels)
    abut_w = h_text * 2.0
    cap_h = h_text * 1.0
    # Embedment comes from the project's pile length when it declares one, and
    # is clipped to the frame: a level the fixture puts above the deck (a
    # brownfield site, or a synthetic case) must not push the foundation off
    # the sheet.
    pile_len_m = float(getattr(project.foundation_details, "pile_length_m", None) or 0.0)
    embed_m = pile_len_m if pile_len_m > 0 else max(0.0, ground_min - founding)
    room_mm = max(0.0, Y(founding) - cap_h - h_text * 2.0)
    embed_mm = min(m(embed_m), room_mm)

    with layer(ms, "SUB-ABUT"):
        for x0 in (X(0.0), X(total) - abut_w):
            box(ms, x0, Y(founding), abut_w, Y(soffit) - Y(founding))
    with layer(ms, "FOUND-CAP"):
        for x0 in (X(0.0), X(total) - abut_w):
            box(ms, x0, Y(founding) - cap_h, abut_w, cap_h)
    with layer(ms, "FOUND-PILE"):
        if embed_mm > 0:
            for x0 in (X(0.0), X(total) - abut_w):
                for frac in (0.25, 0.75):
                    xc = x0 + abut_w * frac
                    segment(
                        ms,
                        (xc, Y(founding) - cap_h),
                        (xc, Y(founding) - cap_h - embed_mm),
                    )
    with layer(ms, "HTCH"):
        for x0 in (X(0.0), X(total) - abut_w):
            for k in range(1, 5):
                t = k / 5.0
                segment(
                    ms,
                    (x0, Y(founding) + t * (Y(soffit) - Y(founding))),
                    (x0 + abut_w * t, Y(founding)),
                )

    # ── bearings: a schematic pad at every support ──────────────────────────
    # One pad per support — both abutments plus every pier — so the count
    # follows the span count (a 3-span bridge shows four, a 1-span bridge two).
    # Clamped to the frame because chainage 0 is the paper's left edge.
    bearing_h = h_text * 0.6
    bearing_w = h_text * 0.9
    supports = [0.0, *piers, total]
    with layer(ms, "SUB-BEARING"):
        for ch in supports:
            bx = min(max(X(ch) - bearing_w / 2.0, 0.0), frame_w - bearing_w)
            box(ms, bx, Y(soffit) - bearing_h, bearing_w, bearing_h)

    # ── flow direction indicator ────────────────────────────────────────────
    # A long section is an elevation, so the orientation note is the direction
    # of flow rather than a north point. Drawn above the deck, clear of the
    # level tags and the chainage axis.
    y_flow = Y(deck) + h_text * 8.0
    fx0, fx1 = X(0.0), X(total)
    with layer(ms, "SYM-NORTHARROW"):
        segment(ms, (fx0, y_flow), (fx1, y_flow))
        head = h_text * 1.2
        segment(ms, (fx1, y_flow), (fx1 - head, y_flow + head * 0.5))
        segment(ms, (fx1, y_flow), (fx1 - head, y_flow - head * 0.5))
    with layer(ms, "TEXT"):
        label(
            ms,
            ((fx0 + fx1) / 2.0 - h_text * 3.0, y_flow + h_text * 1.2),
            "FLOW DIRECTION",
            height=h_text,
        )
        label(ms, (fx0, y_flow - h_text * 1.8), "UPSTREAM", height=h_text)
        label(ms, (fx1 - h_text * 5.0, y_flow - h_text * 1.8), "DOWNSTREAM", height=h_text)

    # ── annotations: chainage grid, deck level, ground and founding levels ──
    with layer(ms, "TEXT"):
        label(ms, (X(0.0), Y(deck) + h_text * 3.6), "CHAINAGE (m)", height=h_text)
        label(
            ms,
            (X(0.0), Y(deck) + h_text * 4.6),
            f"DECK LEVEL {LABEL_FORMAT.format(deck)}",
            height=h_text,
        )
        label(
            ms,
            (X(0.0) + h_text * 0.5, Y(ground_min) + h_text * 0.5),
            f"GL {LABEL_FORMAT.format(ground_min)}",
            height=h_text,
        )
        label(
            ms,
            (X(0.0) + h_text * 0.5, Y(founding) + h_text * 0.5),
            f"FOUNDING LEVEL {LABEL_FORMAT.format(founding)}",
            height=h_text,
        )
        # support labels: A1 / A2 at the abutments, P1..Pn at the piers (above)
        label(ms, (X(0.0) + h_text * 0.5, Y(soffit) - h_text * 1.8), "A1", height=h_text)
        label(
            ms,
            (X(total) - abut_w - h_text * 2.5, Y(soffit) - h_text * 1.8),
            "A2",
            height=h_text,
        )
    with layer(ms, "CL"):
        for x0 in (X(0.0), X(total) - abut_w):
            label(ms, (x0, Y(deck) + h_text * 5.6), "CL", height=h_text)

    # ── native dimensions: the DIMENSION entities the contract counts ──────
    y_overall = Y(founding) - h_text * 7.0
    y_spans = Y(founding) - h_text * 9.0
    y_chain = Y(founding) - h_text * 11.0

    real_dim(
        ms,
        (X(0.0), y_overall),
        (X(total), y_overall),
        base=(X(total) / 2.0, y_overall - h_text * 1.6),
        angle=0.0,
        height=h_text,
        text=f"{total:.3f} m",
    )
    bounds = [0.0, *piers, total]
    for a, b in itertools.pairwise(bounds):
        xa, xb = X(a), X(b)
        real_dim(
            ms,
            (xa, y_spans),
            (xb, y_spans),
            base=((xa + xb) / 2.0, y_spans - h_text * 1.6),
            angle=0.0,
            height=h_text,
            text=f"{b - a:.3f}",
        )
    marks = sorted({i * TICK_PITCH_M for i in range(n_ticks)} | {total})
    for a, b in itertools.pairwise(marks):
        xa, xb = X(a), X(b)
        real_dim(
            ms,
            (xa, y_chain),
            (xb, y_chain),
            base=((xa + xb) / 2.0, y_chain - h_text * 1.6),
            angle=0.0,
            height=h_text,
            text=f"{b - a:.3f}",
        )

    # right-hand level staff: every level measured from the founding level
    staff_dim_x = X(total) + h_text * 2.0
    for lv in (deck, hfl, lwl):
        real_dim(
            ms,
            (staff_dim_x, Y(founding)),
            (staff_dim_x, Y(lv)),
            base=(staff_dim_x + h_text * 1.2, (Y(founding) + Y(lv)) / 2.0),
            angle=90.0,
            height=h_text,
            text=f"{lv - founding:.3f}",
        )

    # structural thicknesses, on a second staff further right
    struct_dim_x = X(total) + h_text * 6.0
    for a, b in ((wc_under, deck), (soffit, wc_under), (deck, deck + parapet_m)):
        if b > a:
            real_dim(
                ms,
                (struct_dim_x, Y(a)),
                (struct_dim_x, Y(b)),
                base=(struct_dim_x + h_text * 1.2, (Y(a) + Y(b)) / 2.0),
                angle=90.0,
                height=h_text,
                text=f"{(b - a) * 1000.0:.0f}",
            )
    if soffit > hfl:  # vertical clearance above the flood level
        real_dim(
            ms,
            (struct_dim_x, Y(hfl)),
            (struct_dim_x, Y(soffit)),
            base=(struct_dim_x + h_text * 1.2, (Y(hfl) + Y(soffit)) / 2.0),
            angle=90.0,
            height=h_text,
            text=f"{soffit - hfl:.3f}",
        )
    if ground_min > founding:  # founding depth below natural ground
        real_dim(
            ms,
            (struct_dim_x, Y(founding)),
            (struct_dim_x, Y(ground_min)),
            base=(struct_dim_x + h_text * 1.2, (Y(founding) + Y(ground_min)) / 2.0),
            angle=90.0,
            height=h_text,
            text=f"{ground_min - founding:.3f}",
        )

    # abutment height and pile-cap thickness, on the A1 side
    abut_dim_x = X(0.0) + abut_w + h_text * 1.5
    real_dim(
        ms,
        (abut_dim_x, Y(founding)),
        (abut_dim_x, Y(soffit)),
        base=(abut_dim_x + h_text * 1.2, (Y(founding) + Y(soffit)) / 2.0),
        angle=90.0,
        height=h_text,
        text=f"{soffit - founding:.3f}",
    )
    real_dim(
        ms,
        (abut_dim_x, Y(founding) - cap_h),
        (abut_dim_x, Y(founding)),
        base=(abut_dim_x + h_text * 1.2, Y(founding) - cap_h / 2.0),
        angle=90.0,
        height=h_text,
        text=f"{cap_h:.0f}",
    )

    return doc
