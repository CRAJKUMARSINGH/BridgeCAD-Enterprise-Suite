"""bridgecad_bill.measure — geometry-derived measurement contract.

Every quantity traces to the entities it was measured from.  ``entity_ids``
may not be empty and ``derivation`` must resolve arithmetically to
``quantity`` — :func:`resolve_derivation` is the single evaluator tests use.
"""

from __future__ import annotations

import re
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MeasureBasis(StrEnum):
    VOLUME_SOLID = "VOLUME_SOLID"
    AREA_FACE = "AREA_FACE"
    LENGTH_LINEAR = "LENGTH_LINEAR"
    COUNT = "COUNT"


class MeasuredItem(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    item_code: str = Field(description="MORTH schedule item code")
    element: str = Field(description="Element key, e.g. ABUTMENT_CAP, DIRT_WALL")
    basis: MeasureBasis
    quantity: Decimal = Field(gt=0)
    unit: str = Field(description="cum / sqm / rm / no / kg")
    entity_ids: tuple[str, ...] = Field(min_length=1)
    derivation: str = Field(description="Arithmetic that resolves to quantity")

    @model_validator(mode="after")
    def _derivation_matches(self) -> MeasuredItem:
        value = resolve_derivation(self.derivation)
        if value is None:
            raise ValueError(f"{self.item_code}: derivation does not parse: {self.derivation!r}")
        if abs(value - self.quantity) > Decimal("0.01") * max(Decimal("1"), self.quantity):
            raise ValueError(
                f"{self.item_code}: derivation {self.derivation!r} = {value} "
                f"but quantity = {self.quantity}"
            )
        return self


_EXPR = re.compile(r"^[\d\s.xX+\-*/().]+$")


def resolve_derivation(derivation: str) -> Decimal | None:
    """Evaluate a numeric-only derivation expression safely.

    Accepts ``12.80 x 0.45 x 0.25`` and ``3.5 * 0.2 * 11.8`` forms; rejects
    anything containing names or calls.
    """
    expr = derivation.replace("x", "*").replace("X", "*").replace(",", ".")
    if not _EXPR.match(expr):
        return None
    try:
        result = eval(expr, {"__builtins__": {}}, {})  # — numeric-only, regex-gated
        return Decimal(str(result)).quantize(Decimal("0.0001"))
    except Exception:
        return None


__all__ = ["MeasureBasis", "MeasuredItem", "resolve_derivation"]
