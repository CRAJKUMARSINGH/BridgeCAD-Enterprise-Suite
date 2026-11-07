"""
bridgecad_export.bbs — Bar bending schedule (BBS) generator.

GAD-stage only: reinforcement is inferred from member dimensions and the
modelled bar inputs, then expressed as bar marks with shape codes so a
detailer has a starting schedule.  Not a substitute for the detail sheet.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# kg/m, IS 1786 nominal mass
_UNIT_MASS = {8: 0.395, 10: 0.617, 12: 0.888, 16: 1.580, 20: 2.470, 25: 3.850, 32: 6.310}

# shape code -> description
_SHAPES = {"00": "Straight", "21": "L-bend", "51": "U-stirrup"}


@dataclass
class BbsRow:
    member: str
    bar_mark: str
    diameter_mm: int
    shape_code: str
    cut_length_m: float
    count: int
    total_mass_kg: float

    # IS 2502 schedule columns (derived, kept in sync with the base fields)
    @property
    def total_length_m(self) -> float:
        return round(self.cut_length_m * self.count, 3)

    @property
    def unit_weight_kg_m(self) -> float:
        return _UNIT_MASS.get(self.diameter_mm, 0.0)

    @property
    def weight_kg(self) -> float:
        return round(self.unit_weight_kg_m * self.total_length_m, 2)


def _mass(dia: int, length_m: float, count: int) -> float:
    return _UNIT_MASS.get(dia, 0.0) * length_m * count


def _bar(value: int | None, default: int) -> int:
    return int(value) if value else default


def _spacing_m(value: float | int | None, default_mm: int) -> float:
    if value is None:
        return default_mm / 1000.0
    v = float(value)
    # Modelled spacing fields are mm; tolerate a metres value (< 1) by treating
    # it as already-metres only when it is implausibly small for mm.
    return v / 1000.0 if v > 50 else v


def generate_rows(project: Any) -> list[BbsRow]:
    sub = project.substructure
    fd = project.foundation_details
    rows: list[BbsRow] = []

    abt_h = float(sub.abutment_height_m or 3.0)
    abt_l = float(sub.abutment_length_m or 11.0)
    abt_w = float(sub.abutment_width_m or 1.2)
    dw_t = float(sub.dirt_wall_thickness_mm or 300) / 1000.0

    main_d = _bar(getattr(sub, "abutment_main_bar_dia_mm", None), 20)
    main_s = _spacing_m(getattr(sub, "abutment_main_bar_spacing_mm", None), 150)
    link_d = _bar(getattr(sub, "abutment_link_dia_mm", None), 12)
    link_s = _spacing_m(getattr(sub, "abutment_link_spacing_mm", None), 200)
    cap_bar_d = _bar(getattr(sub, "cap_main_bar_dia_mm", None), 25)
    cap_bar_s = _spacing_m(getattr(sub, "cap_main_bar_spacing_mm", None), 150)
    dw_v_dia = _bar(getattr(sub, "dirt_wall_vert_bar_dia_mm", None), 16)
    dw_v_sp = _spacing_m(getattr(sub, "dirt_wall_vert_bar_spacing_mm", None), 150)
    dw_h_dia = _bar(getattr(sub, "dirt_wall_horiz_bar_dia_mm", None), 12)
    dw_h_sp = _spacing_m(getattr(sub, "dirt_wall_horiz_bar_spacing_mm", None), 200)

    # Abutment shaft — main bars both faces + links
    n_main = max(4, int(abt_l / main_s))
    rows.append(
        BbsRow(
            "Abutment shaft",
            "A1",
            main_d,
            "21",
            abt_h + 0.45,
            n_main,
            _mass(main_d, abt_h + 0.45, n_main),
        )
    )
    n_link = max(3, int(abt_h / link_s))
    link_len = 2 * (abt_w + 0.05) - 0.10
    rows.append(
        BbsRow(
            "Abutment shaft", "A2", link_d, "51", link_len, n_link, _mass(link_d, link_len, n_link)
        )
    )

    # Cap — main steel both ways + links
    n_cap = max(4, int(abt_l / cap_bar_s))
    rows.append(
        BbsRow(
            "Abutment cap",
            "C1",
            cap_bar_d,
            "21",
            abt_w + 0.30,
            n_cap,
            _mass(cap_bar_d, abt_w + 0.30, n_cap),
        )
    )
    n_cap2 = max(3, int(abt_w / cap_bar_s))
    rows.append(BbsRow("Abutment cap", "C2", 16, "00", abt_l, n_cap2, _mass(16, abt_l, n_cap2)))

    # Dirt wall — vertical bars + horizontal distribution
    n_dw = max(4, int(abt_l / dw_v_sp))
    rows.append(BbsRow("Dirt wall", "D1", dw_v_dia, "21", 1.20, n_dw, _mass(dw_v_dia, 1.20, n_dw)))
    n_dw_h = max(3, int(dw_t / dw_h_sp))
    rows.append(
        BbsRow("Dirt wall", "D2", dw_h_dia, "00", abt_l, n_dw_h, _mass(dw_h_dia, abt_l, n_dw_h))
    )

    # Piles — cage longitudinal
    pile_d = float(fd.pile_diameter_mm or 1000) / 1000.0
    pile_l = float(fd.pile_length_m or 12.0)
    n_cage = max(6, int(3.14159 * pile_d / 0.15))
    rows.append(BbsRow("Bored pile", "P1", 20, "00", pile_l, n_cage, _mass(20, pile_l, n_cage)))

    return rows


def total_mass_kg(project: Any) -> float:
    """Total BBS steel mass for *project*, kg."""
    return sum(r.total_mass_kg for r in generate_rows(project))


def write_csv(project: Any, path: str | Path) -> Path:
    rows = generate_rows(project)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    # IS 2502 column order: mark, dia, shape, length, number, total length,
    # unit weight, weight.
    fields = [
        "bar_mark",
        "diameter_mm",
        "shape_code",
        "cut_length_m",
        "count",
        "total_length_m",
        "unit_weight_kg_m",
        "weight_kg",
        "member",
    ]
    with p.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(fields)
        for r in rows:
            w.writerow(
                [
                    r.bar_mark,
                    r.diameter_mm,
                    r.shape_code,
                    r.cut_length_m,
                    r.count,
                    r.total_length_m,
                    r.unit_weight_kg_m,
                    r.weight_kg,
                    r.member,
                ]
            )
        w.writerow(["TOTAL", "", "", "", "", "", "", f"{total_mass_kg(project):.2f}", ""])
    return p


def write_xlsx(project: Any, path: str | Path) -> Path:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "BBS"
    ws.append(
        [
            "bar_mark",
            "dia_mm",
            "shape",
            "length_m",
            "no",
            "total_len_m",
            "unit_kg_m",
            "weight_kg",
            "member",
        ]
    )
    for r in generate_rows(project):
        ws.append(
            [
                r.bar_mark,
                r.diameter_mm,
                r.shape_code,
                r.cut_length_m,
                r.count,
                r.total_length_m,
                r.unit_weight_kg_m,
                r.weight_kg,
                r.member,
            ]
        )
    ws.append([])
    ws.append(["TOTAL", "", "", "", "", "", "", round(total_mass_kg(project), 2), ""])
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    wb.save(p)
    return p


__all__ = ["BbsRow", "generate_rows", "total_mass_kg", "write_csv", "write_xlsx"]
