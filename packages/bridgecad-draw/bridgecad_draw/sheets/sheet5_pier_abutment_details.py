"""bridgecad_draw.sheets.sheet5_pier_abutment_details — pier and abutment details.

Wing-16. The promoted sheet, and the only one that draws a wing wall, so it is
where the ABTL ladder becomes visible. Four panels and a schedule:

    A  pier elevation            shaft, cap, pedestals, bearings, piles
    B  section A-A through pier  the same pier seen along the bridge axis
    C  abutment elevation + plan ABTL, return wall, splayed wing walls
    D  bearing schedule          one row per bearing in the model

THE ABTL SOURCE LABEL
    ``contract.resolve_abtl`` returns ``(value, source)``, where the source is
    the ladder rung that fired (ABTL -> FUTL -> FOOTL -> FUTRL -> ALCL -> ALCW
    -> "default"). The value alone is not enough: an auditor has to be able to
    tell an abutment length the designer stated from one the code defaulted to
    13.0 m. The rung is printed beside the length, on the sheet.

LEVELS ARE ANNOTATED, NOT PLACED
    Sheet 5's declared datum is RL 0 (``coordinates.FRAMES``), and a typical HFL
    of RL 112 is eighty sheet-heights above it. The levels are therefore printed
    as text on the panel, exactly as sheet 4 does it — not ``Canvas.y(112.5)``,
    which would put the line somewhere off the paper.
"""

from __future__ import annotations

from bridgecad_draw.contract import resolve_abtl, wing_wall_geometry
from bridgecad_draw.primitives import circle
from bridgecad_draw.sheets._common import Canvas, field

SHEET = "sheet5_pier_abutment_details"
TITLE = "S5 Pier and Abutment Details"
INDEX = 5


def _num(obj, name: str, default: float) -> float:
    """``field`` with a numeric cast that never raises and never goes non-positive."""
    try:
        value = float(field(obj, name, default) or default)
    except (TypeError, ValueError):
        value = float(default)
    return value if value > 0 else float(default)


def _pile_grid(fd) -> tuple[int, int]:
    """(rows, cols) from the model's pile group config, e.g. "2x2 @2.0m c/c"."""
    cfg = str(field(fd, "pile_group_config", "") or "").replace("×", "x").upper()
    head = cfg.split("@")[0].strip()
    if "X" in head:
        try:
            rows, cols = head.split("X")[:2]
            return max(int(rows.strip()), 1), max(int(cols.strip()), 1)
        except ValueError:
            pass
    return 2, 2


def _bearing_rows(bj) -> list[list[str]]:
    """The bearing schedule, or one honest row saying it is not fixed."""
    rows = []
    for item in list(field(bj, "bearing_schedule", []) or []):
        rows.append(
            [
                str(field(item, "location", "-")),
                str(field(item, "bearing_type", "-")).replace("_", " "),
                f"{_num(item, 'size_x_mm', 0):.0f}x{_num(item, 'size_y_mm', 0):.0f}",
                f"{_num(item, 'design_load_kn', 0):.0f}",
                str(field(item, "fixed_or_guide_or_free", "-")).upper(),
                f"{int(_num(item, 'quantity', 0))}",
            ]
        )
    return rows or [["-", "NOT FIXED", "-", "-", "-", "-"]]


def build(project):
    """Build the pier and abutment details for *project*; returns the DXF document."""
    cv = Canvas(SHEET, TITLE, INDEX)
    sub = project.substructure
    ss = project.superstructure
    fd = project.foundation_details
    bj = project.bearings_joints
    levels = project.levels

    # Resolve the wing walls FIRST: the ladder writes its terminal default back
    # into ``foundation_details.abtl``, so a later ``resolve_abtl`` reports the
    # rung that actually fired ("ABTL") on every build instead of "default" on
    # the first and "ABTL" on the second — which would make the sheet render
    # differently on every re-build of the same project.
    walls = wing_wall_geometry(project)
    abtl_m, abtl_source = resolve_abtl(project)
    splay_deg = float(walls[0].splay_deg) if walls else 45.0
    face_run_m = float(walls[0].face_run_m) if walls else 0.0
    return_m = float(walls[0].return_m) if walls else 0.0
    n_span = int(_num(project.geometry_input, "span_count", 1))
    piers = [float(p) for p in project.geometry.pier_positions()]

    h = cv.height

    # ── model facts, read once ──────────────────────────────────────────────
    pier_len = _num(sub, "pier_shaft_length_m", 9.0)  # across the bridge
    pier_wid = _num(sub, "pier_shaft_width_m", 1.2)  # along the bridge
    pier_hgt = _num(sub, "pier_height_typical_m", 6.0)
    cap_wid = _num(sub, "pier_cap_width_m", 1.8)
    cap_dep = _num(sub, "pier_cap_depth_m", 0.65)
    abt_hgt = _num(sub, "abutment_height_m", 2.8)
    ret_hgt = _num(sub, "return_wall_height_m", 2.5)
    n_gird = max(int(_num(ss, "girders_per_deck_count", 4)), 2)
    girder_d = cv.mm(_num(ss, "girder_depth_mm", 900) / 1000.0)
    deck_t = cv.mm(_num(ss, "deck_thickness_mm", 200) / 1000.0)
    deck_w = cv.mm(_num(project.geometry_input, "carriageway_width_m", 7.5) + 1.4)

    foot_h = cv.mm(_num(fd, "pile_cap_thickness_mm", 1200) / 1000.0)
    pile_d = _num(fd, "pile_diameter_mm", 1000) / 1000.0
    pile_len = cv.mm(min(_num(fd, "pile_length_m", 12.0), 6.0))
    rows, cols = _pile_grid(fd)
    n_piles = rows * cols

    n_bear_pier = max(int(_num(sub, "bearings_per_pier", 4)), 2)

    # ── the shared vertical stack, so panels A and B line up ────────────────
    y_foot_b = cv.mm(9.0)
    y_foot_t = y_foot_b + foot_h
    y_shaft_t = y_foot_t + cv.mm(pier_hgt)
    y_cap_t = y_shaft_t + cv.mm(cap_dep)
    pad_h = h * 1.4
    y_bear_t = y_cap_t + pad_h
    y_pile_b = y_foot_b - pile_len

    # ══ panel A — pier elevation ═══════════════════════════════════════════
    xa = cv.mm(2.5)
    w_a = cv.mm(pier_len)
    over = cv.mm(0.6)
    pile_w = cv.mm(max(pile_d, 0.8))

    with cv.on("FOUND-CAP"):
        cv.rect(xa - over, y_foot_b, w_a + 2 * over, foot_h)
    with cv.on("SUB-PIER"):
        cv.rect(xa, y_foot_t, w_a, cv.mm(pier_hgt))
        cv.rect(xa - over, y_shaft_t, w_a + 2 * over, cv.mm(cap_dep))
    with cv.on("FOUND-PILE"):
        for c in range(cols):
            px = xa + w_a * (c + 0.5) / cols - pile_w / 2.0
            cv.rect(px, y_pile_b, pile_w, pile_len)
    with cv.on("HTCH"):
        cv.hatch(xa - over, y_foot_b, w_a + 2 * over, foot_h, scale=h * 0.4)
        cv.hatch(xa, y_foot_t, w_a, cv.mm(pier_hgt), scale=h * 0.4)
        cv.hatch(xa - over, y_shaft_t, w_a + 2 * over, cv.mm(cap_dep), scale=h * 0.4)
        for c in range(cols):
            px = xa + w_a * (c + 0.5) / cols - pile_w / 2.0
            cv.hatch(px, y_pile_b, pile_w, pile_len, scale=h * 0.4)

    pad_w = cv.mm(0.35)
    with cv.on("SUB-BEARING"):
        for i in range(n_bear_pier):
            bx = xa + w_a * (i + 0.5) / n_bear_pier - pad_w / 2.0
            cv.rect(bx, y_cap_t, pad_w, pad_h)
    with cv.on("CL"):
        cx_a = xa + w_a / 2.0
        cv.line((cx_a, y_pile_b - h * 2.0), (cx_a, y_bear_t + h * 2.0))
    with cv.on("HIDD"):
        cv.dash((xa - h * 3, y_foot_t), (xa + w_a + h * 3, y_foot_t))
    with cv.on("TEXT-HEADER"):
        cv.text("PIER ELEVATION", xa, y_bear_t + h * 9.0)
    with cv.on("TEXT"):
        cv.text(f"{n_piles} No. PILES \u00d8 {pile_d:.2f} m", xa, y_pile_b - h * 2.0)
        cv.text(f"{n_bear_pier} No. BEARINGS ON PIER CAP", xa, y_cap_t + pad_h * 0.4)

    # ── the pier cap / bearing seat detail, enlarged beside the elevation ───
    x_seat = cv.mm(12.6)
    y_seat = y_shaft_t
    seat_w = cv.mm(1.6)
    with cv.on("SUB-PIER"):
        cv.rect(x_seat, y_seat, seat_w, cv.mm(cap_dep))
    with cv.on("SUB-BEARING"):
        cv.rect(x_seat, y_seat + cv.mm(cap_dep), seat_w, pad_h)
    with cv.on("HTCH"):
        cv.hatch(x_seat, y_seat, seat_w, cv.mm(cap_dep), scale=h * 0.3)
    with cv.on("TEXT"):
        cv.text("PIER CAP / BEARING SEAT", x_seat, y_seat + cv.mm(cap_dep) + pad_h + h * 1.5)
        cv.text("ENLARGED", x_seat, y_seat + cv.mm(cap_dep) + pad_h + h * 3.0)

    # ══ panel B — section A-A through the pier ═════════════════════════════
    xb = cv.mm(16.0)
    cx_b = xb + deck_w / 2.0
    w_b_foot = cv.mm(pier_wid + 1.2)
    w_b_shaft = cv.mm(pier_wid)
    w_b_cap = cv.mm(cap_wid)

    with cv.on("FOUND-CAP"):
        cv.rect(cx_b - w_b_foot / 2.0, y_foot_b, w_b_foot, foot_h)
    with cv.on("SUB-PIER"):
        cv.rect(cx_b - w_b_shaft / 2.0, y_foot_t, w_b_shaft, cv.mm(pier_hgt))
        cv.rect(cx_b - w_b_cap / 2.0, y_shaft_t, w_b_cap, cv.mm(cap_dep))
    with cv.on("HTCH"):
        cv.hatch(cx_b - w_b_foot / 2.0, y_foot_b, w_b_foot, foot_h, scale=h * 0.4)
        cv.hatch(cx_b - w_b_shaft / 2.0, y_foot_t, w_b_shaft, cv.mm(pier_hgt), scale=h * 0.4)
        cv.hatch(cx_b - w_b_cap / 2.0, y_shaft_t, w_b_cap, cv.mm(cap_dep), scale=h * 0.4)

    y_gir_b = y_bear_t
    y_gir_t = y_gir_b + girder_d
    y_deck_t = y_gir_t + deck_t
    with cv.on("SUB-BEARING"):
        for i in range(n_bear_pier):
            bx = cx_b - w_b_cap / 2.0 + w_b_cap * (i + 0.5) / n_bear_pier - pad_w / 2.0
            cv.rect(bx, y_cap_t, pad_w, pad_h)
    with cv.on("SUPER-GIRDER"):
        for i in range(n_gird):
            gx = xb + deck_w * (i + 0.5) / n_gird - cv.mm(0.3) / 2.0
            cv.rect(gx, y_gir_b, cv.mm(0.3), girder_d)
    with cv.on("SUPER-DECK"):
        cv.rect(xb, y_gir_t, deck_w, deck_t)
    with cv.on("STRUC-SECTION"):
        for edge in (xb, xb + deck_w):
            cv.line((edge, y_gir_b), (edge, y_deck_t + h))
    with cv.on("CL"):
        cv.line((cx_b, y_foot_t - h * 2.0), (cx_b, y_deck_t + h * 2.0))
    with cv.on("TEXT-HEADER"):
        cv.text("SECTION A-A THROUGH PIER", xb, y_deck_t + h * 9.0)
    with cv.on("TEXT"):
        cv.text(
            f"PIER WALL {pier_wid:.2f} m THICK \u00d7 {pier_hgt:.2f} m HIGH",
            xb,
            y_gir_t - girder_d - h * 2.0,
        )

    # the deck furniture over section A-A, read off the model like sheet 3
    wear_t = cv.mm(_num(ss, "wearing_coat_thickness_mm", 65) / 1000.0)
    kerb_w = cv.mm(_num(project.geometry_input, "kerb_width_left_m", 0.25) or 0.25)
    kerb_h = h * 2.4
    para_h = cv.mm(_num(ss, "parapet_height_mm", 900) / 1000.0)
    crown_m = cv.mm(_num(ss, "camber_mm", 20) / 1000.0)
    with cv.on("SUPER-WEARING"):
        cv.rect(xb, y_deck_t, deck_w, wear_t)
    with cv.on("HTCH"):
        cv.hatch(xb, y_gir_t, deck_w, deck_t, scale=h * 0.35)
    with cv.on("SUPER-DECK"):
        cv.rect(xb, y_deck_t + wear_t, kerb_w, kerb_h)
        cv.rect(xb + deck_w - kerb_w, y_deck_t + wear_t, kerb_w, kerb_h)
    with cv.on("STRUC-OUTLINE"):
        cv.rect(xb + kerb_w, y_deck_t + wear_t + kerb_h, kerb_w * 0.8, para_h)
        cv.rect(xb + deck_w - kerb_w * 1.8, y_deck_t + wear_t + kerb_h, kerb_w * 0.8, para_h)
    n_cam = 7
    with cv.on("SUPER-CAMBER"):
        cv.poly(
            [
                (
                    xb + deck_w * i / (n_cam - 1),
                    y_deck_t + wear_t + crown_m * (1.0 - (2.0 * i / (n_cam - 1) - 1.0) ** 2),
                )
                for i in range(n_cam)
            ],
            close=False,
        )
    with cv.on("TEXT"):
        cv.text(
            "KERB + PARAPET \u2014 READ FROM SUPERSTRUCTURE MODEL",
            xb,
            y_deck_t + wear_t + kerb_h + para_h + h * 1.5,
        )

    # ══ panel C — abutment elevation, ABTL and the splayed wing walls ══════
    xc = cv.mm(26.0)
    w_c = cv.mm(abtl_m)
    y_abt_b = cv.mm(17.5)
    y_abt_t = y_abt_b + cv.mm(abt_hgt)

    with cv.on("SUB-ABUT"):
        cv.rect(xc, y_abt_b, w_c, cv.mm(abt_hgt))
    with cv.on("HTCH"):
        cv.hatch(xc, y_abt_b, w_c, cv.mm(abt_hgt), scale=h * 0.4)
    with cv.on("SUB-ABUT"):
        for side in (-1.0, 1.0):
            rx = xc - cv.mm(0.4) if side < 0 else xc + w_c
            cv.rect(rx, y_abt_b, cv.mm(0.4), cv.mm(ret_hgt))
    with cv.on("CL"):
        cv.line((xc - h * 2.0, y_abt_b), (xc + w_c + h * 2.0, y_abt_b))

    with cv.on("TEXT-HEADER"):
        cv.text(
            f"ABUTMENT A1 \u2014 ABTL {abtl_m:.2f} m (SOURCE: {abtl_source.upper()})",
            xc,
            y_abt_t + h * 8.0,
        )
    with cv.on("TEXT-LEVEL"):
        cv.text(f"DECK LEVEL RL {float(levels.deck_level_m or 0.0):.3f}", xc, y_abt_t + h * 5.0)
        cv.text(f"HFL RL {float(levels.hfl_m or 0.0):.3f}", xc, y_abt_t + h * 3.0)
        cv.text(f"LWL RL {float(levels.lwl_m or 0.0):.3f}", xc, y_abt_t + h * 1.0)
        cv.text(
            f"FOUNDING LEVEL RL {float(levels.founding_level_m or 0.0):.3f}", xc, y_abt_b - h * 1.5
        )

    y_wp = cv.mm(9.5)
    thick = cv.mm(0.4)
    for wall in walls:
        sign = -1.0 if wall.side == "left" else 1.0
        run = cv.mm(float(wall.face_run_m))
        ret = cv.mm(float(wall.return_m))
        nose = (xc, y_wp)
        toe = (xc + ret, y_wp + sign * run)
        with cv.on("SUB-ABUT"):
            cv.poly([nose, toe, (toe[0], toe[1] + sign * thick), (nose[0], nose[1] + sign * thick)])
        with cv.on("HTCH"):
            cv.hatch(xc, min(y_wp, toe[1]), ret or thick, abs(run) or thick, scale=h * 0.3)
        with cv.on("TEXT"):
            cv.text(
                f"WING WALL {wall.side.upper()} \u2014 {float(wall.length_m):.2f} m",
                xc + ret + h * 2.0,
                y_wp + sign * run,
            )
    with cv.on("TEXT-HEADER"):
        cv.text(
            f"WING WALL SPLAY {splay_deg:.1f}\u00b0 FROM ABUTMENT FACE "
            f"(FACE RUN {face_run_m:.2f} m, RETURN {return_m:.2f} m)",
            xc,
            y_wp - h * 3.0,
        )

    # ══ panel D — bearing schedule ═════════════════════════════════════════
    y_tbl = cv.mm(5.6)
    x_tbl = cv.mm(2.5)
    with cv.on("TEXT-HEADER"):
        cv.text("BEARING SCHEDULE", x_tbl, y_tbl + h * 2.5)
    cv.table(
        x_tbl,
        y_tbl,
        [cv.mm(1.7), cv.mm(2.9), cv.mm(2.0), cv.mm(1.7), cv.mm(1.4), cv.mm(1.0)],
        [["LOCATION", "TYPE", "SIZE (mm)", "LOAD (kN)", "FIXITY", "QTY"], *_bearing_rows(bj)],
        row_h=h * 2.4,
    )

    # ══ panel E — pier pile foundation layout plan ═════════════════════════
    xpl = cv.mm(16.4)
    ypl = cv.mm(2.6)
    plan_w = cv.mm(pier_len)
    plan_d = cv.mm(pier_wid + 1.2)
    with cv.on("FOUND-CAP"):
        cv.rect(xpl, ypl, plan_w, plan_d)
    with cv.on("HTCH"):
        cv.hatch(xpl, ypl, plan_w, plan_d, scale=h * 0.3)
    with cv.on("FOUND-PILE"):
        for r in range(rows):
            for c in range(cols):
                circle(
                    cv.ms,
                    xpl + plan_w * (c + 0.5) / cols,
                    ypl + plan_d * (r + 0.5) / rows,
                    pile_w / 2.0,
                    layer=cv.ms.layer_name,
                )
    with cv.on("CL"):
        cv.line((xpl + plan_w / 2.0, ypl - h * 1.5), (xpl + plan_w / 2.0, ypl + plan_d + h * 1.5))
        cv.line((xpl - h * 1.5, ypl + plan_d / 2.0), (xpl + plan_w + h * 1.5, ypl + plan_d / 2.0))
    with cv.on("TEXT-HEADER"):
        cv.text("PIER \u2014 PILE FOUNDATION LAYOUT PLAN", xpl, ypl + plan_d + h * 3.5)
    with cv.on("TEXT"):
        cv.text(
            f"PILE GROUP {rows}\u00d7{cols} \u2014 {n_piles} No. \u00d8 {pile_d:.2f} m",
            xpl,
            ypl - h * 3.0,
        )
        cv.text(f"PILE CAP {pier_len:.2f} m \u00d7 {pier_wid + 1.2:.2f} m", xpl, ypl - h * 5.0)
    with cv.on("DIM"):
        cv.dimension(
            (xpl, ypl - h * 7.0),
            (xpl + plan_w, ypl - h * 7.0),
            base=(xpl + plan_w / 2.0, ypl - h * 9.5),
            text=f"PILE CAP {pier_len:.2f} m",
        )
        cv.dimension(
            (xpl - h * 2.0, ypl),
            (xpl - h * 2.0, ypl + plan_d),
            base=(xpl - h * 5.5, ypl),
            angle=90.0,
            text=f"CAP {pier_wid + 1.2:.2f} m",
        )

    # ══ panel F — pile foundation schedule ═════════════════════════════════
    x_sch = cv.mm(30.6)
    y_sch = cv.mm(9.5)
    with cv.on("TEXT-HEADER"):
        cv.text("PILE FOUNDATION SCHEDULE", x_sch, y_sch + h * 2.5)
    cv.table(
        x_sch,
        y_sch,
        [cv.mm(4.2), cv.mm(3.4)],
        [
            ["PARAMETER", "VALUE"],
            ["Pile diameter", f"{pile_d:.2f} m"],
            ["Pile group", f"{rows}\u00d7{cols} = {n_piles} No."],
            ["Pile cap", f"{pier_len:.2f} \u00d7 {pier_wid + 1.2:.2f} m"],
            ["Pile length", f"{_num(fd, 'pile_length_m', 12.0):.2f} m"],
            ["Cap thickness", f"{_num(fd, 'pile_cap_thickness_mm', 1200):.0f} mm"],
        ],
        row_h=h * 2.4,
    )

    # ══ dimensions ═════════════════════════════════════════════════════════
    y_dim_a = y_pile_b - h * 4.0
    with cv.on("DIM"):
        cv.dimension(
            (xa, y_dim_a),
            (xa + w_a, y_dim_a),
            base=(cx_a, y_dim_a - h * 2.5),
            text=f"PIER WALL {pier_len:.2f} m",
        )
        cv.dimension(
            (xa - over, y_foot_b),
            (xa + w_a + over, y_foot_b),
            base=(cx_a, y_foot_b - h * 2.5),
            text=f"PILE CAP {w_a / 1000.0 + 1.2:.2f} m",
        )
        cv.dimension(
            (xa - h * 3, y_foot_t),
            (xa - h * 3, y_shaft_t),
            base=(xa - h * 10, y_foot_t),
            angle=90.0,
            text=f"PIER {pier_hgt:.2f} m",
        )
        cv.dimension(
            (xa - h * 3, y_pile_b),
            (xa - h * 3, y_foot_b),
            base=(xa - h * 16, y_pile_b),
            angle=90.0,
            text=f"PILE {pile_len / 1000.0:.2f} m",
        )
        cv.dimension(
            (xa + w_a + h * 3, y_shaft_t),
            (xa + w_a + h * 3, y_cap_t),
            base=(xa + w_a + h * 11, y_shaft_t),
            angle=90.0,
            text=f"CAP {cv.mm(cap_dep) / 1000.0 * 1000 / 1000:.0f} mm",
        )
        cv.dimension(
            (xa + w_a * 0.5 / n_bear_pier, y_bear_t + h * 2.0),
            (xa + w_a * 1.5 / n_bear_pier, y_bear_t + h * 2.0),
            base=(xa + w_a / n_bear_pier, y_bear_t + h * 5.0),
            text=f"{pier_len / n_bear_pier:.2f} m C/C",
        )

        cv.dimension(
            (cx_b - w_b_cap / 2.0, y_deck_t),
            (cx_b + w_b_cap / 2.0, y_deck_t),
            base=(cx_b - w_b_cap, y_deck_t + h * 4.0),
            text=f"CAP {cap_wid:.2f} m",
        )
        cv.dimension(
            (cx_b - w_b_foot / 2.0, y_deck_t),
            (cx_b + w_b_foot / 2.0, y_deck_t),
            base=(cx_b + w_b_foot, y_deck_t + h * 4.0),
            text=f"FOOTING {pier_wid + 1.2:.2f} m",
        )
        cv.dimension(
            (xb - h * 3, y_foot_t),
            (xb - h * 3, y_shaft_t),
            base=(xb - h * 10, y_foot_t),
            angle=90.0,
            text=f"PIER {pier_hgt:.2f} m",
        )
        cv.dimension(
            (xb - h * 3, y_foot_b),
            (xb - h * 3, y_foot_t),
            base=(xb - h * 16, y_foot_b),
            angle=90.0,
            text=f"PILE CAP {foot_h / 1000.0 * 1000 / 1000 * 1000:.0f} mm",
        )
        cv.dimension(
            (xb, y_deck_t),
            (xb + deck_w, y_deck_t),
            base=(xb + deck_w / 2.0, y_deck_t + h * 8.0),
            text=f"DECK {deck_w / 1000.0:.2f} m",
        )

        cv.dimension(
            (xc, y_abt_b),
            (xc + w_c, y_abt_b),
            base=(xc + w_c / 2.0, y_abt_b - h * 6.0),
            text=f"ABTL {abtl_m:.2f} m",
        )
        cv.dimension(
            (xc - h * 3, y_abt_b),
            (xc - h * 3, y_abt_t),
            base=(xc - h * 9, y_abt_b),
            angle=90.0,
            text=f"ABUTMENT {abt_hgt:.2f} m",
        )
        cv.dimension(
            (xc + w_c + h * 3, y_abt_b),
            (xc + w_c + h * 3, y_abt_b + cv.mm(ret_hgt)),
            base=(xc + w_c + h * 11, y_abt_b),
            angle=90.0,
            text=f"RETURN WALL {ret_hgt:.2f} m",
        )
        cv.dimension(
            (xc, y_wp - h * 4.0),
            (xc + cv.mm(face_run_m), y_wp - h * 4.0),
            base=(xc + cv.mm(face_run_m) / 2.0, y_wp - h * 7.0),
            text=f"FACE RUN {face_run_m:.2f} m",
        )
        cv.dimension(
            (xc + cv.mm(return_m) + h * 3, y_wp),
            (xc + cv.mm(return_m) + h * 3, y_wp + cv.mm(face_run_m)),
            base=(xc + cv.mm(return_m) + h * 11, y_wp),
            angle=90.0,
            text=f"RETURN {return_m:.2f} m",
        )

    # ══ notes ══════════════════════════════════════════════════════════════
    span_note = (
        "3. Simple span: NO INTERMEDIATE PIER on this bridge."
        if not piers
        else f"3. {len(piers)} intermediate PIER(S) at "
        f"{', '.join(f'{p:.3f}' for p in piers)} m chainage."
    )
    cv.note(
        [
            "1. All dimensions in metres unless stated otherwise.",
            f"2. Abutment total length (ABTL) {abtl_m:.2f} m, resolved from the "
            f"{abtl_source.upper()} rung of the ABTL ladder.",
            span_note,
            f"4. Wing wall splay {splay_deg:.1f}\u00b0 from the abutment face; "
            f"{len(walls)} wing wall(s) drawn.",
            f"5. Spans on this structure: {n_span}; plot scale 1:{cv.scale}.",
        ],
        cv.mm(2.5),
        cv.mm(16.6),
    )

    return cv.doc
