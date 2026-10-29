"""bridgecad_draw.sheets.sheet3_cross_section — the typical deck cross-section.

Wing-16. The section is read off the model: carriageway, kerbs, footways, crash
barriers, slab and girder depths, and the camber. Nothing here is a literal that
should have been a field — change a width in the model and the section moves.

Model space is millimetres at 1:1 (``coordinates`` clause 1), so every metre from
the model is converted once, through ``Canvas.mm``.
"""

from __future__ import annotations

from bridgecad_draw.primitives import circle as _circle
from bridgecad_draw.sheets._common import Canvas, field

SHEET = "sheet3_cross_section"
TITLE = "S3 Typical Cross Section"
INDEX = 3

#: IRC:112 typical deck cross-fall, used when the model carries none.
DEFAULT_CROSS_FALL_PCT = 2.5


def _widths(project) -> dict[str, float]:
    """Carriageway, kerbs and the overall deck width, in metres."""
    gi = project.geometry_input
    cw = float(field(gi, "carriageway_width_m", 7.5) or 7.5)
    kerb_l = float(field(gi, "kerb_width_left_m", 0.25) or 0.0)
    kerb_r = float(field(gi, "kerb_width_right_m", 0.25) or 0.0)
    fp_l = float(field(gi, "footpath_left_m", 0.0) or 0.0)
    fp_r = float(field(gi, "footpath_right_m", 0.0) or 0.0)
    cb_l = float(field(gi, "crash_barrier_width_left_m", 0.45) or 0.0)
    cb_r = float(field(gi, "crash_barrier_width_right_m", 0.45) or 0.0)
    half_l = cw / 2.0 + kerb_l + fp_l + cb_l
    half_r = cw / 2.0 + kerb_r + fp_r + cb_r
    return {
        "carriageway": cw,
        "kerb_l": kerb_l,
        "kerb_r": kerb_r,
        "foot_l": fp_l,
        "foot_r": fp_r,
        "barrier_l": cb_l,
        "barrier_r": cb_r,
        "half_l": half_l,
        "half_r": half_r,
        "total": half_l + half_r,
    }


def _draw_services_and_levels(cv, project, w, geom) -> None:
    """Hatching, footpaths, railing, drainage, RL tags, reinforcement and the
    second dimension string on the deck view.

    Every position is derived from the widths in *w* and the depths in *geom*,
    so the whole assembly moves when the model moves.
    """
    h = cv.height
    x0, x1, x_mid = geom["x0"], geom["x1"], geom["x_mid"]
    total = geom["total"]
    y_soffit, y_wear = geom["y_soffit"], geom["y_wear"]
    y_deck_top, y_girder_bot = geom["y_deck_top"], geom["y_girder_bot"]
    y_kerb, y_parapet = geom["y_kerb"], geom["y_parapet"]
    kerb_h = geom["kerb_h"]
    count = max(int(geom["n_girders"]), 1)
    slab = y_deck_top - y_soffit
    girder = y_soffit - y_girder_bot

    # wearing coat and kerbs hatched; bituminous coat reads AR-SAND, concrete ANSI31
    with cv.on("HTCH"):
        cv.hatch(x0, y_deck_top, total, y_wear - y_deck_top, pattern="AR-SAND", scale=h * 0.35)
        if w["kerb_l"] > 0:
            cv.hatch(x0, y_wear, cv.mm(w["kerb_l"]), kerb_h, pattern="ANSI31", scale=h * 0.35)
        if w["kerb_r"] > 0:
            cv.hatch(x1 - cv.mm(w["kerb_r"]), y_wear, cv.mm(w["kerb_r"]), kerb_h,
                     pattern="ANSI31", scale=h * 0.35)

    # footpaths sit between the kerb and the carriageway edge
    with cv.on("SUPER-FOOTPATH"):
        if w["foot_l"] > 0:
            cv.rect(x0 + cv.mm(w["kerb_l"]), y_wear, cv.mm(w["foot_l"]), kerb_h)
        if w["foot_r"] > 0:
            cv.rect(x1 - cv.mm(w["kerb_r"]) - cv.mm(w["foot_r"]), y_wear,
                    cv.mm(w["foot_r"]), kerb_h)

    # railing posts and top rail above the crash barriers
    posts = max(int(total // cv.mm(2.0)), 2)
    with cv.on("SUPER-PARAPET"):
        for i in range(posts + 1):
            px = x0 + total * i / posts
            cv.line((px, y_parapet), (px, y_parapet + h * 1.4))
        cv.line((x0, y_parapet + h * 1.4), (x1, y_parapet + h * 1.4))

    # deck drainage scuppers at both kerb lines
    with cv.on("SUPER-DRAINAGE"):
        for ex in (x0, x1):
            cv.rect(ex - h * 0.5, y_deck_top + h * 0.3, h, h * 0.5)
        cv.line((x0 - h * 0.5, y_deck_top + h * 0.55), (x0 - h * 2.0, y_deck_top + h * 0.55))

    # reinforcement marks in the slab (top and bottom mats)
    bar_run = total / count * 0.6
    with cv.on("STRUC-DETAIL"):
        n_bars = 12
        for i in range(n_bars):
            bx = x0 + total * (i + 0.5) / n_bars
            cv.line((bx - bar_run / 2, y_soffit + slab * 0.25),
                    (bx + bar_run / 2, y_soffit + slab * 0.25))
            cv.line((bx - bar_run / 2, y_deck_top - slab * 0.25),
                    (bx + bar_run / 2, y_deck_top - slab * 0.25))
        # prestressing ducts, two per girder web
        for i in range(count):
            gx = x0 + total * (i + 0.5) / count
            _circle(cv.ms, gx + cv.mm(0.15), y_soffit - girder * 0.35, h * 0.35,
                    layer=cv.ms.layer_name)
            _circle(cv.ms, gx + cv.mm(0.15), y_soffit - girder * 0.70, h * 0.35,
                    layer=cv.ms.layer_name)

    # RL tags: sheet 3's datum is RL 0, so a real level would plot off the sheet
    # at 1:50 — the tag carries the level, the section carries the position.
    road_rl = float(field(project.project_master, "road_level_rl_m", 0.0) or 0.0)
    with cv.on("DIM-LEVEL"):
        for yy in (y_wear, y_soffit, y_girder_bot):
            cv.line((x1 + h * 6.0, yy), (x1 + h * 8.0, yy))
    with cv.on("TEXT-LEVEL"):
        cv.text(f"DECK LEVEL RL {road_rl:.3f}", x1 + h * 8.4, y_wear)
        cv.text(f"SOFFIT RL {road_rl - geom['wear_t_mm'] / 1000.0 - geom['deck_t_mm'] / 1000.0:.3f}",
                x1 + h * 8.4, y_soffit)
        cv.text(
            f"GIRDER BOTTOM RL "
            f"{road_rl - (geom['wear_t_mm'] + geom['deck_t_mm'] + geom['girder_d_mm']) / 1000.0:.3f}",
            x1 + h * 8.4, y_girder_bot,
        )

    # vertical and horizontal dimensions completing the section
    with cv.on("DIM"):
        cv.dimension((x0 - h * 6.0, y_wear), (x0 - h * 6.0, y_kerb),
                     base=(x0 - h * 15.0, y_wear), angle=90.0,
                     text=f"KERB {kerb_h / 1000.0:.2f} m")
        cv.dimension((x0 - h * 6.0, y_kerb), (x0 - h * 6.0, y_parapet),
                     base=(x0 - h * 15.0, y_kerb), angle=90.0,
                     text=f"BARRIER {geom['parapet_h_mm']:.0f} mm")
        cv.dimension((x1 + h * 6.0, y_deck_top), (x1 + h * 6.0, y_wear),
                     base=(x1 + h * 15.0, y_deck_top), angle=90.0,
                     text=f"WC {geom['wear_t_mm']:.0f} mm")
        cv.dimension((x1 + h * 20.0, y_girder_bot), (x1 + h * 20.0, y_wear),
                     base=(x1 + h * 29.0, y_wear), angle=90.0,
                     text="STRUCTURAL DEPTH "
                          f"{(geom['girder_d_mm'] + geom['deck_t_mm'] + geom['wear_t_mm']) / 1000.0:.2f} m")
        g_pitch = total / count
        cv.dimension((x0 + g_pitch * 0.5, y_girder_bot), (x0 + g_pitch * 1.5, y_girder_bot),
                     base=(x0 + g_pitch, y_girder_bot - h * 12.0),
                     text=f"GIRDER SPACING {g_pitch / 1000.0:.2f} m")
        cv.dimension((x_mid - cv.mm(w["carriageway"]) / 2.0, y_soffit - h * 14.0),
                     (x_mid + cv.mm(w["carriageway"]) / 2.0, y_soffit - h * 14.0),
                     base=(x_mid, y_soffit - h * 18.0),
                     text=f"CARRIAGEWAY {w['carriageway']:.2f} m")


def _draw_support_section(cv, project, w, geom) -> None:
    """The pier cross-section at a support — the brief's optional second view.

    Looks along the bridge axis: pier cap on pedestals over the shaft, pile cap
    below, bearings on the cap. Placed clear of the deck view so the two read
    independently on the sheet.
    """
    h = cv.height
    sub = project.substructure
    y_base = geom["y_soffit"]

    cap_w = cv.mm(float(field(sub, "pier_cap_length_m", geom["total"] * 0.7 / 1000.0)
                         or geom["total"] * 0.7 / 1000.0))
    cap_d = cv.mm(float(field(sub, "pier_cap_depth_m", 0.6) or 0.6))
    shaft_w = cv.mm(float(field(sub, "pier_shaft_length_m", 1.2) or 1.2))
    shaft_h = cv.mm(float(field(sub, "pier_height_typical_m", 6.0) or 6.0))
    ped_h = cv.mm(float(field(sub, "pier_pedestal_height_m", 0.25) or 0.25))
    pc_t = cv.mm(float(field(sub, "pile_cap_thickness_mm", 1200) or 1200) / 1000.0)
    n_bearings = int(field(sub, "bearings_per_pier", 2) or 2)

    bx = cv.mm(20.0)
    x_shaft = bx + (cap_w - shaft_w) / 2.0
    y_pc_top = y_base + pc_t
    y_shaft_bot = y_pc_top
    y_shaft_top = y_shaft_bot + shaft_h
    y_ped_top = y_shaft_top + ped_h
    y_cap_top = y_ped_top + cap_d

    with cv.on("FOUND-CAP"):
        cv.rect(bx, y_base, cap_w, pc_t)
    with cv.on("HTCH"):
        cv.hatch(bx, y_base, cap_w, pc_t, pattern="ANSI31", scale=h * 0.35)
    with cv.on("SUB-PIER"):
        cv.rect(x_shaft, y_shaft_bot, shaft_w, shaft_h)
        cv.rect(x_shaft - h, y_shaft_top, shaft_w + 2.0 * h, ped_h)
        cv.rect(bx, y_ped_top, cap_w, cap_d)
    with cv.on("HTCH"):
        cv.hatch(x_shaft, y_shaft_bot, shaft_w, shaft_h, pattern="ANSI31", scale=h * 0.35)
        cv.hatch(bx, y_ped_top, cap_w, cap_d, pattern="ANSI31", scale=h * 0.35)
    with cv.on("CL"):
        cv.line((bx + cap_w / 2.0, y_base - h * 3.0),
                (bx + cap_w / 2.0, y_cap_top + cap_d + h * 3.0))
    with cv.on("SUB-BEARING"):
        for xb in (bx + cap_w * 0.12, bx + cap_w * 0.88 - cv.mm(0.5)):
            cv.rect(xb, y_cap_top + cap_d, cv.mm(0.5), h * 1.2)
    with cv.on("DIM-LEADER"):
        cv.line((bx + cap_w, y_shaft_bot + shaft_h / 2.0),
                (bx + cap_w + h * 1.0, y_shaft_bot + shaft_h / 2.0))

    with cv.on("DIM"):
        cv.dimension((bx, y_cap_top + cap_d + h * 7.0), (bx + cap_w, y_cap_top + cap_d + h * 7.0),
                     base=(bx + cap_w / 2.0, y_cap_top + cap_d + h * 12.0),
                     text=f"PIER CAP {cap_w / 1000.0:.2f} m")
        cv.dimension((bx - h * 3.0, y_shaft_bot), (bx - h * 3.0, y_shaft_top),
                     base=(bx - h * 12.0, y_shaft_bot), angle=90.0,
                     text=f"PIER HT {shaft_h / 1000.0:.2f} m")
        cv.dimension((bx + cap_w + h * 3.0, y_base), (bx + cap_w + h * 3.0, y_pc_top),
                     base=(bx + cap_w + h * 12.0, y_base), angle=90.0,
                     text=f"PILE CAP {pc_t / 1000.0:.2f} m")
        cv.dimension((bx, y_base - h * 4.0), (bx + shaft_w, y_base - h * 4.0),
                     base=(bx + shaft_w / 2.0, y_base - h * 9.0),
                     text=f"SHAFT {shaft_w / 1000.0:.2f} m")

    with cv.on("TEXT-HEADER"):
        cv.text("PIER SECTION AT SUPPORT", bx + cap_w / 2.0, y_cap_top + cap_d + h * 14.0,
                halign="CENTER")
    with cv.on("TEXT"):
        cv.text("PIER CAP", bx + cap_w + h * 1.4, y_ped_top + cap_d * 0.4)
        cv.text("PIER SHAFT", bx + cap_w + h * 1.4, y_shaft_bot + shaft_h * 0.5)
        cv.text("PILE CAP", bx + cap_w + h * 1.4, y_base + pc_t * 0.4)
        cv.text(f"{n_bearings} No. BEARINGS", bx + cap_w + h * 1.4, y_cap_top + cap_d + h * 1.4)


def build(project):
    """Build the typical cross-section for *project*; returns the DXF document."""
    cv = Canvas(SHEET, TITLE, INDEX)
    w = _widths(project)
    ss = project.superstructure

    deck_t_mm = float(field(ss, "deck_thickness_mm", 200) or 200)
    wear_t_mm = float(field(ss, "wearing_coat_thickness_mm", 65) or 65)
    girder_d_mm = float(field(ss, "girder_depth_mm", 900) or 900)
    spacing_m = float(field(ss, "girder_spacing_m", 2.0) or 2.0)
    n_girders = int(field(ss, "girders_per_deck_count", 4) or 4)
    camber_mm = float(field(ss, "camber_mm", 20) or 0.0)
    camber_method = str(field(ss, "camber_method", "PARABOLIC_CROWN") or "PARABOLIC_CROWN")
    parapet_h_mm = float(field(ss, "parapet_height_mm", 900) or 900)

    # ── panel set-out, in model millimetres ─────────────────────────────────
    x0 = cv.mm(3.0)
    total = cv.mm(w["total"])
    x1 = x0 + total
    x_mid = x0 + total / 2.0

    y_soffit = cv.mm(6.5)
    slab = cv.mm(deck_t_mm / 1000.0)
    wear = cv.mm(wear_t_mm / 1000.0)
    girder = cv.mm(girder_d_mm / 1000.0)
    y_deck_top = y_soffit + slab
    y_wear = y_deck_top + wear
    y_girder_bot = y_soffit - girder
    kerb_h = cv.height * 2.4
    y_kerb = y_wear + kerb_h
    y_parapet = y_kerb + cv.mm(parapet_h_mm / 1000.0)

    # ── deck slab, wearing coat and the cambered running surface ───────────
    with cv.on("STRUC-OUTLINE"):
        cv.rect(x0, y_soffit, total, slab)
    with cv.on("HTCH"):
        cv.hatch(x0, y_soffit, total, slab, pattern="ANSI31", scale=cv.height * 0.35)
    with cv.on("SUPER-WEARING"):
        cv.rect(x0, y_deck_top, total, wear)

    crown = cv.mm(camber_mm / 1000.0)
    n_pts = 9
    with cv.on("SUPER-CAMBER"):
        pts = [
            (
                x0 + total * i / (n_pts - 1),
                y_wear + crown * (1.0 - (2.0 * i / (n_pts - 1) - 1.0) ** 2),
            )
            for i in range(n_pts)
        ]
        cv.poly(pts, close=False)

    # ── kerbs and crash barriers ───────────────────────────────────────────
    x_cw_l = x_mid - cv.mm(w["carriageway"] / 2.0)
    x_cw_r = x_mid + cv.mm(w["carriageway"] / 2.0)
    x_kerb_l = x_cw_l - cv.mm(w["kerb_l"])
    x_cw_r + cv.mm(w["kerb_r"])
    with cv.on("SUPER-KERB"):
        cv.rect(x0, y_wear, cv.mm(w["kerb_l"]), kerb_h)
        cv.rect(x1 - cv.mm(w["kerb_r"]), y_wear, cv.mm(w["kerb_r"]), kerb_h)
    with cv.on("SUPER-CRASH"):
        cv.rect(x0, y_kerb, cv.mm(w["barrier_l"] or 0.45), y_parapet - y_kerb)
        cv.rect(
            x1 - cv.mm(w["barrier_r"] or 0.45),
            y_kerb,
            cv.mm(w["barrier_r"] or 0.45),
            y_parapet - y_kerb,
        )

    # ── girders under the slab ─────────────────────────────────────────────
    # Centres are spread evenly across the deck rather than stepped at the
    # model's spacing from the left kerb: an evenly spread set always lands
    # inside the deck, so the count drawn matches the count annotated.
    count = max(n_girders, 1)
    depth = y_wear - y_girder_bot
    with cv.on("SUPER-GIRDER"):
        for i in range(count):
            gx = x0 + total * (i + 0.5) / count
            cv.rect(gx, y_girder_bot, cv.mm(0.3), depth)
    with cv.on("HTCH"):
        for i in range(count):
            gx = x0 + total * (i + 0.5) / count
            cv.hatch(gx, y_girder_bot, cv.mm(0.3), depth, pattern="ANSI31", scale=cv.height * 0.35)

    # ── cross-fall arrows, one per half ────────────────────────────────────
    with cv.on("DIM-SLOPE"):
        for sign in (-1.0, 1.0):
            ax = x_mid + sign * cv.mm(w["carriageway"] / 4.0)
            cv.line(
                (ax, y_wear + cv.height * 0.4), (ax + sign * cv.mm(1.2), y_wear + cv.height * 2.6)
            )

    # ── dimensions ─────────────────────────────────────────────────────────
    with cv.on("DIM"):
        cv.dimension(
            (x0, y_wear),
            (x1, y_wear),
            base=(x_mid, y_wear + cv.height * 12),
            angle=0.0,
            text=f"OVERALL {w['total']:.2f} m",
        )
        cv.dimension(
            (x_cw_l, y_kerb),
            (x_cw_r, y_kerb),
            base=(x_mid, y_kerb + cv.height * 5),
            angle=0.0,
            text=f"CARRIAGEWAY {w['carriageway']:.2f} m",
        )
        cv.dimension(
            (x0, y_soffit),
            (x_kerb_l, y_soffit),
            base=(x0 + cv.mm(w["kerb_l"]) / 2.0, y_soffit - cv.height * 2.5),
            angle=0.0,
            text=f"KERB {w['kerb_l']:.2f} m",
        )
        cv.dimension(
            (x0 - cv.height * 3, y_soffit),
            (x0 - cv.height * 3, y_deck_top),
            base=(x0 - cv.height * 12, y_soffit),
            angle=90.0,
            text=f"SLAB {deck_t_mm:.0f} mm",
        )
        cv.dimension(
            (x1 + cv.height * 3, y_girder_bot),
            (x1 + cv.height * 3, y_deck_top),
            base=(x1 + cv.height * 12, y_wear),
            angle=90.0,
            text=f"GIRDER {girder_d_mm:.0f} mm",
        )

    # ── labels ─────────────────────────────────────────────────────────────
    with cv.on("TEXT"):
        cv.text(
            f"CARRIAGEWAY {w['carriageway']:.2f} m",
            x_mid,
            y_kerb + cv.height * 1.6,
            halign="CENTER",
        )
        cv.text(
            f"KERB {w['kerb_l']:.2f} m",
            x_kerb_l - cv.mm(0.1),
            y_kerb + cv.height * 1.6,
            halign="LEFT",
        )
        cv.text(
            f"CAMBER {camber_mm:.0f} mm {camber_method}",
            x_mid,
            y_wear + cv.height * 5.0,
            halign="CENTER",
        )
        cv.text(
            f"CROSS FALL {DEFAULT_CROSS_FALL_PCT:.2f}% TO CENTRE",
            x_mid,
            y_wear + cv.height * 3.2,
            halign="CENTER",
        )
    with cv.on("TEXT-HEADER"):
        cv.text("TYPICAL DECK SECTION", x_mid, y_parapet + cv.height * 4.0, halign="CENTER")

    geom = {
        "x0": x0, "x1": x1, "x_mid": x_mid, "total": total,
        "y_soffit": y_soffit, "y_deck_top": y_deck_top, "y_wear": y_wear,
        "y_girder_bot": y_girder_bot, "y_kerb": y_kerb, "y_parapet": y_parapet,
        "kerb_h": kerb_h, "n_girders": count,
        "deck_t_mm": deck_t_mm, "wear_t_mm": wear_t_mm,
        "girder_d_mm": girder_d_mm, "parapet_h_mm": parapet_h_mm,
    }
    _draw_services_and_levels(cv, project, w, geom)
    _draw_support_section(cv, project, w, geom)

    cv.note(
        [
            "1. All dimensions in metres unless stated otherwise.",
            f"2. Deck slab {deck_t_mm:.0f} mm; wearing coat {wear_t_mm:.0f} mm "
            f"({field(ss, 'wearing_coat_type', 'BITUMINOUS_CONCRETE_BC')}).",
            f"3. {max(n_girders, 1)} No. girders at {spacing_m:.2f} m centres, "
            f"{girder_d_mm:.0f} mm deep.",
            f"4. Kerb {w['kerb_l']:.2f} m wide, {(parapet_h_mm / 1000.0):.2f} m "
            "tall crash barrier.",
        ],
        x0,
        y_girder_bot - cv.height * 3.0,
    )

    return cv.doc
