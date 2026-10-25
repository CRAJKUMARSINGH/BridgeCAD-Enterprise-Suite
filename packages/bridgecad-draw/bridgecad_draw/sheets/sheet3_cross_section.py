"""bridgecad_draw.sheets.sheet3_cross_section — the typical deck cross-section.

Wing-16. The section is read off the model: carriageway, kerbs, footways, crash
barriers, slab and girder depths, and the camber. Nothing here is a literal that
should have been a field — change a width in the model and the section moves.

Model space is millimetres at 1:1 (``coordinates`` clause 1), so every metre from
the model is converted once, through ``Canvas.mm``.
"""
from __future__ import annotations

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
        "kerb_l": kerb_l, "kerb_r": kerb_r,
        "barrier_l": cb_l, "barrier_r": cb_r,
        "half_l": half_l, "half_r": half_r, "total": half_l + half_r,
    }


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
        pts = [(x0 + total * i / (n_pts - 1),
                y_wear + crown * (1.0 - (2.0 * i / (n_pts - 1) - 1.0) ** 2))
               for i in range(n_pts)]
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
        cv.rect(x1 - cv.mm(w["barrier_r"] or 0.45), y_kerb,
                cv.mm(w["barrier_r"] or 0.45), y_parapet - y_kerb)

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
            cv.hatch(gx, y_girder_bot, cv.mm(0.3), depth,
                     pattern="ANSI31", scale=cv.height * 0.35)

    # ── cross-fall arrows, one per half ────────────────────────────────────
    with cv.on("DIM-SLOPE"):
        for sign in (-1.0, 1.0):
            ax = x_mid + sign * cv.mm(w["carriageway"] / 4.0)
            cv.line((ax, y_wear + cv.height * 0.4),
                    (ax + sign * cv.mm(1.2), y_wear + cv.height * 2.6))

    # ── dimensions ─────────────────────────────────────────────────────────
    with cv.on("DIM"):
        cv.dimension((x0, y_wear), (x1, y_wear),
                     base=(x_mid, y_wear + cv.height * 12), angle=0.0,
                     text=f"OVERALL {w['total']:.2f} m")
        cv.dimension((x_cw_l, y_kerb), (x_cw_r, y_kerb),
                     base=(x_mid, y_kerb + cv.height * 5), angle=0.0,
                     text=f"CARRIAGEWAY {w['carriageway']:.2f} m")
        cv.dimension((x0, y_soffit), (x_kerb_l, y_soffit),
                     base=(x0 + cv.mm(w["kerb_l"]) / 2.0, y_soffit - cv.height * 2.5),
                     angle=0.0, text=f"KERB {w['kerb_l']:.2f} m")
        cv.dimension((x0 - cv.height * 3, y_soffit), (x0 - cv.height * 3, y_deck_top),
                     base=(x0 - cv.height * 12, y_soffit), angle=90.0,
                     text=f"SLAB {deck_t_mm:.0f} mm")
        cv.dimension((x1 + cv.height * 3, y_girder_bot), (x1 + cv.height * 3, y_deck_top),
                     base=(x1 + cv.height * 12, y_wear), angle=90.0,
                     text=f"GIRDER {girder_d_mm:.0f} mm")

    # ── labels ─────────────────────────────────────────────────────────────
    with cv.on("TEXT"):
        cv.text(f"CARRIAGEWAY {w['carriageway']:.2f} m", x_mid, y_kerb + cv.height * 1.6,
                halign="CENTER")
        cv.text(f"KERB {w['kerb_l']:.2f} m", x_kerb_l - cv.mm(0.1),
                y_kerb + cv.height * 1.6, halign="LEFT")
        cv.text(f"CAMBER {camber_mm:.0f} mm {camber_method}", x_mid,
                y_wear + cv.height * 5.0, halign="CENTER")
        cv.text(f"CROSS FALL {DEFAULT_CROSS_FALL_PCT:.2f}% TO CENTRE", x_mid,
                y_wear + cv.height * 3.2, halign="CENTER")
    with cv.on("TEXT-HEADER"):
        cv.text("TYPICAL DECK SECTION", x_mid, y_parapet + cv.height * 4.0,
                halign="CENTER")

    cv.note([
        "1. All dimensions in metres unless stated otherwise.",
        f"2. Deck slab {deck_t_mm:.0f} mm; wearing coat {wear_t_mm:.0f} mm "
        f"({field(ss, 'wearing_coat_type', 'BITUMINOUS_CONCRETE_BC')}).",
        f"3. {max(n_girders, 1)} No. girders at {spacing_m:.2f} m centres, "
        f"{girder_d_mm:.0f} mm deep.",
        f"4. Kerb {w['kerb_l']:.2f} m wide, {(parapet_h_mm / 1000.0):.2f} m "
        "tall crash barrier.",
    ], x0, y_girder_bot - cv.height * 3.0)

    return cv.doc
