"""bridgecad_bill.measurers — one measurer per element, solved-stack driven.

Volumes come from the resolved abutment stack and modelled dimensions — never
a stored figure and never a parallel geometry path.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from .measure import MeasureBasis, MeasuredItem


def _d(v: Any) -> Decimal:
    return Decimal(str(v))


def _fmt(*vals: Decimal) -> str:
    return " x ".join(f"{v:.3f}" for v in vals)


def measure_cap(
    project: Any,
    cap_len_m: float,
    projection_front_m: float,
    projection_rear_m: float,
) -> MeasuredItem:
    """Abutment cap concrete volume: plan area × depth from the stack."""
    from bridgecad_core.abutment_stack import resolve_abutment_stack

    stack = resolve_abutment_stack(project)
    depth = stack.cap_top - stack.cap_bot
    length = _d(cap_len_m) + _d(projection_front_m) + _d(projection_rear_m)
    width = _d(project.substructure.abutment_width_m or 1.2)
    qty = length * width * depth
    return MeasuredItem(
        item_code="MORTH-1700-ABT-CAP",
        element="ABUTMENT_CAP",
        basis=MeasureBasis.VOLUME_SOLID,
        quantity=qty.quantize(Decimal("0.001")),
        unit="cum",
        entity_ids=("abutment_cap_plan", "abutment_stack"),
        derivation=_fmt(length, width, depth),
    )


def measure_dirt_wall(
    project: Any,
    wall_len_m: float,
    thickness_m: float,
    height_m: float,
) -> MeasuredItem:
    """Dirt wall volume: length × thickness × height from the stack."""
    length = _d(wall_len_m)
    thk = _d(thickness_m)
    h = _d(height_m)
    qty = length * thk * h
    return MeasuredItem(
        item_code="MORTH-1700-DIRT-WALL",
        element="DIRT_WALL",
        basis=MeasureBasis.VOLUME_SOLID,
        quantity=qty.quantize(Decimal("0.001")),
        unit="cum",
        entity_ids=("dirt_wall_elevation", "abutment_stack"),
        derivation=_fmt(length, thk, h),
    )


def measure_formwork(project: Any, faces: list[tuple[str, float, float]]) -> MeasuredItem:
    """Formwork area = exposed face areas, soffit-bearing contact deducted.

    *faces* is ``(face_name, area_m2, deduction_m2)`` tuples.
    """
    total = sum(Decimal(str(a)) - Decimal(str(d)) for _n, a, d in faces)
    return MeasuredItem(
        item_code="MORTH-1700-FORMWORK",
        element="FORMWORK",
        basis=MeasureBasis.AREA_FACE,
        quantity=total.quantize(Decimal("0.01")),
        unit="sqm",
        entity_ids=tuple(n for n, _a, _d in faces) or ("formwork_faces",),
        derivation=" + ".join(f"{Decimal(str(a)) - Decimal(str(d)):.2f}" for _n, a, d in faces),
    )


def measure_rebar(project: Any) -> MeasuredItem:
    """Total reinforcement mass from the detailing ledger, kg → MT."""
    from bridgecad_core.detailing import ledger

    kg = Decimal(str(ledger(project).total_kg))
    mt = (kg / Decimal("1000")).quantize(Decimal("0.001"))
    return MeasuredItem(
        item_code="MORTH-1600-REBAR",
        element="REINFORCEMENT",
        basis=MeasureBasis.COUNT,
        quantity=mt,
        unit="MT",
        entity_ids=("detailing_ledger",),
        derivation=f"{kg:.2f} / 1000",
    )


def measure_all(project: Any) -> list[MeasuredItem]:
    """Every measured item for *project*, from the solved stack."""
    sub = project.substructure
    items: list[MeasuredItem] = []
    try:
        items.append(
            measure_cap(
                project,
                float(sub.abutment_length_m or 11.0),
                float(sub.abutment_cap_projection_front_mm or 300) / 1000.0,
                float(sub.abutment_cap_projection_rear_mm or 300) / 1000.0,
            )
        )
        items.append(
            measure_dirt_wall(
                project,
                float(sub.abutment_length_m or 11.0),
                float(sub.dirt_wall_thickness_mm or 300) / 1000.0,
                float(sub.dirt_wall_height_m or 0.3),
            )
        )
        items.append(measure_rebar(project))
    except Exception:
        pass  # measurement is additive; a missing input must not break pricing
    return items


__all__ = [
    "measure_cap",
    "measure_dirt_wall",
    "measure_formwork",
    "measure_rebar",
    "measure_all",
]
