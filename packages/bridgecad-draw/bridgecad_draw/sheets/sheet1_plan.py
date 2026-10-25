"""bridgecad_draw.sheets.sheet1_plan — the general arrangement plan, in memory.

Wing-16. Sheet 1 is the reference datum: ``coordinates.origin_xy`` gives it a
zero origin, so a chainage drawn here resolves through the same Wing-11 contract
as the long section, the foundation sheet and the details sheet.

THE SET-OUT OFFSET
    The bridge is drawn at true chainage plus one declared offset, because the
    frame's left edge is chainage 0 and the abutment box and its label run
    *upstream* of it. Drawing them at true chainage would put them at negative x,
    off the sheet; the offset is stated once, here, and nothing else is moved.
"""
from __future__ import annotations

import itertools

from bridgecad_draw.contract import wing_wall_geometry
from bridgecad_draw.primitives import north_arrow, scale_bar
from bridgecad_draw.sheets._common import Canvas, field

SHEET = "sheet1_plan"
TITLE = "S1 General Arrangement Plan"
INDEX = 1

#: Chainage marker pitch, metres. Coarsened if the bridge would need too many.
TICK_PITCH_M = 5.0


def _half_widths(project) -> dict[str, float]:
    """Deck half-widths and the faces a plan view has to show, in metres.

    Built up from the model rather than assumed: carriageway, then kerbs, then
    footways, then the crash barrier — the order IRC SP:55 Annex F draws them.
    """
    gi = project.geometry_input
    cw = float(field(gi, "carriageway_width_m", 7.5) or 7.5)
    kerb_l = float(field(gi, "kerb_width_left_m", 0.0) or 0.0)
    kerb_r = float(field(gi, "kerb_width_right_m", 0.0) or 0.0)
    fp_l = float(field(gi, "footpath_left_m", 0.0) or 0.0)
    fp_r = float(field(gi, "footpath_right_m", 0.0) or 0.0)
    cb_l = float(field(gi, "crash_barrier_width_left_m", 0.0) or 0.0)
    cb_r = float(field(gi, "crash_barrier_width_right_m", 0.0) or 0.0)
    return {
        "carriageway": cw,
        "half_left": cw / 2.0 + kerb_l + fp_l + cb_l,
        "half_right": cw / 2.0 + kerb_r + fp_r + cb_r,
        "kerb_half_left": cw / 2.0 + kerb_l,
        "kerb_half_right": cw / 2.0 + kerb_r,
    }


def _abutment_length(project) -> float:
    sub = project.substructure
    return float(field(sub, "abutment_length_m", 9.0) or 9.0)


def _pier_thickness(project) -> float:
    sub = project.substructure
    return float(field(sub, "pier_shaft_width_m", 1.2) or 1.2)


def build(project):
    """Build the general arrangement plan for *project*."""
    cv = Canvas(SHEET, TITLE, INDEX)
    total = float(project.geometry.total_length_m)
    piers = [float(p) for p in project.geometry.pier_positions()]
    walls = wing_wall_geometry(project)

    w = _half_widths(project)
    approach = float(field(project.substructure, "approach_slab_length_m", 3.5) or 3.5)
    abt_l = _abutment_length(project)
    # The offset has to clear the abutment box (centred on each end) and the
    # approach slab that runs upstream of it, or the left-hand geometry lands at
    # negative x and clause 7 rejects it.
    setout = cv.mm(abt_l + approach) + cv.height

    def X(chainage_m: float) -> float:
        return setout + cv.x(chainage_m)

    half_l, half_r = cv.mm(w["half_left"]), cv.mm(w["half_right"])
    yc = cv.frame_h * 0.58                        # bridge centreline
    y_left, y_right = yc - half_l, yc + half_r
    y_top = cv.frame_h * 0.88                     # chainage band
    y_span = cv.frame_h * 0.30                    # per-span dimension band
    y_over = cv.frame_h * 0.22                    # overall dimension band

    # ── deck outline, then the faces inside it ──────────────────────────────
    with cv.on("STRUC-OUTLINE"):
        cv.poly([(X(0.0), y_left), (X(total), y_left),
                 (X(total), y_right), (X(0.0), y_right)], close=True)
        for kerb, sign in ((w["kerb_half_left"], -1.0),
                           (w["kerb_half_right"], 1.0)):
            y_kerb = yc + sign * cv.mm(kerb)
            cv.line((X(0.0), y_kerb), (X(total), y_kerb))
    with cv.on("CIVIL-ROAD"):
        for side in (-1.0, 1.0):
            edge = yc + side * cv.mm(w["carriageway"] / 2.0)
            cv.line((X(0.0), edge), (X(total), edge))

    # ── bridge centreline, run past the deck so it reads as a centreline ────
    with cv.on("CL"):
        cv.line((X(0.0) - cv.height * 2, yc), (X(total) + cv.height * 2, yc))

    # ── approach slabs, upstream and downstream of the abutments ────────────
    with cv.on("CIVIL-ROAD"):
        for a, b in ((-approach, 0.0), (total, total + approach)):
            cv.rect(X(a), y_left, cv.mm(b - a), y_right - y_left)

    # ── abutments ──────────────────────────────────────────────────────────
    with cv.on("SUB-ABUT"):
        for end in (0.0, total):
            cv.rect(X(end) - cv.mm(abt_l) / 2.0, y_left, cv.mm(abt_l),
                    y_right - y_left)
    with cv.on("STRUC-SECTION"):
        for end in (0.0, total):
            cv.line((X(end), y_left - cv.height), (X(end), y_right + cv.height))

    # ── wing walls, splayed, one pair per abutment ─────────────────────────
    thickness = cv.mm(0.40)
    for wall in walls:
        direction = -1.0 if wall.side == "left" else 1.0
        for end, outward in ((0.0, -1.0), (total, 1.0)):
            base = y_right if wall.side == "left" else y_left
            nose = (X(end), base)
            toe = (X(end) + outward * cv.mm(float(wall.return_m)),
                   base + direction * cv.mm(float(wall.face_run_m)))
            off = (0.0, direction * thickness)
            with cv.on("SUB-ABUT"):
                cv.poly([nose, toe,
                         (toe[0] + off[0], toe[1] + off[1]),
                         (nose[0] + off[0], nose[1] + off[1])], close=True)
            with cv.on("STRUC-HATCHING"):
                cv.hatch(min(nose[0], toe[0]), min(nose[1], toe[1]),
                         abs(toe[0] - nose[0]) or thickness,
                         abs(toe[1] - nose[1]) or thickness,
                         pattern="ANSI31", scale=thickness * 0.2)

    # ── piers, then the bearings that sit on them ──────────────────────────
    pt = cv.mm(_pier_thickness(project))
    with cv.on("SUB-PIER"):
        for p in piers:
            cv.rect(X(p) - pt / 2.0, y_left, pt, y_right - y_left)
    with cv.on("SUB-BEARING"):
        for p in piers:
            for side in (-1.0, 1.0):
                y = yc + side * cv.mm(w["carriageway"] / 2.0)
                cv.rect(X(p) - pt / 2.0, y - cv.height * 0.4,
                        pt, cv.height * 0.8)
    with cv.on("CL"):
        for p in piers:
            cv.line((X(p), y_left - cv.height), (X(p), y_right + cv.height))
    with cv.on("TEXT"):
        for i, p in enumerate(piers, start=1):
            cv.text(f"P{i}", X(p) + cv.height * 0.4, y_left - cv.height * 1.8)

    # ── chainage markers along the top ─────────────────────────────────────
    pitch = TICK_PITCH_M
    while total / pitch > 40:
        pitch *= 2
    n_ticks = int(total / pitch) + 1
    with cv.on("CIVIL-CHAINAGE"):
        for i in range(n_ticks):
            ch = min(i * pitch, total)
            cv.line((X(ch), y_top - cv.height), (X(ch), y_top + cv.height))
        for i in range(n_ticks):
            ch = min(i * pitch, total)
            cv.text(f"{ch:.3f}", X(ch), y_top + cv.height * 1.3, halign="CENTER")
    with cv.on("TEXT-HEADER"):
        cv.text("CHAINAGE (m)", X(0.0) - cv.height * 6, y_top + cv.height * 1.3)

    # ── annotation ─────────────────────────────────────────────────────────
    with cv.on("TEXT-HEADER"):
        cv.text("PLAN", X(total) / 2.0, y_right + cv.height * 5, halign="CENTER")
        cv.text(f"TOTAL LENGTH {total:.3f} m", X(total) / 2.0,
                y_right + cv.height * 2.4, halign="CENTER")
    with cv.on("TEXT"):
        cv.text("A1", X(0.0) - cv.mm(abt_l), y_left - cv.height * 4.0)
        cv.text("A2", X(total) + cv.mm(abt_l) * 0.2, y_left - cv.height * 4.0)
    north_arrow(cv.ms, X(total) + cv.height * 8, y_top, size=cv.height * 0.9)
    scale_bar(cv.ms, X(0.0), cv.frame_h * 0.14, cv.scale,
              segments=4, seg_len_m=cv.mm(5.0), text_height=cv.height)

    # ── dimensions: overall, per span, then the widths ─────────────────────
    dim_x = X(total) + cv.height * 4
    bounds = [0.0, *piers, total]
    with cv.on("DIM"):
        cv.dimension((X(0.0), y_over), (X(total), y_over),
                     base=(X(total) / 2.0, y_over - cv.height * 2.5),
                     text=f"{total:.3f} m")
        for a, b in itertools.pairwise(bounds):
            cv.dimension((X(a), y_span), (X(b), y_span),
                         base=(X((a + b) / 2.0), y_span - cv.height * 2.0),
                         text=f"{b - a:.3f}")
        cv.dimension((dim_x, yc - cv.mm(w["carriageway"] / 2.0)),
                     (dim_x, yc + cv.mm(w["carriageway"] / 2.0)),
                     base=(dim_x + cv.height * 3, yc), angle=90.0,
                     text=f"CARRIAGEWAY {w['carriageway']:.2f} m")
        cv.dimension((dim_x, y_left), (dim_x, y_right),
                     base=(dim_x + cv.height * 8, yc), angle=90.0,
                     text=f"DECK {w['half_left'] + w['half_right']:.2f} m")
        for label, half, sign in (("HALF L", w["half_left"], -1.0),
                                  ("HALF R", w["half_right"], 1.0)):
            cv.dimension((dim_x, yc), (dim_x, yc + sign * cv.mm(half)),
                         base=(dim_x + cv.height * 13, yc), angle=90.0,
                         text=f"{label} {half:.2f} m")
        for label, half, sign in (("KERB L", w["kerb_half_left"], -1.0),
                                  ("KERB R", w["kerb_half_right"], 1.0)):
            y_edge = yc + sign * cv.mm(w["carriageway"] / 2.0)
            y_face = yc + sign * cv.mm(half)
            cv.dimension((dim_x, y_edge), (dim_x, y_face),
                         base=(dim_x + cv.height * 18, yc), angle=90.0,
                         text=label)

    # ── notes ──────────────────────────────────────────────────────────────
    cv.note([
        "1. All dimensions in metres unless stated otherwise.",
        f"2. Plot scale 1:{cv.scale}. Model space is millimetres at 1:1.",
        f"3. Span configuration: {len(bounds) - 1} span(s), {len(piers)} intermediate pier(s).",
        "4. Wing walls splayed as detailed on sheet 5.",
        "5. Approach slabs and kerbs as per typical cross-section, sheet 3.",
    ], X(total) + cv.height * 14, y_top)

    return cv.doc
