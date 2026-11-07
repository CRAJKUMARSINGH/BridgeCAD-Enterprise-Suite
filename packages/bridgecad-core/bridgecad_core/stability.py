"""
bridgecad_core.stability — GAD-stage abutment stability: overturning, sliding,
base pressure.

Rankine active pressure, dry unit weights, IRC:6 surcharge.  Indicative only —
a GAD sheet reports these so a reviewer sees the order of magnitude, not to
replace the design report.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

GAMMA_CONCRETE = 25.0  # kN/m3
KA = math.tan(math.radians(45.0 - 30.0 / 2.0)) ** 2  # phi = 30 deg
SURCHARGE_KPA = 12.0
FOS_OVERTURNING_MIN = 1.40
FOS_SLIDING_MIN = 1.40
MU_BASE = 0.55

__all__ = [
    "StabilityResult",
    "check_abutment",
    "FOS_OVERTURNING_MIN",
    "FOS_SLIDING_MIN",
]


@dataclass(frozen=True)
class StabilityResult:
    height_m: float
    pa_kn_per_m: float
    overturning_moment: float
    restoring_moment: float
    fos_overturning: float
    fos_sliding: float
    base_pressure_kpa: float
    ok_overturning: bool
    ok_sliding: bool
    ok_bearing: bool


def check_abutment(project: Any) -> StabilityResult:
    """Rankine/dry check on the abutment shaft + cap for *project*."""
    sub = project.substructure
    h = float(sub.abutment_height_m or 3.0)
    w = float(sub.abutment_width_m or 1.2)
    cap_d = float(sub.abutment_cap_depth_mm or 600) / 1000.0
    gamma_fill = float(project.approaches.soil_embankment_unit_weight_kN_m3 or 18.0)
    q_allow = float(project.foundation_details.bearing_capacity_kpa or 250.0)

    # Active thrust from fill + surcharge, per metre run
    pa = 0.5 * KA * gamma_fill * h**2 + KA * SURCHARGE_KPA * h
    arm = h / 3.0
    m_over = pa * arm

    wt = (w * h + (w + 0.30) * cap_d) * GAMMA_CONCRETE
    m_rest = wt * (w / 2.0)

    fos_o = m_rest / m_over if m_over else 99.0
    fos_s = (MU_BASE * wt) / pa if pa else 99.0
    base_p = wt / w + 6.0 * abs(m_rest - m_over) / w**2

    return StabilityResult(
        height_m=h,
        pa_kn_per_m=pa,
        overturning_moment=m_over,
        restoring_moment=m_rest,
        fos_overturning=fos_o,
        fos_sliding=fos_s,
        base_pressure_kpa=base_p,
        ok_overturning=fos_o >= FOS_OVERTURNING_MIN,
        ok_sliding=fos_s >= FOS_SLIDING_MIN,
        ok_bearing=base_p <= q_allow,
    )
