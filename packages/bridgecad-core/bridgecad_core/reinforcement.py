"""bridgecad_core.reinforcement — reinforcement items, As/prov and utilisation.

``As,prov`` = ``1000 / spacing * pi * (dia/2)**2`` mm²/m.
``utilisation`` = ``As,req / As,prov`` — below 1.0 is adequate; do not invert.
"""

from __future__ import annotations

import math
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, computed_field

_MINIMA_PATH = Path(__file__).resolve().parent / "standards" / "reinforcement_minima.yaml"


class RebarItem(BaseModel):
    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    mark: str = Field(description="Bar mark, e.g. S1/S2, B1, K1")
    element: str = Field(description="Element key, e.g. ABUTMENT_CAP, DIRT_WALL")
    face: str = Field(description="Face description, e.g. REAR_FACE_VERTICAL")
    section_depth_mm: int = Field(ge=1)
    as_required_mm2_per_m: Decimal = Field(ge=0)
    design_dia_mm: int = Field(ge=6)
    design_spacing_mm: int = Field(ge=50, le=400)
    dia_mm: int | None = Field(default=None, ge=6)
    spacing_mm: int | None = Field(default=None, ge=50, le=400)
    user_defined: bool = False

    @computed_field
    @property
    def as_provided_mm2_per_m(self) -> Decimal:
        spacing = self.spacing_mm if self.spacing_mm is not None else self.design_spacing_mm
        dia = self.dia_mm if self.dia_mm is not None else self.design_dia_mm
        if not spacing:
            return Decimal("0")
        return Decimal(str(1000.0 / spacing * math.pi * (dia / 2.0) ** 2)).quantize(Decimal("0.01"))

    @computed_field
    @property
    def utilisation(self) -> Decimal:
        prov = self.as_provided_mm2_per_m
        if prov <= 0:
            return Decimal("999")
        return (self.as_required_mm2_per_m / prov).quantize(Decimal("0.001"))

    @property
    def source(self) -> str:
        return "minima_table_v1"


def _minima() -> dict[str, Any]:
    return yaml.safe_load(_MINIMA_PATH.read_text(encoding="utf-8")) or {}


def as_required_for(element: str, section_depth_mm: int) -> tuple[Decimal, str]:
    """``(as_req_mm2_per_m, source)`` for *element* at *section_depth_mm*."""
    table = _minima()
    rows = (table.get("elements") or {}).get(element, {}).get("rows") or []
    for row in rows:
        if section_depth_mm <= int(row["depth_max_mm"]):
            return Decimal(str(row["as_req_mm2_per_m"])), str(row.get("source", "minima_table_v1"))
    return Decimal("1000"), "minima_table_v1"


def _item(
    mark: str,
    element: str,
    face: str,
    depth_mm: int,
    design_dia: int,
    design_sp: int,
) -> RebarItem:
    as_req, _src = as_required_for(element, depth_mm)
    return RebarItem(
        mark=mark,
        element=element,
        face=face,
        section_depth_mm=depth_mm,
        as_required_mm2_per_m=as_req,
        design_dia_mm=design_dia,
        design_spacing_mm=design_sp,
    )


def default_items(project: Any) -> list[RebarItem]:
    """Rebar items derived from the modelled bar inputs on *project*."""
    sub = project.substructure
    items: list[RebarItem] = []

    cap_d = int(sub.abutment_cap_depth_mm or 600)
    items.append(
        _item(
            "C1",
            "ABUTMENT_CAP",
            "TOP_BARS",
            cap_d,
            int(sub.cap_main_bar_dia_mm or 25),
            int(sub.cap_main_bar_spacing_mm or 150),
        )
    )
    items.append(
        _item(
            "C2",
            "ABUTMENT_CAP",
            "BOTTOM_BARS",
            cap_d,
            16,
            int(sub.cap_main_bar_spacing_mm or 150),
        )
    )

    abt_h_mm = int(float(sub.abutment_height_m or 3.0) * 1000)
    items.append(
        _item(
            "A1",
            "ABUTMENT_SHAFT",
            "FRONT_FACE_MAIN",
            abt_h_mm,
            int(sub.abutment_main_bar_dia_mm or 20),
            int(sub.abutment_main_bar_spacing_mm or 150),
        )
    )
    items.append(
        _item(
            "A2",
            "ABUTMENT_SHAFT_LINK",
            "LINKS",
            abt_h_mm,
            int(sub.abutment_link_dia_mm or 12),
            int(sub.abutment_link_spacing_mm or 200),
        )
    )

    dw_h_mm = int(float(sub.dirt_wall_height_m or 0.3) * 1000)
    items.append(
        _item(
            "D1",
            "DIRT_WALL",
            "VERTICAL_BARS",
            dw_h_mm,
            int(sub.dirt_wall_vert_bar_dia_mm or 16),
            int(sub.dirt_wall_vert_bar_spacing_mm or 150),
        )
    )
    items.append(
        _item(
            "D2",
            "DIRT_WALL_DIST",
            "HORIZONTAL_DIST",
            dw_h_mm,
            int(sub.dirt_wall_horiz_bar_dia_mm or 12),
            int(sub.dirt_wall_horiz_bar_spacing_mm or 200),
        )
    )

    app_t = int(sub.approach_slab_thickness_mm or 200)
    items.append(
        _item(
            "P1",
            "APPROACH_SLAB",
            "TOP_MESH",
            app_t,
            16,
            150,
        )
    )
    return items


__all__ = ["RebarItem", "as_required_for", "default_items"]
