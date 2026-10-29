"""
Random GAD drawing generator for BridgeCAD app testing.

Generates N randomized-but-coherent BridgeProject fixtures, renders the 8-sheet
DXF package for each via ``bridgecad_draw.booklet.generate_package`` and writes
a machine-readable ``manifest.json`` summarising the run.

Each case lands in its own folder under the output directory:

    tests/e2e/random_drawings/
        manifest.json
        rand_000_psc_igirder_3x30m/
            rand_000_psc_igirder_3x30m_Sheet1_Plan.dxf
            ...
            fixture.json              <- the exact input that produced them

Usage:
    python scripts/generate_random_drawings.py --count 10
    python scripts/generate_random_drawings.py --count 25 --seed 42
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import random
import shutil
import sys
import traceback
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

# ── package path bootstrap (mirrors tests/e2e/run_e2e.py) ──────────────────
_SUITE = Path(__file__).resolve().parents[1]
for _pkg in ["bridgecad-core", "bridgecad-io", "bridgecad-draw",
             "bridgecad-bill", "bridgecad-qa", "bridgecad-export"]:
    _p = _SUITE / "packages" / _pkg
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

FIXTURES_DIR = _SUITE / "tests" / "e2e" / "fixtures"
DEFAULT_OUT = _SUITE / "tests" / "e2e" / "random_drawings"
BASE_FIXTURE = FIXTURES_DIR / "simple_12m.json"


def _rel(p: Path) -> str:
    """Path relative to the suite root when possible, else absolute."""
    try:
        return str(p.relative_to(_SUITE))
    except ValueError:
        return str(p)


def _load_builder() -> Callable[[dict], Any]:
    """Import ``_build_from_fixture`` from run_e2e.py without running its main."""
    spec = importlib.util.spec_from_file_location(
        "_bridgecad_run_e2e", _SUITE / "tests" / "e2e" / "run_e2e.py"
    )
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise RuntimeError("Unable to load tests/e2e/run_e2e.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return cast("Callable[[dict], Any]", mod._build_from_fixture)


# ---------------------------------------------------------------------------
# Coherent design families — every family is known to render all 8 sheets.
# ---------------------------------------------------------------------------
FAMILIES: list[dict] = [
    {
        "type": "RCC_TBEAM",
        "slug": "rcc_tbeam",
        "category": "MINOR_BRIDGE",
        "design_code": "IRC_21_2000",
        "span_range": (1, 3),
        "span_pool": [8.0, 10.0, 12.0, 15.0, 18.0, 20.0],
        "girder_type": "T_BEAM_RCC",
        "girder_spacing": 2.0,
        "deck_grades": ["M30", "M35", "M40"],
        "depth_range": (750, 1500),
    },
    {
        "type": "PSC_IGIRDER",
        "slug": "psc_igirder",
        "category": "MAJOR_BRIDGE",
        "design_code": "IRC_112_2020",
        "span_range": (2, 6),
        "span_pool": [20.0, 25.0, 30.0, 35.0, 40.0],
        "girder_type": "I_GIRDER_PSC",
        "girder_spacing": 2.5,
        "deck_grades": ["M45", "M50", "M55"],
        "depth_range": (1500, 2600),
    },
    {
        "type": "PSC_BOX_GIRDER",
        "slug": "psc_box_girder",
        "category": "MAJOR_BRIDGE",
        "design_code": "IRC_112_2020",
        "span_range": (1, 4),
        "span_pool": [25.0, 30.0, 35.0, 40.0, 45.0],
        "girder_type": "BOX_PSC_SINGLE_CELL",
        "girder_spacing": 0.0,
        "deck_grades": ["M45", "M50", "M55", "M60"],
        "depth_range": (1800, 3200),
    },
    {
        "type": "SOLID_SLAB",
        "slug": "solid_slab",
        "category": "MINOR_BRIDGE",
        "design_code": "IRC_21_2000",
        "span_range": (1, 2),
        "span_pool": [6.0, 8.0, 10.0, 12.0],
        "girder_type": None,
        "girder_spacing": 0.0,
        "deck_grades": ["M25", "M30", "M35"],
        "depth_range": (350, 700),
    },
    {
        "type": "VOIDED_SLAB",
        "slug": "voided_slab",
        "category": "MINOR_BRIDGE",
        "design_code": "IRC_21_2000",
        "span_range": (1, 3),
        "span_pool": [8.0, 10.0, 12.0, 15.0],
        "girder_type": None,
        "girder_spacing": 0.0,
        "deck_grades": ["M30", "M35", "M40"],
        "depth_range": (500, 900),
    },
]

# (carriageway_config name, carriageway width in metres)
CARRIAGEWAY_OPTIONS = [
    ("TWO_LANE_7M5_CLASS_A", 7.5),
    ("LANE_2", 7.5),
    ("LANE_4", 14.0),
    ("FOUR_LANE_14M_CLASS_A", 14.0),
    ("LANE_6", 21.0),
]

LOADING_CLASSES = ["CLASS_A", "CLASS_A", "CLASS_70R", "CLASS_AA"]
SEISMIC_ZONES = ["ZONE_II", "ZONE_III", "ZONE_IV", "ZONE_V"]
WIND_ZONES = ["VB_33_ms_ZONE_1", "VB_39_ms_ZONE_2", "VB_44_ms_ZONE_3",
              "VB_47_ms_ZONE_4", "VB_50_ms_ZONE_5"]
STATES = ["MH", "GJ", "RJ", "MP", "UP", "KA", "TN", "KL", "WB", "OR", "BR", "HR"]
PIER_TYPES = ["WALL", "HAMMERHEAD", "ROUND", "SQUARE", "RECTANGULAR",
              "MULTI_COLUMN_2", "MULTI_COLUMN_3"]
ABUTMENT_TYPES = ["CANTILEVER", "GRAVITY", "STUB", "SEMI_GRAVITY", "SPILL_THROUGH"]
WING_WALLS = ["SPLAYED_45_DEG", "SPLAYED_30_DEG", "PARALLEL_TO_CARRIAGEWAY",
              "PERPENDICULAR_TO_CARRIAGEWAY"]


def _foundation(bs: dict, fd: dict, rng: random.Random) -> str:
    """Pick a foundation type and populate matching foundation_details fields."""
    ft = rng.choice(["PILE", "PILE", "OPEN", "WELL"])
    bs["foundation_type"] = ft
    fd["type"] = ft
    if ft == "PILE":
        dia = rng.choice([800, 1000, 1200, 1500])
        fd.update({
            "pile_type": "BORED_CAST_IN_SITU",
            "pile_shape": "CIRCULAR_ROUND",
            "pile_diameter_mm": dia,
            "pile_length_m": round(rng.uniform(10.0, 30.0), 1),
            "piles_per_pier": rng.choice([4, 6, 8]),
            "pile_group_config": rng.choice(["2x2 @2.0m c/c", "2x3 @2.5m c/c", "3x3 @2.5m c/c"]),
            "pile_spacing_m": rng.choice([2.0, 2.5]),
            "pile_cap_thickness_mm": rng.choice([1000, 1200, 1500]),
            "pile_cutoff_level_m": round(rng.uniform(108.0, 112.0), 2),
            "under_ream_count": 0,
            "factor_of_safety_on_bearing": 3.0,
            "bearing_capacity_kpa": rng.choice([250.0, 350.0, 450.0]),
        })
    elif ft == "OPEN":
        fd.update({
            "pile_type": None, "pile_shape": None, "pile_diameter_mm": None,
            "pile_length_m": None, "piles_per_pier": None,
            "pile_group_config": None, "pile_spacing_m": None,
            "pile_cap_thickness_mm": None, "pile_cutoff_level_m": None,
            "under_ream_count": 0,
            "factor_of_safety_on_bearing": 3.0,
            "bearing_capacity_kpa": rng.choice([180.0, 220.0, 280.0]),
        })
    else:  # WELL
        fd.update({
            "pile_type": None, "pile_shape": None, "pile_diameter_mm": None,
            "pile_length_m": None, "piles_per_pier": None,
            "pile_group_config": None, "pile_spacing_m": None,
            "pile_cap_thickness_mm": None, "pile_cutoff_level_m": None,
            "under_ream_count": 0,
            "factor_of_safety_on_bearing": 2.5,
            "bearing_capacity_kpa": rng.choice([400.0, 500.0, 600.0]),
        })
    return ft


def randomize(base: dict, rng: random.Random, index: int) -> dict:
    """Return a deep-copied base fixture mutated into a random valid variant."""
    d = copy.deepcopy(base)
    p = d["project"]
    pm, bs, gi = p["project_master"], p["bridge_selection"], p["geometry_input"]
    ss, sub, fd = p["superstructure"], p["substructure"], p["foundation_details"]
    hd, mt = p["hydraulic_data"], p["materials"]
    bj, dc, ca = p["bearings_joints"], p["drawing_control"], p["calculations"]

    fam = rng.choice(FAMILIES)
    n_spans = rng.randint(*fam["span_range"])
    spans = [rng.choice(fam["span_pool"]) for _ in range(n_spans)]
    total_len = round(sum(spans), 2)

    # ── project master ────────────────────────────────────────────────────
    chainage = round(rng.uniform(0.5, 120.0), 3)
    pm.update({
        "project_title": f"{fam['type'].replace('_', ' ')} BRIDGE — RANDOM CASE {index:03d}",
        "project_code": f"RND{index:03d}-2026-{index + 1:03d}",
        "bridge_name": f"RANDOM-BRIDGE-{index:03d}",
        "chainage_km": chainage,
        "client": rng.choice(["NHAI", "STATE_PWD", "MORTH", "RAILWAYS", "PVT_DEVELOPER"]),
        "revision": rng.choice(["R0", "R1", "R2"]),
        "state_code": rng.choice(STATES),
        "language": rng.choice(["EN", "EN", "HI", "BILINGUAL_EN_HI"]),
        "road_level_rl_m": round(rng.uniform(105.0, 130.0), 3),
        "ground_level_rl_m": round(rng.uniform(100.0, 125.0), 3),
        "project_phase": rng.choice(["DPR", "DESIGN_GAD_30_PCT", "DESIGN_GAD_90_PCT", "TENDER"]),
        "currency": "INR",
    })

    # ── bridge selection ──────────────────────────────────────────────────
    cw_cfg, cw = rng.choice(CARRIAGEWAY_OPTIONS)
    bs.update({
        "bridge_category": fam["category"],
        "bridge_type": fam["type"],
        "span_configuration": "SIMPLY_SUPPORTED" if n_spans == 1
                               else rng.choice(["SIMPLY_SUPPORTED", "CONTINUOUS"]),
        "span_count": n_spans,
        "carriageway_config": cw_cfg,
        "design_code": fam["design_code"],
        "loading_class": rng.choice(LOADING_CLASSES),
        "seismic_zone": rng.choice(SEISMIC_ZONES),
        "wind_zone_ms": rng.choice(WIND_ZONES),
    })
    foundation = _foundation(bs, fd, rng)

    # ── geometry ──────────────────────────────────────────────────────────
    skew = rng.choice([0.0, 0.0, 5.0, 15.0, 30.0, 45.0])
    footpath = 0.0 if cw <= 7.5 else rng.choice([0.0, 1.5, 2.0])
    gi.update({
        "span_count": n_spans,
        "span_lengths_m": spans,
        "alignment_type": "STRAIGHT",
        "gradient_pct": rng.choice([0.5, 1.0, 1.5, 2.0]),
        "carriageway_width_m": cw,
        "footpath_left_m": footpath,
        "footpath_right_m": footpath,
        "median_width_m": rng.choice([0.0, 0.5]) if cw >= 14.0 else 0.0,
        "skew_angle_deg": skew,
        "skew_direction": "NONE" if skew == 0 else rng.choice(["LEFT", "RIGHT"]),
        "curved_bridge_flag": False,
        "camber_mm": rng.choice([15, 20, 25, 30]),
        "chainage_start_km": round(chainage - total_len / 2000.0, 4),
        "chainage_end_km": round(chainage + total_len / 2000.0, 4),
    })

    # ── superstructure ────────────────────────────────────────────────────
    girder_depth = int(round(rng.uniform(*fam["depth_range"]) / 50.0) * 50)
    spacing = fam["girder_spacing"]
    girders = 1 if spacing == 0 else max(2, int(round(cw / spacing)) + 1)
    ss.update({
        "type": fam["type"],
        "deck_material": rng.choice(fam["deck_grades"]),
        "deck_thickness_mm": rng.choice([180, 200, 220, 250]),
        "girder_type": fam["girder_type"],
        "girder_depth_mm": girder_depth,
        "girder_spacing_m": spacing,
        "girders_per_deck_count": girders,
        "parapet_type": rng.choice(["RCC_PARAPET_FULL_HEIGHT", "METAL_CRASH_BARRIER",
                                    "RCC_CRASH"]),
        "parapet_height_mm": rng.choice([900, 1100]),
        "camber_mm": gi["camber_mm"],
    })

    # ── substructure ──────────────────────────────────────────────────────
    pier_type = rng.choice(PIER_TYPES)
    wing = rng.choice(WING_WALLS)
    sub.update({
        "pier_type": pier_type,
        "pier_material": rng.choice(["M25", "M30", "M35", "M40"]),
        "pier_height_typical_m": round(rng.uniform(3.0, 12.0), 1),
        "pier_cap_length_m": round(cw + 1.0, 2),
        "pier_shaft_length_m": round(min(cw + 1.0, 15.0), 2),
        "abutment_type": rng.choice(ABUTMENT_TYPES),
        "abutment_material": rng.choice(["M25", "M30", "M35"]),
        "abutment_length_m": round(cw + 1.2, 2),
        "abutment_height_m": round(rng.uniform(2.0, 6.0), 1),
        "wing_wall_type": wing,
        "wing_wall_angle_deg": (rng.choice([30.0, 45.0, 60.0])
                                if "SPLAYED" in wing else 90.0),
        "wing_wall_splay_length_m": round(rng.uniform(1.5, 4.0), 1),
        "wing_wall_height_m": round(rng.uniform(1.5, 4.0), 1),
        "bearings_per_pier": girders,
        "bearings_per_abutment": girders,
    })

    # ── hydraulic data (kept consistent with the new road level) ──────────
    road_rl = pm["road_level_rl_m"]
    hfl = round(road_rl - rng.uniform(2.0, 4.0), 3)
    hd.update({
        "design_discharge_cumecs": round(rng.uniform(20.0, 800.0), 1),
        "hfl_m": hfl,
        "lwl_m": round(hfl - rng.uniform(1.0, 2.5), 3),
        "normal_wl_m": round(hfl - rng.uniform(0.5, 1.5), 3),
        "scour_level_m": round(hfl - rng.uniform(2.0, 6.0), 3),
        "design_scour_depth_m": round(rng.uniform(1.0, 4.0), 2),
        "actual_soffit_level_m": round(road_rl - rng.uniform(1.0, 2.5), 3),
        "waterway_required_m2": round(rng.uniform(15.0, 120.0), 1),
        "waterway_provided_m2": round(rng.uniform(25.0, 180.0), 1),
        "catchment_area_sqkm": round(rng.uniform(50.0, 3000.0), 1),
    })

    # ── materials ─────────────────────────────────────────────────────────
    mt.update({
        "concrete_superstructure": ss["deck_material"],
        "concrete_substructure": sub["pier_material"],
        "concrete_foundation": rng.choice(["M25", "M30", "M35"]),
        "reinforcement_steel_grade": rng.choice(["Fe500D", "Fe550D", "Fe415"]),
        "prestressing_steel": rng.choice(["G1860", "G1770", "G1720"]),
    })

    # ── schedules ─────────────────────────────────────────────────────────
    n_bear_pier = sub["bearings_per_pier"]
    n_bear_abut = sub["bearings_per_abutment"]
    bearing_rows = []
    for i in range(n_spans - 1):
        bearing_rows.append({
            "location": f"P{i + 1}-Bearing", "bearing_type": mt["bearing_type"],
            "size_x_mm": 400, "size_y_mm": 400,
            "design_load_kn": round(rng.uniform(300.0, 2000.0), 1),
            "fixed_or_guide_or_free": rng.choice(["FIXED", "GUIDE", "FREE"]),
            "quantity": n_bear_pier,
        })
    for tag in ("A1", f"A{n_spans + 1}"):
        bearing_rows.append({
            "location": f"{tag}-Bearing", "bearing_type": mt["bearing_type"],
            "size_x_mm": 350, "size_y_mm": 350,
            "design_load_kn": round(rng.uniform(250.0, 900.0), 1),
            "fixed_or_guide_or_free": "FREE", "quantity": n_bear_abut,
        })
    expj_rows = []
    for tag in ("A1", f"A{n_spans + 1}"):
        expj_rows.append({
            "location": f"{tag}-End", "joint_type": mt["expansion_joint_type"],
            "width_mm": rng.choice([40, 50, 60]),
            "movement_range_mm": rng.choice([20, 40, 60]),
            "gap_mm": 12,
            "transverse_length_m": round(cw + footpath * 2 + 0.9, 2),
            "quantity": 1,
        })
    bj["bearing_schedule"] = bearing_rows
    bj["expansion_joint_schedule"] = expj_rows

    # ── calculations (recomputed, self-consistent) ────────────────────────
    overall_width = cw + 2 * footpath + 0.9 + gi["median_width_m"]
    ca.update({
        "total_length_m": total_len,
        "span_count": n_spans,
        "span_depth_ratio": round(sum(spans) / max(n_spans, 1) * 1000.0 / max(girder_depth, 1), 2),
        "deck_area_sqm": round(total_len * overall_width, 1),
        "bearing_count": n_bear_pier * max(n_spans - 1, 0) + 2 * n_bear_abut,
        "expansion_joint_count": 2,
        "total_estimated_quantity_cost_inr": int(round(total_len * overall_width * 1_200_000)),
    })

    # drawing_control left at the base defaults (all sheets enabled) so every
    # random case exercises the full 8-sheet package.
    dc.setdefault("output_formats", ["DXF"])

    fid = f"rand_{index:03d}_{fam['slug']}_{n_spans}x{int(sum(spans))}m"
    d["_meta"].update({
        "fixture_id": fid,
        "description": (f"{fam['type']} bridge {n_spans}×{sum(spans)/n_spans:.0f}m, "
                        f"cw {cw:.1f}m, skew {skew:.0f}°, {foundation} foundation"),
        "scribd_refs": [],
        "design_standard": fam["design_code"],
        "expected_qa_grade": "A",
        "generator": "scripts/generate_random_drawings.py",
    })
    return d


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate random GAD drawings for testing.")
    ap.add_argument("--count", type=int, default=10, help="number of random cases (default 10)")
    ap.add_argument("--seed", type=int, default=None, help="RNG seed for reproducibility")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output directory")
    ap.add_argument("--clean", action="store_true",
                    help="wipe the output directory before generating")
    args = ap.parse_args()

    seed = args.seed if args.seed is not None else random.SystemRandom().randint(0, 2**31 - 1)
    rng = random.Random(seed)

    out_dir: Path = Path(args.out).resolve()
    if args.clean and out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    build_from_fixture = _load_builder()
    base = json.loads(BASE_FIXTURE.read_text(encoding="utf-8"))

    from bridgecad_draw.booklet import generate_package

    sep = "=" * 72
    print()
    print(sep)
    print("  BRIDGECAD RANDOM DRAWING GENERATOR")
    print(sep)
    print(f"  Cases      : {args.count}")
    print(f"  Seed       : {seed}")
    print(f"  Output dir : {out_dir}")
    print()

    manifest: list[dict] = []
    for i in range(args.count):
        entry: dict = {"index": i}
        try:
            data = randomize(base, rng, i)
            fid = data["_meta"]["fixture_id"]
            case_dir = out_dir / fid
            case_dir.mkdir(parents=True, exist_ok=True)

            project = build_from_fixture(data)
            sheets = generate_package(project, case_dir, prefix=fid, scale_denom=100)
            total_kb = sum(s.stat().st_size for s in sheets) // 1024

            (case_dir / "fixture.json").write_text(
                json.dumps(data, indent=2), encoding="utf-8")

            qa_score = None
            boq_total = None
            try:
                from bridgecad_core.validation import run_all
                qa_score = float(run_all(project).score)
            except Exception:
                pass
            try:
                from bridgecad_bill.processor import extract_and_price
                boq_total = float(extract_and_price(project).grand_total)
            except Exception:
                pass

            meta = data["_meta"]
            gi = project.geometry_input
            entry.update({
                "fixture_id": fid,
                "description": meta["description"],
                "type": data["project"]["bridge_selection"]["bridge_type"],
                "span_count": int(gi.span_count),
                "total_length_m": float(gi.total_length_m),
                "carriageway_width_m": float(gi.carriageway_width_m),
                "skew_angle_deg": float(gi.skew_angle_deg),
                "foundation_type": data["project"]["foundation_details"]["type"],
                "pier_type": data["project"]["substructure"]["pier_type"],
                "sheets": len(sheets),
                "total_kb": total_kb,
                "qa_score": qa_score,
                "boq_grand_total_inr": boq_total,
                "dxf_dir": _rel(case_dir),
                "fixture_json": _rel(case_dir / "fixture.json"),
                "status": "OK" if sheets else "NO_SHEETS",
            })
            print(f"  [{len(sheets)}/8 sheets] {fid}  ({total_kb} KB)"
                  + (f"  QA={qa_score:.1f}" if qa_score is not None else ""))
        except Exception as exc:
            entry.update({"status": "FAILED", "error": f"{exc}"})
            print(f"  [FAILED] case {i}: {exc}")
            traceback.print_exc()

        manifest.append(entry)

    ok = sum(1 for e in manifest if e.get("status") == "OK")
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "seed": seed,
        "count": args.count,
        "ok": ok,
        "failed": args.count - ok,
        "cases": manifest,
    }
    (out_dir / "manifest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print()
    print(sep)
    print(f"  Generated : {ok}/{args.count} cases with DXF sheets")
    print(f"  Manifest  : {out_dir / 'manifest.json'}")
    print(f"  VERDICT   : {'*** OK ***' if ok == args.count else 'PARTIAL'}")
    print(sep)
    return 0 if ok == args.count else 1


if __name__ == "__main__":
    sys.exit(main())
