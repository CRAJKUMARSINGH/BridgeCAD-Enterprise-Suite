"""
bridgecad_draw.booklet — 11-sheet DXF package generator.

Sheet manifest:
  Sheet 1   PLAN VIEW                       sheet1_plan
  Sheet 2   LONGITUDINAL SECTION            sheet2_long_section
  Sheet 3   CROSS SECTION (MID-SPAN)        sheet3_cross_section
  Sheet 4   FOUNDATION DETAILS              sheet4_foundation
  Sheet 5   PIER & ABUTMENT DETAILS         sheet5_pier_abutment_details
  Sheet 5A  ENLARGED PIER DETAILS           sheet5_enlarged_details (pier)
  Sheet 5B  ENLARGED ABUTMENT DETAILS       sheet5_enlarged_details (abutment)
  Sheet 6   BEARINGS & JOINTS SCHEDULE      sheet6_bearings_joints
  Sheet 7   BILL OF QUANTITIES              sheet7_bill_of_quantities
  Sheet 8   SIDE & END ELEVATIONS           sheet8_side_elevations
  Sheet 9   REINFORCEMENT SCHEDULE          sheet9_reinforcement

EP-2026-12 changes (applied):
  • Sheets 5A and 5B added to the manifest.
  • After every sheet is generated, ``dim_style.apply_native_dimensions`` is
    called to convert all DIMENSION entities to measured ``"<>"`` text with the
    correct ``DIMLFAC`` for the sheet's scale.  Sheets with no DIMENSION
    entities (count = 0) are written back unchanged.
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

# Fall-back scale denominator used by the native-dimension pass for sheets that
# resolve their own rung at generate time and do not expose it.  1:100 is
# conservative: it errs on the side of a larger DIMLFAC (displayed value is
# slightly too large) rather than a smaller one (text would read mm instead of m).
_FALLBACK_SCALE = 100


class PackageGenerationError(RuntimeError):
    """Raised when one or more GAD sheets fail to generate.

    A partial package that is silently returned as success produces a ZIP or
    drawing folder that is missing a sheet with no signal to the caller. The
    failure of even a single sheet is therefore fatal: callers (API, CLI,
    export orchestrator) surface it instead of shipping an incomplete set.
    """

    def __init__(self, failures: dict[str, str]) -> None:
        self.failures = dict(failures)
        detail = "; ".join(f"Sheet {no}: {msg}" for no, msg in failures.items())
        super().__init__(
            f"{len(self.failures)} of {len(_SHEET_MANIFEST)} GAD sheets failed — {detail}"
        )


# Each entry: (sheet_id, module_attr, filename_stem, default_scale, part)
#
# ``sheet_id``    — string identifier used in error messages and spec keys
# ``module_attr`` — bridgecad_draw sub-module name
# ``stem``        — output filename stem (prefix_<stem>.dxf)
# ``default_scale`` — None → sheet picks own rung; int → passed as scale_denom
# ``part``        — extra kwarg for sheets that generate more than one variant
#                   (sheet5_enlarged_details uses part="pier"/"abutment");
#                   None for all other sheets
#
# A ``None`` default_scale means "let the sheet pick its own scale": the plan (1),
# long section (2), cross section (3), pier & abutment details (5), and end
# elevations (8) each resolve their own rung.  Sheet 4 (foundation) is pinned
# at 1:50.  Sheets 6, 7 and 9 are schedules (NTS).
_SHEET_MANIFEST = [
    ("1",   "sheet1_plan",                 "Sheet1_Plan",            None, None),
    ("2",   "sheet2_long_section",         "Sheet2_LongSection",     None, None),
    ("3",   "sheet3_cross_section",        "Sheet3_CrossSection",    None, None),
    ("4",   "sheet4_foundation",           "Sheet4_Foundation",      50,   None),
    ("5",   "sheet5_pier_abutment_details","Sheet5_PierAbutment",    None, None),
    ("5A",  "sheet5_enlarged_details",     "Sheet5A_PierEnlarged",   None, "pier"),
    ("5B",  "sheet5_enlarged_details",     "Sheet5B_AbutEnlarged",   None, "abutment"),
    ("6",   "sheet6_bearings_joints",      "Sheet6_BearingsJoints",  20,   None),
    ("7",   "sheet7_bill_of_quantities",   "Sheet7_BOQ",             1,    None),
    ("8",   "sheet8_side_elevations",      "Sheet8_SideElevations",  None, None),
    ("9",   "sheet9_reinforcement",        "Sheet9_Reinforcement",   1,    None),
]


def _apply_native_dims(path: Path, scale_denom: int | None) -> None:
    """Post-process a generated DXF: convert all DIMENSIONs to measured text.

    Reads the file, applies ``dim_style.apply_native_dimensions``, and
    overwrites.  If ezdxf or dim_style is unavailable the file is left as-is
    (no exception propagated — the sheet itself is valid; only dimension text
    quality degrades).
    """
    try:
        import ezdxf
        from .dim_style import DimStyleConfig, apply_native_dimensions

        sc = scale_denom if (scale_denom and scale_denom > 1) else _FALLBACK_SCALE
        doc = ezdxf.readfile(str(path))
        n = apply_native_dimensions(doc, DimStyleConfig(units="m", decimals=3), sc)
        if n:
            doc.saveas(str(path))
            logger.debug("Native dims applied to %s: %d entities converted", path.name, n)
    except Exception as exc:
        logger.debug("Native dim pass skipped for %s: %s", path.name, exc)


def generate_package(
    project: Any,
    output_dir: str | Path,
    prefix: str = "GAD",
    scale_denom: int | None = None,
) -> list[Path]:
    """Generate all 11 GAD sheets for *project*.

    Parameters
    ----------
    project : BridgeProject
    output_dir : str | Path
        Directory where DXF files are saved.
    prefix : str
        Filename prefix  (e.g. ``"GAD"`` → ``GAD_Sheet1_Plan.dxf``)
    scale_denom : int | None
        Plot-scale denominator.  ``None`` (default) uses each sheet's own
        standard scale from the manifest.  An int overrides every sheet with
        that denominator.

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
    failures: dict[str, str] = {}

    for sheet_id, mod_attr, stem, sheet_scale, part in _SHEET_MANIFEST:
        sc = sheet_scale if scale_denom is None else scale_denom
        out_path = out / f"{prefix}_{stem}.dxf"
        try:
            mod = importlib.import_module(f".{mod_attr}", package="bridgecad_draw")
            if part is not None:
                # Modules with a 'part' argument (e.g. sheet5_enlarged_details)
                p = mod.generate(project, out_path, part=part)
            else:
                p = mod.generate(project, out_path, scale_denom=sc)
            # EP-2026-12: convert hard-typed dim text to measured "<>" after generation
            _apply_native_dims(p, sc)
            results.append(p)
            logger.info(
                "Sheet %s (%s) → %s  (%d KB)", sheet_id, stem, p.name, p.stat().st_size // 1024
            )
        except Exception as exc:
            failures[sheet_id] = f"{type(exc).__name__}: {exc}"
            # Only the optional-dependency case is de-duplicated. A genuine
            # ImportError inside a sheet module stays a loud per-sheet warning.
            if isinstance(exc, ImportError) and "ezdxf" in str(exc):
                if _missing_dep_warned:
                    logger.debug("Sheet %s (%s) skipped: %s", sheet_id, stem, exc)
                else:
                    logger.warning("Sheet %s (%s) skipped: %s", sheet_id, stem, exc)
                    _missing_dep_warned = True
            else:
                logger.warning("Sheet %s (%s) failed: %s", sheet_id, stem, exc)

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
