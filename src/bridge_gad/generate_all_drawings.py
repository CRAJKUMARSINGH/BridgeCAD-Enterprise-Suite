"""TEST RUN DEVELOP DRAWINGS — generate every drawing, in all forms, for
all registered ``BRIDGE_TEMPLATES`` plus any number of additional templates.

Entry points (1 → N drawings supported):

* ``generate_all_drawings(out_dir, templates=None)``  — directory tree of
  DXF + PDF + master multi-page PDF + mega ZIP + CSV manifest.
* ``generate_n_drawings(out_dir, n=10)`` — if you want N randomised
  variants beyond the 5 templates (for "1 to infinity" workloads).
* CLI: ``python -m bridge_gad.generate_all_drawings <out_dir> [--n 10]``
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import logging
import random
import sys
import zipfile
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

logger = logging.getLogger("generate_all_drawings")

from .bridge_canvas_features import (
    BRIDGE_TEMPLATES,
    make_template_excel,
    validate_bridge_parameters,
)
from .bridge_generator import BridgeGADGenerator
from .dxf_to_pdf import (
    LAYOUT_PRESETS,
    RenderOptions,
    bundle_drawings_to_pdf,
    convert_dxf_to_pdf,
    convert_directory_to_pdfs,
)
from .multi_sheet_generator import DetailedSheetGenerator
from .standards import (
    DEFAULT_METADATA,
    get_owner_profile,
    merge_with_metadata,
)


def _ensure_tree(out: Path) -> Dict[str, Path]:
    dirs = {
        "root": out,
        "dxfs": out / "DXF",
        "dxfs_single": out / "DXF" / "01_gad_single",
        "dxfs_pkg": out / "DXF" / "02_phase_two_7sheet",
        "pdfs": out / "PDF",
        "pdfs_single": out / "PDF" / "01_gad_single",
        "pdfs_pkg": out / "PDF" / "02_phase_two_7sheet",
        "pdfs_booklets": out / "PDF" / "03_booklets",
        "workbooks": out / "Workbooks",
        "manifests": out / "Manifests",
        "zips": out / "ZIP_Bundles",
    }
    for p in dirs.values():
        p.mkdir(parents=True, exist_ok=True)
    return dirs


def _params_for_variant(template_key: str, variant: int, seed: Optional[int] = None) -> Dict[str, Any]:
    """Build N parameter variants from a base template — small, valid jitter.

    Used by ``generate_n_drawings`` for "1 to infinity" runs.
    """
    rng = random.Random((seed or 0) + variant)
    base = dict(BRIDGE_TEMPLATES[template_key]["parameters"])

    def jitter(key: str, low: float, high: float, step: float = 0.1) -> None:
        cur = float(base.get(key, 0.0))
        j = rng.choice([-step, 0.0, step])
        base[key] = round(max(low, min(high, cur + j)), 3)

    jitter("SPAN1", 10.0, 40.0, 0.5)
    jitter("SLBTHE", 0.5, 1.5, 0.05)
    jitter("PIERTW", 1.0, 2.5, 0.05)
    jitter("SKEW", 0.0, 30.0, 1.0)
    jitter("FOOTPATHW", 1.5, 3.0, 0.1)
    jitter("MEDIANW", 0.0, 3.0, 0.1)
    base["DRAWING_NO"] = f"{base.get('DRAWING_NO', 'GAD-001')}-V{variant:03d}"
    base["REVISION"] = f"V{variant:02d}"
    return base


def generate_all_drawings(
    out_dir: Path,
    templates: Optional[Sequence[Tuple[str, Dict[str, Any]]]] = None,
    *,
    pdf_layout: str = "A4_landscape",
    master_pdf_name: str = "ALL_DRAWINGS_COMPLETE.pdf",
    mega_zip_name: str = "COMPLETE_DRAWINGS_BUNDLE.zip",
    progress_log: bool = True,
) -> Dict[str, Any]:
    """DEVELOP ALL DRAWINGS (DXF + PDF + Booklets + Master PDF + ZIP).

    For every template in ``templates`` (default: all 5 BRIDGE_TEMPLATES):
      - Build 1x single-GAD DXF + 1x PDF (8 total → booklet)
      - Build 7x phase-two package DXFs + 7x PDFs (booklet per template)
    Cross-cut deliverables:
      - ``ALL_DRAWINGS_COMPLETE.pdf`` — one  multi-page booklet of every sheet
      - ``COMPLETE_DRAWINGS_BUNDLE.zip`` — every DXF, PDF, workbook, manifest
      - ``manifest.csv`` — every file produced with checksum/size/template/sheet
      - ``run_summary.json`` — overall stats
    """
    out_dir = Path(out_dir).resolve()
    tree = _ensure_tree(out_dir)
    if progress_log:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

    if templates is None:
        templates = list(BRIDGE_TEMPLATES.items())

    opts = RenderOptions(layout=pdf_layout)
    gen = BridgeGADGenerator()
    dsg = DetailedSheetGenerator()

    manifest_rows: List[Dict[str, Any]] = []
    # List of (dxf_path, title_for_master_pdf) in global sort order
    all_sheets_global: List[Tuple[Path, str]] = []
    run_stats = {
        "templates_total": len(templates),
        "single_gad_dxfs": 0,
        "phase_two_sheet_dxfs": 0,
        "single_pdfs": 0,
        "pkg_pdfs": 0,
        "per_template_booklets": 0,
        "total_files": 0,
        "validation_scores": {},
    }

    try:
        import pandas as pd
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("pandas required for workbook generation") from exc

    def record(rel: Path, kind: str, template: str, sheet: str = "-") -> None:
        path = tree["root"] / rel
        size = path.stat().st_size if path.exists() else 0
        manifest_rows.append({
            "template": template,
            "sheet": sheet,
            "kind": kind,
            "relative_path": rel.as_posix(),
            "bytes": size,
        })
        run_stats["total_files"] += 1

    for tpl_idx, (tpl_key, tpl) in enumerate(templates, start=1):
        tpl_name = tpl.get("name") or tpl_key
        params = dict(tpl.get("parameters") or tpl)
        enriched = merge_with_metadata(params)

        v = validate_bridge_parameters(enriched)
        run_stats["validation_scores"][tpl_key] = v["score"]

        # 1) Write parameter workbook for the template
        wb_bytes = make_template_excel(enriched)
        wb_path = tree["workbooks"] / f"{tpl_idx:02d}_{tpl_key}_parameters.xlsx"
        wb_path.write_bytes(wb_bytes)
        record(wb_path.relative_to(tree["root"]), "xlsx", tpl_key, "Parameters")

        # 2) Excel input required for single GAD generation
        rows = [[vv, kk, kk] for kk, vv in enriched.items()]
        df = pd.DataFrame(rows, columns=["Value", "Variable", "Description"])
        excel_in = tree["workbooks"] / f"{tpl_idx:02d}_{tpl_key}_input.xlsx"
        df.to_excel(excel_in, index=False, header=False)
        record(excel_in.relative_to(tree["root"]), "xlsx", tpl_key, "Input")

        # 3) Single GAD DXF + PDF
        single_dxf = tree["dxfs_single"] / f"{tpl_idx:02d}_{tpl_key}_GAD.dxf"
        ok1 = bool(gen.generate_complete_drawing(excel_in, single_dxf))
        if ok1 and single_dxf.exists():
            run_stats["single_gad_dxfs"] += 1
            rel = single_dxf.relative_to(tree["root"])
            record(rel, "dxf", tpl_key, "GAD-single")
            single_pdf = tree["pdfs_single"] / (single_dxf.stem + ".pdf")
            convert_dxf_to_pdf(
                single_dxf, single_pdf, opts=opts,
                page_title=f"{tpl_name} — GAD Plan + Elevation"
            )
            record(single_pdf.relative_to(tree["root"]), "pdf", tpl_key, "GAD-single")
            run_stats["single_pdfs"] += 1
            all_sheets_global.append((single_dxf, f"{tpl_name} — GAD Plan+Elevation"))

        # 4) Phase 2 7-sheet package DXF + per-sheet PDF + booklet PDF
        pkg_base = tree["dxfs_pkg"] / f"{tpl_idx:02d}_{tpl_key}_Sheet.dxf"
        ok2 = bool(dsg.generate_phase_two_package(enriched, pkg_base))
        # The generator names each sheet {stem}Sheet1..Sheet7; glob on that.
        produced = sorted(pkg_base.parent.glob(
            f"{pkg_base.stem.replace('Sheet', '')}Sheet*.dxf"
        ))
        per_tpl_sheets: List[Path] = []
        for dxf in produced:
            run_stats["phase_two_sheet_dxfs"] += 1
            rel = dxf.relative_to(tree["root"])
            sheet_tag = dxf.stem.split("Sheet")[-1]
            record(rel, "dxf", tpl_key, f"P2-Sheet{sheet_tag}")
            pdf_out = tree["pdfs_pkg"] / (dxf.stem + ".pdf")
            convert_dxf_to_pdf(
                dxf, pdf_out, opts=opts,
                page_title=f"{tpl_name} — Sheet {sheet_tag}"
            )
            record(pdf_out.relative_to(tree["root"]), "pdf", tpl_key,
                   f"P2-Sheet{sheet_tag}")
            run_stats["pkg_pdfs"] += 1
            per_tpl_sheets.append(dxf)
            all_sheets_global.append((dxf, f"{tpl_name} — Sheet {sheet_tag}"))

        if per_tpl_sheets:
            if single_dxf.exists():
                ordered = [single_dxf] + per_tpl_sheets
                titles = [f"{tpl_name} — GAD Plan+Elevation"] + [
                    f"{tpl_name} — Sheet {p.stem.split('Sheet')[-1]}"
                    for p in per_tpl_sheets
                ]
            else:
                ordered = per_tpl_sheets
                titles = [
                    f"{tpl_name} — Sheet {p.stem.split('Sheet')[-1]}"
                    for p in per_tpl_sheets
                ]
            book_path = tree["pdfs_booklets"] / (
                f"{tpl_idx:02d}_{tpl_key}_complete_drawings.pdf"
            )
            profile = get_owner_profile(enriched.get("OWNER_PROFILE"))
            bundle_drawings_to_pdf(
                ordered, book_path, opts=opts, page_titles=titles,
                cover_page_title=(
                    f"{tpl_name} — Complete Drawings — {profile.owner}"
                    f" — {len(ordered)} sheet(s)"
                ),
            )
            record(book_path.relative_to(tree["root"]), "pdf-booklet", tpl_key,
                   "Booklet")
            run_stats["per_template_booklets"] += 1

    # 5) Master multi-page PDF — 1 → every drawing
    master_pdf_path = tree["pdfs_booklets"] / master_pdf_name
    if all_sheets_global:
        master_ordered = [p for p, _ in all_sheets_global]
        master_titles = [t for _, t in all_sheets_global]
        bundle_drawings_to_pdf(
            master_ordered, master_pdf_path, opts=opts,
            page_titles=master_titles,
            cover_page_title=(
                f"MASTER — All Drawings — {len(master_ordered)} sheet(s)"
            ),
        )
        record(master_pdf_path.relative_to(tree["root"]), "pdf-master",
               "ALL", "Master-Booklet")

    # 6) Manifest CSV + run_summary JSON
    manifest_csv = tree["manifests"] / "manifest.csv"
    with manifest_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["template", "sheet", "kind", "relative_path", "bytes"],
        )
        writer.writeheader()
        writer.writerows(manifest_rows)
    run_stats["total_files"] += 1
    manifest_rows_meta = {
        "manifest.csv": manifest_csv.stat().st_size,
    }

    summary = dict(run_stats)
    summary["pdf_layout"] = pdf_layout
    summary["pdf_layout_presets_available"] = sorted(LAYOUT_PRESETS.keys())
    summary["templates"] = [k for k, _ in templates]
    summary["master_pdf"] = master_pdf_path.relative_to(tree["root"]).as_posix()
    summary["files"] = manifest_rows
    summary_path = tree["manifests"] / "run_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    run_stats["total_files"] += 1

    # 7) Mega ZIP — absolute tree bundle
    mega_zip = tree["zips"] / mega_zip_name
    with zipfile.ZipFile(mega_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for sub in ("DXF", "PDF", "Workbooks", "Manifests"):
            for f in (tree["root"] / sub).rglob("*"):
                if f.is_file():
                    zf.write(f, f.relative_to(tree["root"]).as_posix())
        # add the master booklet directly under /
        if master_pdf_path.exists():
            zf.write(master_pdf_path, master_pdf_path.name)
    run_stats["total_files"] += 1

    summary["mega_zip"] = mega_zip.relative_to(tree["root"]).as_posix()
    summary["mega_zip_bytes"] = mega_zip.stat().st_size
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    if progress_log:
        logger.info("%d templates processed", len(templates))
        logger.info("  single GAD DXF = %d", run_stats["single_gad_dxfs"])
        logger.info("  phase-two sheet DXF = %d", run_stats["phase_two_sheet_dxfs"])
        logger.info("  per-template booklets = %d", run_stats["per_template_booklets"])
        logger.info("  MASTER PDF = %s", master_pdf_path)
        logger.info("  MEGA ZIP = %s (%.1f MB)", mega_zip, mega_zip.stat().st_size / 1e6)

    return {
        "out_dir": tree["root"],
        "master_pdf": master_pdf_path,
        "mega_zip": mega_zip,
        "manifest_csv": manifest_csv,
        "run_summary_json": summary_path,
        "stats": run_stats,
    }


def generate_n_drawings(
    out_dir: Path,
    n: int = 10,
    *,
    base_template: str = "continuous_3x12m",
    pdf_layout: str = "A4_landscape",
    seed: int = 7,
    progress_log: bool = True,
) -> Dict[str, Any]:
    """Build a parameterised set of N drawings (supports "1 → infinity" runs).

    Parameters
    ----------
    n:
        Number of drawings variants to produce.
    base_template:
        Key in ``BRIDGE_TEMPLATES`` used as the base for jitter.
    """
    if base_template not in BRIDGE_TEMPLATES:
        raise KeyError(f"Unknown base_template {base_template!r}")

    variant_list: List[Tuple[str, Dict[str, Any]]] = []
    for i in range(1, n + 1):
        vkey = f"{base_template}_var{i:03d}"
        variant_list.append((vkey, {
            "name": f"{BRIDGE_TEMPLATES[base_template].get('name')} — Variant {i:03d}",
            "parameters": _params_for_variant(base_template, i, seed=seed),
        }))
    return generate_all_drawings(
        out_dir, templates=variant_list, pdf_layout=pdf_layout,
        master_pdf_name=f"N{n}_DRAWINGS_MASTER.pdf",
        mega_zip_name=f"N{n}_DRAWINGS_BUNDLE.zip",
        progress_log=progress_log,
    )


def _cli(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bridge_gad.generate_all_drawings",
        description="DEVELOP ALL DRAWINGS — DXF + PDF (1 → N, booklets + ZIP)",
    )
    parser.add_argument(
        "out_dir", type=Path,
        help="Directory where the full output tree is written.",
    )
    parser.add_argument(
        "--n", type=int, default=0,
        help="If > 0, run generate_n_drawings (parameterised N variants) instead of all templates.",
    )
    parser.add_argument(
        "--base-template", type=str, default="continuous_3x12m",
        help="Base BRIDGE_TEMPLATES key used for --n variants.",
    )
    parser.add_argument(
        "--pdf-layout", type=str, default="A4_landscape",
        choices=sorted(LAYOUT_PRESETS.keys()),
        help="PDF page layout preset.",
    )
    parser.add_argument(
        "--seed", type=int, default=7,
        help="Random seed for --n variant jitter.",
    )
    args = parser.parse_args(argv)

    if args.n > 0:
        res = generate_n_drawings(
            args.out_dir, n=args.n,
            base_template=args.base_template,
            pdf_layout=args.pdf_layout, seed=args.seed,
        )
    else:
        res = generate_all_drawings(
            args.out_dir, pdf_layout=args.pdf_layout,
        )
    print(json.dumps({
        k: str(v) if isinstance(v, Path) else v
        for k, v in res.items() if k != "stats"
    }, indent=2))
    print(json.dumps(res["stats"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
