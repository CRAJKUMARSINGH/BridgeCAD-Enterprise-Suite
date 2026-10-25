"""
bridgecad_draw.booklet — 8-sheet DXF package generator.

Sheet manifest:
  Sheet 1  PLAN VIEW                    sheet1_plan
  Sheet 2  LONGITUDINAL SECTION         sheet2_long_section
  Sheet 3  CROSS SECTION (MID-SPAN)     sheet3_cross_section
  Sheet 4  FOUNDATION DETAILS           sheet4_foundation
  Sheet 5  PIER & ABUTMENT DETAILS      sheet5_pier_abutment_details
  Sheet 6  BEARINGS & JOINTS SCHEDULE   sheet6_bearings_joints
  Sheet 7  BILL OF QUANTITIES           sheet7_bill_of_quantities
  Sheet 8  SIDE & END ELEVATIONS        sheet8_side_elevations
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Each entry: (sheet_no, module_attr, filename_stem, default_scale)
_SHEET_MANIFEST = [
    (1, "sheet1_plan", "Sheet1_Plan", 100),
    (2, "sheet2_long_section", "Sheet2_LongSection", 100),
    (3, "sheet3_cross_section", "Sheet3_CrossSection", 50),
    (4, "sheet4_foundation", "Sheet4_Foundation", 50),
    (5, "sheet5_pier_abutment_details", "Sheet5_PierAbutment", 50),
    (6, "sheet6_bearings_joints", "Sheet6_BearingsJoints", 20),
    (7, "sheet7_bill_of_quantities", "Sheet7_BOQ", 1),
    (8, "sheet8_side_elevations", "Sheet8_SideElevations", 50),
]


def generate_package(
    project: Any,
    output_dir: str | Path,
    prefix: str = "GAD",
    scale_denom: int = 100,
) -> list[Path]:
    """Generate all 8 GAD sheets for *project*.

    Parameters
    ----------
    project : BridgeProject
    output_dir : str | Path
        Directory where DXF files are saved.
    prefix : str
        Filename prefix  (e.g. ``"GAD"`` → ``GAD_Sheet1_Plan.dxf``)
    scale_denom : int
        Default horizontal scale denominator; each sheet may override.

    Returns
    -------
    list[Path]
        Paths of successfully generated DXF files (may be < 8 on partial failure).
    """
    import importlib

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    results: list[Path] = []

    for sheet_no, mod_attr, stem, sheet_scale in _SHEET_MANIFEST:
        sc = sheet_scale if scale_denom == 100 else scale_denom
        out_path = out / f"{prefix}_{stem}.dxf"
        try:
            mod = importlib.import_module(f".{mod_attr}", package="bridgecad_draw")
            p = mod.generate(project, out_path, scale_denom=sc)
            results.append(p)
            logger.info(
                "Sheet %d (%s) → %s  (%d KB)", sheet_no, stem, p.name, p.stat().st_size // 1024
            )
        except Exception as exc:
            logger.warning("Sheet %d (%s) failed: %s", sheet_no, stem, exc)

    logger.info("Package complete: %d/8 sheets in %s", len(results), out)
    return results


__all__ = ["generate_package"]
