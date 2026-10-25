"""bridgecad_bill.formatters — BOQ output formatters (Excel, CSV, PDF, HTML)."""
from html import escape
from typing import Any

from .csv_formatter import format_csv
from .excel_formatter import format_excel
from .pdf_formatter import format_pdf


def _fmt(value: Any, places: int = 2, dash: str = "—") -> str:
    """Render a number for the report; an unknown value shows as a dash."""
    if value is None:
        return dash
    try:
        return f"{float(value):,.{places}f}"
    except (TypeError, ValueError):
        return escape(str(value))


def to_html(lines: list[Any]) -> str:
    """Render BOQ lines to a provenance-aware HTML table.

    Every line shows its status, the formula or multiplier that produced it,
    and the rate source — a reader must not have to open the source to know
    whether a number is calculated, estimated, or absent.
    """
    headers = [
        "Item", "Description", "Unit", "Quantity", "Rate (INR)",
        "Amount (INR)", "Status", "Formula", "Multiplier",
        "Multiplier Source", "Rate Source", "Reason",
    ]
    rows: list[str] = []
    for ln in lines:
        cells = [
            escape(str(getattr(ln, "item_no", ""))),
            escape(str(getattr(ln, "description", ""))),
            escape(str(getattr(ln, "unit", ""))),
            _fmt(getattr(ln, "quantity", None), places=3),
            _fmt(getattr(ln, "rate", None)),
            _fmt(getattr(ln, "amount", None)),
            escape(str(getattr(getattr(ln, "status", None), "value",
                                getattr(ln, "status", "")))),
            escape(str(getattr(ln, "formula", "") or "")),
            _fmt(getattr(ln, "multiplier", None), places=4),
            escape(str(getattr(ln, "multiplier_source", "") or "")),
            escape(str(getattr(getattr(ln, "rate_source", None), "value",
                                getattr(ln, "rate_source", "")))),
            escape(str(getattr(ln, "reason", "") or "")),
        ]
        rows.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")

    head = "".join(f"<th>{escape(h)}</th>" for h in headers)
    body = "\n".join(rows)
    return (
        "<!DOCTYPE html>\n<html><head><meta charset=\"utf-8\">"
        "<title>Bill of Quantities — provenance</title>"
        "<style>table{border-collapse:collapse;font-family:Arial,sans-serif;"
        "font-size:12px}th,td{border:1px solid #999;padding:3px 6px;"
        "text-align:left}th{background:#1F3864;color:#fff}</style></head>\n"
        "<body>\n<h2>Bill of Quantities — line provenance</h2>\n"
        f"<table>\n<thead><tr>{head}</tr></thead>\n<tbody>\n{body}\n"
        "</tbody></table>\n</body></html>\n"
    )


__all__ = ["format_excel", "format_csv", "format_pdf", "to_html"]
