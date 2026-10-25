"""
bridgecad_draw.sheet7_bill_of_quantities — Sheet 7: Bill of Quantities (Abstract).

Generates a formatted BOQ table directly in DXF:
  - Concrete items (superstructure / substructure / foundation)
  - Reinforcement steel
  - Prestressing steel
  - Wearing coat
  - Bearings & expansion joints
  - Approach slabs
  - Earthwork (embankment)
  - Totals row

Quantities come from BridgeProject.calculations (computed/estimated values).
Unit rates are left blank (TBC by estimator) — this is the abstract BOQ,
not the priced BOQ (that lives in bridgecad-bill).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .dxf_engine import new_sheet, save
from .primitives import LayoutCursor, rectangle, text
from .titleblocks import draw_border, draw_title_block

# MORTH chapter codes (schedule of rates reference)
_BOQ_ITEMS = [
    # (item_no, description, unit, qty_field_or_value, rate_code)
    ("1", "EARTHWORK — EMBANKMENT (IMPORTED MOORUM)", "CUM", "earthwork_cum", "MORTH 300"),
    ("2", "GRANULAR SUB-BASE (GSB) — APPROACH ROAD", "CUM", "gsb_cum", "MORTH 401"),
    ("3", "CONCRETE M25 — PILE FOUNDATION", "CUM", "concrete_found_cum", "MORTH 1700"),
    ("4", "CONCRETE M30 — SUBSTRUCTURE (PIER & ABUTMENT)", "CUM", "concrete_sub_cum", "MORTH 1700"),
    ("5", "CONCRETE M40 — SUPERSTRUCTURE DECK & GIRDERS", "CUM", "concrete_sup_cum", "MORTH 1700"),
    ("6", "REINFORCEMENT STEEL Fe500D — ALL ITEMS", "MT", "rebar_mt", "MORTH 1600"),
    ("7", "PRESTRESSING STEEL (STRANDS G1860)", "MT", "prestress_mt", "MORTH 1600"),
    ("8", "FORMWORK — SUPERSTRUCTURE", "SQM", "formwork_sqm", "MORTH 1700"),
    ("9", "BITUMINOUS CONCRETE (BC) WEARING COAT", "SQM", "wc_sqm", "MORTH 510"),
    ("10", "ELASTOMERIC / POT BEARINGS (SUPPLY & INSTALL)", "EACH", "bearing_nos", "MORTH 2800"),
    ("11", "EXPANSION JOINTS (STRIP SEAL / MODULAR)", "RM", "expjoint_rm", "MORTH 2800"),
    ("12", "APPROACH SLAB M30 (BOTH ENDS)", "CUM", "approach_slab_cum", "MORTH 1700"),
    ("13", "RIVER TRAINING WORKS (LUMP SUM ESTIMATE)", "LS", "river_training_ls", "MORTH 2500"),
    ("14", "RAILING / CRASH BARRIER (M.S. W-BEAM, HDG)", "RM", "railing_rm", "MORTH 800"),
    ("15", "WATERPROOFING MEMBRANE — DECK", "SQM", "waterproof_sqm", "MORTH 2600"),
    ("", "TOTAL (CIVIL WORKS — BRIDGE)", "", "total", ""),
]


def generate(project: Any, output_path: str | Path, scale_denom: int = 1) -> Path:
    doc, msp = new_sheet("S7 BOQ")
    _draw(msp, project)
    return save(doc, output_path)


def _draw(msp: Any, project: Any) -> None:
    pm = project.project_master
    calc = project.calculations
    gi = project.geometry_input
    sub = project.substructure

    draw_border(msp, "A1")
    draw_title_block(
        msp,
        project_title=getattr(pm, "project_title", "") or "",
        bridge_name=getattr(pm, "bridge_name", "") or "",
        drawing_no=getattr(pm, "drawing_no", "GAD-007") or "GAD-007",
        drawing_title="ABSTRACT BILL OF QUANTITIES",
        revision=getattr(getattr(pm, "revision", None), "name", "R0") or "R0",
        sheet_no="7",
        total_sheets="8",
    )

    th = 2.8

    # ── Derive quantities from model ──────────────────────────────────────
    total_len = float(gi.total_length_m)
    overall_w = float(gi.overall_width_m)
    cw = float(gi.carriageway_width_m or 7.5)

    conc_sup = float(getattr(calc, "concrete_volume_superstructure_cum", 0) or 0)
    conc_sub = float(getattr(calc, "concrete_volume_substructure_cum", 0) or 0)
    conc_fnd = float(getattr(calc, "concrete_volume_foundation_cum", 0) or 0)
    rebar_mt = float(getattr(calc, "rebar_weight_tonnes_approx", 0) or 0)
    prestress = float(getattr(calc, "prestress_tonnes_approx", 0) or 0)
    bearing_n = int(getattr(calc, "bearing_count", 0) or 0)
    expjt_n = int(getattr(calc, "expansion_joint_count", 0) or 0)
    total_cost = float(getattr(calc, "total_estimated_quantity_cost_inr", 0) or 0)

    # Derived estimates
    wc_sqm = total_len * cw
    formwork_sqm = conc_sup * 4.5  # approximate ratio
    app_slab_l = float(getattr(sub, "approach_slab_length_m", 3.5) or 3.5)
    app_slab_t = float(getattr(sub, "approach_slab_thickness_mm", 200) or 200) / 1000.0
    approach_cum = app_slab_l * overall_w * app_slab_t * 2  # both ends
    expjt_rm = overall_w * expjt_n
    railing_rm = total_len * 2 + app_slab_l * 4
    waterproof_sqm = total_len * overall_w
    earthwork = total_len * overall_w * 2.5  # rough embankment

    qty_map = {
        "earthwork_cum": f"{earthwork:.1f}",
        "gsb_cum": f"{total_len * cw * 0.25:.1f}",
        "concrete_found_cum": f"{conc_fnd:.2f}",
        "concrete_sub_cum": f"{conc_sub:.2f}",
        "concrete_sup_cum": f"{conc_sup:.2f}",
        "rebar_mt": f"{rebar_mt:.2f}",
        "prestress_mt": f"{prestress:.2f}",
        "formwork_sqm": f"{formwork_sqm:.1f}",
        "wc_sqm": f"{wc_sqm:.1f}",
        "bearing_nos": str(bearing_n),
        "expjoint_rm": f"{expjt_rm:.1f}",
        "approach_slab_cum": f"{approach_cum:.2f}",
        "river_training_ls": "1",
        "railing_rm": f"{railing_rm:.1f}",
        "waterproof_sqm": f"{waterproof_sqm:.1f}",
        "total": f"INR {total_cost:,.0f}" if total_cost else "TBD",
    }

    # ── Table layout (cursor-relative — change row_h / col_w in one place) ──
    tx = 20.0
    ty_start = 490.0
    row_h = 12.0
    headers = ["Item", "Description", "Unit", "Quantity", "Rate (INR)", "Amount (INR)", "Ref."]
    col_w = [15, 175, 22, 35, 45, 55, 30]
    total_w = sum(col_w)
    cell_pad_x = 1.5
    cell_pad_y = 3.5

    # Title band
    rectangle(msp, tx, ty_start + row_h, total_w, row_h * 1.5, layer="TITLEBLK-BOX")
    text(
        msp,
        f"ABSTRACT OF ESTIMATED COST — {getattr(pm,'bridge_name','') or 'BRIDGE'}",
        tx + total_w / 2,
        ty_start + row_h * 1.5,
        height=th * 1.3,
        layer="TEXT-HEADER",
        halign="CENTER",
    )

    # Sub-header row (project summary)
    rectangle(msp, tx, ty_start, total_w, row_h, layer="TITLEBLK-BOX")
    text(
        msp,
        f"Chainage: {float(getattr(pm,'chainage_km',0) or 0):.3f} km  |  "
        f"State: {getattr(getattr(pm,'state_code',None),'name','') or ''}  |  "
        f"Total Length: {total_len:.3f} m  |  Overall Width: {overall_w:.3f} m",
        tx + cell_pad_x,
        ty_start + cell_pad_y,
        height=th * 0.85,
        layer="TEXT-GENERAL",
    )

    # ---- Column headers + data rows + notes all driven by a LayoutCursor ----
    # Cursor starts at the TOP-LEFT of the column-header row and walks DOWN
    # (decreasing y) through data rows, then continues into the notes block.
    table = LayoutCursor(tx, ty_start - row_h)

    # -- Column headers (one row, columns advance LEFT → RIGHT per cell) --
    row_start_x = table.x
    for hdr, cw in zip(headers, col_w, strict=False):
        table.rect(msp, cw, row_h, layer="TITLEBLK-BOX")
        text(
            msp,
            hdr,
            table.x + cell_pad_x,
            table.y + cell_pad_y,
            height=th * 0.9,
            layer="TEXT-GENERAL",
        )
        table.advance_x(cw)

    # Descend to the top of the FIRST data row.
    table.move_to(row_start_x, table.y - row_h)

    # -- Data rows: outer cursor walks DOWN, inner cursor walks column widths
    for item_no, desc, unit, qty_key, ref in _BOQ_ITEMS:
        qty_str = qty_map.get(qty_key, "")
        is_total = item_no == ""
        vals = [item_no, desc, unit, qty_str, "TBC", "", ref]

        row_save = table.x, table.y
        for val, cw in zip(vals, col_w, strict=False):
            table.rect(msp, cw, row_h, layer="TITLEBLK-BOX")
            text(
                msp,
                str(val)[:28],
                table.x + cell_pad_x,
                table.y + cell_pad_y,
                height=th * (1.0 if is_total else 0.85),
                layer="TEXT-GENERAL",
            )
            table.advance_x(cw)
        if is_total and qty_str:
            # Bold total figure in the Quantity column (index 3 → sum col_w[:3])
            bold_x = row_start_x + sum(col_w[:3])
            text(
                msp,
                qty_str,
                bold_x + cell_pad_x,
                row_save[1] + cell_pad_y,
                height=th,
                layer="TEXT-HEADER",
            )

        # Next row starts below (y decreases by row_h) and at the left edge.
        table.move_to(row_start_x, row_save[1] - row_h)

    # ---- Notes block — uses the cursor's final y so adding/removing BOQ rows
    # automatically moves the notes up or down — no hand-edited offset.
    notes = [
        "NOTES:",
        "1. Quantities are preliminary estimates for budget purposes only.",
        "2. Final quantities to be measured as per IS:1200 / MORTH specifications.",
        "3. Rates as per prevailing State PWD / MORTH Schedule of Rates.",
        "4. 15% contingency to be added for unforeseen items.",
        f"5. Preliminary estimated cost: INR {total_cost:,.0f}"
        if total_cost
        else "5. Preliminary estimated cost: To Be Determined (TBD).",
    ]
    table.advance_y(-5.0)  # small gap between last row and notes heading
    for i, n in enumerate(notes):
        text(
            msp,
            n,
            tx,
            table.y,
            height=th * (1.0 if i == 0 else 0.85),
            layer="TEXT-SPEC" if i > 0 else "TEXT-GENERAL",
        )
        table.advance_y(-7.5)


__all__ = ["generate"]
