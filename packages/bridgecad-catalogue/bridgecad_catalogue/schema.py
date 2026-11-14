"""Variable control surface for the Maharashtra PWD booklet catalogue.

Every controllable field of every booklet type is declared once, here, with a
unit, a legal range and the clause that sets it.  Nothing in cards/ may hold a
value that this module does not describe.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

CLAUSE_FREEBOARD = "IRC 5 cl.104 / IRC SP:13"
CLAUSE_DEPTH = "IRC 112 Table 12.1 (span/depth)"
CLAUSE_BEARING = "IRC 83 cl.903 / IRC 6"
CLAUSE_PILE = "IRC 78 cl.709"
CLAUSE_SKEW = "IRC 5 cl.101.3"


class Kind(str, Enum):
    FREE = "free"
    DERIVED = "derived"
    LOCKED = "locked"


class Violation(Exception):
    """A rejected override.  Carries field, accepted range and clause."""


@dataclass(frozen=True)
class VariableSpec:
    key: str
    unit: str
    kind: Kind
    lo: Decimal | None = None
    hi: Decimal | None = None
    step: Decimal | None = None
    choices: tuple[object, ...] = ()
    clause: str = ""
    note: str = ""

    def coerce(self, raw: object) -> object:
        if isinstance(raw, bool):
            raise Violation(f"{self.key}: booleans are not valid variable values")
        if self.choices:
            if all(isinstance(choice, (int, float, Decimal)) for choice in self.choices):
                try:
                    candidate = Decimal(str(raw))
                except Exception as exc:
                    raise Violation(f"{self.key}: {raw!r} is not numeric") from exc
                if not candidate.is_finite():
                    raise Violation(f"{self.key}: value must be finite")
                for choice in self.choices:
                    if candidate == Decimal(str(choice)):
                        return choice
            if raw not in self.choices:
                raise Violation(
                    f"{self.key}: {raw!r} not in {list(self.choices)} [{self.clause}]"
                )
            return raw
        # A LOCKED identity field is not a dial: it carries no range and no
        # choices, so its value passes through unchanged once ``--force`` has
        # authorised the edit.  FREE/DERIVED fields are numeric and are checked.
        if self.kind is Kind.LOCKED:
            return raw
        try:
            val = Decimal(str(raw))
        except Exception as exc:
            raise Violation(f"{self.key}: {raw!r} is not numeric ({self.unit})") from exc
        if not val.is_finite():
            raise Violation(f"{self.key}: value must be finite")
        if self.key in {"span_count", "girders_per_deck", "piles_per_pier"} and val != val.to_integral_value():
            raise Violation(f"{self.key}: must be a whole number")
        if self.lo is not None and val < self.lo:
            raise Violation(f"{self.key}: {val} < min {self.lo} {self.unit} [{self.clause}]")
        if self.hi is not None and val > self.hi:
            raise Violation(f"{self.key}: {val} > max {self.hi} {self.unit} [{self.clause}]")
        if self.step and val % self.step:
            raise Violation(f"{self.key}: {val} not a multiple of {self.step} {self.unit}")
        return val


def _free(
    key: str,
    unit: str,
    lo: object,
    hi: object,
    clause: str,
    step: object = None,
    note: str = "",
) -> VariableSpec:
    return VariableSpec(
        key,
        unit,
        Kind.FREE,
        Decimal(str(lo)),
        Decimal(str(hi)),
        Decimal(str(step)) if step else None,
        clause=clause,
        note=note,
    )


def _lock(key: str, unit: str, note: str = "") -> VariableSpec:
    return VariableSpec(key, unit, Kind.LOCKED, note=note)


# ── the dials ────────────────────────────────────────────────────────────────
VARIABLES: dict[str, VariableSpec] = {
    "span_count": _free("span_count", "no", 1, 12, "IRC 5 cl.101"),
    "span_length_m": _free(
        "span_length_m",
        "m",
        6.0,
        50.0,
        CLAUSE_DEPTH,
        step=0.5,
        note="applies to every span; use span_overrides for a mix",
    ),
    "carriageway_width": VariableSpec(
        "carriageway_width", "m", Kind.FREE, choices=(3.5, 7.5, 11.0), clause="IRC 73 / IRC 5 cl.101"
    ),
    "footpath_width": _free("footpath_width", "m", 0.0, 2.0, "IRC 103", step=0.25),
    "skew_deg": _free("skew_deg", "deg", 0, 30, CLAUSE_SKEW, step=5),
    "pier_height_m": _free("pier_height_m", "m", 3.0, 25.0, "site datum"),
    "pier_shaft_width_m": _free(
        "pier_shaft_width_m", "m", 0.8, 3.0, "IRC 112 cl.16", step=0.1
    ),
    "deck_thickness_mm": _free("deck_thickness_mm", "mm", 200, 900, CLAUSE_DEPTH, step=25),
    "girder_depth_mm": _free("girder_depth_mm", "mm", 600, 3000, CLAUSE_DEPTH, step=50),
    "girder_spacing_m": _free("girder_spacing_m", "m", 1.5, 3.5, CLAUSE_DEPTH, step=0.1),
    "girders_per_deck": _free("girders_per_deck", "no", 1, 8, CLAUSE_DEPTH),
    "hfl_m": _free("hfl_m", "m", 0.0, 1000.0, "PSD"),
    "freeboard_m": _free("freeboard_m", "m", 0.6, 4.0, CLAUSE_FREEBOARD, step=0.05),
    "scour_depth_m": _free("scour_depth_m", "m", 0.5, 8.0, "IRC 78 cl.703"),
    "pile_diameter_mm": VariableSpec(
        "pile_diameter_mm", "mm", Kind.FREE, choices=(1000, 1200, 1500), clause=CLAUSE_PILE
    ),
    "pile_length_m": _free("pile_length_m", "m", 6.0, 45.0, CLAUSE_PILE, step=0.5),
    "piles_per_pier": _free("piles_per_pier", "no", 2, 12, CLAUSE_PILE),
    "well_diameter_m": _free("well_diameter_m", "m", 4.0, 8.0, "IRC 78 cl.709", step=0.5),
    "sbc_t_per_m2": _free("sbc_t_per_m2", "t/m²", 10.0, 200.0, "IRC 78 cl.701"),
    # booklet identity — protected
    "foundation_type": _lock("foundation_type", "-"),
    "superstructure_type": _lock("superstructure_type", "-"),
    "abutment_type": _lock("abutment_type", "-"),
    "bearing_type": _lock("bearing_type", "-"),
    "pier_material": _lock("pier_material", "-"),
    "submersible": _lock("submersible", "bool"),
    "dirt_wall_thickness_mm": _lock("dirt_wall_thickness_mm", "mm"),
    # always computed
    "total_length_m": VariableSpec("total_length_m", "m", Kind.DERIVED),
    "soffit_level": VariableSpec("soffit_level", "m", Kind.DERIVED),
    "road_level": VariableSpec("road_level", "m", Kind.DERIVED),
    "foundation_level": VariableSpec("foundation_level", "m", Kind.DERIVED),
    "pier_count": VariableSpec("pier_count", "no", Kind.DERIVED),
    "span_lengths": VariableSpec("span_lengths", "m[]", Kind.DERIVED),
}
