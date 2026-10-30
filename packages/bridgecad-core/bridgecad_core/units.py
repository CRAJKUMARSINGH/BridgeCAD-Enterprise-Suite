"""
bridgecad_core.units — SI ↔ FPS conversion, unit-system guards and rounding policy.

Single home for (a) the unit conversions bridge work needs and (b) the
significant-figure / engineering rounding rules, so printed quantities stay
deterministic and are never rounded ad hoc (one fact, one place — GUIDE.md §14).

Every factor is the exact, standard definition:

    1 ft      = 0.3048 m                     (exact, international foot)
    1 in      = 25.4 mm                      (exact)
    1 kip     = 4.4482216152605 kN           (exact, 1000 lbf)
    1 kip·ft  = 1.3558179483314004 kN·m      (exact)
    1 ksi     = 6.894757293168361 MPa        (exact)

The guards make a wrong-unit read impossible to pass silently: a symbol must
resolve to a known unit family, and ``require_unit_system`` raises when the
caller's declared system disagrees with the symbol's own.

Pure functions only — no I/O, no globals mutated, no side effects
(CONTRIBUTING.md §4).
"""

from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum

__all__ = [
    "FT_TO_M",
    "IN_TO_MM",
    "KIP_TO_KN",
    "KIPFT_TO_KNM",
    "KSI_TO_MPA",
    "UnitError",
    "UnitSystem",
    "feet_to_metres",
    "inches_to_millimetres",
    "kilonewton_metres_to_kip_feet",
    "kilonewtons_to_kip_force",
    "kip_feet_to_kilonewton_metres",
    "kip_force_to_kilonewtons",
    "ksi_to_megapascals",
    "megapascals_to_ksi",
    "metres_to_feet",
    "millimetres_to_inches",
    "require_unit_system",
    "round_engineering",
    "round_sig",
    "unit_system",
]

# ---------------------------------------------------------------------------
# Exact conversion factors
# ---------------------------------------------------------------------------

FT_TO_M = 0.3048  # 1 ft = 0.3048 m exactly
IN_TO_MM = 25.4  # 1 in = 25.4 mm exactly
KIP_TO_KN = 4.4482216152605  # 1 kip = 4.4482216152605 kN exactly
KIPFT_TO_KNM = 1.3558179483314004  # 1 kip·ft = 1.3558179483314004 kN·m exactly
KSI_TO_MPA = 6.894757293168361  # 1 ksi = 6.894757293168361 MPa exactly


class UnitSystem(Enum):
    """The two unit families a bridge deliverable may be expressed in."""

    SI = "SI"
    FPS = "FPS"


class UnitError(ValueError):
    """Explicit error for a wrong unit system, unknown symbol or bad domain."""


# Canonical symbols per family. Keys are the tokens the converter files use.
_SI_UNITS = frozenset({"m", "mm", "kN", "kN·m", "MPa"})
_FPS_UNITS = frozenset({"ft", "in", "kip", "kip·ft", "ksi"})


def _finite(value: float, name: str) -> float:
    """Coerce *value* to float, refusing NaN / ±inf so bad input cannot propagate."""
    x = float(value)
    if not math.isfinite(x):
        raise UnitError(f"{name} must be a finite number, got {value!r}")
    return x


# ---------------------------------------------------------------------------
# Unit-system guards
# ---------------------------------------------------------------------------


def unit_system(symbol: str) -> UnitSystem:
    """Unit family a canonical symbol belongs to (``"kN"`` → ``SI``)."""
    if symbol in _SI_UNITS:
        return UnitSystem.SI
    if symbol in _FPS_UNITS:
        return UnitSystem.FPS
    raise UnitError(f"unknown unit symbol {symbol!r}")


def require_unit_system(symbol: str, expected: UnitSystem) -> None:
    """Raise unless *symbol* belongs to *expected*.

    This is the guard that stops a kN / mm value being read as kip / inch: the
    caller states the system it is working in and a mismatched symbol errors.
    """
    actual = unit_system(symbol)
    if actual is not expected:
        raise UnitError(f"unit {symbol!r} is {actual.value}, not {expected.value}")


# ---------------------------------------------------------------------------
# SI ↔ FPS conversion helpers (direction-named — no ambiguity)
# ---------------------------------------------------------------------------


def metres_to_feet(metres: float) -> float:
    """Metres → international feet."""
    return _finite(metres, "metres") / FT_TO_M


def feet_to_metres(feet: float) -> float:
    """International feet → metres."""
    return _finite(feet, "feet") * FT_TO_M


def millimetres_to_inches(millimetres: float) -> float:
    """Millimetres → inches."""
    return _finite(millimetres, "millimetres") / IN_TO_MM


def inches_to_millimetres(inches: float) -> float:
    """Inches → millimetres."""
    return _finite(inches, "inches") * IN_TO_MM


def kilonewtons_to_kip_force(kilonewtons: float) -> float:
    """Kilonewtons → kip-force."""
    return _finite(kilonewtons, "kilonewtons") / KIP_TO_KN


def kip_force_to_kilonewtons(kip_force: float) -> float:
    """Kip-force → kilonewtons."""
    return _finite(kip_force, "kip_force") * KIP_TO_KN


def kilonewton_metres_to_kip_feet(kilonewton_metres: float) -> float:
    """Kilonewton·metres → kip·feet."""
    return _finite(kilonewton_metres, "kilonewton_metres") / KIPFT_TO_KNM


def kip_feet_to_kilonewton_metres(kip_feet: float) -> float:
    """Kip·feet → kilonewton·metres."""
    return _finite(kip_feet, "kip_feet") * KIPFT_TO_KNM


def megapascals_to_ksi(megapascals: float) -> float:
    """Megapascals → kips per square inch."""
    return _finite(megapascals, "megapascals") / KSI_TO_MPA


def ksi_to_megapascals(ksi: float) -> float:
    """Kips per square inch → megapascals."""
    return _finite(ksi, "ksi") * KSI_TO_MPA


# ---------------------------------------------------------------------------
# Rounding policy
# ---------------------------------------------------------------------------


def round_sig(x: float, n: int) -> float:
    """Round *x* to *n* significant figures, half-up, as a float.

    Deterministic (``Decimal`` + ``ROUND_HALF_UP``) and independent of binary
    float representation, so 2.345 at two figures is the code answer 2.3 — not
    whatever ``round()`` happens to do with the nearest double.
    """
    value = _finite(x, "x")
    if not isinstance(n, int) or n < 1:
        raise UnitError(f"n (significant figures) must be an int >= 1, got {n!r}")
    if value == 0.0:
        return 0.0
    decimal = Decimal(repr(value))
    shift = (n - 1) - decimal.adjusted()
    quantum = Decimal(1).scaleb(-shift)
    return float(decimal.quantize(quantum, rounding=ROUND_HALF_UP))


def round_engineering(x: float, decimals: int) -> float:
    """Quantise *x* to *decimals* decimal places, half-up, as a float."""
    value = _finite(x, "x")
    if not isinstance(decimals, int) or decimals < 0:
        raise UnitError(f"decimals must be an int >= 0, got {decimals!r}")
    quantum = Decimal(1).scaleb(-decimals)
    return float(Decimal(repr(value)).quantize(quantum, rounding=ROUND_HALF_UP))
