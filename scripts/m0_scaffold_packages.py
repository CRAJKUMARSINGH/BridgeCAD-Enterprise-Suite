"""
Batch generator for M0 scaffold — creates the remaining 8 Python packages
(io, draw, plugins, bill, qa, export, ai, infra) each with:
  pyproject.toml, package __init__.py, placeholder submodules, tests/__init__.py
Run once from root with: python scripts/m0_scaffold_packages.py
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGES = ROOT / "packages"

# (package_name, human_description, dependencies_list, [submodule_files_or_tuples])
PACK = [
    ("bridgecad-io",
     "Excel / CSV / JSON ↔ BridgeProject serialization",
     ["pandas>=2.0.0", "openpyxl>=3.1.0", "pyyaml>=6.0",
      "bridgecad-core @ file://../bridgecad-core"],
     [
         "excel_template.py",
         "excel_reader.py",
         "excel_writer.py",
         "csv_adapter.py",
         "json_adapter.py",
     ]),
    ("bridgecad-draw",
     "2D/3D drawing package: 5 engines × 7 sheets",
     ["ezdxf>=1.4.0", "reportlab>=4.0.0", "cairosvg>=2.7.0",
      "matplotlib>=3.7.0", "pillow>=10.0.0",
      "bridgecad-core @ file://../bridgecad-core"],
     [
         ("engines", ["__init__.py", "dxf_engine.py", "svg_engine.py",
                      "pdf_engine.py", "png_engine.py", "three_engine.py"]),
         ("sheets",  ["__init__.py",
                      "sheet1_plan.py", "sheet2_long_section.py",
                      "sheet3_cross_section.py", "sheet4_foundation.py",
                      "sheet5_pier_abutment_details.py",
                      "sheet6_bearings_joints.py",
                      "sheet7_bill_of_quantities.py"]),
         "primitives.py",
         "titleblocks.py",
         "layers.py",
         "booklet.py",
     ]),
    ("bridgecad-plugins",
     "Plugin registry: 10 per-bridge-type plugins with installer",
     ["importlib-metadata>=7.0", "pluggy>=1.4.0",
      "bridgecad-core @ file://../bridgecad-core",
      "bridgecad-draw @ file://../bridgecad-draw"],
     [
         "registry.py",
         "runner.py",
         "installer.py",
         "manifest_schema.py",
         # 10 plugin dir stubs (each has manifest.json, draw_overrides.py, defaults.yaml)
         ("plugins", {
             "rcc_tbeam":     ["manifest.json", "draw_overrides.py", "defaults.yaml"],
             "psc_igirder":   ["manifest.json", "draw_overrides.py", "defaults.yaml"],
             "psc_boxgirder": ["manifest.json", "draw_overrides.py", "defaults.yaml"],
             "solid_slab":    ["manifest.json", "draw_overrides.py", "defaults.yaml"],
             "voided_slab":   ["manifest.json", "draw_overrides.py", "defaults.yaml"],
             "arch_bridge":   ["manifest.json", "draw_overrides.py", "defaults.yaml"],
             "steel_composite":["manifest.json", "draw_overrides.py", "defaults.yaml"],
             "box_culvert":   ["manifest.json", "draw_overrides.py", "defaults.yaml"],
             "pipe_culvert":  ["manifest.json", "draw_overrides.py", "defaults.yaml"],
             "cable_stayed":  ["manifest.json", "draw_overrides.py", "defaults.yaml"],
         }),
     ]),
    ("bridgecad-bill",
     "Statutory bill engine (MORTH rates, 4 formatters, statements)",
     ["openpyxl>=3.1.0", "reportlab>=4.0.0", "pandas>=2.0.0",
      "pyyaml>=6.0", "jinja2>=3.1.0",
      "bridgecad-core @ file://../bridgecad-core"],
     [
         "models.py",
         "rates_db.py",
         "processor.py",
         ("formatters", ["__init__.py", "excel_formatter.py",
                         "pdf_formatter.py", "html_formatter.py",
                         "csv_formatter.py"]),
         "statements.py",
     ]),
    ("bridgecad-qa",
     "QA compliance: 150 rules engine, 0-100 scoring, reports, recommendations",
     ["reportlab>=4.0.0", "jinja2>=3.1.0",
      "bridgecad-core @ file://../bridgecad-core"],
     [
         "rules_engine.py",
         "compliance.py",
         "reports.py",
         "recommendations.py",
     ]),
    ("bridgecad-export",
     "Unified export pipeline: orchestrator, ZIP bundler, PDF booklet, versioner",
     ["ezdxf>=1.4.0", "reportlab>=4.0.0", "cairosvg>=2.7.0",
      "bridgecad-core @ file://../bridgecad-core",
      "bridgecad-draw @ file://../bridgecad-draw",
      "bridgecad-bill @ file://../bridgecad-bill",
      "bridgecad-qa @ file://../bridgecad-qa"],
     [
         "orchestrator.py",
         "bundler.py",
         "booklet.py",
         "versioner.py",
     ]),
    ("bridgecad-ai",
     "ML/optimization layer: scipy optimizer, estimator, comparator, suggester",
     ["numpy>=1.26.0", "scipy>=1.12.0", "pandas>=2.0.0",
      "scikit-learn>=1.4.0", "matplotlib>=3.7.0",
      "bridgecad-core @ file://../bridgecad-core"],
     [
         "optimizer.py",
         "estimator.py",
         "comparator.py",
         "param_suggester.py",
     ]),
    ("bridgecad-infra",
     "Persistence / ops: DB, cache, queue, storage, logging, metrics, auth",
     ["sqlalchemy>=2.0.0", "alembic>=1.13.0", "redis>=5.0.0",
      "boto3>=1.34.0", "structlog>=24.0.0", "prometheus-client>=0.20.0",
      "arq>=0.26.0", "python-jose[cryptography]>=3.3.0", "passlib[bcrypt]>=1.7.0",
      "pydantic>=2.6.0", "pydantic-settings>=2.2.0", "pyyaml>=6.0",
      "bridgecad-core @ file://../bridgecad-core"],
     [
         "db.py",
         "repositories.py",
         "cache.py",
         "queue.py",
         "storage.py",
         "logging_setup.py",
         "metrics.py",
         "auth.py",
     ]),
]


PYPROJECT_TEMPLATE = '''[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{name}"
version = "0.1.0"
description = "BridgeCAD Enterprise — {desc}"
requires-python = ">=3.11"
dependencies = {deps}

[tool.setuptools]
packages = ["{import_name}"]

[tool.setuptools.package-dir]
"" = "."
'''

PACKAGE_INIT_TEMPLATE = '''"""
BridgeCAD Enterprise — {name} ({desc}).

M0 scaffold. Implementation scheduled per 01_ACTION_PLAN_M0_to_M10.md.
Submodules: {subs}
"""

__version__ = "0.1.0"
'''

PLACEHOLDER_MODULE_DOC = {
    # io
    "excel_template.py": "Generate 14-sheet Excel workbook (styled, validation, protected) — M2.",
    "excel_reader.py":   "Parse 14 sheets → BridgeProject Pydantic model — M2.",
    "excel_writer.py":   "BridgeProject → styled Excel workbook with locked calc cells — M2.",
    "csv_adapter.py":    "CSV ↔ BridgeProject adapter — M2.",
    "json_adapter.py":   "JSON ↔ BridgeProject adapter — M2.",
    # draw
    "primitives.py":     "Drawing primitives: lines, arcs, hatch, dimensions, text — M3.",
    "titleblocks.py":    "3 title-block styles: Standard / Compact / Detailed — M3.",
    "layers.py":         "IRC-compliant layer registry (colors, lineweights) — M3.",
    "booklet.py":        "7-sheet PDF booklet with cover + TOC — M3.",
    # draw.engines
    "dxf_engine.py":   "ezdxf R2010/R2018 output engine — M3.",
    "svg_engine.py":   "cairosvg web-preview engine — M3.",
    "pdf_engine.py":   "reportlab page composer engine — M3.",
    "png_engine.py":   "matplotlib raster engine — M3.",
    "three_engine.py": "three.js JSON 3D scene engine — M3.",
    # draw.sheets
    "sheet1_plan.py":              "Plan-view drawing module — M3.",
    "sheet2_long_section.py":      "Longitudinal section drawing module — M3.",
    "sheet3_cross_section.py":     "Cross-sections (kerbs, camber) drawing module — M3.",
    "sheet4_foundation.py":        "Pile/well/open foundation drawing module — M3.",
    "sheet5_pier_abutment_details.py": "Pier cap, shaft, abutment, return-wall details — M3.",
    "sheet6_bearings_joints.py":   "Bearing & expansion-joint schedule details — M3.",
    "sheet7_bill_of_quantities.py":"BoQ schedule drawing sheet — M3/M5.",
    # plugins
    "registry.py":       "Plugin discovery & registry (importlib entry-points + local dirs) — M4.",
    "runner.py":         "Per-project plugin runner: applies draw_overrides — M4.",
    "installer.py":      "Install/uninstall CLI for plugin zip / git URL / pypi — M4.",
    "manifest_schema.py":"JSON schema for plugin manifest.json — M4.",
    # bill
    "models.py":         "Bill domain: BillGroup, BillItem, Deviation, Statement — M5.",
    "rates_db.py":       "YAML-backed MORTH 5000+ item rate DB with State-PWD override chain — M5.",
    "processor.py":      "Apply tender premium, deviations, draft versioning → final bill — M5.",
    "statements.py":     "RA-bill / Running-account / Final-bill statement generators — M5.",
    "excel_formatter.py": "Excel-styled bill (exact column widths) — M5.",
    "pdf_formatter.py":   "A4 PDF bill with header, footer, table pagination — M5.",
    "html_formatter.py":  "Jinja2 professional HTML bill — M5.",
    "csv_formatter.py":   "CSV Master bill for ERP import — M5.",
    # qa
    "rules_engine.py":    "Runs 150 validation check functions, returns ValidationReport — M6.",
    "compliance.py":      "Weighted 0-100 IRC:05/IRC:21/IRC:SP:55 compliance score — M6.",
    "reports.py":         "PDF/HTML QA report generator with severity matrix — M6.",
    "recommendations.py": "Per-failure auto-fix recommendation engine — M6.",
    # export
    "orchestrator.py":    "Fan-out drawing + bill export job with status tracking — M6.",
    "bundler.py":         "ZIP bundle with manifest.json (DXF+PDF+XLSX+JSON) — M6.",
    "booklet.py":         "PDF booklet (alias of draw.booklet; here for completeness) — M6.",
    "versioner.py":       "Git-tag stamp in title-block + PDF metadata + manifest rev — M6.",
    # ai
    "optimizer.py":       "scipy SLSQP cost-minimization of span/depth/width — M8.",
    "estimator.py":       "Heuristic + regressor no-API cost/quantity predictor — M8.",
    "comparator.py":      "Side-by-side bridge delta % + radar chart (matplotlib) — M8.",
    "param_suggester.py": "Default values from 28 Scribd reference corpus — M8.",
    # infra
    "db.py":              "SQLAlchemy engine + session (SQLite dev / Postgres prod) — M8.",
    "repositories.py":    "ProjectRepo, BridgeRepo, HistoryRepo — M8.",
    "cache.py":           "Redis adapter + in-memory LRU fallback — M8.",
    "queue.py":           "arq async drawing/bill/export job runner — M8.",
    "storage.py":         "Local disk + S3 (boto3) dual adapter — M8.",
    "logging_setup.py":   "structlog + OTel structured logging bootstrap — M8.",
    "metrics.py":         "Prometheus counters + histograms for pipelines — M8.",
    "auth.py":            "JWT, API keys, optional OAuth2 Google auth — M8.",
}


def format_deps(deps: list[str]) -> str:
    lines = ['"%s"' % d for d in deps]
    return "[\n" + ",\n".join("  " + l for l in lines) + "\n]"


def mkdir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def write_if_missing(p: Path, content: str) -> None:
    if p.exists():
        return
    p.write_text(content, encoding="utf-8")


def build_package(pkg_name: str, desc: str, deps: list[str], structure: list) -> None:
    import_name = pkg_name.replace("-", "_")
    pkg_root = PACKAGES / pkg_name
    import_root = pkg_root / import_name
    tests_root = pkg_root / "tests"
    mkdir(import_root)
    mkdir(tests_root)

    write_if_missing(
        pkg_root / "pyproject.toml",
        PYPROJECT_TEMPLATE.format(
            name=pkg_name,
            desc=desc,
            deps=format_deps(deps),
            import_name=import_name,
        ),
    )

    # Flatten structure into (relative_path, submodule_name) pairs for listing
    sub_names: list[str] = []
    pending: list[tuple[str, object]] = [("", x) for x in structure]
    while pending:
        prefix, item = pending.pop()
        if isinstance(item, tuple) and len(item) == 2:
            subdir, contents = item
            new_prefix = f"{prefix}/{subdir}" if prefix else subdir
            sub_names.append(subdir + "/")
            if isinstance(contents, dict):
                for k, v in contents.items():
                    pending.append((f"{new_prefix}/{k}", v))
            else:
                for c in contents:
                    pending.append((new_prefix, c))
        else:
            fname = str(item)
            sub_names.append(fname)
            dir_path = import_root / prefix if prefix else import_root
            mkdir(dir_path)
            # Special: plugin dict leaves
            if prefix.startswith("plugins/") and fname == "manifest.json":
                write_if_missing(
                    dir_path / fname,
                    PLUGIN_MANIFEST.format(pkg=prefix.split("/")[-1]),
                )
            elif prefix.startswith("plugins/") and fname == "defaults.yaml":
                write_if_missing(dir_path / fname, "# Default parameters\nname: " + prefix.split("/")[-1] + "\n")
            elif prefix.startswith("plugins/") and fname == "draw_overrides.py":
                write_if_missing(
                    dir_path / fname,
                    f'\"\"\"Plugin drawing overrides: {prefix.split("/")[-1]}. M4 implementation.\"\"\"\n',
                )
            elif fname == "__init__.py":
                # Write package init
                subdir_name = dir_path.name
                write_if_missing(
                    dir_path / fname,
                    f'\"\"\"bridgecad.{import_name}.{subdir_name} — M0 scaffold.\"\"\"\n',
                )
            else:
                doc = PLACEHOLDER_MODULE_DOC.get(fname, f"{fname} — M1..M10 implementation.")
                write_if_missing(dir_path / fname, f'\"\"\"{doc}\"\"\"\n')

    # top-level __init__.py
    write_if_missing(
        import_root / "__init__.py",
        PACKAGE_INIT_TEMPLATE.format(
            name=pkg_name,
            desc=desc,
            subs=", ".join(sorted(set(sub_names))),
        ),
    )

    # tests/__init__.py
    write_if_missing(tests_root / "__init__.py", f'\"\"\"{pkg_name} tests — M0 scaffold.\"\"\"\n')


PLUGIN_MANIFEST = '''{{
  "name": "{pkg}",
  "version": "0.1.0",
  "description": "BridgeCAD plugin — {pkg}",
  "supported_bridge_types": [],
  "entry_overrides": {{
    "draw_plan": null,
    "draw_long_section": null
  }},
  "defaults_yaml": "defaults.yaml"
}}
'''


def main() -> None:
    for name, desc, deps, structure in PACK:
        build_package(name, desc, deps, structure)
        print(f"  ✔ {name}")
    print(f"\nAll {len(PACK)} packages scaffolded.")


if __name__ == "__main__":
    main()
