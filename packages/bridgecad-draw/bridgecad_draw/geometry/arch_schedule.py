"""Open-spandrel arch driven by the booklet 014 coordinate schedule.

The printed schedule is authoritative: the booklet's own ``Y = AX² (A = 0.04955)``
reproduces the crown and the springings but not the flanks — the tabulated
haunches sit up to 0.82 m above the parabola — so the parabola is a *check*,
never the source.  ``X`` is measured from the crown; that is the only reading
under which the equation reproduces the crown at all, and it makes ``A`` the
ordinary ``4·rise/span²`` (``4 × 7.805/25.10² = 0.04955``) with ``X`` in metres
and ``Y`` the drop — the same parabola as ``A·x²/1000`` for ``x`` in mm.
"""

from __future__ import annotations

import math

from ._errors import Violation

Pt = tuple[float, float]
PARABOLA_A = 0.04955
RIB_SPACING_M = 4.183


def stations(schedule_mm: list[tuple[int, int]], ch0: float, rl0: float) -> list[Pt]:
    """Place the schedule at (ch0, rl0).  No interpolation — the table is the shape."""
    if len(schedule_mm) < 5:
        raise Violation(f"arch schedule has {len(schedule_mm)} stations, need ≥ 5")
    if abs(schedule_mm[0][1]) > 1 or abs(schedule_mm[-1][1]) > 1:
        raise Violation("arch schedule does not return to Y=0 at both springings")
    return [(ch0 + x / 1000.0, rl0 + y / 1000.0) for x, y in schedule_mm]


def _normals(pts: list[Pt]) -> list[Pt]:
    out = []
    for i, (x, y) in enumerate(pts):
        ax, ay = pts[max(i - 1, 0)]
        bx, by = pts[min(i + 1, len(pts) - 1)]
        tx, ty = bx - ax, by - ay
        n = math.hypot(tx, ty) or 1.0
        out.append((-ty / n, tx / n))  # left normal = upward for a rising curve
    return out


def offset(pts: list[Pt], dist: float) -> list[Pt]:
    """Offset along station normals — constant ring thickness, no mitre blow-ups."""
    return [(x + nx * dist, y + ny * dist) for (x, y), (nx, ny) in zip(pts, _normals(pts))]


def ring_outline(soffit: list[Pt], thickness_m: float) -> list[Pt]:
    """Closed ring: intrados, up the end face, extrados reversed, down the other end."""
    extrados = offset(soffit, thickness_m)
    return soffit + [extrados[-1]] + list(reversed(extrados)) + [soffit[0]]


def rib_stations(soffit: list[Pt], rib_m: float = RIB_SPACING_M) -> list[Pt]:
    """Ribs sit on schedule stations — the spacing is a whole multiple of the pitch.

    A rib that lands between stations is a schedule transcription error, not
    something to paper over with an interpolated point: raise instead.
    """
    span = soffit[-1][0] - soffit[0][0]
    pitch = span / (len(soffit) - 1)
    if abs(rib_m / pitch - round(rib_m / pitch)) > 0.01:
        raise Violation(f"rib spacing {rib_m} is not a whole multiple of pitch {pitch:.3f}")
    step = int(round(rib_m / pitch))
    return [soffit[i] for i in range(step, len(soffit) - 1, step)]


def parabola_deviation(schedule_mm: list[tuple[int, int]]) -> float:
    """Max |drop from the crown − A·x²/1000| in mm, ``x`` measured from the crown.

    Referenced from the *springing* the equation runs away to 31 m at the far
    end — it would no longer reproduce the crown, which the booklet says it
    does — so the apex is taken as the origin and the value is the honest
    "how far the printed table departs from a true parabola" the sheet prints.
    """
    apex_x, apex_y = max(schedule_mm, key=lambda p: p[1])
    return max(
        abs((apex_y - y) - PARABOLA_A * (x - apex_x) ** 2 / 1000.0)
        for x, y in schedule_mm
    )
