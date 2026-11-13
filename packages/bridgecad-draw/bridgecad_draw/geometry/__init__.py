"""Geometric primitives for the booklet types the engine draws parametrically.

Three booklet families have a shape the generic span/depth engine cannot
express — the multi-unit box cell (004), the open-spandrel arch driven by a
printed coordinate schedule (014) and the precast-block arch (015).  Each is a
pure-geometry module here; the sheets consume it and the QA rows assert its
defining counts.
"""

from __future__ import annotations

from ._errors import Violation
from .arch_schedule import (
    PARABOLA_A,
    RIB_SPACING_M,
    offset,
    parabola_deviation,
    rib_stations,
    ring_outline,
    stations,
)
from .box_cell import Band, Cell, CellGrid, assert_closed
from .precast_arch import (
    BLOCK_LEN_MAX_M,
    BLOCK_LEN_MIN_M,
    Block,
    block_count,
    blocks,
    gap_pairs,
    gap_segments,
    socket,
    strip_offsets,
)

__all__ = [
    "BLOCK_LEN_MAX_M",
    "BLOCK_LEN_MIN_M",
    "Block",
    "Band",
    "Cell",
    "CellGrid",
    "PARABOLA_A",
    "RIB_SPACING_M",
    "Violation",
    "assert_closed",
    "block_count",
    "blocks",
    "gap_pairs",
    "gap_segments",
    "offset",
    "parabola_deviation",
    "rib_stations",
    "ring_outline",
    "socket",
    "stations",
    "strip_offsets",
]
