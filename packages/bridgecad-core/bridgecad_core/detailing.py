"""bridgecad_core.detailing — per-project reinforcement detailing store.

Bars start from :func:`bridgecad_core.reinforcement.default_items`; a reviewer
may override dia/spacing per mark.  The store is session-scoped (keyed by the
live project object) — persistence belongs to the project file, which carries
the modelled bar inputs the defaults derive from.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .reinforcement import RebarItem, default_items

_STEEL_DENSITY_KG_M3 = 7850.0


@dataclass
class Ledger:
    total_kg: float
    design_kg: float
    delta_kg: float
    delta_pct: float
    kg_per_m3: float
    user_defined_count: int
    failing_count: int


class ReinforcementStore:
    """Mark-keyed overlay of bar overrides for one project."""

    def __init__(self, project: Any) -> None:
        self._project = project
        self._items: dict[str, RebarItem] = {item.mark: item for item in default_items(project)}

    def items(self) -> list[RebarItem]:
        return list(self._items.values())

    def get(self, mark: str) -> RebarItem | None:
        return self._items.get(mark)

    def set_bar(self, mark: str, dia_mm: int, spacing_mm: int) -> RebarItem:
        item = self._items.get(mark)
        if item is None:
            raise KeyError(f"unknown bar mark '{mark}'")
        updated = item.model_copy(
            update={"dia_mm": dia_mm, "spacing_mm": spacing_mm, "user_defined": True}
        )
        self._items[mark] = updated
        return updated

    def reset_item(self, mark: str) -> RebarItem:
        fresh = {i.mark: i for i in default_items(self._project)}.get(mark)
        if fresh is None:
            raise KeyError(f"unknown bar mark '{mark}'")
        self._items[mark] = fresh
        return fresh

    def reset_all(self) -> None:
        self._items = {i.mark: i for i in default_items(self._project)}

    # ── steel ledger ──────────────────────────────────────────────────────
    def _length_m(self, item: RebarItem) -> float:
        """Bar length from the solved geometry the item belongs to."""
        sub = self._project.substructure
        if item.element == "ABUTMENT_CAP":
            return float(sub.abutment_length_m or 11.0) + 0.60
        if item.element == "DIRT_WALL":
            return float(sub.dirt_wall_height_m or 0.3) + 0.40
        if item.element == "ABUTMENT_SHAFT":
            return float(sub.abutment_height_m or 3.0) + 0.45
        if item.element == "APPROACH_SLAB":
            return float(sub.approach_slab_length_m or 3.5) + 0.30
        if item.element == "DECK_SLAB":
            return float(self._project.geometry_input.total_length_m or 30.0)
        return 1.0

    def _kg(self, item: RebarItem) -> float:
        prov_m2 = float(item.as_provided_mm2_per_m) / 1e6  # m2 per m run
        return prov_m2 * self._length_m(item) * _STEEL_DENSITY_KG_M3

    def ledger(self) -> Ledger:
        total = sum(self._kg(i) for i in self._items.values())
        design = sum(self._kg(i) for i in self._items.values() if not i.user_defined)
        # design baseline = all items at design dia/spacing
        baseline_items = default_items(self._project)
        baseline = sum(_kg_of(i, self._length_m(i)) for i in baseline_items)
        user_n = sum(1 for i in self._items.values() if i.user_defined)
        failing = sum(1 for i in self._items.values() if i.utilisation > Decimal("1.0"))
        conc_m3 = max(
            1.0,
            float(self._project.geometry_input.total_length_m or 30.0)
            * float(self._project.geometry_input.overall_width_m or 8.0)
            * 0.25,
        )
        delta = total - baseline
        return Ledger(
            total_kg=round(total, 2),
            design_kg=round(design, 2),
            delta_kg=round(delta, 2),
            delta_pct=round(100.0 * delta / baseline, 2) if baseline else 0.0,
            kg_per_m3=round(total / conc_m3, 2),
            user_defined_count=user_n,
            failing_count=failing,
        )


def _kg_of(item: RebarItem, length_m: float) -> float:
    prov_m2 = float(item.as_provided_mm2_per_m) / 1e6
    return prov_m2 * length_m * _STEEL_DENSITY_KG_M3


_STORES: dict[int, ReinforcementStore] = {}


def store_for(project: Any) -> ReinforcementStore:
    key = id(project)
    store = _STORES.get(key)
    if store is None or store._project is not project:
        store = ReinforcementStore(project)
        _STORES[key] = store
    return store


def set_bar(project: Any, mark: str, dia_mm: int, spacing_mm: int) -> RebarItem:
    return store_for(project).set_bar(mark, dia_mm, spacing_mm)


def reset_item(project: Any, mark: str) -> RebarItem:
    return store_for(project).reset_item(mark)


def reset_all(project: Any) -> None:
    store_for(project).reset_all()


def ledger(project: Any) -> Ledger:
    return store_for(project).ledger()


def failing_count(project: Any) -> int:
    return store_for(project).ledger().failing_count


__all__ = [
    "Ledger",
    "ReinforcementStore",
    "store_for",
    "set_bar",
    "reset_item",
    "reset_all",
    "ledger",
    "failing_count",
]
