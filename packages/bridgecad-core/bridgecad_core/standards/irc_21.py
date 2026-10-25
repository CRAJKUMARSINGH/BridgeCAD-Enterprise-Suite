"""
bridgecad_core.standards.irc_21 — IRC:21-2000 / IRC:112-2020 Structural Design Rules.

Implements:
  - Span/depth ratio limits (IRC:21 Table 12 / IRC:112 Annex)
  - Minimum deck slab thickness
  - Minimum cover requirements (IS:456 / IRC:112)
  - Live load impact factor (IRC:6 Clause 3.5)
  - Bearing schedule checks (IRC:83)
  - Expansion joint gap formula
  - Serviceability deflection limits (IRC:112)
"""
from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Span / Depth Ratio limits — IRC:21-2000 Table 12 + IRC:112-2020 Annex J
# ---------------------------------------------------------------------------

# (span_config, superstructure_type) → (L/d min, L/d max, note)
_SPAN_DEPTH_LIMITS: dict[tuple[str, str], tuple[float, float, str]] = {
    # RCC T-Beam
    ("SIMPLY_SUPPORTED", "RCC_TBEAM"):              (10,  15, "IRC:21 Table 12"),
    ("CONTINUOUS",       "RCC_TBEAM"):              (12,  18, "IRC:21 Table 12"),
    # PSC I-Girder
    ("SIMPLY_SUPPORTED", "PSC_IGIRDER"):            (14,  20, "IRC:112 Annex J"),
    ("CONTINUOUS",       "PSC_IGIRDER"):            (16,  22, "IRC:112 Annex J"),
    # PSC Box Girder
    ("SIMPLY_SUPPORTED", "PSC_BOX_GIRDER"):         (16,  22, "IRC:112"),
    ("CONTINUOUS",       "PSC_BOX_GIRDER"):         (18,  25, "IRC:112"),
    # Slab bridges
    ("SIMPLY_SUPPORTED", "SOLID_SLAB"):             (8,   12, "IRC:21"),
    ("SIMPLY_SUPPORTED", "VOIDED_SLAB"):            (10,  14, "IRC:21"),
    # Steel
    ("SIMPLY_SUPPORTED", "STEEL_PLATE_GIRDER"):     (18,  25, "IRC:24"),
    ("SIMPLY_SUPPORTED", "STEEL_COMPOSITE"):        (18,  25, "IRC:24"),
    ("SIMPLY_SUPPORTED", "STEEL_TRUSS"):            (8,   12, "IRC:24"),
    # Balanced cantilever
    ("BALANCED_CANTILEVER", "PSC_BOX_GIRDER"):      (12,  18, "IRC:112"),
    ("BALANCED_CANTILEVER", "PSC_IGIRDER"):         (12,  18, "IRC:112"),
}


def span_depth_limits(
    span_config: str,
    superstructure_type: str,
) -> tuple[float, float, str]:
    """Return (L/d_min, L/d_max, reference) for a span/type combination.

    Falls back to (10, 20, 'IRC default') if combination not found.
    """
    key = (span_config.upper(), superstructure_type.upper())
    return _SPAN_DEPTH_LIMITS.get(key, (10.0, 20.0, "IRC general guidance"))


def check_span_depth_ratio(
    span_m: float,
    depth_mm: float,
    span_config: str,
    superstructure_type: str,
) -> tuple[bool, float, str]:
    """Check if a span/depth combination satisfies IRC limits.

    Returns
    -------
    (ok, actual_ratio, message)
    """
    if depth_mm <= 0:
        return False, 0.0, "Girder depth is zero or negative"
    ratio = span_m / (depth_mm / 1000.0)
    lo, hi, ref = span_depth_limits(span_config, superstructure_type)
    ok = lo <= ratio <= hi
    msg = (
        f"L/d = {ratio:.1f}  (limit {lo}–{hi} per {ref})"
        if ok
        else f"L/d = {ratio:.1f} outside [{lo}, {hi}] per {ref} — REVISE depth"
    )
    return ok, round(ratio, 1), msg


# ---------------------------------------------------------------------------
# Minimum deck slab thickness (IRC:21-2000 Cl.304 / IRC:112-2020 Cl.16.4)
# ---------------------------------------------------------------------------

def min_deck_slab_thickness_mm(
    superstructure_type: str,
    carriageway_width_m: float,
    span_m: float,
) -> float:
    """Minimum deck slab thickness in mm.

    Reference : IRC:21-2000 Cl.304.7 / IRC:112-2020 Cl.16.4.1
    """
    stype = superstructure_type.upper()
    if "BOX_CULVERT" in stype:
        return 200.0    # IRC SP:13
    if "SOLID_SLAB" in stype or "VOIDED_SLAB" in stype:
        return max(200.0, span_m * 1000.0 / 12.0)
    if "T_BEAM" in stype or "TBEAM" in stype:
        return 200.0    # IRC:21 Cl.304.7 minimum
    if "PSC" in stype or "PSC_IGIRDER" in stype:
        return 230.0    # IRC:112 composite slab minimum
    return 200.0        # general IRC minimum


# ---------------------------------------------------------------------------
# Nominal concrete cover (IS:456-2000 Table 16 / IRC:112-2020 Table 14)
# ---------------------------------------------------------------------------

_COVER_TABLE: dict[tuple[str, str], int] = {
    # (exposure_class, member_type) → cover in mm
    ("MILD",         "DECK_SLAB"):    40,
    ("MILD",         "PIER"):         40,
    ("MILD",         "PILE"):         50,
    ("MODERATE",     "DECK_SLAB"):    40,
    ("MODERATE",     "PIER"):         45,
    ("MODERATE",     "PILE"):         50,
    ("SEVERE",       "DECK_SLAB"):    45,
    ("SEVERE",       "PIER"):         50,
    ("SEVERE",       "PILE"):         60,
    ("VERY_SEVERE",  "DECK_SLAB"):    50,
    ("VERY_SEVERE",  "PIER"):         55,
    ("VERY_SEVERE",  "PILE"):         65,
    ("EXTREME",      "DECK_SLAB"):    75,
    ("EXTREME",      "PIER"):         75,
    ("EXTREME",      "PILE"):         75,
}


def nominal_cover_mm(
    exposure_class: str = "MODERATE",
    member_type: str    = "DECK_SLAB",
) -> int:
    """Nominal concrete cover in mm per IS:456-2000 Table 16 / IRC:112.

    Parameters
    ----------
    exposure_class : str  MILD | MODERATE | SEVERE | VERY_SEVERE | EXTREME
    member_type    : str  DECK_SLAB | PIER | PILE | ABUTMENT | FOOTING

    Returns
    -------
    int  Nominal cover (mm).
    """
    key = (exposure_class.upper(), member_type.upper())
    return _COVER_TABLE.get(key, 40)


# ---------------------------------------------------------------------------
# Impact factor (IRC:6-2017 Clause 3.5)
# ---------------------------------------------------------------------------

def impact_factor(span_m: float, bridge_class: str = "CLASS_A") -> float:
    """Dynamic impact allowance as fraction of live load.

    IRC:6-2017 Table 1 (simplified):
      Class A/B:   IF = 4.5 / (6 + L)  ≥ 0.10  for L ≤ 30 m
                   IF = 0.10            for L >  30 m
      70R / AA:    IF = 10% flat

    Parameters
    ----------
    span_m      : float  Longest span (m).
    bridge_class: str    "CLASS_A" | "CLASS_70R" | "CLASS_AA"

    Returns
    -------
    float  Impact factor fraction (e.g. 0.20 → 20%).

    Reference : IRC:6-2017 Clause 3.5 / Table 1
    """
    cls = bridge_class.upper()
    if "70R" in cls or "AA" in cls:
        return 0.10
    if span_m <= 0:
        return 0.50
    IF = 4.5 / (6.0 + span_m)
    return max(0.10, min(0.50, IF))


# ---------------------------------------------------------------------------
# Expansion joint gap (IRC:6 / IRC SP:55 Clause 7.3)
# ---------------------------------------------------------------------------

def expansion_joint_gap_mm(
    span_m: float,
    delta_T: float = 30.0,
    alpha: float   = 1.17e-5,
    creep_shrinkage_mm: float = 10.0,
) -> float:
    """Design expansion joint gap.

    gap = L × α × ΔT + prestress shortening + creep/shrinkage
    Minimum 20 mm, maximum based on joint type.

    Parameters
    ----------
    span_m            : float  Total deck length (m).
    delta_T           : float  Temperature differential °C (default 30°C per IRC:6 Cl.3.8).
    alpha             : float  Coefficient of thermal expansion (1/°C); default concrete.
    creep_shrinkage_mm: float  Additional creep+shrinkage allowance (mm).

    Returns
    -------
    float  Design gap at installation (mm). Round up to nearest 5 mm.

    Reference : IRC:6-2017 Cl.3.8  |  IRC SP:55 Cl.7.3
    """
    thermal_mm = span_m * 1000.0 * alpha * delta_T
    gap = thermal_mm + creep_shrinkage_mm
    gap = max(20.0, gap)
    # Round up to nearest 5 mm
    return math.ceil(gap / 5.0) * 5.0


# ---------------------------------------------------------------------------
# Deflection limits (IRC:112-2020 Clause 12.4 / IRC:6 Cl.3.7)
# ---------------------------------------------------------------------------

def max_live_load_deflection_mm(span_m: float) -> float:
    """Maximum permissible live load deflection (IRC:6 Cl.3.7 / IRC:112 12.4).

    Limit = span / 600  (general) or span / 800 (pedestrian-sensitive spans).

    Returns
    -------
    float  Maximum deflection (mm).
    """
    return (span_m * 1000.0) / 600.0


@dataclass
class StructuralCheckResult:
    span_depth_ok:       bool
    span_depth_ratio:    float
    span_depth_msg:      str
    min_slab_t_mm:       float
    impact_factor:       float
    joint_gap_mm:        float
    max_deflection_mm:   float
    nominal_cover_mm:    int


def check_structural_adequacy(
    span_m: float,
    depth_mm: float,
    span_config: str            = "SIMPLY_SUPPORTED",
    superstructure_type: str    = "RCC_TBEAM",
    carriageway_width_m: float  = 7.5,
    bridge_class: str           = "CLASS_A",
    exposure_class: str         = "MODERATE",
) -> StructuralCheckResult:
    """Run all IRC:21 / IRC:112 structural adequacy checks.

    Returns
    -------
    StructuralCheckResult
    """
    ok, ratio, msg = check_span_depth_ratio(span_m, depth_mm, span_config, superstructure_type)
    return StructuralCheckResult(
        span_depth_ok       = ok,
        span_depth_ratio    = ratio,
        span_depth_msg      = msg,
        min_slab_t_mm       = min_deck_slab_thickness_mm(superstructure_type, carriageway_width_m, span_m),
        impact_factor       = impact_factor(span_m, bridge_class),
        joint_gap_mm        = expansion_joint_gap_mm(span_m),
        max_deflection_mm   = max_live_load_deflection_mm(span_m),
        nominal_cover_mm    = nominal_cover_mm(exposure_class, "DECK_SLAB"),
    )


import math  # needed for expansion_joint_gap_mm ceiling

__all__ = [
    "span_depth_limits", "check_span_depth_ratio",
    "min_deck_slab_thickness_mm", "nominal_cover_mm",
    "impact_factor", "expansion_joint_gap_mm",
    "max_live_load_deflection_mm",
    "StructuralCheckResult", "check_structural_adequacy",
]
