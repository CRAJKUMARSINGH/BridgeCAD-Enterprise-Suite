"""
bridgecad_core.geometry.cross_section — Typical mid-span cross-section geometry.
M1 Week 1 Day 4: parabolic camber profile, half-width zone offsets,
kerb/footpath/parapet/median widths, deck slab levels.
All dimensions in metres; Y is vertical (positive upward from datum).
X is transverse (0 at bridge centreline, positive toward left when facing A2).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from bridgecad_core.models import BridgeProject


# ---------------------------------------------------------------------------
# Public dataclass
# ---------------------------------------------------------------------------

@dataclass
class CrossSectionGeometry:
    """Typical mid-span cross-section geometry of the bridge deck.

    Coordinate convention
    ---------------------
    - X = 0 at bridge centreline; positive → left (viewer facing A2).
    - Y = 0 at top of deck slab (datum); positive upward (into wearing coat).

    ``half_width_offsets`` lists cumulative X values from centreline outward
    (left side only — mirror for right side), corresponding to zone boundaries:

        CL | median/2 | cw/2 | kerb | footpath | parapet | outer edge
    """

    # ---- overall dimensions (metres) ------------------------------------
    carriageway_width_m: float    = 0.0
    overall_width_m: float        = 0.0
    median_width_m: float         = 0.0
    footpath_left_m: float        = 0.0
    footpath_right_m: float       = 0.0
    kerb_width_left_m: float      = 0.0
    kerb_width_right_m: float     = 0.0
    crash_barrier_width_left_m: float  = 0.0
    crash_barrier_width_right_m: float = 0.0

    # ---- camber ----------------------------------------------------------
    camber_mm: float = 0.0
    """Peak parabolic crown height above edge level (mm)."""

    # ---- zone boundary offsets from CL (left side, metres) --------------
    half_width_offsets: list[float] = field(default_factory=list)
    """Cumulative offsets: [0, median/2, cw/2, +kerb, +footpath, +parapet, outer_edge]"""

    zone_labels: list[str] = field(default_factory=list)
    """Zone name for each band between consecutive offsets."""

    # ---- deck levels (Y relative to top-of-wearing-coat at CL) ----------
    top_of_wearing_coat_y: float = 0.0   # = camber_mm/1000 at CL
    bottom_of_slab_y: float      = 0.0   # = -(deck_thickness_mm/1000)
    bottom_of_girder_y: float    = 0.0   # = -(deck_thickness + girder_depth)/1000

    # ---- slope ----------------------------------------------------------
    deck_slope_pct: float = 2.0
    """Drainage cross-fall percentage (default 2 %)."""

    def camber_y_at_x(self, x_from_cl: float) -> float:
        """Parabolic crown camber height (mm) at transverse offset x_from_cl (m).

        Formula (IRC:112 Clause 6.5 / IRC:86 4.2):
            y(x) = camber_mm * (1 - (2x / carriageway_width_m)²)
        Peak at CL (x=0) = camber_mm; zero at carriageway edges (x=±cw/2).
        Outside carriageway the value is clamped to 0 (flat footpath assumed).
        """
        half_cw = self.carriageway_width_m / 2.0
        if half_cw <= 0.0:
            return 0.0
        ratio = x_from_cl / half_cw
        raw = self.camber_mm * (1.0 - ratio ** 2)
        return max(0.0, raw)

    def deck_surface_y_at_x(self, x_from_cl: float) -> float:
        """Top of wearing coat Y (metres) at transverse offset x_from_cl (m).

        Combines parabolic camber (mm→m) with any uniform gradient slope.
        """
        return self.camber_y_at_x(x_from_cl) / 1000.0


# ---------------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------------

def compute_cross_section_geometry(project: "BridgeProject") -> CrossSectionGeometry:
    """Derive typical mid-span cross-section geometry from a validated BridgeProject.

    Parameters
    ----------
    project : BridgeProject
        Fully-validated Pydantic model instance.

    Returns
    -------
    CrossSectionGeometry
        Populated dataclass.
    """
    gi = project.geometry_input
    ss = project.superstructure

    # ---- basic dimensions (float) ----------------------------------------
    cw         = float(gi.carriageway_width_m)
    median     = float(gi.median_width_m)      if gi.median_width_m      else 0.0
    fp_left    = float(gi.footpath_left_m)     if gi.footpath_left_m     else 0.0
    fp_right   = float(gi.footpath_right_m)    if gi.footpath_right_m    else 0.0
    kerb_left  = float(gi.kerb_width_left_m)   if gi.kerb_width_left_m   else 0.0
    kerb_right = float(gi.kerb_width_right_m)  if gi.kerb_width_right_m  else 0.0
    cb_left    = float(gi.crash_barrier_width_left_m)  if gi.crash_barrier_width_left_m  else 0.0
    cb_right   = float(gi.crash_barrier_width_right_m) if gi.crash_barrier_width_right_m else 0.0
    overall_w  = float(gi.overall_width_m)     # computed field

    camber_mm  = float(gi.camber_mm) if gi.camber_mm else 0.0

    # ---- zone boundary half-widths from CL (left side, metres) ----------
    # Order from centreline outward:
    #   0.0 → median/2 → carriageway/2 → +kerb → +footpath → +crash_barrier → outer edge
    offsets: list[float] = [0.0]
    labels:  list[str]  = []

    half_median = median / 2.0
    if half_median > 0.0:
        offsets.append(half_median)
        labels.append("MEDIAN")

    half_cw = cw / 2.0
    offsets.append(half_median + half_cw)
    labels.append("CARRIAGEWAY")

    if kerb_left > 0.0:
        offsets.append(offsets[-1] + kerb_left)
        labels.append("KERB")

    if fp_left > 0.0:
        offsets.append(offsets[-1] + fp_left)
        labels.append("FOOTPATH")

    if cb_left > 0.0:
        offsets.append(offsets[-1] + cb_left)
        labels.append("CRASH BARRIER")

    # outer edge = overall_w / 2
    outer_edge = overall_w / 2.0
    if abs(offsets[-1] - outer_edge) > 1e-6:
        offsets.append(outer_edge)
        labels.append("PARAPET/RAILING")

    # ---- deck levels (Y from top-of-wearing-coat at CL) ------------------
    deck_t_mm    = float(ss.deck_thickness_mm)    if ss.deck_thickness_mm    else 230.0
    wc_t_mm      = float(ss.wearing_coat_thickness_mm) if ss.wearing_coat_thickness_mm else 40.0
    girder_d_mm  = float(ss.girder_depth_mm)       if ss.girder_depth_mm       else 0.0

    top_of_wc_y      =  camber_mm / 1000.0     # CL crown height above edge
    bottom_of_slab_y = -(deck_t_mm / 1000.0)
    bottom_of_girder = bottom_of_slab_y - girder_d_mm / 1000.0

    # ---- drainage cross-fall (default 2 %) --------------------------------
    deck_slope_pct = 2.0   # IRC standard for bituminous deck (IRC:86 Clause 4.2)

    return CrossSectionGeometry(
        carriageway_width_m=cw,
        overall_width_m=overall_w,
        median_width_m=median,
        footpath_left_m=fp_left,
        footpath_right_m=fp_right,
        kerb_width_left_m=kerb_left,
        kerb_width_right_m=kerb_right,
        crash_barrier_width_left_m=cb_left,
        crash_barrier_width_right_m=cb_right,
        camber_mm=camber_mm,
        half_width_offsets=offsets,
        zone_labels=labels,
        top_of_wearing_coat_y=top_of_wc_y,
        bottom_of_slab_y=bottom_of_slab_y,
        bottom_of_girder_y=bottom_of_girder,
        deck_slope_pct=deck_slope_pct,
    )


__all__ = ["CrossSectionGeometry", "compute_cross_section_geometry"]
