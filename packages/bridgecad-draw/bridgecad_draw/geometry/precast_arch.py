"""Precast block arch with strips and sockets (booklet type 015).

Blocks are equal, cut on radial joints, and the 100 mm strip gaps are real
drawing entities — the audit counts them.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

Pt = tuple[float, float]
BLOCK_LEN_MIN_M, BLOCK_LEN_MAX_M = 2.0, 2.5


@dataclass(frozen=True)
class Block:
    p0: Pt
    p1: Pt
    thickness: float
    socket_w: float = 0.62
    socket_d: float = 0.20


def block_count(span_m: float, rise_m: float) -> int:
    """Derive the count so the block arc length stays in 2.0–2.5 m, then freeze it."""
    arc = _arc_length(span_m, rise_m)
    return max(5, round(arc / ((BLOCK_LEN_MIN_M + BLOCK_LEN_MAX_M) / 2)))


def _arc_length(span_m: float, rise_m: float) -> float:
    r = (span_m**2 / (8 * rise_m)) + rise_m / 2
    half = math.asin((span_m / 2) / r)
    return 2 * r * half


def _stations(span_m: float, rise_m: float, n: int) -> list[Pt]:
    r = (span_m**2 / (8 * rise_m)) + rise_m / 2
    cy = rise_m - r
    out = []
    for i in range(n + 1):
        x = -span_m / 2 + span_m * i / n
        out.append((x, cy + math.sqrt(max(r * r - x * x, 0.0))))
    return out


def blocks(span_m: float, rise_m: float, n: int, thickness_m: float = 0.4) -> list[Block]:
    pts = _stations(span_m, rise_m, n)
    return [Block(pts[i], pts[i + 1], thickness_m) for i in range(n)]


def strip_offsets(count: int, width_m: float, gap_m: float) -> list[float]:
    """Strip centrelines across the deck width, ``gap_m`` clear between strips."""
    pitch = width_m + gap_m
    span = count * pitch - gap_m
    return [-(span / 2) + i * pitch + width_m / 2 for i in range(count)]


def gap_pairs(count: int, width_m: float, gap_m: float) -> int:
    """Longitudinal gaps between strips — one per adjacent strip pair."""
    return max(0, count - 1)


def gap_segments(block_count: int, strip_count: int) -> int:
    """Gap entities a transverse sheet must show: each gap breaks at every joint.

    A longitudinal gap is interrupted by each radial block joint, so
    ``gap_pairs × (blocks − 1)`` — 2 × 26 = 52 for the booklet's 3 strips of 27.
    """
    return gap_pairs(strip_count, 0.0, 0.0) * max(0, block_count - 1)


def socket(block: Block) -> tuple[float, float, float, float]:
    """Riser-side pocket: 620 × 200, 20 mm clearance, centred on the block."""
    cx = (block.p0[0] + block.p1[0]) / 2
    cy = (block.p0[1] + block.p1[1]) / 2
    return (cx - block.socket_w / 2, cy, block.socket_w, block.socket_d)
