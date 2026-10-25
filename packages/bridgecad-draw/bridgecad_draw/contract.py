"""bridgecad_draw.contract — the geometry facts a sheet is allowed to trust.

WHY THIS EXISTS
    Two different callers need the same two things from the product package:
    the wing-wall arithmetic (so a test can check it without importing the core
    geometry package by path) and a *geometry hash* (so a review record can be
    bound to the geometry it reviewed).

THE HASH
    ``geometry_hash`` is a stable digest of every fact a drawing sheet reads out
    of the project: the span lengths, the four levels, the carriageway width and
    the splay. Move any of them and the digest moves, which is what makes a
    stale signoff detectable instead of invisible.

    It is deliberately a *project* hash tagged with the *sheet* name, not a
    digest of the emitted DXF: a review is made against the geometry, and two
    renders of the same geometry are the same geometry.
"""
from __future__ import annotations

import hashlib
import json

from bridgecad_core.geometry.abutment import (
    LADDER as ABTL_LADDER,
)
from bridgecad_core.geometry.abutment import (
    WingWall,
    resolve_abtl,
    wing_wall_geometry,
)
from bridgecad_core.geometry.long_section import (
    pier_positions,
    span_boundaries,
    span_lengths_m,
)

#: The levels a section sheet draws. Named once so the hash and the sheets agree.
HASHED_LEVELS: tuple[str, ...] = ("deck_level_m", "hfl_m", "lwl_m", "founding_level_m")


def _plain(value) -> str:
    """A deterministic string form. ``Decimal``/``float`` both reduce to text."""
    return "None" if value is None else str(value)


def _read(holder, name):
    try:
        return getattr(holder, name)
    except Exception:  # - a drafting view may simply not carry it
        return None


def geometry_hash(project, sheet: str) -> str:
    """A 16-character digest of the geometry sheet *sheet* draws from *project*.

    CONTRACT: pure — it never writes back to the project — and sensitive to the
    span lengths, the four levels, the carriageway width and the splay.
    """
    levels = _read(project, "levels")
    gi = _read(project, "geometry_input")
    dc = _read(project, "drawing_control")
    fd = _read(project, "foundation_details")

    payload = {
        "sheet": str(sheet),
        "span_lengths_m": [_plain(x) for x in span_lengths_m(project)],
        "levels": {name: _plain(_read(levels, name)) for name in HASHED_LEVELS},
        "carriageway_width_m": _plain(_read(gi, "carriageway_width_m")),
        "skew_angle_deg": _plain(_read(gi, "skew_angle_deg")),
        "splay_deg": _plain(_read(dc, "splay_deg")),
        "abtl_m": _plain(_read(fd, "abtl")),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


__all__ = [
    "ABTL_LADDER", "WingWall", "HASHED_LEVELS", "geometry_hash",
    "resolve_abtl", "wing_wall_geometry",
    "span_lengths_m", "span_boundaries", "pier_positions",
]
