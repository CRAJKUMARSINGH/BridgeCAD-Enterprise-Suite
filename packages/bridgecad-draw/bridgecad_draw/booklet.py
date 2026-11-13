"""
bridgecad_draw.booklet — 9-sheet DXF package generator.

Sheet manifest:
  Sheet 1  PLAN VIEW                    sheet1_plan
  Sheet 2  LONGITUDINAL SECTION         sheet2_long_section
  Sheet 3  CROSS SECTION (MID-SPAN)     sheet3_cross_section
  Sheet 4  FOUNDATION DETAILS           sheet4_foundation
  Sheet 5  PIER & ABUTMENT DETAILS      sheet5_pier_abutment_details
  Sheet 6  BEARINGS & JOINTS SCHEDULE   sheet6_bearings_joints
  Sheet 7  BILL OF QUANTITIES           sheet7_bill_of_quantities
  Sheet 8  SIDE & END ELEVATIONS        sheet8_side_elevations
  Sheet 9  REINFORCEMENT SCHEDULE       sheet9_reinforcement
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# A missing optional dependency (ezdxf) makes every sheet fail identically, so a
# naive per-sheet warning prints the same line 8 times and buries any real
# failure. Warn once for the first sheet, then drop to debug — the full
# per-sheet trace stays available at -v.
_missing_dep_warned = False


class PackageGenerationError(RuntimeError):
    """Raised when one or more GAD sheets fail to generate.

    A partial package that is silently returned as success produces a ZIP or
    drawing folder that is missing a sheet with no signal to the caller. The
    failure of even a single sheet is therefore fatal: callers (API, CLI,
    export orchestrator) surface it instead of shipping an incomplete set.
    """

    def __init__(self, failures: dict[int, str]) -> None:
        self.failures = dict(failures)
        detail = "; ".join(f"Sheet {no}: {msg}" for no, msg in failures.items())
        super().__init__(
            f"{len(self.failures)} of {len(_SHEET_MANIFEST)} GAD sheets failed — {detail}"
        )


# Each entry: (sheet_no, module_attr, filename_stem, default_scale)
# A ``None`` default means "let the sheet pick its own scale": the plan (1),
# the long section (2), the cross section (3), the pier & abutment details (5)
# and the end elevations (8) each resolve their own rung — sheets 1/2/3/8 fit
# the largest rung of ``fit.LADDER`` that fits the view, sheet 5 uses the rung
# its pinned layout was designed at — and print that rung in the title block.
# A fixed default there produced a caption that disagreed with the geometry.
# Sheet 4 (foundation) is pinned at 1:50 and prints it. Sheets 6, 7 and 9 are
# schedules, tabulated rather than plotted: their title blocks honestly read
# NTS, so the entry here is a nominal placeholder the sheet ignores.
_SHEET_MANIFEST = [
    (1, "sheet1_plan", "Sheet1_Plan", None),
    (2, "sheet2_long_section", "Sheet2_LongSection", None),
    (3, "sheet3_cross_section", "Sheet3_CrossSection", None),
    (4, "sheet4_foundation", "Sheet4_Foundation", 50),
    (5, "sheet5_pier_abutment_details", "Sheet5_PierAbutment", None),
    (6, "sheet6_bearings_joints", "Sheet6_BearingsJoints", 20),
    (7, "sheet7_bill_of_quantities", "Sheet7_BOQ", 1),
    (8, "sheet8_side_elevations", "Sheet8_SideElevations", None),
    (9, "sheet9_reinforcement", "Sheet9_Reinforcement", 1),
]


def generate_package(
    project: Any,
    output_dir: str | Path,
    prefix: str = "GAD",
    scale_denom: int | None = None,
) -> list[Path]:
    """Generate all 9 GAD sheets for *project*.

    Parameters
    ----------
    project : BridgeProject
    output_dir : str | Path
        Directory where DXF files are saved.
    prefix : str
        Filename prefix  (e.g. ``"GAD"`` → ``GAD_Sheet1_Plan.dxf``)
    scale_denom : int | None
        Plot-scale denominator.  ``None`` (default) uses each sheet's own
        standard scale from the manifest (e.g. 1:100 plan, 1:1 BOQ).  An int
        overrides **every** sheet with that denominator — including 100, which
        is now an explicit request rather than a magic "use defaults" value.

    Returns
    -------
    list[Path]
        Paths of the generated DXF files, one per manifest entry.

    Raises
    ------
    PackageGenerationError
        If any sheet fails to generate.  A partial package is never returned.
    """
    import importlib

    global _missing_dep_warned

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    results: list[Path] = []
    failures: dict[int, str] = {}

    for sheet_no, mod_attr, stem, sheet_scale in _SHEET_MANIFEST:
        sc = sheet_scale if scale_denom is None else scale_denom
        out_path = out / f"{prefix}_{stem}.dxf"
        try:
            mod = importlib.import_module(f".{mod_attr}", package="bridgecad_draw")
            p = mod.generate(project, out_path, scale_denom=sc)
            results.append(p)
            logger.info(
                "Sheet %d (%s) → %s  (%d KB)", sheet_no, stem, p.name, p.stat().st_size // 1024
            )
        except Exception as exc:
            failures[sheet_no] = f"{type(exc).__name__}: {exc}"
            # Only the optional-dependency case is de-duplicated. A genuine
            # ImportError inside a sheet module stays a loud per-sheet warning.
            if isinstance(exc, ImportError) and "ezdxf" in str(exc):
                if _missing_dep_warned:
                    logger.debug("Sheet %d (%s) skipped: %s", sheet_no, stem, exc)
                else:
                    logger.warning("Sheet %d (%s) skipped: %s", sheet_no, stem, exc)
                    _missing_dep_warned = True
            else:
                logger.warning("Sheet %d (%s) failed: %s", sheet_no, stem, exc)

    if failures:
        logger.error(
            "Package incomplete: %d/%d sheets generated, %d failed",
            len(results),
            len(_SHEET_MANIFEST),
            len(failures),
        )
        raise PackageGenerationError(failures)

    logger.info("Package complete: %d/%d sheets in %s", len(results), len(_SHEET_MANIFEST), out)
    return results


__all__ = ["generate_package", "PackageGenerationError"]
