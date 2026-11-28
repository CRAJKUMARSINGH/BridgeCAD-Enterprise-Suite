"""bridgecad_draw.sheets.superstructure_section — conditional superstructure renderer.

Fixes the two root causes of the 2026-01 drawing audit (GUIDE.md Part 5):

  R1  Girders were drawn (and labelled) on every deck, including solid slabs.
  R2  Girder centres were "spread evenly across the deck" so the drawn count
      matched the annotated count — instead of the modelled spacing with a
      real edge overhang.

This module is framework-free: it returns primitive specs (rects, dims, texts,
labels).  The sheet module renders them onto its canvas, so the behaviour is
unit-testable without ezdxf.

Usage inside a sheet module::

    from .superstructure_section import section_primitives, render

    prims = section_primitives(spec)
    render(cv, prims)  # cv is the sheets/_common Canvas
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    w: float
    h: float
    layer: str
    hatch: bool = False


@dataclass(frozen=True)
class Dim:
    x1: float
    y1: float
    x2: float
    y2: float
    text: str
    layer: str = "DIM"


@dataclass(frozen=True)
class Label:
    x: float
    y: float
    text: str
    layer: str = "TEXT-SPEC"


@dataclass
class SectionPrimitives:
    rects: list[Rect] = field(default_factory=list)
    dims: list[Dim] = field(default_factory=list)
    labels: list[Label] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SectionSpec:
    """All dimensions in metres unless the field name says mm.

    x0/x1 are the deck extents in drawing units (model mm); y_* likewise.
    """

    bridge_type: str  # slab | t_beam | i_girder | box | box_cell | arch | unknown
    deck_t_mm: float
    wear_t_mm: float
    girder_d_mm: float
    girder_spacing_m: float
    girders_per_deck: int
    girder_top_flange_mm: float = 150.0
    girder_web_mm: float = 200.0
    girder_bottom_flange_mm: float = 300.0
    n_cells: int = 1  # box_cell only


def _classify(bridge_type: str) -> str:
    t = (bridge_type or "").upper().replace("-", "_")
    if "BOX_CELL" in t or "VOIDED" in t and "BOX" in t:
        return "box_cell"
    if "BOX" in t:
        return "box"
    if "T_BEAM" in t or "TBEAM" in t:
        return "t_beam"
    if "I_GIRDER" in t or "IGIRDER" in t or "I-GIRDER" in t:
        return "i_girder"
    if "SLAB" in t:
        return "slab"
    return "unknown"


def girder_positions(spec: SectionSpec, x0: float, x1: float) -> list[float]:
    """Girder centre positions from the MODELLED spacing, not even spreading.

    Girders are stepped from the left deck edge at the modelled spacing; the
    residual edge overhang is whatever it is and is annotated, never fudged.
    """
    if _classify(spec.bridge_type) in ("slab", "box_cell", "unknown"):
        return []
    n = max(int(spec.girders_per_deck), 0)
    if n == 0:
        return []
    pitch = spec.girder_spacing_m * 1000.0  # mm
    width_mm = x1 - x0
    if not pitch > 0 or (n - 1) * pitch >= width_mm:
        raise ValueError("Girder centres must fit within the declared overall deck width.")
    # Start half a pitch clear of each edge where possible, then centre the
    # group on the deck: standard PWD practice shows symmetric spacing about CL.
    span_of_girders = (n - 1) * pitch
    start = x0 + (width_mm - span_of_girders) / 2.0
    return [start + i * pitch for i in range(n)]


def section_primitives(
    spec: SectionSpec, x0: float, x1: float, y_deck_top: float, y_wear: float, y_girder_bot: float
) -> SectionPrimitives:
    kind = _classify(spec.bridge_type)
    out = SectionPrimitives()
    total = x1 - x0

    # Wearing course over the full deck (all types).
    out.rects.append(Rect(x0, y_deck_top, total, y_wear - y_deck_top, "SUPER-WEARING", hatch=True))

    if kind == "slab":
        # Solid slab: deck slab band only.  No girders, no girder dimensions,
        # no girder labels — this is the audit's DXF-01 rule.
        out.rects.append(
            Rect(x0, y_girder_bot, total, y_deck_top - y_girder_bot, "SUPER-DECK", hatch=True)
        )
        out.dims.append(
            Dim(x0, y_girder_bot, x1, y_girder_bot, f"SLAB {spec.deck_t_mm:.0f} mm THK")
        )
        out.notes.append("Solid slab superstructure; deck slab thickness as dimensioned.")
        return out

    if kind == "box_cell":
        cells = max(int(spec.n_cells), 1)
        cell_w = total / cells
        wall = max(0.20 * 1000.0, total * 0.03)  # webs, mm
        for i in range(cells):
            cx0 = x0 + i * cell_w
            # webs
            out.rects.append(
                Rect(cx0, y_girder_bot, wall, y_deck_top - y_girder_bot, "SUPER-DECK", hatch=True)
            )
            out.rects.append(
                Rect(
                    cx0 + cell_w - wall,
                    y_girder_bot,
                    wall,
                    y_deck_top - y_girder_bot,
                    "SUPER-DECK",
                    hatch=True,
                )
            )
            # bottom slab between webs
            out.rects.append(
                Rect(
                    cx0 + wall,
                    y_girder_bot,
                    cell_w - 2 * wall,
                    y_deck_top - y_girder_bot - max(0.20 * 1000.0, total * 0.03),
                    "SUPER-DECK",
                    hatch=True,
                )
            )
        out.labels.append(Label((x0 + x1) / 2.0, y_girder_bot - 120.0, f"{cells}-CELL BOX GIRDER"))
        out.notes.append("Single/multi-cell box superstructure; cell arrangement as shown.")
        return out

    if kind in ("t_beam", "i_girder", "box"):
        xs = girder_positions(spec, x0, x1)
        n = len(xs)
        web = spec.girder_web_mm
        for gx in xs:
            out.rects.append(
                Rect(
                    gx - web / 2.0,
                    y_girder_bot,
                    web,
                    y_deck_top - y_girder_bot,
                    "SUPER-GIRDER",
                    hatch=True,
                )
            )
        if n >= 2:
            pitch = xs[1] - xs[0]
            out.dims.append(
                Dim(
                    xs[0],
                    y_girder_bot,
                    xs[1],
                    y_girder_bot,
                    f"GIRDER SPACING {pitch / 1000.0:.2f} m c/c",
                )
            )
            edge = xs[0] - x0
            out.dims.append(
                Dim(x0, y_girder_bot, xs[0], y_girder_bot, f"EDGE OVERHANG {edge / 1000.0:.2f} m")
            )
        label = {
            ("t_beam"): "RCC T-BEAM GIRDERS",
            ("i_girder"): "PSC I-GIRDERS",
            ("box"): "PSC BOX GIRDER",
        }[kind]
        out.labels.append(Label((x0 + x1) / 2.0, y_girder_bot - 120.0, label))
        out.notes.append(
            f"{n} No. girders at {spec.girder_spacing_m:.2f} m centres, "
            f"{spec.girder_d_mm:.0f} mm deep; edge overhang as dimensioned."
        )
        return out

    # unknown: deck band only, with an explicit warning note — never invent
    # superstructure the model did not declare.
    out.rects.append(
        Rect(x0, y_girder_bot, total, y_deck_top - y_girder_bot, "SUPER-DECK", hatch=True)
    )
    out.notes.append(
        "Superstructure type not declared in the model — deck band drawn at GAD level only."
    )
    return out


def render(cv: Any, prims: SectionPrimitives) -> None:
    """Render primitives onto a sheets/_common Canvas (cv)."""
    for r in prims.rects:
        with cv.on(r.layer):
            cv.rect(r.x, r.y, r.w, r.h)
            if r.hatch:
                cv.hatch(r.x, r.y, r.w, r.h)
    for d in prims.dims:
        with cv.on(d.layer):
            cv.text(d.text, (d.x1 + d.x2) / 2.0, d.y1 - 60.0)
    for label in prims.labels:
        with cv.on(label.layer):
            cv.text(label.text, label.x, label.y)
    if prims.notes:
        xs = [r.x for r in prims.rects] + [label.x for label in prims.labels]
        ys = [r.y for r in prims.rects]
        cv.note(prims.notes, min(xs) if xs else 0.0, (min(ys) if ys else 0.0) - 240.0)
