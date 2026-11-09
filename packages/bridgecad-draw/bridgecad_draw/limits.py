"""
bridgecad_draw.limits — Single-source design limit values for QA and sheet checks.

Both the sheet self-audit check tables and the QA rule functions read from
here. A parity test in ``tests/draw/test_limits_parity.py`` asserts the QA
literals agree, so the two sets of values cannot drift.

References
----------
IRC:21-2000  Clause 305 — minimum cap depth and bearing-shelf dimensions.
IRC:78-2014  Clause 710 — dirt wall thickness and drainage requirements.
"""

from __future__ import annotations

# ── Abutment cap ────────────────────────────────────────────────────────────
CAP_DEPTH_MIN_M: float = 0.45
"""IRC:21 Clause 305: abutment cap (bearing shelf) vertical depth ≥ 450 mm."""

CAP_PROJ_MIN_M: float = 0.10
"""Minimum cap FRONT projection beyond the shaft face (bearing shelf), m."""

CAP_PROJ_MAX_M: float = 0.25
"""Maximum cap FRONT projection beyond the shaft face (bearing shelf), m."""

CAP_PROJ_REAR_MIN_M: float = 0.25
"""Minimum cap REAR projection (dirt-wall seat) — must take the dirt-wall stem, m."""

CAP_PROJ_REAR_MAX_M: float = 0.60
"""Maximum cap REAR projection (dirt-wall seat) — the model's own upper bound, m."""

# ── Dirt wall ────────────────────────────────────────────────────────────────
DIRT_WALL_THK_MIN_M: float = 0.25
"""IRC:78 Clause 710: dirt wall stem thickness ≥ 250 mm."""

DIRT_WALL_FREEBOARD_M: float = 0.10
"""Height margin between top of dirt wall and soffit of approach slab, m."""

WEEP_HOLE_SPACING_M: float = 3.0
"""Maximum spacing between 50 mm dia weep holes through the dirt wall, m."""

# ── Bearing seat ─────────────────────────────────────────────────────────────
BEARING_SEAT_MIN_M: float = 0.60
"""Minimum bearing seat (clear width at soffit level), m."""

# ── Bar spacing ──────────────────────────────────────────────────────────────
BAR_SPACING_MAX_MM: int = 200
"""Maximum bar spacing for primary reinforcement per IS 456 Clause 26.3.3."""

__all__ = [
    "CAP_DEPTH_MIN_M",
    "CAP_PROJ_MIN_M",
    "CAP_PROJ_MAX_M",
    "CAP_PROJ_REAR_MIN_M",
    "CAP_PROJ_REAR_MAX_M",
    "DIRT_WALL_THK_MIN_M",
    "DIRT_WALL_FREEBOARD_M",
    "WEEP_HOLE_SPACING_M",
    "BEARING_SEAT_MIN_M",
    "BAR_SPACING_MAX_MM",
]
