"""Excel BOQ formatter — outputs a professional styled .xlsx workbook.

The workbook is *live*: ``Amount`` is ``=D*E`` (quantity × rate), each section
total is ``=SUM(...)`` over its own item rows, and the sub-total / contingency /
grand-total block chains off those cells. A rate change in column E therefore
re-prices the whole bill on open — the sheet is a model, not a screenshot.
Pass ``live_formulas=False`` only for a fully-static export.

Layout contract (column letters are relied on by the formulas and by
``tests/interop``):

    A Item | B Description | C Unit | D Quantity | E Rate | F Amount | G Ref | H Remarks
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

_AMOUNT_COL = 6  # F


def format_excel(boq: Any, output_path: str | Path, live_formulas: bool = True) -> Path:
    """Write *boq* to a styled Excel workbook.

    With *live_formulas* (default) the Amount column and every total are Excel
    formulas; with it off they are the pre-computed values. Returns the saved
    path. Requires openpyxl.
    """
    try:
        import openpyxl
        from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        raise ImportError("openpyxl required: pip install openpyxl") from None

    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "BOQ"

    # Styles
    hdr_font = Font(bold=True, color="FFFFFF", size=11, name="Arial")
    hdr_fill = PatternFill("solid", fgColor="1F3864")
    sec_fill = PatternFill("solid", fgColor="BDD7EE")
    alt_fill = PatternFill("solid", fgColor="F2F2F2")
    cen = Alignment(horizontal="center", vertical="center")
    right = Alignment(horizontal="right")
    thin = Side(style="thin")
    bdr = Border(left=thin, right=thin, top=thin, bottom=thin)

    def _cell(
        r: int,
        c: int,
        val: Any,
        bold: bool = False,
        fill: Any = None,
        align: Any = None,
        num_fmt: str | None = None,
    ) -> Any:
        cell = ws.cell(row=r, column=c, value=val)
        if bold:
            cell.font = Font(bold=True, name="Arial")
        if fill:
            cell.fill = fill
        if align:
            cell.alignment = align
        if num_fmt:
            cell.number_format = num_fmt
        cell.border = bdr
        return cell

    # Title rows
    ws.merge_cells("A1:I1")
    t = ws.cell(row=1, column=1, value=f"ABSTRACT BILL OF QUANTITIES — {boq.project_name}")
    t.font = Font(bold=True, size=14, color="FFFFFF", name="Arial")
    t.fill = PatternFill("solid", fgColor="1F3864")
    t.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 24

    ws.merge_cells("A2:I2")
    ws.cell(row=2, column=1, value=f"Bridge: {boq.bridge_name}  |  Chainage: {boq.chainage_km} km")
    ws.cell(row=2, column=1).alignment = Alignment(horizontal="center")

    # Headers
    headers = [
        "Item",
        "Description",
        "Unit",
        "Quantity",
        "Rate (INR)",
        "Amount (INR)",
        "MORTH Ref",
        "Remarks",
        "",
    ]
    col_w = [10, 60, 10, 14, 16, 18, 14, 20, 5]
    for c, (h, w) in enumerate(zip(headers, col_w, strict=False), 1):
        cell = ws.cell(row=3, column=c, value=h)
        cell.font = hdr_font
        cell.fill = hdr_fill
        cell.alignment = cen
        cell.border = bdr
        ws.column_dimensions[get_column_letter(c)].width = w

    row = 4
    section_total_rows: list[int] = []
    for sec in boq.sections:
        # Section header
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=9)
        sh = ws.cell(row=row, column=1, value=f"{sec.section_code}  {sec.title}")
        sh.font = Font(bold=True, name="Arial", size=10)
        sh.fill = sec_fill
        sh.border = bdr
        ws.row_dimensions[row].height = 16
        row += 1

        first_item_row = row
        for i, item in enumerate(sec.items):
            fill = alt_fill if i % 2 else None
            _cell(row, 1, item.item_code, fill=fill, align=cen)
            _cell(row, 2, item.description, fill=fill)
            _cell(row, 3, item.unit, fill=fill, align=cen)
            _cell(row, 4, float(item.quantity), fill=fill, align=right, num_fmt="#,##0.00")
            _cell(
                row,
                5,
                float(item.rate) if item.rate else "TBC",
                fill=fill,
                align=right,
                num_fmt="#,##0.00",
            )
            # A priced line is a live product of its own quantity and rate.
            amount = f"=D{row}*E{row}" if (live_formulas and item.rate) else _static_amount(item)
            _cell(row, _AMOUNT_COL, amount, fill=fill, align=right, num_fmt="₹#,##0.00")
            _cell(row, 7, item.ref, fill=fill, align=cen)
            _cell(row, 8, item.remarks, fill=fill)
            row += 1
        last_item_row = row - 1

        # Section total — sums this section's own Amount cells.
        st = ws.cell(row=row, column=1, value=f"Total — {sec.title}")
        st.font = Font(bold=True, name="Arial")
        st.border = bdr
        for c in range(2, 9):
            ws.cell(row=row, column=c).border = bdr
        if live_formulas and sec.items:
            total_val: Any = f"=SUM(F{first_item_row}:F{last_item_row})"
        else:
            total_val = float(sec.total)
        amt = ws.cell(row=row, column=_AMOUNT_COL, value=total_val)
        amt.font = Font(bold=True, name="Arial")
        amt.number_format = "₹#,##0.00"
        amt.alignment = right
        amt.border = bdr
        section_total_rows.append(row)
        row += 2

    # Grand total block — each row references the ones above it.
    subtotal_row = row
    contingency_row = row + 1
    if live_formulas and section_total_rows:
        subtotal_expr = "=" + "+".join(f"F{r}" for r in section_total_rows)
    else:
        subtotal_expr = float(boq.subtotal)
    contingency_expr = (
        f"=F{subtotal_row}*{float(boq.contingency_pct)}/100"
        if live_formulas
        else float(boq.contingency_amount)
    )
    grand_expr = f"=F{subtotal_row}+F{contingency_row}" if live_formulas else float(boq.grand_total)
    for label, val in [
        ("SUB-TOTAL (Civil Works)", subtotal_expr),
        (f"CONTINGENCY @ {boq.contingency_pct}%", contingency_expr),
        ("GRAND TOTAL", grand_expr),
    ]:
        ws.cell(row=row, column=1, value=label).font = Font(bold=True, size=11, name="Arial")
        c = ws.cell(row=row, column=_AMOUNT_COL, value=val)
        c.font = Font(bold=True, size=11, name="Arial")
        c.number_format = "₹#,##0.00"
        c.alignment = right
        for col in range(1, 9):
            ws.cell(row=row, column=col).border = bdr
        row += 1

    wb.save(str(p))
    return p


def _static_amount(item: Any) -> Any:
    """Column-F value for a line that has no rate to multiply by."""
    return float(item.amount) if item.amount else 0


__all__ = ["format_excel"]
