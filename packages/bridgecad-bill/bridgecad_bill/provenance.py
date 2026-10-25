"""Per-line BOQ provenance.

WHY
    `processor.py` used multipliers and fell back to plausible numbers. A line
    reading 42.0 looked the same whether it came from a formula, a multiplier,
    or a guess. An auditor could not tell, so every line was effectively
    unverified.

THE CONTRACT
    1. Every line has a status: calculated | estimated | not_calculated.
    2. `calculated` requires a formula string AND the source field names it read.
    3. `estimated` requires a multiplier AND the multiplier's source note.
    4. `not_calculated` requires a reason. It is never a number.
    5. A missing input propagates to not_calculated, never to a default.
    6. Every line records its rate source: MORTH_2024_25 | PWD_OVERRIDE | missing.
    7. The section total is the sum of calculated + estimated only, and says how
       much of the section is not_calculated.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class LineStatus(str, Enum):
    CALCULATED = "calculated"
    ESTIMATED = "estimated"
    NOT_CALCULATED = "not_calculated"


class RateSource(str, Enum):
    MORTH_2024_25 = "MORTH_2024_25"
    PWD_OVERRIDE = "PWD_OVERRIDE"
    MISSING = "missing"


@dataclass
class BoqLine:
    item_no: str
    description: str
    unit: str
    quantity: float | None
    rate: float | None
    amount: float | None
    status: LineStatus
    formula: str | None = None
    source_fields: list[str] = field(default_factory=list)
    multiplier: float | None = None
    multiplier_source: str | None = None
    rate_source: RateSource = RateSource.MISSING
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.status is LineStatus.CALCULATED:
            if not self.formula or not self.source_fields:
                raise ValueError(f"{self.item_no}: calculated line needs formula + source_fields")
            if self.amount is None:
                raise ValueError(f"{self.item_no}: calculated line with no amount")
        elif self.status is LineStatus.ESTIMATED:
            if self.multiplier is None or not self.multiplier_source:
                raise ValueError(f"{self.item_no}: estimated line needs multiplier + source")
        else:
            if not self.reason:
                raise ValueError(f"{self.item_no}: not_calculated line needs a reason")


def section_summary(lines: list[BoqLine]) -> dict:
    """Totals plus an honesty header. The header is what a reader needs first."""
    known = [ln for ln in lines if ln.status is not LineStatus.NOT_CALCULATED]
    unknown = [ln for ln in lines if ln.status is LineStatus.NOT_CALCULATED]
    return {
        "lines": len(lines),
        "calculated": sum(1 for ln in lines if ln.status is LineStatus.CALCULATED),
        "estimated": sum(1 for ln in lines if ln.status is LineStatus.ESTIMATED),
        "not_calculated": len(unknown),
        "total_amount": sum(ln.amount or 0.0 for ln in known),
        "unknown_items": [ln.item_no for ln in unknown],
        "completeness": (len(known) / len(lines)) if lines else 0.0,
    }
