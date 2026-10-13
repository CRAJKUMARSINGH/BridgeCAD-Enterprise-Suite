"""CSV BOQ formatter — flat CSV for import into spreadsheets."""
from __future__ import annotations
import csv
from pathlib import Path
from typing import Any


def format_csv(boq: Any, output_path: str | Path) -> Path:
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["Project", boq.project_name])
        writer.writerow(["Bridge",  boq.bridge_name])
        writer.writerow(["Chainage km", boq.chainage_km])
        writer.writerow([])
        writer.writerow(["Item Code", "Section", "Description", "Unit",
                          "Quantity", "Rate (INR)", "Amount (INR)", "Ref"])
        for sec in boq.sections:
            for item in sec.items:
                writer.writerow([
                    item.item_code, sec.title, item.description, item.unit,
                    float(item.quantity),
                    float(item.rate) if item.rate else "",
                    float(item.amount) if item.amount else "",
                    item.ref,
                ])
        writer.writerow([])
        writer.writerow(["", "", "SUB-TOTAL", "", "", "", float(boq.subtotal), ""])
        writer.writerow(["", "", f"CONTINGENCY {boq.contingency_pct}%", "",
                          "", "", float(boq.contingency_amount), ""])
        writer.writerow(["", "", "GRAND TOTAL", "", "", "",
                          float(boq.grand_total), ""])
    return p


__all__ = ["format_csv"]
