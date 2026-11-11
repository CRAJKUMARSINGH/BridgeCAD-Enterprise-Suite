"""
bridgecad_draw.sheet3_cross_section — Sheet 3: Typical Mid-Span Cross Section.

Production-quality drawing:
  - True PSC Box Girder single-cell cross-section (bottom slab + webs + top flange + haunches)
  - True RCC T-Beam cross-section (stem + top flange + diaphragm indication)
  - True I-Girder cross-section (top flange + web + bottom flange)
  - Solid Slab cross-section
  - Full-width deck slab with hatching (ANSI31 = concrete)
  - Wearing coat (AR-SAND = bituminous)
  - New Jersey / W-beam / RCC parapet correct profiles
  - Kerb and footpath correct geometry
  - Parabolic camber shown as DASHED line on SUPER-CAMBER layer
  - ezdxf native linear dimensions (proper arrowheads + extension lines)
  - RL level tags at each structural level
  - Zone labels with leaders
  - IRC SP:55 layer names, lineweights, text hierarchy
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .dxf_engine import new_sheet, save
from .primitives import (
    dim_linear_h,
    dim_linear_v,
    hatch_poly,
    hatch_rect,
    level_tag,
    line,
    polyline,
    rectangle,
    scale_bar,
    text,
)
from .titleblocks import draw_border, draw_title_block

# ── Constants ────────────────────────────────────────────────────────────────
_SHEET_CX = 420.0  # A1 horizontal centre (mm)
_BASE_Y = 200.0  # road surface Y on sheet (mm)

# Bounded annotation gutters (mm). Previously these were written as multiples of
# the fit scale (``th * 18`` …), so a narrow section — which is drawn at the
# largest scale — pushed the dimension staffs and level labels clean off the A1
# frame. They are now fixed paper millimetres, and the section is fitted into
# 560 mm (not 650) so ~140 mm of clear gutter remains on both sides for any width.
_FIT_W = 560.0  # transverse fit budget (mm) inside the sheet
_OFF_DIM_R = 16.0  # right dimension staff, from half overall width
_OFF_DIM_RS = 12.0  # separation between successive right vertical staffs
_OFF_DIM_L = 12.0  # left dimension staff, from half overall width
_OFF_DIM_LS = 12.0  # separation between successive left vertical staffs
_OFF_GS = 12.0  # girder-spacing dimension, below girder soffit
_OFF_CW = 26.0  # carriageway dimension, below girder soffit
_OFF_OW = 46.0  # overall-width dimension, below girder soffit
_OFF_SB = 70.0  # scale-bar baseline, below girder soffit


def generate(project: Any, output_path: str | Path, scale_denom: int = 50) -> Path:
    """Generate Sheet 3 — Typical Mid-Span Cross Section (production quality)."""
    doc, msp = new_sheet("S3 Cross Section")
    _draw(msp, project, scale_denom)
    return save(doc, output_path)


def _draw(msp: Any, project: Any, scale_denom: int = 50) -> None:
    from bridgecad_core.geometry import compute_cross_section_geometry

    gi = project.geometry_input
    ss = project.superstructure
    pm = project.project_master

    cs = compute_cross_section_geometry(project)
    sst = str(getattr(ss.type, "name", ss.type)).upper()
    is_box = "BOX" in sst
    is_t = "T_BEAM" in sst or "TBEAM" in sst
    is_psc = "PSC" in sst or "I_GIRDER" in sst
    is_slab = "SLAB" in sst and "VOID" not in sst

    # ── Scale: fit overall width into the transverse budget ──────────────────
    ow_m = float(cs.overall_width_m)
    sc = min(_FIT_W / max(ow_m, 0.1), 35.0)
    cx = _SHEET_CX
    base_y = _BASE_Y

    deck_t_m = float(ss.deck_thickness_mm or 230) / 1000.0
    wc_t_m = float(ss.wearing_coat_thickness_mm or 65) / 1000.0
    gd_m = float(ss.girder_depth_mm or 1200) / 1000.0
    gs_m = float(ss.girder_spacing_m or 2.5)
    n_g = int(ss.girders_per_deck_count or 4)
    cw = float(gi.carriageway_width_m)
    half_ow = ow_m / 2.0
    half_cw = cw / 2.0
    fp_l = float(gi.footpath_left_m or 0.0)
    fp_r = float(gi.footpath_right_m or 0.0)
    kerb_l = float(gi.kerb_width_left_m or 0.25)
    kerb_r = float(gi.kerb_width_right_m or 0.25)
    camber_mm = float(gi.camber_mm or 0.0)
    par_h_m = float(ss.parapet_height_mm or 1000) / 1000.0

    # Adaptive text height, capped so the right-hand annotation block (RL value
    # plus descriptive label) still fits the ~130 mm gutter that the 560 mm fit
    # budget leaves. Un-capped, a narrow section draws at sc=35 → th=8.75, and on
    # a wide box the "GIRDER SOFFIT / RL" label ran ~24 mm past the right border.
    th = min(6.0, max(2.2, sc * 0.25))

    def hx(x_m):
        return cx + x_m * sc  # transverse offset → sheet X

    def vy(y_m):
        return base_y + y_m * sc  # vertical (m) → sheet Y

    # ── BORDER + TITLE BLOCK ─────────────────────────────────────────────────
    draw_border(msp, "A1")
    draw_title_block(
        msp,
        project_title=getattr(pm, "project_title", "") or "",
        bridge_name=getattr(pm, "bridge_name", "") or "",
        drawing_no=getattr(pm, "drawing_no", "GAD-003") or "GAD-003",
        drawing_title="TYPICAL MID-SPAN CROSS SECTION",
        revision=getattr(getattr(pm, "revision", None), "name", "R0") or "R0",
        sheet_no="3",
        total_sheets="9",
    )

    # ── WEARING COAT ─────────────────────────────────────────────────────────
    # Carriageway WC only (not footpath)
    wc_y = base_y
    wc_h = wc_t_m * sc
    hatch_rect(
        msp,
        hx(-half_cw),
        wc_y - wc_h,
        cw * sc,
        wc_h,
        pattern="AR-SAND",
        scale=sc * 0.004,
        layer="SUPER-WEARING",
        color=8,
    )
    rectangle(msp, hx(-half_cw), wc_y - wc_h, cw * sc, wc_h, layer="SUPER-WEARING")

    # ── DECK SLAB ─────────────────────────────────────────────────────────────
    slab_top = wc_y - wc_h
    slab_bot = slab_top - deck_t_m * sc
    rectangle(msp, hx(-half_ow), slab_bot, ow_m * sc, deck_t_m * sc, layer="SUPER-DECK", lw=50)
    hatch_rect(
        msp,
        hx(-half_ow),
        slab_bot,
        ow_m * sc,
        deck_t_m * sc,
        pattern="ANSI31",
        scale=sc * 0.02,
        layer="STRUC-HATCHING",
    )

    # ── SUPERSTRUCTURE (girder type-specific) ─────────────────────────────────
    gird_top = slab_bot
    gird_bot = gird_top - gd_m * sc

    if is_box:
        # PSC Mono Box Girder — top flange + two webs + bottom flange + haunches
        tw = max(0.25, ow_m * 0.06) * sc  # web thickness (mm)
        bf_h = gd_m * 0.15 * sc  # bottom flange height
        gd_m * 0.12 * sc  # haunch
        ow_m * 0.6 * sc  # inner void width
        inner_h = (gd_m - deck_t_m - bf_h / sc) * sc * 0.88  # inner void height

        # Outer box outline
        box_pts = [
            (hx(-half_ow), gird_top),
            (hx(half_ow), gird_top),
            (hx(half_ow), gird_bot + bf_h),
            (hx(half_ow) - tw, gird_bot + bf_h),
            (hx(half_ow) - tw, gird_bot),
            (hx(-half_ow) + tw, gird_bot),
            (hx(-half_ow) + tw, gird_bot + bf_h),
            (hx(-half_ow), gird_bot + bf_h),
        ]
        polyline(msp, box_pts, layer="SUPER-GIRDER", close=True, lw=50)
        hatch_poly(msp, box_pts, pattern="ANSI31", scale=sc * 0.018, layer="STRUC-HATCHING")

        # Inner void cutout (white/no-hatch region) — draw void boundary
        void_x0 = hx(-half_ow) + tw
        void_y0 = gird_bot + bf_h
        void_w = ow_m * sc - 2 * tw
        void_h = inner_h
        if void_w > 10 and void_h > 10:
            rectangle(msp, void_x0, void_y0, void_w, void_h, layer="SUPER-GIRDER")
            # White fill for void (solid hatch background = sheet paper white)
            h = msp.add_hatch(dxfattribs={"layer": "STRUC-HATCHING", "color": 0})
            h.set_solid_fill()
            h.paths.add_polyline_path(
                [
                    (void_x0, void_y0),
                    (void_x0 + void_w, void_y0),
                    (void_x0 + void_w, void_y0 + void_h),
                    (void_x0, void_y0 + void_h),
                ],
                is_closed=True,
            )

        text(
            msp,
            "PSC MONO-BOX GIRDER",
            hx(0),
            gird_bot - th * 4,
            height=th * 1.2,
            layer="TEXT-GENERAL",
            halign="CENTER",
        )

    elif is_t:
        # RCC T-Beam girder cross-section
        stem_w = max(0.25, min(0.45, gd_m * 0.28)) * sc
        flg_w = gs_m * sc * 0.95
        g_cents = [(i - (n_g - 1) / 2.0) * gs_m for i in range(n_g)]
        for gx in g_cents:
            # Stem
            pts_stem = [
                (hx(gx) - stem_w / 2, gird_top),
                (hx(gx) + stem_w / 2, gird_top),
                (hx(gx) + stem_w / 2, gird_bot),
                (hx(gx) - stem_w / 2, gird_bot),
            ]
            polyline(msp, pts_stem, layer="SUPER-GIRDER", close=True, lw=40)
            hatch_poly(msp, pts_stem, pattern="ANSI31", scale=sc * 0.016, layer="STRUC-HATCHING")
            # Top flange indication (dashed - already part of deck slab)
            line(
                msp,
                (hx(gx) - flg_w / 2, slab_bot),
                (hx(gx) + flg_w / 2, slab_bot),
                layer="STRUC-CENTRE",
            )
        text(
            msp,
            "RCC T-BEAM GIRDERS",
            hx(0),
            gird_bot - th * 4,
            height=th * 1.2,
            layer="TEXT-GENERAL",
            halign="CENTER",
        )

    elif is_psc:
        # PSC I-Girder cross-section — top flange + web + bottom flange
        tf_w = gs_m * sc * 0.45  # top flange half-width
        tw_ = gd_m * 0.10 * sc  # web thickness
        bf_w = gs_m * sc * 0.20  # bottom flange half-width
        tf_h = gd_m * 0.12 * sc  # top flange height
        bf_h = gd_m * 0.12 * sc  # bottom flange height
        g_cents = [(i - (n_g - 1) / 2.0) * gs_m for i in range(n_g)]
        for gx in g_cents:
            # I-section outline
            pts = [
                (hx(gx) - tf_w, gird_top),
                (hx(gx) + tf_w, gird_top),
                (hx(gx) + tf_w, gird_top - tf_h),
                (hx(gx) + tw_ / 2, gird_top - tf_h),
                (hx(gx) + tw_ / 2, gird_bot + bf_h),
                (hx(gx) + bf_w, gird_bot + bf_h),
                (hx(gx) + bf_w, gird_bot),
                (hx(gx) - bf_w, gird_bot),
                (hx(gx) - bf_w, gird_bot + bf_h),
                (hx(gx) - tw_ / 2, gird_bot + bf_h),
                (hx(gx) - tw_ / 2, gird_top - tf_h),
                (hx(gx) - tf_w, gird_top - tf_h),
            ]
            polyline(msp, pts, layer="SUPER-GIRDER", close=True, lw=40)
            hatch_poly(msp, pts, pattern="ANSI31", scale=sc * 0.014, layer="STRUC-HATCHING")
        text(
            msp,
            "PSC I-GIRDERS",
            hx(0),
            gird_bot - th * 4,
            height=th * 1.2,
            layer="TEXT-GENERAL",
            halign="CENTER",
        )

    elif is_slab:
        # Solid slab — just the deck (already drawn)
        gird_bot = slab_bot  # no separate girder
        text(
            msp,
            "RCC SOLID SLAB",
            hx(0),
            slab_bot - th * 4,
            height=th * 1.2,
            layer="TEXT-GENERAL",
            halign="CENTER",
        )

    # ── KERBS ─────────────────────────────────────────────────────────────────
    kerb_h = 0.22 * sc
    kerb_profile_l = [
        (hx(-half_cw - kerb_l), wc_y),
        (hx(-half_cw), wc_y),
        (hx(-half_cw), wc_y + kerb_h * 0.6),
        (hx(-half_cw - kerb_l * 0.3), wc_y + kerb_h),
        (hx(-half_cw - kerb_l), wc_y + kerb_h),
    ]
    polyline(msp, kerb_profile_l, layer="SUPER-KERB", close=True, lw=35)
    hatch_poly(msp, kerb_profile_l, pattern="ANSI31", scale=sc * 0.014, layer="STRUC-HATCHING")

    # Mirror for right side
    kerb_profile_r = [
        (hx(half_cw), wc_y),
        (hx(half_cw + kerb_r), wc_y),
        (hx(half_cw + kerb_r), wc_y + kerb_h),
        (hx(half_cw + kerb_r * 0.3 + kerb_r * 0.0), wc_y + kerb_h),
        (hx(half_cw), wc_y + kerb_h * 0.6),
    ]
    polyline(msp, kerb_profile_r, layer="SUPER-KERB", close=True, lw=35)
    hatch_poly(msp, kerb_profile_r, pattern="ANSI31", scale=sc * 0.014, layer="STRUC-HATCHING")

    # ── FOOTPATHS ─────────────────────────────────────────────────────────────
    fp_h_m = 0.15 * sc
    if fp_l > 0:
        x0 = hx(-half_ow)
        rectangle(msp, x0, wc_y, fp_l * sc, fp_h_m, layer="SUPER-FOOTPATH", lw=25)
        text(
            msp,
            f"FP {fp_l:.2f}m",
            x0 + fp_l * sc / 2,
            wc_y + fp_h_m + th * 0.5,
            height=th * 0.8,
            layer="TEXT-GENERAL",
            halign="CENTER",
        )
    if fp_r > 0:
        x0 = hx(half_ow - fp_r)
        rectangle(msp, x0, wc_y, fp_r * sc, fp_h_m, layer="SUPER-FOOTPATH", lw=25)

    # ── PARAPETS ─────────────────────────────────────────────────────────────
    par_h = par_h_m * sc
    par_w = 0.25 * sc
    par_type = str(getattr(getattr(ss, "parapet_type", None), "name", "")).upper()

    for side in [-1, 1]:
        xp = hx(side * half_ow) + (-par_w if side == 1 else 0)
        if "NEW_JERSEY" in par_type or "CONCRETE_NEW_JERSEY" in par_type:
            # New Jersey profile (IRC:6 standard barrier shape)
            pts_nj = [
                (xp, wc_y),
                (xp + par_w, wc_y) if side == -1 else (xp, wc_y),
                (xp + par_w * 0.85 if side == -1 else xp + par_w * 0.15, wc_y + par_h * 0.12),
                (xp + par_w * 0.70 if side == -1 else xp + par_w * 0.30, wc_y + par_h * 0.55),
                (xp + par_w * 0.55 if side == -1 else xp + par_w * 0.45, wc_y + par_h * 0.70),
                (xp + par_w * 0.50 if side == -1 else xp + par_w * 0.50, wc_y + par_h),
            ]
            if side == -1:
                pts_nj = [
                    (hx(-half_ow), wc_y),
                    (hx(-half_ow) + par_w, wc_y),
                    (hx(-half_ow) + par_w * 0.85, wc_y + par_h * 0.12),
                    (hx(-half_ow) + par_w * 0.70, wc_y + par_h * 0.55),
                    (hx(-half_ow) + par_w * 0.55, wc_y + par_h * 0.70),
                    (hx(-half_ow) + par_w * 0.50, wc_y + par_h),
                    (hx(-half_ow), wc_y + par_h),
                ]
            else:
                pts_nj = [
                    (hx(half_ow) - par_w, wc_y),
                    (hx(half_ow), wc_y),
                    (hx(half_ow), wc_y + par_h),
                    (hx(half_ow) - par_w * 0.50, wc_y + par_h),
                    (hx(half_ow) - par_w * 0.55, wc_y + par_h * 0.70),
                    (hx(half_ow) - par_w * 0.70, wc_y + par_h * 0.55),
                    (hx(half_ow) - par_w * 0.85, wc_y + par_h * 0.12),
                ]
            polyline(msp, pts_nj, layer="SUPER-PARAPET", close=True, lw=40)
            hatch_poly(msp, pts_nj, pattern="ANSI31", scale=sc * 0.012, layer="STRUC-HATCHING")
        else:
            # Generic RCC vertical/crash parapet
            rectangle(msp, xp, wc_y, par_w, par_h, layer="SUPER-PARAPET", lw=40)
            hatch_rect(
                msp,
                xp,
                wc_y,
                par_w,
                par_h,
                pattern="ANSI31",
                scale=sc * 0.012,
                layer="STRUC-HATCHING",
            )

    # ── CAMBER PARABOLA (dashed reference) ────────────────────────────────────
    if camber_mm > 0:
        cam_pts = []
        for i in range(21):
            xf = -half_cw + i * cw / 20.0
            yf = cs.camber_y_at_x(xf) / 1000.0 * sc * 4
            cam_pts.append((hx(xf), wc_y + yf))
        if len(cam_pts) >= 2:
            polyline(msp, cam_pts, layer="SUPER-CAMBER", color=6)
        text(
            msp,
            f"CAMBER {camber_mm:.0f} mm (IRC:112 Cl.6.5)",
            hx(0),
            wc_y + camber_mm / 1000.0 * sc * 4 + th * 1.2,
            height=th * 0.9,
            layer="SUPER-CAMBER",
            halign="CENTER",
            color=6,
        )

    # ── CENTRELINE ───────────────────────────────────────────────────────────
    cl_top = wc_y + par_h + th * 4
    line(msp, (hx(0), gird_bot - th * 6), (hx(0), cl_top), layer="STRUC-CENTRE")
    text(msp, "CL", hx(0) + th * 0.5, cl_top, height=th * 1.2, layer="STRUC-CENTRE")

    # ── EZDXF NATIVE LINEAR DIMENSIONS ───────────────────────────────────────
    # Carriageway width
    dim_cw_y = gird_bot - _OFF_CW
    try:
        doc = msp.doc
        # Overall width dimension
        dim = (
            doc.dimstyles.new("BRG_DIM")
            if not doc.dimstyles.has_entry("BRG_DIM")
            else doc.dimstyles.get("BRG_DIM")
        )
        dim.dxf.dimtxt = th / 1000.0  # ezdxf: in drawing units (mm)
        dim.dxf.dimasz = th * 1.0
        msp.add_linear_dim(
            base=(hx(0), dim_cw_y),
            p1=(hx(-half_cw), wc_y),
            p2=(hx(half_cw), wc_y),
            text=f"CW={cw:.3f} m",
            dimstyle="BRG_DIM",
            override={
                "dimtxt": th,
                "dimasz": th,
                "dimgap": th * 0.4,
                "dimclrt": 3,
            },
            dxfattribs={"layer": "DIM-LINEAR"},
        ).render()
    except Exception:
        dim_linear_h(
            msp,
            hx(-half_cw),
            wc_y,
            hx(half_cw),
            wc_y,
            dim_y=dim_cw_y,
            label=f"CW={cw:.3f} m",
            text_height=th,
        )

    # Overall width dimension
    dim_ow_y = gird_bot - _OFF_OW
    dim_linear_h(
        msp,
        hx(-half_ow),
        wc_y,
        hx(half_ow),
        wc_y,
        dim_y=dim_ow_y,
        label=f"OW={ow_m:.3f} m",
        text_height=th,
    )

    # Depth dimensions (right side)
    dim_x = hx(half_ow) + _OFF_DIM_R
    if not is_slab and gd_m > 0:
        dim_linear_v(
            msp,
            dim_x,
            gird_bot,
            dim_x,
            slab_bot,
            dim_x=dim_x + _OFF_DIM_RS,
            label=f"GD={gd_m:.3f}m",
            text_height=th * 0.9,
        )
    dim_linear_v(
        msp,
        dim_x,
        slab_bot,
        dim_x,
        wc_y,
        dim_x=dim_x + _OFF_DIM_RS + _OFF_DIM_RS,
        label=f"D={deck_t_m:.3f}m+WC{int(wc_t_m*1000)}mm",
        text_height=th * 0.85,
    )

    # ── Principal section dimensions (IRC SP:55 §4) ───────────────────────
    # Kerb widths (left / right) — transverse.
    kerb_dim_y = wc_y + kerb_h + th * 2.5
    dim_linear_h(
        msp,
        hx(-half_cw - kerb_l),
        kerb_dim_y - th,
        hx(-half_cw),
        kerb_dim_y - th,
        dim_y=kerb_dim_y,
        label=f"KERB L={kerb_l:.2f} m",
        text_height=th * 0.8,
    )
    dim_linear_h(
        msp,
        hx(half_cw),
        kerb_dim_y - th,
        hx(half_cw + kerb_r),
        kerb_dim_y - th,
        dim_y=kerb_dim_y,
        label=f"KERB R={kerb_r:.2f} m",
        text_height=th * 0.8,
    )
    # Wearing coat + deck slab thicknesses — vertical staff at left edge.
    staff_x = hx(-half_ow) - _OFF_DIM_L
    dim_linear_v(
        msp,
        staff_x,
        wc_y - wc_h,
        staff_x,
        wc_y,
        dim_x=staff_x - _OFF_DIM_LS,
        label=f"WC {int(wc_t_m * 1000)}mm",
        text_height=th * 0.8,
    )
    dim_linear_v(
        msp,
        staff_x,
        slab_bot,
        staff_x,
        wc_y - wc_h,
        dim_x=staff_x - _OFF_DIM_LS,
        label=f"DECK {int(deck_t_m * 1000)}mm",
        text_height=th * 0.8,
    )
    # Parapet height — vertical staff at right edge.
    par_x = hx(half_ow) + _OFF_DIM_R
    dim_linear_v(
        msp,
        par_x,
        wc_y,
        par_x,
        wc_y + par_h,
        dim_x=par_x + _OFF_DIM_RS,
        label=f"PAR {int(par_h_m * 1000)}mm",
        text_height=th * 0.8,
    )
    # Girder spacing — transverse between the first two girder centres.
    if not is_slab and n_g >= 2:
        g0 = (0 - (n_g - 1) / 2.0) * gs_m
        g1 = (1 - (n_g - 1) / 2.0) * gs_m
        dim_linear_h(
            msp,
            hx(g0),
            gird_bot - 4.0,
            hx(g1),
            gird_bot - 4.0,
            dim_y=gird_bot - _OFF_GS,
            label=f"GS={gs_m:.2f} m",
            text_height=th * 0.8,
        )

    # ── LEVEL TAGS ───────────────────────────────────────────────────────────
    road_rl = float(getattr(pm, "road_level_rl_m", 0) or 0)
    sof_rl = road_rl - (deck_t_m + wc_t_m) - (0 if is_slab else gd_m)

    tag_x = hx(half_ow) + 3.0
    # Descriptive labels sit clear of the "RL …" value that level_tag writes to
    # the right of the tick (tick half-width 3·th, value ~5·th wide), so the two
    # never overlap; the section is fitted into 560 mm which guarantees the
    # gutter is wide enough for both.
    off_desc = 9.0 * th
    level_tag(msp, tag_x, wc_y, road_rl, text_height=th * 0.9)
    level_tag(msp, tag_x, slab_bot, road_rl - deck_t_m - wc_t_m, text_height=th * 0.9)
    if not is_slab and gd_m > 0:
        level_tag(msp, tag_x, gird_bot, sof_rl, text_height=th * 0.9)

    text(msp, "TOP OF WC / RL", tag_x + off_desc, wc_y, height=th * 0.85, layer="TEXT-LEVEL")
    text(msp, "SOFFIT OF SLAB", tag_x + off_desc, slab_bot, height=th * 0.85, layer="TEXT-LEVEL")
    if not is_slab and gd_m > 0:
        text(
            msp,
            "GIRDER SOFFIT / RL",
            tag_x + off_desc,
            gird_bot,
            height=th * 0.85,
            layer="TEXT-LEVEL",
        )

    # ── DRAINAGE SLOPE ARROW ─────────────────────────────────────────────────
    slope_pct = float(ss.wearing_coat_slope_pct or 2.0)
    for xf, sign in [(-cw * 0.3, -1), (cw * 0.3, 1)]:
        ax1 = hx(xf)
        ay1 = wc_y + camber_mm / 1000.0 * sc * 3 if camber_mm > 0 else wc_y + 0.5
        ax2 = ax1 + sign * cw * sc * 0.18
        ay2 = ay1 - slope_pct / 100.0 * cw * sc * 0.18 * 0.5
        line(msp, (ax1, ay1), (ax2, ay2), layer="DIM-SLOPE", color=3)
    text(
        msp,
        f"{slope_pct:.1f}% XF",
        hx(cw * 0.15),
        wc_y + th * 1.0,
        height=th * 0.85,
        layer="DIM-SLOPE",
        color=3,
    )

    # ── SCALE BAR ─────────────────────────────────────────────────────────────
    # seg_len_m is a paper length in mm (see primitives.scale_bar), so scale the
    # chosen number of metres by the fit scale — otherwise the bar plotted a few
    # millimetres wide with five unreadable labels.
    sb_x = hx(-half_ow)
    sb_y = gird_bot - _OFF_SB
    sb_seg_m = max(1.0, round(24.0 / max(sc, 1e-6)))
    scale_bar(
        msp,
        sb_x,
        sb_y,
        scale_denom,
        segments=4,
        seg_len_m=sb_seg_m * sc,
        text_height=th * 0.85,
    )

    # ── VIEW LABEL ────────────────────────────────────────────────────────────
    view_y = wc_y + par_h + th * 18
    text(
        msp,
        "SECTION A-A — TYPICAL MID-SPAN CROSS SECTION",
        cx,
        view_y,
        height=th * 1.6,
        layer="TEXT-HEADER",
        halign="CENTER",
    )
    sst_label = (
        "PSC BOX GIRDER"
        if is_box
        else ("RCC T-BEAM" if is_t else ("PSC I-GIRDER" if is_psc else "SOLID SLAB"))
    )
    text(
        msp,
        f"{sst_label}  |  Scale 1:{scale_denom}  |  IRC:112-2020",
        cx,
        view_y - th * 4,
        height=th * 1.0,
        layer="TEXT-SPEC",
        halign="CENTER",
    )

    # ── ZONE LABELS ───────────────────────────────────────────────────────────
    label_y = wc_y + par_h + th * 8
    for label, x_m in [
        ("MEDIAN" if float(gi.median_width_m or 0) > 0 else "", 0.0),
        (f"CW {cw:.2f}m", 0.0),
    ]:
        if label:
            text(
                msp, label, hx(x_m), label_y, height=th * 0.9, layer="TEXT-GENERAL", halign="CENTER"
            )


__all__ = ["generate"]
