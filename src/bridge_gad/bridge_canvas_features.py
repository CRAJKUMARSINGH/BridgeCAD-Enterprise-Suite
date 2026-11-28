"""BridgeCanvas features integrated into Bridge GAD Generator.

Sourced from: BridgeCanvas/bridge_processor.py and BridgeCanvas/streamlit_app/app_with_all_features.py
Integrated features:
  - IRC/IS parameter validation with compliance scoring
  - DXF entity cleanup (orphan points, degenerate entities)
  - 5 standard bridge templates (simple, continuous, girder, culvert, arch)
  - Batch processing helper
  - Smart title block recentering utility
"""

from __future__ import annotations

import json
import logging
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd

from .standards import (
    build_template_rows,
    checklist_rows,
    get_owner_profile,
    merge_with_metadata,
    owner_profile_rows,
    phase_two_sheet_rows,
    phase_three_sheet_rows,
)

logger = logging.getLogger(__name__)

# ── IRC/IS Bridge Parameter Validator ────────────────────────────────────────


def validate_bridge_parameters(variables: Dict[str, Any]) -> Dict[str, Any]:
    """Validate bridge parameters against IRC/IS standards.

    Sourced from BridgeCanvas/streamlit_app/app_with_all_features.py::validate_bridge_parameters

    Returns:
        Dict with keys: is_valid, critical_issues, warnings, score (0-100)
    """
    issues: List[str] = []
    warnings: List[str] = []

    try:
        # Vertical clearance (IRC 5:2015 — minimum 5.5m)
        rtl = float(variables.get("RTL", variables.get("rtl", 100)))
        datum = float(variables.get("DATUM", variables.get("datum", 95)))
        clearance = rtl - datum
        if clearance < 5.5:
            issues.append(
                f"Vertical clearance {clearance:.2f}m < 5.5m (IRC 5:2015 minimum)"
            )

        # Slab thickness — L/20 rule
        span1 = float(variables.get("SPAN1", variables.get("span1", 12)))
        slbthe = float(variables.get("SLBTHE", variables.get("slbthe", 0.75)))
        min_thickness = span1 / 20
        if slbthe < min_thickness:
            issues.append(
                f"Slab thickness {slbthe:.2f}m < {min_thickness:.2f}m (L/20 rule)"
            )

        # Pier width minimum
        piertw = float(variables.get("PIERTW", variables.get("piertw", 1.2)))
        if piertw < 1.0:
            warnings.append(f"Pier width {piertw:.2f}m < 1.0m (recommended minimum)")

        # Footing depth minimum
        futd = float(variables.get("FUTD", variables.get("futd", 2.0)))
        if futd < 0.8:
            warnings.append(f"Footing depth {futd:.2f}m < 0.8m (recommended minimum)")

        # Span limit for slab bridges
        if span1 > 50:
            warnings.append(f"Span {span1:.1f}m exceeds typical slab bridge limit (50m)")

        # Number of spans sanity check
        nspan = int(float(variables.get("NSPAN", variables.get("nspan", 1))))
        if nspan > 10:
            warnings.append(f"Unusual number of spans: {nspan}")

        # Skew angle
        skew = float(variables.get("SKEW", variables.get("skew", 0)))
        if abs(skew) > 45:
            issues.append(f"Skew angle {skew}° exceeds ±45° limit")

        # Deck width
        ccbr = float(variables.get("CCBR", variables.get("ccbr", 8.0)))
        if ccbr < 4.25:
            warnings.append(f"Carriageway width {ccbr:.2f}m < 4.25m (IRC 5 minimum for single lane)")

        # Lane-based carriageway sanity
        lanes = int(float(variables.get("LANES", variables.get("lanes", 1))))
        if lanes <= 0:
            issues.append("LANES must be at least 1")
        elif lanes == 1 and ccbr < 4.25:
            issues.append("Single-lane bridge should provide at least 4.25m carriageway")
        elif lanes == 2 and ccbr < 7.5:
            issues.append("Two-lane bridge should provide at least 7.5m carriageway")

        # Footpath practice check
        footpathw = float(variables.get("FOOTPATHW", variables.get("footpathw", 0.0)))
        if 0 < footpathw < 1.5:
            warnings.append(
                f"Footpath width {footpathw:.2f}m is below the usual 1.5m minimum where pedestrian facility is intended"
            )

        # Cross fall / camber practice check
        crossfall = float(variables.get("CROSSFALL", variables.get("crossfall", 0.025)))
        if not 0.015 <= crossfall <= 0.04:
            warnings.append(
                f"Cross fall {crossfall:.3f} is outside the usual 1.5%-4.0% practical range"
            )

        # Wearing course practical range
        wcth = float(variables.get("WCTH", variables.get("wcth", 0.08)))
        if not 0.05 <= wcth <= 0.12:
            warnings.append(
                f"Wearing course thickness {wcth:.3f}m is outside the usual 50-120mm practical range"
            )

        # Safety edge treatment
        crashb = int(float(variables.get("CRASHB", variables.get("crashb", 0))))
        barrierh = float(variables.get("BARRIERH", variables.get("barrierh", 0.0)))
        if crashb and barrierh < 1.0:
            warnings.append("Crash barrier is enabled but barrier height is below 1.0m")

        # Drainage
        drainsp = float(variables.get("DRAINSP", variables.get("drainsp", 0.0)))
        if drainsp <= 0:
            warnings.append("Drainage spout spacing is not specified")
        elif drainsp > 10:
            warnings.append(f"Drainage spout spacing {drainsp:.2f}m may be too sparse for bridge deck drainage")

        # Bearings and joints
        expjt = float(variables.get("EXPJT", variables.get("expjt", 0.025)))
        if not 0.0 <= expjt <= 0.10:
            warnings.append(f"Expansion joint width {expjt:.3f}m looks unusual")

        bearing_type = str(variables.get("BEARING_TYPE", variables.get("bearing_type", ""))).strip()
        if nspan > 1 and not bearing_type:
            warnings.append("Bearing type is not identified for a multi-span bridge")

        # Title block completeness
        metadata_fields = ("PROJECT_NAME", "DRAWING_NO", "REVISION", "DRAWN_BY", "CHECKED_BY", "APPROVED_BY")
        missing_metadata = [field for field in metadata_fields if not str(variables.get(field, "")).strip()]
        if missing_metadata:
            warnings.append("Title block metadata missing: " + ", ".join(missing_metadata))

    except Exception as exc:
        warnings.append(f"Validation error: {exc}")

    score = max(0, 100 - (len(issues) * 20 + len(warnings) * 5))
    return {
        "is_valid": len(issues) == 0,
        "critical_issues": issues,
        "warnings": warnings,
        "score": score,
    }


# ── DXF Entity Cleanup ────────────────────────────────────────────────────────

def cleanup_dxf_entities(doc, eps: float = 1e-6) -> Dict[str, int]:
    """Remove orphan/degenerate entities from a DXF document.

    Sourced from BridgeCanvas/bridge_processor.py::remove_orphan_points_and_degenerate_entities

    Removes:
      - Zero-length LINEs
      - LWPOLYLINEs with <2 distinct vertices or near-zero extents
      - Zero-radius CIRCLEs and ARCs
      - Stray POINT entities

    Returns:
        Dict with removed counts per entity type.
    """
    msp = doc.modelspace()
    removed = {
        "lines": 0,
        "polylines": 0,
        "circles": 0,
        "arcs": 0,
        "points": 0,
    }
    to_remove: List[Tuple[str, Any]] = []

    for e in list(msp.query("LINE")):
        try:
            s, t = e.dxf.start, e.dxf.end
            dx, dy, dz = float(s.x) - float(t.x), float(s.y) - float(t.y), float(s.z) - float(t.z)
            if dx * dx + dy * dy + dz * dz <= eps * eps:
                to_remove.append(("lines", e))
        except Exception:
            continue

    for e in list(msp.query("LWPOLYLINE")):
        try:
            pts = [tuple(p[:2]) for p in e.get_points("xy")]
            if len(pts) < 2:
                to_remove.append(("polylines", e))
                continue
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            if (max(xs) - min(xs))**2 + (max(ys) - min(ys))**2 <= eps * eps:
                to_remove.append(("polylines", e))
        except Exception:
            continue

    for e in list(msp.query("CIRCLE")):
        try:
            if float(e.dxf.radius) <= eps:
                to_remove.append(("circles", e))
        except Exception:
            continue

    for e in list(msp.query("ARC")):
        try:
            if float(e.dxf.radius) <= eps:
                to_remove.append(("arcs", e))
        except Exception:
            continue

    for e in list(msp.query("POINT")):
        to_remove.append(("points", e))

    for key, ent in to_remove:
        try:
            ent.destroy()
            removed[key] += 1
        except Exception:
            continue

    total = sum(removed.values())
    if total:
        logger.info("DXF cleanup removed %d entities: %s", total, removed)
    return removed


# ── Bridge Templates ──────────────────────────────────────────────────────────

BRIDGE_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "simple_12m": {
        "name": "Simple Span 12m",
        "description": "Single span RCC slab bridge (12m)",
        "parameters": merge_with_metadata({
            "SCALE1": 186, "SCALE2": 1, "SKEW": 0, "DATUM": 95, "TOPRL": 100,
            "LEFT": 0, "RIGHT": 100, "XINCR": 5, "YINCR": 1, "NOCH": 2,
            "NSPAN": 1, "LBRIDGE": 12, "ABTL": 0, "RTL": 100.5, "SOFL": 99.5,
            "LANES": 1, "FOOTPATHW": 0.0, "MEDIANW": 0.0,
            "KERBW": 0.23, "KERBD": 0.15, "CCBR": 8.0, "SLBTHC": 0.6,
            "SLBTHE": 0.6, "SLBTHT": 0.6, "CROSSFALL": 0.025, "WCTH": 0.08,
            "CRASHB": 1, "BARRIERH": 1.10, "BARRIERT": "RCC crash barrier",
            "UTILITYD": 0.0, "DRAINSP": 6.0, "EXPJT": 0.025,
            "BEARING_TYPE": "Elastomeric", "BEARING_W": 0.45,
            "CAPT": 100.5, "CAPB": 99.3,
            "CAPW": 1.2, "PIERTW": 1.2, "BATTR": 10, "PIERST": 5, "PIERN": 0,
            "SPAN1": 12, "FUTRL": 90, "FUTD": 2, "FUTW": 2.5, "FUTL": 3.5,
            "DWTH": 0.3, "ALCW": 0.75, "ALCD": 1.2, "ALFB": 10, "ALFBL": 101,
            "ALTB": 10, "ALTBL": 100.5, "ALFO": 0.5, "ALBB": 5, "ALBBL": 101.5,
            "ABTLEN": 8.46, "LASLAB": 3.5, "APWTH": 8.46, "APTHK": 0.2,
            "WCTH": 0.08, "ALFL": 95, "ARFL": 95, "ALFBR": 100.75,
            "ALTBR": 100.5, "ALFD": 1.5, "ALBBR": 101.5,
        }, DRAWING_NO="GAD-001", PROJECT_NAME="Simple Span 12 m Bridge"),
    },
    "continuous_3x12m": {
        "name": "Continuous 3×12m",
        "description": "3-span continuous RCC slab (3×12m)",
        "parameters": merge_with_metadata({
            "SCALE1": 186, "SCALE2": 1, "SKEW": 0, "DATUM": 95, "TOPRL": 100,
            "LEFT": 0, "RIGHT": 100, "XINCR": 5, "YINCR": 1, "NOCH": 2,
            "NSPAN": 3, "LBRIDGE": 36, "ABTL": 0, "RTL": 100.98, "SOFL": 99.5,
            "LANES": 2, "FOOTPATHW": 1.5, "MEDIANW": 0.0,
            "KERBW": 0.23, "KERBD": 0.15, "CCBR": 10.5, "SLBTHC": 0.75,
            "SLBTHE": 0.75, "SLBTHT": 0.75, "CROSSFALL": 0.025, "WCTH": 0.08,
            "CRASHB": 1, "BARRIERH": 1.10, "BARRIERT": "RCC crash barrier",
            "UTILITYD": 0.60, "DRAINSP": 6.0, "EXPJT": 0.025,
            "BEARING_TYPE": "Elastomeric", "BEARING_W": 0.50,
            "CAPT": 100.5, "CAPB": 99.3,
            "CAPW": 1.2, "PIERTW": 1.5, "BATTR": 10, "PIERST": 5, "PIERN": 2,
            "SPAN1": 12, "FUTRL": 90, "FUTD": 2, "FUTW": 4.5, "FUTL": 3.5,
            "DWTH": 0.3, "ALCW": 0.75, "ALCD": 1.2, "ALFB": 10, "ALFBL": 101,
            "ALTB": 10, "ALTBL": 100.5, "ALFO": 0.5, "ALBB": 5, "ALBBL": 101.5,
            "ABTLEN": 11.0, "LASLAB": 3.5, "APWTH": 11.0, "APTHK": 0.2,
            "WCTH": 0.08, "ALFL": 95, "ARFL": 95, "ALFBR": 100.75,
            "ALTBR": 100.5, "ALFD": 1.5, "ALBBR": 101.5,
        }, DRAWING_NO="GAD-002", PROJECT_NAME="Continuous 3 x 12 m Bridge"),
    },
    "girder_4x18m": {
        "name": "Girder Bridge 4×18m",
        "description": "4-span RCC girder bridge (4×18m)",
        "parameters": merge_with_metadata({
            "SCALE1": 186, "SCALE2": 1, "SKEW": 0, "DATUM": 95, "TOPRL": 105,
            "LEFT": 0, "RIGHT": 100, "XINCR": 5, "YINCR": 1, "NOCH": 2,
            "NSPAN": 4, "LBRIDGE": 72, "ABTL": 0, "RTL": 101.5, "SOFL": 99.8,
            "LANES": 2, "FOOTPATHW": 1.5, "MEDIANW": 0.0,
            "KERBW": 0.23, "KERBD": 0.15, "CCBR": 12.0, "SLBTHC": 0.9,
            "SLBTHE": 0.9, "SLBTHT": 0.9, "CROSSFALL": 0.025, "WCTH": 0.08,
            "CRASHB": 1, "BARRIERH": 1.10, "BARRIERT": "RCC crash barrier",
            "UTILITYD": 0.75, "DRAINSP": 6.0, "EXPJT": 0.030,
            "BEARING_TYPE": "Pot/PTFE bearing", "BEARING_W": 0.60,
            "CAPT": 101.0, "CAPB": 99.8,
            "CAPW": 1.5, "PIERTW": 2.0, "BATTR": 10, "PIERST": 6, "PIERN": 3,
            "SPAN1": 18, "FUTRL": 90, "FUTD": 2.5, "FUTW": 6.5, "FUTL": 4.0,
            "DWTH": 0.3, "ALCW": 0.75, "ALCD": 1.2, "ALFB": 10, "ALFBL": 101,
            "ALTB": 10, "ALTBL": 100.5, "ALFO": 0.5, "ALBB": 5, "ALBBL": 101.5,
            "ABTLEN": 12.5, "LASLAB": 3.5, "APWTH": 12.5, "APTHK": 0.25,
            "WCTH": 0.08, "ALFL": 95, "ARFL": 95, "ALFBR": 100.75,
            "ALTBR": 100.5, "ALFD": 1.5, "ALBBR": 101.5,
        }, DRAWING_NO="GAD-003", PROJECT_NAME="Girder Bridge 4 x 18 m"),
    },
    "box_culvert_8m": {
        "name": "Box Culvert 8m",
        "description": "Single cell box culvert (8m span)",
        "parameters": merge_with_metadata({
            "SCALE1": 186, "SCALE2": 1, "SKEW": 0, "DATUM": 95, "TOPRL": 100,
            "LEFT": 0, "RIGHT": 100, "XINCR": 5, "YINCR": 1, "NOCH": 2,
            "NSPAN": 1, "LBRIDGE": 8, "ABTL": 0, "RTL": 100.0, "SOFL": 99.5,
            "LANES": 1, "FOOTPATHW": 0.0, "MEDIANW": 0.0,
            "KERBW": 0.23, "KERBD": 0.15, "CCBR": 8.0, "SLBTHC": 0.5,
            "SLBTHE": 0.5, "SLBTHT": 0.5, "CROSSFALL": 0.025, "WCTH": 0.08,
            "CRASHB": 0, "BARRIERH": 0.75, "BARRIERT": "Parapet",
            "UTILITYD": 0.0, "DRAINSP": 5.0, "EXPJT": 0.020,
            "BEARING_TYPE": "Not applicable", "BEARING_W": 0.0,
            "CAPT": 100.0, "CAPB": 99.2,
            "CAPW": 1.0, "PIERTW": 0.8, "BATTR": 10, "PIERST": 4, "PIERN": 0,
            "SPAN1": 8, "FUTRL": 92, "FUTD": 1.5, "FUTW": 3.5, "FUTL": 3.0,
            "DWTH": 0.3, "ALCW": 0.75, "ALCD": 1.0, "ALFB": 10, "ALFBL": 100,
            "ALTB": 10, "ALTBL": 99.5, "ALFO": 0.5, "ALBB": 5, "ALBBL": 100.5,
            "ABTLEN": 8.46, "LASLAB": 3.0, "APWTH": 8.46, "APTHK": 0.2,
            "WCTH": 0.08, "ALFL": 95, "ARFL": 95, "ALFBR": 100.25,
            "ALTBR": 99.5, "ALFD": 1.5, "ALBBR": 100.5,
        }, DRAWING_NO="GAD-004", PROJECT_NAME="Box Culvert 8 m"),
    },
    "arch_24m": {
        "name": "Arch Bridge 24m",
        "description": "RCC arch bridge (24m span)",
        "parameters": merge_with_metadata({
            "SCALE1": 186, "SCALE2": 1, "SKEW": 0, "DATUM": 95, "TOPRL": 105,
            "LEFT": 0, "RIGHT": 100, "XINCR": 5, "YINCR": 1, "NOCH": 2,
            "NSPAN": 1, "LBRIDGE": 24, "ABTL": 0, "RTL": 102.0, "SOFL": 100.5,
            "LANES": 2, "FOOTPATHW": 1.5, "MEDIANW": 0.0,
            "KERBW": 0.23, "KERBD": 0.15, "CCBR": 11.0, "SLBTHC": 0.8,
            "SLBTHE": 0.8, "SLBTHT": 0.8, "CROSSFALL": 0.025, "WCTH": 0.08,
            "CRASHB": 1, "BARRIERH": 1.10, "BARRIERT": "RCC crash barrier",
            "UTILITYD": 0.60, "DRAINSP": 6.0, "EXPJT": 0.030,
            "BEARING_TYPE": "Fixed / guided bearing", "BEARING_W": 0.55,
            "CAPT": 101.5, "CAPB": 100.3,
            "CAPW": 1.5, "PIERTW": 2.5, "BATTR": 10, "PIERST": 6, "PIERN": 0,
            "SPAN1": 24, "FUTRL": 90, "FUTD": 2.5, "FUTW": 7.0, "FUTL": 4.5,
            "DWTH": 0.3, "ALCW": 0.75, "ALCD": 1.2, "ALFB": 10, "ALFBL": 101,
            "ALTB": 10, "ALTBL": 100.5, "ALFO": 0.5, "ALBB": 5, "ALBBL": 101.5,
            "ABTLEN": 11.5, "LASLAB": 3.5, "APWTH": 11.5, "APTHK": 0.25,
            "WCTH": 0.08, "ALFL": 95, "ARFL": 95, "ALFBR": 100.75,
            "ALTBR": 100.5, "ALFD": 1.5, "ALBBR": 101.5,
        }, DRAWING_NO="GAD-005", PROJECT_NAME="Arch Bridge 24 m"),
    },
    "pmgsy_7x9": {
        "name": "PMGSY 7×9.0m Minor Bridge",
        "description": (
            "2-sheet PMGSY standard General Arrangement for a 7-span × 9.0m "
            "minor slab bridge: Sheet 01 = Sectional Elevation + Plan; "
            "Sheet 02 = Section A-A + Soil Profile + Abutment/Return sections "
            "+ Weep holes + Schedule Table + 13 Notes (bearing=TAR PAPER)."
        ),
        "parameters": merge_with_metadata({
            # ── Drawing / scales ─────────────────────────────────────
            "SCALE1": 186, "SCALE2": 1, "SKEW": 0, "DATUM": 100.000,
            "TOPRL": 108.0, "LEFT": 0, "RIGHT": 63, "XINCR": 5, "YINCR": 1,
            "NOCH": 2,
            # ── Geometry ─────────────────────────────────────────────
            "NSPAN": 7, "LBRIDGE": 63.0, "ABTL": 0,
            "RTL": 102.515, "SOFL": 101.915,
            "SPAN1": 9.0, "SPAN2": 9.0, "SPAN3": 9.0, "SPAN4": 9.0,
            "SPAN5": 9.0, "SPAN6": 9.0, "SPAN7": 9.0,
            # ── Roadway (sample: 8.400m OA / 7.500m CW / 2x 0.450m)
            "LANES": 2, "FOOTPATHW": 0.0, "MEDIANW": 0.0,
            "CCBR": 7.5,
            "KERBW": 0.45, "KERBD": 0.225,
            "CROSSFALL": 0.020,
            "WCTH": 0.075,
            "CRASHB": 0, "BARRIERH": 0.6, "BARRIERT": "Kerb / Parapet",
            "UTILITYD": 0.0, "DRAINSP": 5.0, "EXPJT": 0.025,
            # ── Superstructure (slab) ───────────────────────────────
            "SLBTHC": 0.60, "SLBTHE": 0.60, "SLBTHT": 0.60,
            # ── Bearings ────────────────────────────────────────────
            # TAR PAPER — PMGSY minor-bridge standard (NOT elastomeric)
            "BEARING_TYPE": "Tar Paper",
            "NOTE_BEARING_OVERRIDE": "TAR PAPER bearing pad — PMGSY Minor Bridge standard",
            "BEARING_W": 0.35,
            # ── Substructure: Pier (6 piers, NSPAN-1) ───────────────
            "CAPT": 101.915, "CAPB": 100.915,
            "CAPW": 1.90, "PIERTW": 0.95, "BATTR": 10, "PIERST": 2.25,
            "PIERN": 6,
            "FUTRL": 96.400, "FUTD": 0.67, "FUTW": 2.25, "FUTL": 2.25,
            # ── Substructure: Abutments (L + R) ─────────────────────
            "DWTH": 0.25,
            "ALCW": 0.75, "ALCD": 1.00,
            "ALFB": 5, "ALFBL": 101.3, "ALFBR": 101.30,
            "ALTB": 5, "ALTBL": 100.80, "ALTBR": 100.80,
            "ALBB": 5, "ALBBL": 102.315,
            "ALFO": 0.5, "ALFD": 1.5,
            "ALFL": 96.900, "ARFL": 96.900,
            "ABTLEN": 8.40, "LASLAB": 3.0, "APWTH": 8.40, "APTHK": 0.20,
            "ALBBR": 102.315,
            # ── Wing / Return walls ─────────────────────────────────
            "WING_W": 0.40, "WING_L": 3.00, "WING_H": 5.615,
            # ── Weep holes: 100 mm Ø @ 1000 c/c, 2 staggered rows ──
            "WEEP_DIAM": 100, "WEEP_C_TO_C": 1000,
            "WEEP_ROWS": 2, "WEEP_STAGGER": 1,
            # ── Soil Profile (3 layers) ─────────────────────────────
            "SOIL1_NAME": "SOFT ROCK", "SOIL1_THICK": 0.50,
            "SOIL1_HATCH": "ANSI31", "SOIL1_COLOR": 6,
            "SOIL2_NAME": "SOIL", "SOIL2_THICK": 0.50,
            "SOIL2_HATCH": "ANSI37", "SOIL2_COLOR": 3,
            "SOIL3_NAME": "HARD ROCK", "SOIL3_THICK": 0.50,
            "SOIL3_HATCH": "AR-SAND", "SOIL3_COLOR": 5,
            "AVG_GL_RL": 101.50,
            # ── Bridge Schedule Table ───────────────────────────────
            "SCHED_SNO": "1",
            "SCHED_CHAINAGE": "CH 2+300",
            "SCHED_TYPE": "Slab",
            "SCHED_FRL": 102.515,
            "SCHED_BL": 96.900,
            "SCHED_PROPOSED": "7x9.0 m",
            "SCHED_SPAN_TEXT": "7x9.0m Slab (Total 63m)",
            "SCHED_HEIGHT": 5.515,
            "SCHED_B1": 1.90,
            "SCHED_B2": 0.95,
            "SCHED_B3": 2.25,
            "SCHED_B4": 0.67,
            # ── Notes Panel (13 items, matching sample PDF exactly) ─
            "NOTE1_TEXT": "1) All dimensions are in millimeters unless otherwise stated. Levels are in metres.",
            "NOTE2_TEXT": "2) All RCC works conforming to the relevant IRC/IS Specifications shall be adopted.",
            "NOTE3_TEXT": "3) Concrete mix: PCC M-10 for soling, PCC M-15 for abutment/return/well, RCC M-20 for general, RCC M-30 for deck slab/pier caps, minimum cement content 320 kg/m³.",
            "NOTE4_TEXT": "4) Reinforcement: HYSD bars Fe 500 IS:1786. TMT bars of approved make only.",
            "NOTE5_TEXT": "5) Clear cover to reinforcement: 40mm for deck, 50mm for piers, 60mm for footings in contact with soil.",
            "NOTE6_TEXT": "6) Bearing type – TAR PAPER bearing pad of approved thickness. Replace at 5 yearly maintenance cycle.",
            "NOTE7_TEXT": "7) Weep holes 100 mm diameter at 1000 mm c/c staggered in abutment & return walls. 300mm thick graded filter behind every weep hole.",
            "NOTE8_TEXT": "8) Backfill behind abutment / wing walls with non-plastic granular material. Parameters: C=0, φ ≥ 30°, γ = 18 kN/m³. Compacted 95% Proctor density in 250mm layers.",
            "NOTE9_TEXT": "9) Design live load basis: Class A-3 Tracked / 70-R Wheeled + Class A, per applicable IRC provisions.",
            "NOTE10_TEXT": "10) Scour depth: Minimum 2.00 m below HFL as per IRC-78 provisions. Founding level shall be checked against latest site bore log.",
            "NOTE11_TEXT": "11) Minimum clear vertical clearance under bridge superstructure: 5.50 m above HFL for waterway and 5.00 m above road top for approaches.",
            "NOTE12_TEXT": "12) Distance from bridge structure to nearest weir / barrage / obstruction: 20.00 metres minimum, verify with site plan.",
            "NOTE13_TEXT": "13) Expansion joints at every pier line. Neoprene / bituminous poured joint with top-seal cover plate at every 9.000 m c/c.",
            "NOTE_CONCRETE_GRADES": "PCC M-10 (soling) | PCC M-15 (abutment/return/well) | RCC M-20 (general) | RCC M-30 (deck/pier caps)",
            "NOTE_REINF_STANDARD": "Fe 500 HYSD bars conforming to IS:1786",
            "NOTE_LIVE_LOAD_COMBO": "Class A-3 Tracked / 70-R Wheeled + Class A (IRC)",
            "NOTE_BACKFILL_PARAMS": "C = 0 ; φ ≥ 30° ; γ = 18 kN/m³",
            "NOTE_SCOUR_CODE": "2.00 m below HFL — IRC-78",
            "NOTE_DIST_TO_WEIR": 20.0,
            # ── Ground profile (optional JSON; user can provide Sheet2)
            "GROUND_PROFILE_JSON": "",
        },
            DRAWING_NO="01-GAD-AT-CH-2-300-7X9-0",
            PROJECT_NAME="PMGSY Minor Bridge — Chainage CH 2+300",
            PROJECT_CODE="CH-2-300",
            REVISION="R0",
            OWNER_PROFILE="PMGSY",
            SHEET_NO="1",
            TOTAL_SHEETS="2",
            DESIGN_LIVE_LOAD="Class A-3 / 70-R + Class A (IRC)",
            DRAWING_STANDARD="PMGSY Minor Bridge 2-Sheet GAD Standard",
            ROAD_CLASS="PMGSY Village Road — 7.50 m clear carriageway",
            DRAWN_BY="Design Cell — Bridge GAD Generator",
            CHECKED_BY="Design Engineer (Structures)",
            APPROVED_BY="Executive Engineer / Competent Authority",
            COMPANY_NAME="RKS LEGAL — Techno Legal Consultants",
            COMPANY_FULL="RKS LEGAL, Techno Legal Consultants, Udaipur",
            DRAWING_TITLE="GENERAL ARRANGEMENT DRAWING (GAD) FOR 7 × 9.0 m MINOR SLAB BRIDGE AT CH 2+300",
        ),
    },
}


def make_template_excel(
    params: Dict[str, Any],
    *,
    sheet_rows: Iterable[Dict[str, str]] | None = None,
) -> bytes:
    """Return Excel bytes for a template parameter dict.

    Parameters
    ----------
    params:
        Bridge parameter dictionary.
    sheet_rows:
        Optional override for the ``SheetIndex`` worksheet rows.  When
        ``None`` (default) the seven-row phase-two schedule is used.
        Pass :func:`phase_three_sheet_rows` for the eleven-row
        submission set.
    """
    df = pd.DataFrame(build_template_rows(params))
    checklist_df = pd.DataFrame(checklist_rows())
    owner_df = pd.DataFrame(owner_profile_rows())
    sheet_df = pd.DataFrame(
        phase_two_sheet_rows() if sheet_rows is None else list(sheet_rows)
    )
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Parameters")
        checklist_df.to_excel(w, index=False, sheet_name="Checklist")
        owner_df.to_excel(w, index=False, sheet_name="OwnerProfiles")
        sheet_df.to_excel(w, index=False, sheet_name="SheetIndex")
    buf.seek(0)
    return buf.getvalue()


def make_phase_two_package_zip(
    params: Dict[str, Any],
    *,
    include_pdfs: bool = False,
    pdf_layout: str = "A4_landscape",
    include_phase_three: bool = False,
) -> bytes:
    """Bundle a phase two starter package into a ZIP archive.

    Parameters
    ----------
    params:
        Bridge parameter dictionary (will be enriched via ``merge_with_metadata``).
    include_pdfs:
        When True, run a full generation pass and include:
            * single GAD DXF + PDF,
            * 7-sheet phase-two package (DXF + per-sheet PDF),
            * a multi-sheet ``DRAWINGS_BOOKLET`` PDF combining everything,
        alongside the standard parameter workbook / sheet index / manifest.
    pdf_layout:
        Page layout preset used when rendering PDFs (``A4_landscape``,
        ``A3_landscape``, etc.).
    include_phase_three:
        When True, also attach the 4 phase-three detail worksheets
        (BRG-DET, EXPJ-DET, WING-DET, DRN-DET) and the 11-row schedule
        in the manifest and CSV.  For the dedicated eleven-sheet ZIP
        helper see :func:`make_phase_three_package_zip`.
    """

    enriched = merge_with_metadata(params)
    if include_phase_three:
        enriched["INCLUDE_PHASE_THREE"] = True
    profile = get_owner_profile(enriched.get("OWNER_PROFILE"))

    rows_source = (
        phase_three_sheet_rows() if include_phase_three else phase_two_sheet_rows()
    )
    manifest: Dict[str, Any] = {
        "owner_profile": profile.key,
        "owner": profile.owner,
        "drawing_standard": enriched.get("DRAWING_STANDARD", profile.drawing_standard),
        "design_live_load": enriched.get("DESIGN_LIVE_LOAD", profile.design_live_load),
        "total_sheets": len(rows_source),
        "sheets": rows_source,
        "include_phase_three": bool(include_phase_three),
    }

    csv_bytes = pd.DataFrame(rows_source).to_csv(index=False).encode("utf-8")
    workbook_bytes = make_template_excel(enriched, sheet_rows=rows_source)

    drawings_extra: List[Tuple[str, bytes]] = []
    pdf_manifest: Dict[str, Any] = {"included": False}

    if include_pdfs:
        import tempfile
        from .bridge_generator import BridgeGADGenerator
        from .multi_sheet_generator import DetailedSheetGenerator
        from .dxf_to_pdf import (
            RenderOptions,
            bundle_drawings_to_pdf,
            convert_dxf_to_pdf,
        )

        with tempfile.TemporaryDirectory() as tmp:
            tdir = Path(tmp)
            rows = [[v, k, k] for k, v in enriched.items()]
            df = pd.DataFrame(rows, columns=["Value", "Variable", "Description"])
            excel_in = tdir / "phase2_params.xlsx"
            df.to_excel(excel_in, index=False, header=False)

            single_dxf = tdir / "phase2_gad.dxf"
            gen = BridgeGADGenerator()
            ok_single = bool(gen.generate_complete_drawing(excel_in, single_dxf))
            ok_single = ok_single and single_dxf.exists()

            sheet_base = tdir / "phase2_pkg.dxf"
            dsg = DetailedSheetGenerator()
            if include_phase_three:
                ok_pkg = bool(dsg.generate_phase_three_package(enriched, sheet_base))
            else:
                ok_pkg = bool(dsg.generate_phase_two_package(enriched, sheet_base))
            produced = sorted(sheet_base.parent.glob(f"{sheet_base.stem}_Sheet*.dxf"))

            opts = RenderOptions(layout=pdf_layout)
            produced_for_book: List[Path] = []
            if single_dxf.exists():
                sp = convert_dxf_to_pdf(
                    single_dxf, opts=opts, page_title="GAD Plan + Elevation"
                )
                drawings_extra.append(
                    ("phase2/drawings/dxf/" + single_dxf.name, single_dxf.read_bytes())
                )
                drawings_extra.append(
                    ("phase2/drawings/pdf/" + sp.name, sp.read_bytes())
                )
                produced_for_book.append(single_dxf)

            for dxf in produced:
                p = convert_dxf_to_pdf(
                    dxf, opts=opts,
                    page_title=dxf.stem.replace("phase2_pkg_", "")
                )
                drawings_extra.append(
                    ("phase2/drawings/dxf/" + dxf.name, dxf.read_bytes())
                )
                drawings_extra.append(
                    ("phase2/drawings/pdf/" + p.name, p.read_bytes())
                )
                produced_for_book.append(dxf)

            if produced_for_book:
                book = tdir / "phase2_DRAWINGS_BOOKLET.pdf"
                titles = []
                for p in produced_for_book:
                    titles.append(
                        p.stem
                        .replace("phase2_pkg_", "")
                        .replace("phase2_gad", "GAD Plan+Elevation")
                    )
                suffix = " + Phase 3 Details" if include_phase_three else ""
                book_p = bundle_drawings_to_pdf(
                    produced_for_book, book, opts=opts, page_titles=titles,
                    cover_page_title=(
                        f"Phase 2{suffix} Drawing Booklet — {profile.owner}"
                        f" — {len(produced_for_book)} sheet(s)"
                    ),
                )
                drawings_extra.append(
                    ("phase2/drawings/pdf/" + book_p.name, book_p.read_bytes())
                )
                pdf_manifest = {
                    "included": True,
                    "layout": pdf_layout,
                    "sheets_rendered": len(produced_for_book),
                    "booklet": "phase2/drawings/pdf/" + book_p.name,
                    "generator_ok_single_dxf": bool(ok_single),
                    "phase_two_ok": bool(ok_pkg),
                }

    manifest["pdf_rendering"] = pdf_manifest

    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("phase2/phase2_parameters.xlsx", workbook_bytes)
        zf.writestr("phase2/phase2_sheet_index.csv", csv_bytes)
        zf.writestr("phase2/phase2_manifest.json", json.dumps(manifest, indent=2))
        for arcname, payload in drawings_extra:
            if isinstance(payload, (bytes, bytearray)):
                zf.writestr(arcname, payload)
    buf.seek(0)
    return buf.getvalue()


def make_phase_three_package_zip(
    params: Dict[str, Any],
    *,
    include_pdfs: bool = False,
    pdf_layout: str = "A4_landscape",
) -> bytes:
    """Bundle the 11-sheet phase three submission package into a ZIP archive.

    This is a thin convenience wrapper around
    :func:`make_phase_two_package_zip` with ``include_phase_three=True`` and
    a phase-three–prefixed ZIP layout.  The resulting archive contains:

    * ``phase3/phase3_parameters.xlsx`` — enriched template workbook with
      the four OwnerProfile presets, the 11-row sheet index, checklist,
      and Phase 3 parameter vocabulary (bearing dims, expansion joint,
      wing-wall reinforcement, drainage downtake specs).
    * ``phase3/phase3_sheet_index.csv`` — CSV of the 11-sheet schedule.
    * ``phase3/phase3_manifest.json`` — owner profile, live-load basis,
      total sheet count (11), ``phase3=true`` flag, PDF rendering info.
    * ``phase3/drawings/dxf/`` — when ``include_pdfs=True``: 1 single GAD
      DXF + 11 numbered sheet DXF files.
    * ``phase3/drawings/pdf/`` — when ``include_pdfs=True``: the matching
      PDFs plus an ``ALL_BATCH_DRAWINGS`` booklet.

    Technical-integrity note: every placeholder proportion on sheets 8–11
    is ring-fenced on the DXF drawing itself with a ``TBC_BY_ENGINEER``
    dashed stamp so the reviewer can see which values still need to be
    resolved by a registered professional before issue.
    """

    inner = make_phase_two_package_zip(
        params,
        include_pdfs=include_pdfs,
        pdf_layout=pdf_layout,
        include_phase_three=True,
    )
    # Rewrite the ZIP: phase2/ → phase3/ AND phase2_ → phase3_ inside names
    import io as _io
    out = _io.BytesIO()
    with zipfile.ZipFile(_io.BytesIO(inner), "r") as zin:
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
            for info in zin.infolist():
                new_name = (
                    info.filename
                    .replace("phase2/", "phase3/", 1)
                    .replace("/phase2_", "/phase3_")
                )
                payload = zin.read(info.filename)
                if "manifest" in new_name.lower() and new_name.endswith(".json"):
                    import json as _json
                    try:
                        obj = _json.loads(payload.decode("utf-8"))
                        obj["phase3"] = True
                        payload = _json.dumps(obj, indent=2).encode("utf-8")
                    except Exception:
                        pass
                zout.writestr(new_name, payload)
    out.seek(0)
    return out.getvalue()


def batch_results_to_zip(
    results: List[Dict[str, Any]],
    *,
    include_pdfs: bool = False,
    pdf_layout: str = "A4_landscape",
) -> bytes:
    """Bundle successful batch results into a ZIP archive.

    When ``include_pdfs`` is True, each successful DXF is also rendered
    into a PDF, plus a multi-page booklet ``ALL_BATCH_DRAWINGS.pdf.
    """
    import tempfile
    from .dxf_to_pdf import (
        RenderOptions,
        bundle_drawings_to_pdf,
        convert_dxf_to_pdf,
    )
    import io
    buf = io.BytesIO()

    drawings_dir: Optional[Path] = None
    tmp_ctx = None
    if include_pdfs:
        tmp_ctx = tempfile.TemporaryDirectory()
        drawings_dir = Path(tmp_ctx.__enter__())

    opts = RenderOptions(layout=pdf_layout)
    dxf_paths: List[Path] = []
    dxf_names: List[str] = []

    try:
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for r in results:
                if not (r["success"] and r.get("dxf_bytes")):
                    continue
                stem = Path(r["filename"]).stem
                dxf_arc = f"drawings/dxf/{stem}.dxf"
                zf.writestr(dxf_arc, r["dxf_bytes"])
                if include_pdfs and drawings_dir is not None:
                    dxf_file = drawings_dir / f"{stem}.dxf"
                    dxf_file.write_bytes(r["dxf_bytes"])
                    pdf_file = convert_dxf_to_pdf(
                        dxf_file, opts=opts, page_title=stem
                    )
                    zf.writestr(
                        f"drawings/pdf/{pdf_file.name}",
                        pdf_file.read_bytes()
                    )
                    dxf_paths.append(dxf_file)
                    dxf_names.append(stem)

            if include_pdfs and dxf_paths and drawings_dir is not None:
                book = drawings_dir / "ALL_BATCH_DRAWINGS.pdf"
                bundle_drawings_to_pdf(
                    dxf_paths, book, opts=opts, page_titles=dxf_names,
                    cover_page_title=(
                        f"Batch Drawing Booklet — {len(dxf_paths)} sheet(s)"
                    ),
                )
                zf.writestr(
                    "drawings/pdf/" + book.name, book.read_bytes()
                )
    finally:
        if tmp_ctx is not None:
            tmp_ctx.__exit__(None, None, None)

    buf.seek(0)
    return buf.getvalue()


# ── Batch Processing ──────────────────────────────────────────────────────────

def batch_generate(
    files: List[Tuple[str, bytes]],
    acad_version: str = "R2010",
) -> List[Dict[str, Any]]:
    """Generate DXF for multiple Excel files.

    Args:
        files: List of (filename, bytes) tuples.
        acad_version: AutoCAD version string.

    Returns:
        List of result dicts with keys: filename, success, dxf_bytes, error.
    """
    import tempfile
    from .bridge_generator import BridgeGADGenerator

    results = []
    for filename, file_bytes in files:
        safe_name = Path(filename).name
        try:
            with tempfile.TemporaryDirectory() as tmp:
                tmp_path = Path(tmp)
                excel_path = tmp_path / safe_name
                excel_path.write_bytes(file_bytes)
                output_path = tmp_path / f"{excel_path.stem}.dxf"

                gen = BridgeGADGenerator(acad_version=acad_version)
                ok = gen.generate_complete_drawing(excel_path, output_path)

                if ok and output_path.exists():
                    results.append({
                        "filename": safe_name,
                        "success": True,
                        "dxf_bytes": output_path.read_bytes(),
                        "error": None,
                    })
                else:
                    results.append({
                        "filename": safe_name,
                        "success": False,
                        "dxf_bytes": None,
                        "error": "Generation returned no output",
                    })
        except Exception as exc:
            logger.exception("Batch generation failed for %s", safe_name)
            results.append({
                "filename": safe_name,
                "success": False,
                "dxf_bytes": None,
                "error": str(exc),
            })
    return results


# ── Smart Title Recentering ───────────────────────────────────────────────────

def smart_recenter_title(
    elements: List[Dict[str, Any]],
    *,
    title_tag: str = "title_block",
    target_origin: Tuple[float, float] = (50.0, 50.0),
) -> None:
    """Move the title block to target_origin, shifting the whole drawing.

    Sourced from BridgeCanvas/smart_title.py
    """
    titles = [e for e in elements if e.get("tag") == title_tag]
    if not titles:
        return
    title = titles[0]
    dx = target_origin[0] - title["x"]
    dy = target_origin[1] - title["y"]
    for el in elements:
        el["x"] += dx
        el["y"] += dy
