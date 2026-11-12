"""bridgecad_draw.asset_pack — build every drawing defined by the asset PDFs.

WHY THIS EXISTS
    ``sample-gad-drawings/`` ships two plotted GAD PDFs and no DXF.  Anyone
    wanting to *edit* those drawings (re-issue at a new chainage, change the
    span, add a pier) had to trace them by hand.  This module reproduces each
    view as editable modelspace geometry, one sheet per source page:

        sheet 1  PMGSY 7x9.0 m  — L-section elevation + plan + schedule
        sheet 2  PMGSY 7x9.0 m  — deck section A-A, soil profile, abutment /
                                  return wall / toe wall sections, notes
        sheet 3  PMGSY 7x9.0 m  — pier elevation, plan, section, retaining wall
        sheet 4  1x6.0 m        — elevation, half plan, level table, boreholes,
                                  index plan, notes

    Page 2 and page 3 of the PMGSY PDF carry the same title-block drawing
    number (02) because the source plots the same sheet file twice with
    different viewports; they are two sheets here because they are two
    different charters of content.

USAGE
    from bridgecad_draw.asset_pack import build_asset_pack
    build_asset_pack("out/")                       # all four sheets
    build_asset_pack("out/", sets=["pmgsy_slab"])  # one set only

    CLI:  python -m bridgecad_draw.asset_pack out/
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Iterable, Sequence

logger = logging.getLogger(__name__)


class AssetPackError(RuntimeError):
    """One or more asset sheets failed. A partial pack is never returned."""

    def __init__(self, failures: dict[str, str]) -> None:
        self.failures = dict(failures)
        detail = "; ".join(f"{k}: {v}" for k, v in failures.items())
        super().__init__(f"{len(failures)} asset sheet(s) failed \u2014 {detail}")


#: (sheet id, module, filename stem, spec key)
_MANIFEST: list[tuple[str, str, str, str]] = [
    ("1", "asset_sheet1_lsection", "Asset_S1_LSection_Plan", "pmgsy_slab"),
    ("2", "asset_sheet2_deck_abutment", "Asset_S2_DeckSection_Substructure", "pmgsy_slab"),
    ("3", "asset_sheet3_pier", "Asset_S3_Pier_RetainingWall", "pmgsy_slab"),
    ("4", "asset_sheet4_single_span", "Asset_S4_SingleSpan_6m", "amarwada_single"),
]

#: Human labels used by the coverage report / tests.
COVERAGE: dict[str, tuple[str, str]] = {
    "Asset_S1_LSection_Plan": ("PMGSY p1", "L-SECTIONAL ELEVATION, PLAN VIEW, SCHEDULE"),
    "Asset_S2_DeckSection_Substructure": (
        "PMGSY p2",
        "SECTION A-A, SOIL PROFILE, PCC ABUTMENT, RETURN WALL, TOE WALL, GENERAL NOTES",
    ),
    "Asset_S3_Pier_RetainingWall": (
        "PMGSY p3",
        "PIER ELEVATION, PIER PLAN, PCC PIER SECTION, RETAINING WALL SECTION",
    ),
    "Asset_S4_SingleSpan_6m": (
        "Amarwada p1",
        "LONGITUDINAL ELEVATION, LEVELS, BORE HOLE RESULTS, HALF PLAN, INDEX PLAN, NOTES",
    ),
}


def build_asset_pack(
    output_dir: str | Path,
    sets: Sequence[str] | None = None,
    prefix: str = "ASSET",
) -> list[Path]:
    """Generate every asset sheet into *output_dir* and return the DXF paths.

    Parameters
    ----------
    output_dir : str | Path
        Destination directory (created if missing).
    sets : sequence of str, optional
        Restrict to ``"pmgsy_slab"`` and/or ``"amarwada_single"``. ``None``
        builds both.
    prefix : str
        Filename prefix.

    Raises
    ------
    AssetPackError
        If any sheet fails; the successful paths are attached as
        ``.results`` so a caller can still inspect what was produced.
    """
    import importlib

    from .asset_specs import SPECS

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    wanted = {s.lower() for s in sets} if sets else set(SPECS)
    results: list[Path] = []
    failures: dict[str, str] = {}

    for sheet_id, mod_name, stem, spec_key in _MANIFEST:
        if spec_key not in wanted:
            continue
        path = out / f"{prefix}_{stem}.dxf"
        try:
            mod = importlib.import_module(f".{mod_name}", package="bridgecad_draw")
            p = mod.generate(SPECS[spec_key], path)
            results.append(p)
            logger.info("Asset sheet %s \u2192 %s (%d KB)", sheet_id, p.name,
                        p.stat().st_size // 1024)
        except Exception as exc:  # noqa: BLE001 - surfaced, never swallowed
            failures[sheet_id] = f"{type(exc).__name__}: {exc}"
            logger.warning("Asset sheet %s (%s) failed: %s", sheet_id, stem, exc)

    if failures:
        err = AssetPackError(failures)
        err.results = results  # type: ignore[attr-defined]
        raise err
    return results


def coverage_report(paths: Iterable[Path] | None = None) -> str:
    """Plain-text coverage table: which source view each sheet reproduces."""
    lines = ["ASSET PACK COVERAGE", "-" * 96]
    for _, _, stem, _ in _MANIFEST:
        src, views = COVERAGE.get(stem, ("?", "?"))
        lines.append(f"{stem:<38} {src:<14} {views}")
    if paths:
        lines.append("-" * 96)
        for p in paths:
            lines.append(f"  \u2713 {Path(p).name}  ({Path(p).stat().st_size // 1024} KB)")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    out = args[0] if args else "asset_pack_out"
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        paths = build_asset_pack(out)
    except AssetPackError as exc:
        print(exc)
        return 1
    print(coverage_report(paths))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())


__all__ = ["COVERAGE", "AssetPackError", "build_asset_pack", "coverage_report", "main"]
