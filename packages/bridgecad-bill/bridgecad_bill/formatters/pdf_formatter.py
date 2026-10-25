"""A4 PDF bill with header, footer, table pagination — M5.

Current status: "TO BE ISSUED" placeholder sheet. Produces a valid A4 PDF
containing project identification, the section summary, and a prominent "TO BE
ISSUED" banner so the booklet pipeline never raises `NotImplementedError` and
the end-user sees an informative output during M5 development.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _call(obj: Any, fallback: Any) -> Any:
    """Return ``obj()`` if callable else ``obj``; always fall back on error."""
    try:
        return obj() if callable(obj) else obj
    except Exception:
        return fallback


def _count_items(boq: Any) -> int:
    raw = _call(getattr(boq, "all_items", lambda: 0), [])
    try:
        return len(raw)
    except Exception:
        return 0


def format_pdf(boq: Any, output_path: str | Path) -> Path:
    """Generate an A4 PDF BOQ sheet — "TO BE ISSUED" placeholder.

    Parameters
    ----------
    boq : BillOfQuantities
        Populated BOQ instance produced by :func:`bridgecad_bill.processor`.
    output_path : str | Path
        Destination PDF path. Parent directory is created if missing.

    Returns
    -------
    Path
        Absolute path of the written PDF file.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)

    margin_l = margin_r = 20 * mm
    margin_t = 25 * mm
    margin_b = 20 * mm

    doc = SimpleDocTemplate(
        str(p),
        pagesize=A4,
        leftMargin=margin_l,
        rightMargin=margin_r,
        topMargin=margin_t,
        bottomMargin=margin_b,
        title=f"BOQ_{boq.project_name or 'PROJECT'}",
        author="BridgeCAD Enterprise Suite",
        subject="Bill of Quantities — TO BE ISSUED placeholder",
    )

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="Banner",
            parent=styles["Title"],
            fontSize=28,
            leading=34,
            textColor=colors.HexColor("#C0392B"),
            alignment=1,
            spaceAfter=6 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Hdr",
            parent=styles["Heading2"],
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#2C3E50"),
            spaceAfter=2 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Cell",
            parent=styles["Normal"],
            fontSize=9,
            leading=11,
        )
    )

    story: list[Any] = []

    story.append(Paragraph("BILL OF QUANTITIES", styles["Banner"]))
    story.append(
        Paragraph(
            "<para align=center spaceb=12>"
            "<b>STATUS: &nbsp;TO BE ISSUED</b><br/>"
            "<font size=9 color='#555555'>"
            "Detailed rate analysis, break-ups and approved schedule of rates "
            "are under preparation and will be issued in a subsequent revision."
            "</font></para>",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 6 * mm))

    n_items = _count_items(boq)

    project_tbl = Table(
        [
            ["Project Name:", str(getattr(boq, "project_name", "") or "—")],
            ["Bridge Name:", str(getattr(boq, "bridge_name", "") or "—")],
            [
                "Chainage km:",
                str(getattr(boq, "chainage_km", "") or getattr(boq, "chainage", "") or "—"),
            ],
            ["Sections:", str(len(_call(getattr(boq, "sections", []), [])))],
            ["Items:", str(n_items)],
        ],
        colWidths=[40 * mm, 120 * mm],
    )
    project_tbl.setStyle(
        TableStyle(
            [
                ("FONT", (0, 0), (-1, -1), "Helvetica", 10),
                ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 10),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#34495E")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#ECF0F1")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#BDC3C7")),
            ]
        )
    )
    story.append(project_tbl)
    story.append(Spacer(1, 8 * mm))

    story.append(Paragraph("Section Summary", styles["Hdr"]))
    sections = _call(getattr(boq, "sections", []), [])
    summary_rows: list[Any] = [
        ["#", "Code", "Section Title", "Items", "Section Total (INR)"],
    ]
    for i, sec in enumerate(sections, start=1):
        total_sec = _call(getattr(sec, "total", 0), 0)
        try:
            total_str = f"{float(total_sec):,.2f}"
        except Exception:
            total_str = "0.00"
        sec_items = _call(getattr(sec, "items", []), [])
        if not sec_items:
            sec_items = _call(getattr(sec, "all_items", []), [])
        summary_rows.append(
            [
                str(i),
                str(getattr(sec, "section_code", "")),
                Paragraph(str(getattr(sec, "title", "") or "—"), styles["Cell"]),
                str(len(sec_items)),
                total_str,
            ]
        )

    try:
        subtotal_f = float(_call(getattr(boq, "subtotal", 0), 0) or 0)
        contingency_f = float(_call(getattr(boq, "contingency_amount", 0), 0) or 0)
        grand_f = float(_call(getattr(boq, "grand_total", 0), 0) or 0)
        cont_pct = float(_call(getattr(boq, "contingency_pct", 15), 15) or 15)
    except Exception:
        subtotal_f = contingency_f = grand_f = 0.0
        cont_pct = 15
    if not grand_f and subtotal_f:
        grand_f = subtotal_f + contingency_f
    if not contingency_f and subtotal_f:
        contingency_f = subtotal_f * (cont_pct / 100.0)
        grand_f = subtotal_f + contingency_f

    summary_rows.append(["", "", "SUB-TOTAL", "", f"{subtotal_f:,.2f}"])
    summary_rows.append(["", "", f"CONTINGENCY @ {cont_pct:.0f}%", "", f"{contingency_f:,.2f}"])
    summary_rows.append(["", "", "GRAND TOTAL", "", f"{grand_f:,.2f}"])

    summary_tbl = Table(
        summary_rows,
        colWidths=[10 * mm, 20 * mm, 80 * mm, 18 * mm, 32 * mm],
        repeatRows=1,
    )
    n_body = len(summary_rows) - 3
    summary_tbl.setStyle(
        TableStyle(
            [
                ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
                ("FONT", (0, 1), (-1, -1), "Helvetica", 9),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (3, 0), (4, -1), "RIGHT"),
                ("ALIGN", (0, 0), (1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, n_body),
                    [colors.white, colors.HexColor("#F8F9FA")],
                ),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#2C3E50")),
                ("LINEABOVE", (0, n_body + 1), (-1, n_body + 1), 0.25, colors.HexColor("#7F8C8D")),
                ("LINEABOVE", (0, -1), (-1, -1), 1.0, colors.HexColor("#2C3E50")),
                ("FONT", (2, -3), (-1, -1), "Helvetica-Bold", 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(summary_tbl)

    story.append(Spacer(1, 15 * mm))
    story.append(
        Paragraph(
            "<para align=center><i>"
            "This BOQ sheet is a placeholder — not for final tender issue.<br/>"
            "Schedule of rates, item-wise analysis, item code cross-references and "
            "detailed measurements will be appended in the next revision."
            "</i></para>",
            styles["Italic"],
        )
    )

    doc.build(story)
    return p


__all__ = ["format_pdf"]
