"""
bridgecad_bill.models — Bill of Quantities data models.

Hierarchy:
  BillOfQuantities
    └── BillSection  (e.g. "1000 EARTHWORK", "1700 CONCRETE WORKS")
          └── BillItem     (one line in the schedule)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional


@dataclass
class BillItem:
    """One line item in a Bill of Quantities."""
    item_code:   str            # e.g. "1701.1"
    description: str
    unit:        str            # e.g. "CUM", "MT", "SQM", "RM", "EACH", "LS"
    quantity:    Decimal        = Decimal("0")
    rate:        Optional[Decimal] = None       # INR per unit
    amount:      Optional[Decimal] = None       # quantity × rate
    ref:         str            = ""            # MORTH clause reference
    remarks:     str            = ""

    def compute_amount(self) -> Optional[Decimal]:
        if self.rate is not None and self.quantity > 0:
            self.amount = (self.quantity * self.rate).quantize(Decimal("0.01"))
            return self.amount
        return None


@dataclass
class BillSection:
    """A chapter / section group in the BOQ."""
    section_code: str           # e.g. "1700"
    title:        str           # e.g. "CONCRETE AND REINFORCEMENT WORKS"
    items:        list[BillItem] = field(default_factory=list)

    def add(self, item: BillItem) -> None:
        self.items.append(item)

    @property
    def total(self) -> Decimal:
        return sum(
            (i.amount for i in self.items if i.amount is not None),
            Decimal("0"),
        )


@dataclass
class BillOfQuantities:
    """Complete hierarchical Bill of Quantities for a bridge project."""
    project_name:  str                   = ""
    bridge_name:   str                   = ""
    chainage_km:   str                   = ""
    sections:      list[BillSection]     = field(default_factory=list)
    contingency_pct: Decimal             = Decimal("15")

    def add_section(self, section: BillSection) -> None:
        self.sections.append(section)

    @property
    def subtotal(self) -> Decimal:
        return sum((s.total for s in self.sections), Decimal("0"))

    @property
    def contingency_amount(self) -> Decimal:
        return (self.subtotal * self.contingency_pct / 100).quantize(Decimal("1"))

    @property
    def grand_total(self) -> Decimal:
        return self.subtotal + self.contingency_amount

    def all_items(self) -> list[BillItem]:
        return [item for sec in self.sections for item in sec.items]


@dataclass
class Deviation:
    """A variation/deviation from the abstract BOQ."""
    ref_item_code: str
    description:   str
    original_qty:  Decimal = Decimal("0")
    revised_qty:   Decimal = Decimal("0")
    reason:        str     = ""

    @property
    def qty_change(self) -> Decimal:
        return self.revised_qty - self.original_qty


__all__ = ["BillItem", "BillSection", "BillOfQuantities", "Deviation"]
