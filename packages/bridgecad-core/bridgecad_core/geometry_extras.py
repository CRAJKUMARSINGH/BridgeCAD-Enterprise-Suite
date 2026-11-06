"""
bridgecad_core.geometry_extras — Supplementary geometry helpers.
Dirt-wall height is derived once here and used by all drawing sheets.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Any

__all__ = ["DirtWallGeometry", "compute_dirt_wall_geometry"]

_MM = 1000.0

@dataclass(frozen=True)
class DirtWallGeometry:
    cap_top_rl: float
    soffit_rl: float
    height_m: float
    is_explicit: bool
    weep_holes_count: int


def compute_dirt_wall_geometry(project: Any) -> DirtWallGeometry:
    ss = project.superstructure
    sub = project.substructure
    pm = project.project_master
    hd = project.hydraulic_data

    wc_t = float(ss.wearing_coat_thickness_mm or 65) / _MM
    app_t = float(sub.approach_slab_thickness_mm or 200) / _MM
    ped_h = float(sub.abutment_pedestal_height_m or 0.15)
    cap_d = float(sub.abutment_cap_depth_mm or 600) / _MM
    brg_t = 0.10

    tod_rl = float(pm.road_level_rl_m or 0.0)
    soffit_rl = float(hd.actual_soffit_level_m or tod_rl - 1.5)

    cap_top_rl = soffit_rl - brg_t - ped_h
    available = (tod_rl - wc_t - app_t) - cap_top_rl

    explicit = float(sub.dirt_wall_height_m or 0.0)
    is_explicit = explicit > 0.0
    height_m = min(explicit, available) if is_explicit else available

    abt_len = float(sub.abutment_length_m or 0.0)
    spacing = float(sub.weep_hole_spacing_m or 3.0)
    n_weep = max(1, math.ceil(abt_len / max(spacing, 0.1))) if abt_len > 0 else 0

    return DirtWallGeometry(
        cap_top_rl=cap_top_rl,
        soffit_rl=tod_rl - wc_t - app_t,
        height_m=max(0.0, height_m),
        is_explicit=is_explicit,
        weep_holes_count=n_weep,
    )
