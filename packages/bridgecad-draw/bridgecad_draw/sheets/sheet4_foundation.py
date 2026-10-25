"""bridgecad_draw.sheets.sheet4_foundation — the foundation general arrangement.

Wing-16. Two panels: the foundation elevation (pile cap or well, driven off the
foundation block and the four levels) and the foundation plan. Scour, founding
and bearing levels are drawn as lines on named layers *and* annotated, because a
level line with no RL tag is a line, not a level.

Levels are annotated as text rather than placed through ``Canvas.y``: sheet 4's
declared datum is RL 0, and at 1:100 the founding level of a typical bridge is
more than a sheet-height above that datum.
"""
from __future__ import annotations

from bridgecad_draw.primitives import circle as _circle
from bridgecad_draw.sheets._common import Canvas, field

SHEET = "sheet4_foundation"
TITLE = "S4 Foundation General Arrangement"
INDEX = 4


def _pile_grid(fd) -> tuple[int, int]:
    """(rows, cols) from the model's pile group config, e.g. "2x2"."""
    cfg = str(field(fd, "pile_group_config", "") or "").replace("×", "x").upper()
    if "X" in cfg:
        try:
            rows, cols = cfg.split("X")[:2]
            return max(int(rows), 1), max(int(cols), 1)
        except ValueError:
            pass
    return 2, 2


def build(project):
    """Build the foundation general arrangement for *project*."""
    cv = Canvas(SHEET, TITLE, INDEX)
    fd = project.foundation_details
    levels = project.levels

    scour_rl = float(levels.founding_level_m or 0.0)
    bearing_rl = float(levels.deck_level_m or 0.0)
    hfl_rl = float(levels.hfl_m or 0.0)

    pile_d_mm = float(field(fd, "pile_diameter_mm", 1000) or 1000)
    pile_l_m = float(field(fd, "pile_length_m", 12.0) or 12.0)
    cap_t_mm = float(field(fd, "pile_cap_thickness_mm", 1200) or 1200)
    spacing_m = float(field(fd, "pile_spacing_m", 2.0) or 2.0)
    cap_kpa = float(field(fd, "bearing_capacity_kpa", 0.0) or 0.0)
    rows, cols = _pile_grid(fd)
    n_piles = rows * cols

    well_d_m = float(field(fd, "well_diameter_m", 0.0) or 0.0)

    # ── panel A — foundation elevation ─────────────────────────────────────
    x_a = cv.mm(5.0)
    cap_w = cv.mm(max(spacing_m * (cols - 1) + 1.5, 2.4))
    cap_t = cv.mm(cap_t_mm / 1000.0)
    pile_l = cv.mm(pile_l_m)
    pile_w = cv.mm(max(pile_d_mm / 1000.0, 0.8))
    y_cap_top = cv.mm(16.0)
    y_cap_bot = y_cap_top - cap_t
    y_pile_bot = y_cap_bot - pile_l
    y_bearing = y_cap_top + cv.mm(6.0)

    with cv.on("FOUND-CAP"):
        cv.rect(x_a, y_cap_bot, cap_w, cap_t)
    with cv.on("HTCH"):
        cv.hatch(x_a, y_cap_bot, cap_w, cap_t, pattern="ANSI31", scale=cv.height * 0.4)
    with cv.on("FOUND-PILE"):
        for c in range(cols):
            px = x_a + cap_w * (c + 0.5) / cols - pile_w / 2.0
            cv.rect(px, y_pile_bot, pile_w, pile_l - cap_t * 0.0)
    with cv.on("HIDD"):
        cv.dash((x_a - cv.height * 4, y_pile_bot), (x_a + cap_w + cv.height * 4, y_pile_bot))
        cv.dash((x_a - cv.height * 4, y_bearing), (x_a + cap_w + cv.height * 4, y_bearing))
    with cv.on("CIVIL-SCOUR"):
        cv.dash((x_a - cv.height * 6, y_cap_bot), (x_a + cap_w + cv.height * 6, y_cap_bot),
                linetype="DASHED2")
    with cv.on("CIVIL-HFL"):
        cv.dash((x_a - cv.height * 6, y_cap_top + cv.height * 3),
                (x_a + cap_w + cv.height * 6, y_cap_top + cv.height * 3))
    with cv.on("TEXT-LEVEL"):
        cv.text(f"SCOUR LEVEL RL {scour_rl:.3f}", x_a + cap_w + cv.height * 5, y_cap_bot)
        cv.text(f"FOUNDATION LEVEL RL {scour_rl - pile_l_m - cap_t_mm / 1000.0:.3f}",
                x_a + cap_w + cv.height * 5, y_pile_bot)
        cv.text(f"BEARING LEVEL RL {bearing_rl:.3f}", x_a + cap_w + cv.height * 5, y_bearing)
        cv.text(f"HFL RL {hfl_rl:.3f}", x_a + cap_w + cv.height * 5,
                y_cap_top + cv.height * 3)
    with cv.on("TEXT-HEADER"):
        cv.text("FOUNDATION ELEVATION — PIER", x_a + cap_w / 2.0,
                y_bearing + cv.height * 3.5, halign="CENTER")

    # ── panel B — foundation plan ──────────────────────────────────────────
    x_b = cv.mm(42.0)
    y_b = cv.mm(9.0)
    if well_d_m > 0:
        r_out = cv.mm(well_d_m / 2.0)
        t_stein = cv.mm((float(field(fd, "well_steining_tmm", 800) or 800)) / 1000.0)
        with cv.on("FOUND-WELL"):
            _circle(cv.ms, x_b + r_out, y_b + r_out, r_out, layer=cv.ms.layer_name)
            _circle(cv.ms, x_b + r_out, y_b + r_out, max(r_out - t_stein, r_out * 0.5),
                    layer=cv.ms.layer_name)
        with cv.on("TEXT"):
            cv.text(f"WELL Ø {well_d_m:.2f} m", x_b, y_b + 2 * r_out + cv.height * 2.0)
    else:
        cell = cv.mm(spacing_m)
        r = cv.mm(max(pile_d_mm / 2000.0, 0.4))
        for i in range(rows):
            for j in range(cols):
                cxx = x_b + r + j * cell
                cyy = y_b + r + i * cell
                with cv.on("FOUND-PILE"):
                    _circle(cv.ms, cxx, cyy, r, layer=cv.ms.layer_name)
                with cv.on("CL"):
                    cv.line((cxx - r * 2, cyy), (cxx + r * 2, cyy))
                    cv.line((cxx, cyy - r * 2), (cxx, cyy + r * 2))
        with cv.on("TEXT"):
            cv.text(f"{n_piles} No. PILES Ø {pile_d_mm:.0f} mm", x_b,
                    y_b + rows * cell + cv.height * 2.0)

    # ── dimensions ─────────────────────────────────────────────────────────
    with cv.on("DIM"):
        cv.dimension((x_a, y_cap_bot), (x_a + cap_w, y_cap_bot),
                     base=(x_a + cap_w / 2.0, y_cap_bot - cv.height * 3.0),
                     text=f"CAP {cap_w / 1000.0:.2f} m")
        cv.dimension((x_a - cv.height * 3, y_cap_bot), (x_a - cv.height * 3, y_cap_top),
                     base=(x_a - cv.height * 12, y_cap_bot), angle=90.0,
                     text=f"CAP {cap_t_mm:.0f} mm")
        cv.dimension((x_a + cap_w + cv.height * 3, y_pile_bot),
                     (x_a + cap_w + cv.height * 3, y_cap_bot),
                     base=(x_a + cap_w + cv.height * 12, y_pile_bot), angle=90.0,
                     text=f"PILE {pile_l_m:.2f} m")
        cv.dimension((x_a, y_cap_top), (x_a, y_bearing),
                     base=(x_a - cv.height * 3.0, y_cap_top), angle=90.0,
                     text="BEARING LEVEL")
        if well_d_m <= 0:
            cv.dimension((x_b, y_b), (x_b + cols * cv.mm(spacing_m), y_b),
                         base=(x_b + cols * cv.mm(spacing_m) / 2.0,
                               y_b - cv.height * 3.0),
                         text=f"PILE SPACING {spacing_m:.2f} m")

    cv.note([
        "1. All dimensions in metres unless stated otherwise.",
        f"2. Safe bearing capacity {cap_kpa:.0f} kPa at founding level "
        f"RL {scour_rl - pile_l_m - cap_t_mm / 1000.0:.3f}.",
        f"3. Pile cut-off level RL "
        f"{float(field(fd, 'pile_cutoff_level_m', scour_rl) or scour_rl):.3f}.",
        "4. Founding stratum to be confirmed by the geotechnical report.",
    ], x_b, y_b + cv.mm(6.0))

    return cv.doc
