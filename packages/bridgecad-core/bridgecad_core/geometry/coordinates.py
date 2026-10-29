"""
Shared coordinate contract — GUIDE.md §12 Phase 2, Step 0.

One source of truth for where every DXF sheet lives in model space.
Sheets never compute their own origin: each sheet module receives a
BridgeProject plus a SheetOrigin and transforms through to_sheet_coords().

Units: the contract is METRES. DXF output is millimetres; conversion
happens exactly once, at the sheet boundary (see to_dxf_mm()).

Pure functions only — no I/O, no globals, no side effects
(CONTRIBUTING.md §4). Every transform here must round-trip to identity.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum

Vec2 = tuple[float, float]

MM_PER_M = 1000.0
ROUND_TRIP_TOL_M = 1e-6  # metres; used by tests, documented here so it has one home


class SheetId(Enum):
    PLAN = "sheet1_plan"
    LONG_SECTION = "sheet2_long_section"
    CROSS_SECTION = "sheet3_cross_section"
    FOUNDATION = "sheet4_foundation"
    PIER_ABUTMENT = "sheet5_pier_abutment_details"
    BEARINGS_JOINTS = "sheet6_bearings_joints"
    BOQ = "sheet7_bill_of_quantities"


@dataclass(frozen=True)
class SheetOrigin:
    """World-space anchor for one sheet, in metres, plus sheet axes.

    rotation_deg is the angle from world +X to sheet +x (CCW). Sheets whose
    geometry is naturally drawn along the alignment (plan, long section)
    use 0.0; cross sections use the skew angle from GeometryInput.
    """

    sheet: SheetId
    x_m: float  # anchor chainage/offset, metres
    y_m: float
    rotation_deg: float = 0.0

    def rotate(self, p: Vec2) -> Vec2:
        import math

        a = math.radians(self.rotation_deg)
        c, s = math.cos(a), math.sin(a)
        return (c * p[0] - s * p[1], s * p[0] + c * p[1])


def sheet_origins(span_lengths_m: Iterable[float], skew_deg: float) -> dict[SheetId, SheetOrigin]:
    """Compute every sheet origin for a bridge from its span chainage.

    Contract (one fact, one place — GUIDE.md §14):
      * PLAN / LONG_SECTION / BOQ: origin at abutment A centreline, chainage 0.
      * CROSS_SECTION: origin at mid-span of the longest span, rotated by skew.
      * FOUNDATION: origin at pier 1 (first interior support) centreline.
      * PIER_ABUTMENT: origin at pier 1 centreline, shifted 5 m below ground
        so elevation geometry never collides with plan-view content.
      * BEARINGS_JOINTS: origin at abutment A bearing line.
    """
    spans = list(span_lengths_m)
    if not spans or any(s <= 0 for s in spans):
        raise ValueError("span_lengths_m must be non-empty and all positive")

    longest_span_idx = max(range(len(spans)), key=lambda i: spans[i])
    mid_longest_m = sum(spans[:longest_span_idx]) + spans[longest_span_idx] / 2.0

    pier1_m = spans[0]  # chainage of first interior pier = end of span 1

    return {
        SheetId.PLAN: SheetOrigin(SheetId.PLAN, 0.0, 0.0, 0.0),
        SheetId.LONG_SECTION: SheetOrigin(SheetId.LONG_SECTION, 0.0, 0.0, 0.0),
        SheetId.BOQ: SheetOrigin(SheetId.BOQ, 0.0, 0.0, 0.0),
        SheetId.CROSS_SECTION: SheetOrigin(SheetId.CROSS_SECTION, mid_longest_m, 0.0, skew_deg),
        SheetId.FOUNDATION: SheetOrigin(SheetId.FOUNDATION, pier1_m, 0.0, 0.0),
        SheetId.PIER_ABUTMENT: SheetOrigin(SheetId.PIER_ABUTMENT, pier1_m, -5.0, 0.0),
        SheetId.BEARINGS_JOINTS: SheetOrigin(SheetId.BEARINGS_JOINTS, 0.0, 0.0, 0.0),
    }


def to_sheet_coords(origin: SheetOrigin, world_point_m: Vec2) -> Vec2:
    """World (bridge chainage frame, metres) -> sheet-local (metres)."""
    shifted = (world_point_m[0] - origin.x_m, world_point_m[1] - origin.y_m)
    return origin.rotate(shifted)


def to_world_coords(origin: SheetOrigin, sheet_point_m: Vec2) -> Vec2:
    """Inverse of to_sheet_coords. Must satisfy the round-trip rule exactly."""
    # rotate by -theta, then translate back
    inv = SheetOrigin(origin.sheet, 0.0, 0.0, -origin.rotation_deg)
    r = inv.rotate(sheet_point_m)
    return (r[0] + origin.x_m, r[1] + origin.y_m)


def to_dxf_mm(sheet_point_m: Vec2) -> Vec2:
    """Sheet-local metres -> DXF millimetres. The ONLY mm conversion allowed."""
    return (sheet_point_m[0] * MM_PER_M, sheet_point_m[1] * MM_PER_M)
