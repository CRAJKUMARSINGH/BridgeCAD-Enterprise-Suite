"""TEST RUN — generate every drawing this repo is capable of producing.

Runs all three drawing pipelines in the repository and files each case into a
dated, human-readable subfolder under the target directory (default
``TEST-28102026/``):

* ``fixtures/``            — the 28 real-world reference bridges from
  ``tests/e2e/fixtures`` rendered as the 8-sheet GAD package
  (``bridgecad_draw.booklet.generate_package``).
* ``design-families/``     — sweeps of the 5 coherent design families
  (RCC_TBEAM, PSC_IGIRDER, PSC_BOX_GIRDER, SOLID_SLAB, VOIDED_SLAB) with
  variable combinations chosen here (spans / width / skew / foundation …).
* ``legacy-gad/``          — the legacy ``bridge_gad`` GAD driver: single GAD
  drawing + phase-two 7-sheet package, DXF + PDF, one workbook each.

Every case folder contains ``input.json`` (the exact input that produced the
drawings) next to the rendered outputs. A top-level ``_manifest.json`` indexes
the whole run.

Usage:
    python scripts/generate_test_corpus.py
    python scripts/generate_test_corpus.py --only fixtures --limit 2
    python scripts/generate_test_corpus.py --out TEST-28102026 --seed 20261028
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import random
import sys
import traceback
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any, cast

# ── path bootstrap ─────────────────────────────────────────────────────────
_SUITE = Path(__file__).resolve().parents[1]
for _pkg in ["bridgecad-core", "bridgecad-io", "bridgecad-draw",
             "bridgecad-bill", "bridgecad-qa", "bridgecad-export"]:
    _p = _SUITE / "packages" / _pkg
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
_SRC = _SUITE / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

FIXTURES_DIR = _SUITE / "tests" / "e2e" / "fixtures"

# Variable-combination knobs used for the design-family sweep (our choice).
FAMILY_CASES_PER_FAMILY = 6
WIDTH_CYCLE = [7.5, 14.0, 7.5, 21.0, 14.0, 7.5]
SKEW_CYCLE = [0.0, 15.0, 30.0, 0.0, 45.0, 5.0]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise RuntimeError(f"Unable to load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_builder() -> Callable[[dict], Any]:
    mod = _load_module("_bridgecad_run_e2e", _SUITE / "tests" / "e2e" / "run_e2e.py")
    return cast("Callable[[dict], Any]", mod._build_from_fixture)


def _load_random_gen():
    return _load_module("_bridgecad_random", _SUITE / "scripts" / "generate_random_drawings.py")


def _rel(p: Path) -> str:
    try:
        return str(p.relative_to(_SUITE))
    except ValueError:
        return str(p)


# ---------------------------------------------------------------------------
# Suite engine — 8-sheet GAD package
# ---------------------------------------------------------------------------

def _render_suite_case(case_dir: Path, data: dict, prefix: str) -> dict:
    """Build a BridgeProject from *data* and render the 8-sheet DXF package."""
    from bridgecad_draw.booklet import generate_package

    build_from_fixture = _load_builder()
    project = build_from_fixture(data)
    sheets = generate_package(project, case_dir, prefix=prefix, scale_denom=100)
    total_kb = sum(s.stat().st_size for s in sheets) // 1024

    qa_score = None
    try:
        from bridgecad_core.validation import run_all
        qa_score = float(run_all(project).score)
    except Exception:
        pass

    (case_dir / "input.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    return {
        "sheets": len(sheets),
        "total_kb": total_kb,
        "qa_score": qa_score,
        "outputs": [s.name for s in sheets],
    }


def run_fixtures(out_root: Path, stamp: str, limit: int | None) -> list[dict]:
    fixture_files = sorted(FIXTURES_DIR.glob("*.json"))
    if limit:
        fixture_files = fixture_files[:limit]

    cases: list[dict] = []
    base_dir = out_root / "fixtures"
    print(f"\n[fixtures] {len(fixture_files)} reference bridges")
    for fp in fixture_files:
        entry: dict = {"engine": "suite", "group": "fixtures", "source": fp.name}
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
            fid = data.get("_meta", {}).get("fixture_id", fp.stem)
            case_dir = base_dir / f"{fid}__{stamp}"
            case_dir.mkdir(parents=True, exist_ok=True)
            res = _render_suite_case(case_dir, data, fid)
            entry.update({
                "id": fid,
                "dir": _rel(case_dir),
                "status": "OK" if res["sheets"] else "NO_SHEETS",
                **res,
            })
            print(f"  [{res['sheets']}/8] {fid}  ({res['total_kb']} KB)")
        except Exception as exc:
            entry.update({"status": "FAILED", "error": str(exc)})
            print(f"  [FAILED] {entry.get('source')}: {exc}")
            traceback.print_exc()
        cases.append(entry)
    return cases


def run_design_families(out_root: Path, stamp: str, seed: int) -> list[dict]:
    rg = _load_random_gen()
    families = rg.FAMILIES
    base_fixture = json.loads(rg.BASE_FIXTURE.read_text(encoding="utf-8"))

    cases: list[dict] = []
    base_dir = out_root / "design-families"
    print(f"\n[design-families] {len(families)} families × {FAMILY_CASES_PER_FAMILY} combinations")
    for fam in families:
        fam_slug = fam["slug"]
        # Pin the family so the shared randomiser draws only within it.
        rg.FAMILIES = [fam]
        for i in range(FAMILY_CASES_PER_FAMILY):
            entry: dict = {"engine": "suite", "group": "design-families",
                           "family": fam["type"], "seed": seed + i}
            try:
                rng = random.Random(seed + i)
                data = rg.randomize(base_fixture, rng, i)
                # Apply our chosen variable combinations deterministically.
                gi = data["project"]["geometry_input"]
                gi["carriageway_width_m"] = WIDTH_CYCLE[i % len(WIDTH_CYCLE)]
                gi["skew_angle_deg"] = SKEW_CYCLE[i % len(SKEW_CYCLE)]
                gi["skew_direction"] = "NONE" if gi["skew_angle_deg"] == 0 else "LEFT"
                data["_meta"]["description"] += (
                    f" | sweep cw {gi['carriageway_width_m']:.1f}m, "
                    f"skew {gi['skew_angle_deg']:.0f}°"
                )
                case_id = f"{fam_slug}_{i:02d}"
                case_dir = base_dir / fam["type"] / f"{case_id}__{stamp}"
                case_dir.mkdir(parents=True, exist_ok=True)
                res = _render_suite_case(case_dir, data, case_id)
                entry.update({
                    "id": case_id,
                    "dir": _rel(case_dir),
                    "status": "OK" if res["sheets"] else "NO_SHEETS",
                    "carriageway_width_m": gi["carriageway_width_m"],
                    "skew_angle_deg": gi["skew_angle_deg"],
                    "span_count": int(data["project"]["geometry_input"]["span_count"]),
                    **res,
                })
                print(f"  [{res['sheets']}/8] {fam['type']:<16} {case_id}"
                      f"  cw={gi['carriageway_width_m']:.1f} skew={gi['skew_angle_deg']:.0f}")
            except Exception as exc:
                entry.update({"status": "FAILED", "error": str(exc)})
                print(f"  [FAILED] {fam['type']} #{i}: {exc}")
                traceback.print_exc()
            cases.append(entry)
    return cases


# ---------------------------------------------------------------------------
# Legacy bridge_gad engine — single GAD + phase-two 7-sheet package
# ---------------------------------------------------------------------------

def run_legacy_gad(out_root: Path, stamp: str) -> list[dict]:
    from bridge_gad.bridge_canvas_features import BRIDGE_TEMPLATES
    from bridge_gad.generate_all_drawings import generate_all_drawings

    cases: list[dict] = []
    base_dir = out_root / "legacy-gad"
    print(f"\n[legacy-gad] {len(BRIDGE_TEMPLATES)} templates (single GAD + 7-sheet)")
    for key, tpl in BRIDGE_TEMPLATES.items():
        entry: dict = {"engine": "legacy-bridge_gad", "group": "legacy-gad", "template": key}
        try:
            case_dir = base_dir / f"{key}__{stamp}"
            case_dir.mkdir(parents=True, exist_ok=True)
            (case_dir / "input.json").write_text(
                json.dumps({"template": key, "name": tpl.get("name"),
                            "parameters": tpl.get("parameters")}, indent=2),
                encoding="utf-8")
            res = generate_all_drawings(case_dir, templates=[(key, tpl)],
                                        progress_log=False)
            stats = res["stats"]
            n_files = sum(1 for _ in case_dir.rglob("*") if _.is_file())
            entry.update({
                "id": key,
                "dir": _rel(case_dir),
                "status": "OK",
                "dxf_count": stats["single_gad_dxfs"] + stats["phase_two_sheet_dxfs"],
                "pdf_count": stats["single_pdfs"] + stats["pkg_pdfs"]
                             + stats["per_template_booklets"],
                "files": n_files,
                "master_pdf": _rel(res["master_pdf"]),
            })
            print(f"  [OK] {key:<20} dxf={entry['dxf_count']} pdf={entry['pdf_count']} "
                  f"files={n_files}")
        except Exception as exc:
            entry.update({"status": "FAILED", "error": str(exc)})
            print(f"  [FAILED] {key}: {exc}")
            traceback.print_exc()
        cases.append(entry)
    return cases


# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Generate the full BridgeCAD drawing corpus.")
    ap.add_argument("--out", type=Path, default=_SUITE / "TEST-28102026",
                    help="root output directory (default TEST-28102026)")
    ap.add_argument("--only", choices=["fixtures", "families", "legacy"], default=None,
                    help="run only one pipeline")
    ap.add_argument("--limit", type=int, default=None, help="limit fixtures (smoke test)")
    ap.add_argument("--seed", type=int, default=20261028, help="seed for design-family sweep")
    args = ap.parse_args()

    out_root = Path(args.out)
    if not out_root.is_absolute():
        out_root = (_SUITE / out_root).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    print("=" * 72)
    print("  BRIDGECAD FULL DRAWING CORPUS — TEST RUN")
    print("=" * 72)
    print(f"  Output root : {out_root}")
    print(f"  Run stamp   : {stamp}")

    all_cases: list[dict] = []
    if args.only in (None, "fixtures"):
        all_cases += run_fixtures(out_root, stamp, args.limit)
    if args.only in (None, "families"):
        all_cases += run_design_families(out_root, stamp, args.seed)
    if args.only in (None, "legacy"):
        all_cases += run_legacy_gad(out_root, stamp)

    ok = sum(1 for c in all_cases if c.get("status") == "OK")
    manifest = {
        "generated_at": datetime.now().isoformat(),
        "run_stamp": stamp,
        "out_root": _rel(out_root),
        "seed": args.seed,
        "totals": {"cases": len(all_cases), "ok": ok, "failed": len(all_cases) - ok},
        "cases": all_cases,
    }
    (out_root / "_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print("\n" + "=" * 72)
    print(f"  Cases : {len(all_cases)}   OK : {ok}   FAILED : {len(all_cases) - ok}")
    print(f"  Manifest : {out_root / '_manifest.json'}")
    print(f"  VERDICT  : {'*** OK ***' if ok == len(all_cases) else 'PARTIAL'}")
    print("=" * 72)
    return 0 if ok == len(all_cases) else 1


if __name__ == "__main__":
    sys.exit(main())
