"""
scripts/generate_all_pwd_gads.py — Maharashtra PWD Booklet GAD Generator.

Generates complete, parametric GAD packages for the 15 standard bridge types
from the official Maharashtra PWD booklet (C.E. Designs letter No. 2473,
dt. 31.12.2022, "Booklet of General Arrangement Drawings for Various Types
of Bridges").

The type cards are not duplicated here: they come from
``bridgecad_catalogue.registry`` and every engineer override goes through
``bridgecad_catalogue.resolve``, so a variation can never silently become the
new baseline.  A run that passes ``--set``/``--sweep`` writes to the transient
``out/pwd_sweep`` tree; only the booklet-faithful defaults touch the canonical
``EXAMPLES_PWD`` corpus.  Each output folder carries a ``params.resolved.json``
holding the exact resolved set and the trace that produced its sheets.

Run:
    python scripts/generate_all_pwd_gads.py
    python scripts/generate_all_pwd_gads.py --type BR-I-2022-006 --set skew_deg=25
    python scripts/generate_all_pwd_gads.py --sweep pier_height_m=6:12:3 --dry-run
    python -m bridgecad generate-all-pwd --set span_length_m=12
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from decimal import Decimal
from pathlib import Path

# ── path bootstrap ───────────────────────────────────────────────────────────
_SUITE = Path(__file__).parents[1]
for _pkg in ["bridgecad-core", "bridgecad-io", "bridgecad-draw",
             "bridgecad-bill", "bridgecad-qa", "bridgecad-export",
             "bridgecad-plugins", "bridgecad-catalogue"]:
    _p = _SUITE / "packages" / _pkg
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
sys.path.insert(0, str(_SUITE / "tests" / "e2e"))

# Canonical corpus — booklet-faithful defaults only.
OUTPUT_ROOT = _SUITE / "EXAMPLES_PWD"
# Transient sweep tree — written whenever --set/--sweep is used, git-ignored.
SWEEP_ROOT = _SUITE / "out" / "pwd_sweep"

MIN_ENTITIES = 20  # minimum DXF entities per sheet (completeness gate)

# ──────────────────────────────────────────────────────────────────────────────
# catalogue card → value-model translation
# ──────────────────────────────────────────────────────────────────────────────
# RCC_BOX_CELL, RCC_PORTAL and RCC_ARCH used to collapse to SOLID_SLAB here,
# which silently made the family-driven rules (sheet 1 "no piers", the sheet 2
# datum, the arch/box-cell presence gates) treat a box cell, a portal frame and
# both arches as slabs and draw them as such.
_SST_MAP = {
    "RCC_SOLID_SLAB": "SOLID_SLAB",
    "RCC_T_BEAM": "RCC_TBEAM",
    "PSC_I_GIRDER": "PSC_IGIRDER",
    "PSC_BOX": "PSC_BOX_GIRDER",
    "RCC_BOX_CELL": "BOX_CELL_MULTI",
    # SuperstructureType has no RCC_PORTAL member; a monolithic portal frame is
    # the closest member the engine and the sheets both understand.
    "RCC_PORTAL": "RCC_FRAME_CULVERT",
}
# The booklet draws two different arches — 014 an open-spandrel pedestrian F.O.B.
# and 015 a precast block arch — so the arch family is named by the card.
_ARCH_BY_ID = {
    "BR-I-2022-014": "RCC_ARCH_OPEN_SPANDREL",
    "BR-I-2022-015": "PRECAST_ARCH",
}
_FOUNDATION_MAP = {"OPEN": "OPEN", "PILE": "PILE", "RAFT": "RAFT", "WELL": "WELL"}
# The booklet's three abutment families map to the closest ``AbutmentType``
# member.  They must not all collapse to CANTILEVER: 004's box cell and 005's
# portal frame are cast integral with the deck (a full-height wall with no
# bearing on the abutment), while the open / pile types carry a cantilever
# wall.  ``AbutmentType`` has no PORTAL member, so the portal abutment takes
# the integral wall it actually is.
_ABUTMENT_MAP = {
    "OPEN": "CANTILEVER",
    "INTEGRAL": "INTEGRAL_ABUTMENT",
    "PORTAL": "INTEGRAL_ABUTMENT",
}
# BearingType has no NONE member: a bearingless (monolithic) deck is an *unset*
# bearing type, so the sheets skip the bearing schedule instead of drawing a
# neoprene pad the booklet does not have.
_BEARING_MAP = {"ELASTOMERIC": "ELASTOMERIC_NEOPRENE", "POT": "POT_PTFE", "NONE": None}


def _superstructure_name(params: dict) -> str:
    """Booklet superstructure family → ``SuperstructureType`` member name."""
    raw = params["superstructure_type"]
    if raw == "RCC_ARCH":
        return _ARCH_BY_ID[params["id"]]
    return _SST_MAP[raw]


def _enum(enum_cls: Any, mapping: dict[str, str], raw: Any, card_id: str) -> Any:
    """Map a booklet value to an enum member, hard-raising on an unknown value.

    ``getattr(cls, name, default)`` silently falls back to the default for a
    typo, so a card whose foundation was misspelt would draw open footings and
    never complain.  The booklet table is a closed enumeration: a value the map
    does not carry is a catalogue data bug, and it must stop the run rather
    than degrade the drawing.
    """
    name = mapping.get(str(raw))
    if name is None or not hasattr(enum_cls, name):
        raise KeyError(
            f"{card_id}: {enum_cls.__name__} has no member for {raw!r} "
            f"(mapped to {name!r})"
        )
    return enum_cls[name]


def _build_project(params: dict):
    """Build a BridgeProject from a resolved catalogue parameter set."""
    from bridgecad_core import types as T
    from bridgecad_core.models import (
        Approaches, BearingsJoints, BridgeProject, BridgeSelection,
        Calculations, ComponentsLib, DrawingControl, FoundationDetails,
        GeometryInput, HydraulicData, Materials, ProjectMaster, Substructure,
        Superstructure, ValidationModel,
    )

    def _dec(v): return Decimal(str(v)) if v is not None else None
    def _int(v): return int(v) if v is not None else None
    def _int_list(v): return [int(n) for n in v] if v is not None else None

    card_id = params["id"]
    sst = T.SuperstructureType[_superstructure_name(params)]
    fdn = _enum(T.FoundationType, _FOUNDATION_MAP, params["foundation_type"], card_id)
    abt = _enum(T.AbutmentType, _ABUTMENT_MAP, params["abutment_type"], card_id)
    pier_material = T.ConcreteGrade[params.get("pier_material", "M25")]
    bearing_name = _BEARING_MAP[params["bearing_type"]]
    bearing = T.BearingType[bearing_name] if bearing_name else None

    hfl = _dec(params["hfl_m"])
    scour = _dec(params["scour_depth_m"])
    footpath = _dec(params.get("footpath_width"))
    # Kerbs are part of the deck's overall width — ``GeometryInput.overall_width_m``
    # sums them in — and sheet 1 draws a kerb staff down each side.  Passing none
    # left ``overall_width_m`` short of the staffs the plan then drew, so the
    # "overall width" dimension and the pier / abutment lengths built from it
    # disagreed with the picture.
    kerb_l = _dec(params.get("kerb_width_left_m") or "0.25")
    kerb_r = _dec(params.get("kerb_width_right_m") or "0.25")

    pm = ProjectMaster(
        project_title=params["title"],
        project_code=f"PWD-2022-{params['id'].split('-')[-1].zfill(3)}",
        bridge_name=f"PWD {params['id']}",
        drawing_no=params["id"],
        client=T.ClientType.STATE_PWD,
        revision=T.RevisionTag.R0,
        state_code=T.IndianStateCode.MH,
        language=T.Language.EN,
        project_phase=T.ProjectPhase.DESIGN_GAD_60_PCT,
        road_level_rl_m=_dec(params["road_level"]),
        ground_level_rl_m=hfl - scour,
    )

    gi = GeometryInput(
        span_count=params["span_count"],
        span_lengths_m=[_dec(s) for s in params["span_lengths"]],
        carriageway_width_m=_dec(params["carriageway_width"]),
        footpath_left_m=footpath,
        footpath_right_m=footpath,
        kerb_width_left_m=kerb_l,
        kerb_width_right_m=kerb_r,
        skew_angle_deg=_dec(params.get("skew_deg", 0)),
        chainage_start_km=Decimal("0.000"),
    )

    # A skewed bridge cuts its piers and abutments at an angle, so their wall
    # length is the deck's overall width divided by cos(skew) — longer than the
    # deck is wide.  Passing the carriageway width left every pier and abutment
    # short of the bearing line it actually carries.
    skew_deg = float(gi.skew_angle_deg or 0)
    cross_len = (gi.overall_width_m / Decimal(str(math.cos(math.radians(skew_deg))))
                 ).quantize(Decimal("0.001"))

    ss = Superstructure(
        type=sst,
        deck_material=T.ConcreteGrade.M30,
        deck_thickness_mm=_int(params.get("deck_thickness_mm", 500)),
        wearing_coat_thickness_mm=65,
        girder_depth_mm=_int(params.get("girder_depth_mm", 0)),
        girder_spacing_m=_dec(params.get("girder_spacing_m", 2.5)),
        girders_per_deck_count=_int(params.get("girders_per_deck", 0)),
        parapet_height_mm=1000,
        # Arch-family identities (booklet 014 / 015).  ``None`` for every type
        # that is not an arch, and the arch sheets then draw the generic deck.
        arch_schedule_mm=params.get("arch_schedule_mm"),
        arch_rise_mm=_int(params.get("arch_rise_mm")),
        arch_ring_thickness_mm=_int(params.get("arch_ring_thickness_mm")),
        arch_strip_count=_int(params.get("arch_strip_count")),
        arch_block_count=_int(params.get("arch_block_count")),
        arch_strip_gap_mm=_int(params.get("arch_strip_gap_mm")),
        spandrel_wall_thickness_mm=_int(params.get("spandrel_wall_thickness_mm")),
    )

    sub = Substructure(
        pier_type=T.PierType.WALL,
        pier_material=pier_material,
        pier_height_typical_m=_dec(params.get("pier_height_m", 6.0)),
        pier_shaft_width_m=_dec(params.get("pier_shaft_width_m", 1.5)),
        pier_shaft_length_m=cross_len,
        pier_cap_depth_m=_dec(params.get("pier_cap_depth_m", 0.8)),
        pier_cap_width_m=Decimal(str(round(float(params.get("pier_shaft_width_m", 1.5)) * 1.3, 3))),
        pier_pedestal_height_m=Decimal("0.15"),
        abutment_type=abt,
        abutment_material=T.ConcreteGrade.M25,
        abutment_width_m=Decimal("1.2"),
        abutment_length_m=cross_len,
        abutment_height_m=_dec(params.get("pier_height_m", 6.0)),
        abutment_pedestal_height_m=Decimal("0.15"),
        approach_slab_length_m=Decimal("3.5"),
        approach_slab_thickness_mm=200,
        wing_wall_splay_length_m=Decimal("3.0"),
        wing_wall_height_m=Decimal("2.5"),
        return_wall_length_m=Decimal("4.0"),
        backfill_type="SELECT MOORUM",
        abutment_cap_depth_mm=600,
        abutment_cap_projection_front_mm=300,
        abutment_cap_projection_rear_mm=300,
        dirt_wall_thickness_mm=300,
        weep_hole_diameter_mm=100,
        weep_hole_spacing_m=Decimal("1.5"),
    )

    fd = FoundationDetails(
        type=fdn,
        pile_diameter_mm=_int(params.get("pile_diameter_mm")) or None,
        pile_length_m=_dec(params.get("pile_length_m", 0)),
        piles_per_pier=_int(params.get("piles_per_pier")) or None,
        pile_spacing_m=Decimal("2.5"),
        pile_cap_thickness_mm=_int(1500 if params["foundation_type"] == "PILE" else 0),
        pile_cutoff_level_m=hfl - Decimal("1.0"),
        well_diameter_m=_dec(params.get("well_diameter_m")),
        # Box-cell identity (booklet 004).  ``None`` for every other type, and
        # the box-cell panel on sheet 4 then does not draw.
        unit_cell_counts=_int_list(params.get("unit_cell_counts")),
        cell_clear_m=_dec(params.get("cell_clear_m")),
        cell_wall_mm=_int(params.get("cell_wall_mm")),
        cell_haunch_mm=_int(params.get("cell_haunch_mm")),
        unit_joint_mm=_int(params.get("unit_joint_mm")),
        raft_thickness_mm=_int(params.get("raft_thickness_mm")),
        cutoff_wall_depth_m=_dec(params.get("cutoff_wall_depth_m")),
    )

    hd = HydraulicData(
        hfl_m=hfl,
        lwl_m=hfl - Decimal("0.5"),
        scour_level_m=hfl - scour,
        design_scour_depth_m=scour,
        actual_soffit_level_m=_dec(params["soffit_level"]),
    )

    mt = Materials(
        concrete_superstructure=T.ConcreteGrade.M30,
        concrete_substructure=pier_material,
        concrete_foundation=T.ConcreteGrade.M25,
        reinforcement_steel_grade=T.SteelGrade.Fe500D,
        prestressing_steel=T.PrestressGrade.G1860,
        bearing_type=T.BearingType.ELASTOMERIC_NEOPRENE,
        expansion_joint_type=T.ExpansionJointType.STRIP_SEAL,
    )

    bj = BearingsJoints(bearing_type=bearing)

    return BridgeProject(
        project_master=pm,
        bridge_selection=BridgeSelection(
            bridge_category=(T.BridgeCategory.MINOR_BRIDGE
                             if params["total_length_m"] < 30
                             else T.BridgeCategory.MAJOR_BRIDGE),
            bridge_type=sst,
            span_configuration=T.SpanConfiguration.SIMPLY_SUPPORTED,
            carriageway_config=T.CarriagewayLaneConfig.LANE_2,
            design_code=T.DesignCode.IRC_6_2017,
            loading_class=T.LoadClass.CLASS_A,
            seismic_zone=T.SeismicZone.ZONE_III,
            wind_zone_ms=T.WindSpeedBasic_ms.VB_39_ms_ZONE_2,
            foundation_type=fdn,
        ),
        geometry_input=gi,
        superstructure=ss,
        substructure=sub,
        foundation_details=fd,
        approaches=Approaches(),
        hydraulic_data=hd,
        materials=mt,
        bearings_joints=bj,
        components_lib=ComponentsLib(),
        drawing_control=DrawingControl(
            sheet_size=T.SheetSize.A1,
            drawing_scale=T.DrawingScale.S100,
            title_block_style=T.TitleBlockStyle.STANDARD,
        ),
        calculations=Calculations(),
        validation=ValidationModel(),
    )


def _check_completeness(sheets: list[Path]) -> list[str]:
    """Check every sheet has enough entities and is non-trivially populated."""
    import ezdxf
    issues = []
    for s in sheets:
        try:
            n = len(list(ezdxf.readfile(str(s)).modelspace()))
            if n < MIN_ENTITIES:
                issues.append(f"{s.name}: only {n} entities (< {MIN_ENTITIES})")
        except Exception as exc:
            issues.append(f"{s.name}: read error — {exc}")
    return issues


def _render_pngs(sheets: list[Path], out_dir: Path, dpi: int = 150,
                 render_paper: str = "A2", render_orientation: str = "landscape") -> list[str]:
    """Return rendering failures, including decoded but entirely blank images."""
    from bridgecad_draw.engines.png_engine import render_png, paper_size_inches
    from PIL import Image, ImageChops

    issues = []
    for s in sheets:
        png_out = out_dir / (s.stem + ".png")
        try:
            if render_paper == "A2" and render_orientation == "landscape":
                render_png(s, png_out, dpi=dpi)
            else:
                render_png(s, png_out, dpi=dpi, size_in=paper_size_inches(render_paper, render_orientation))
            with Image.open(png_out) as image:
                rgba = image.convert("RGBA")
                rgb = Image.new("RGBA", rgba.size, "white")
                rgb.alpha_composite(rgba)
                rgb = rgb.convert("RGB")
                if ImageChops.difference(rgb, Image.new("RGB", rgb.size, "white")).getbbox() is None:
                    issues.append(f"{s.name}: PNG is entirely blank")
        except Exception as exc:
            issues.append(f"{s.name}: PNG render failed: {type(exc).__name__}: {exc}")
    return issues


def _write_readme(out_dir: Path, params: dict, sheets: list[Path],
                  issues: list[str], dxf_kb: int) -> None:
    sheet_table = ""
    for i, s in enumerate(sheets, 1):
        size_kb = s.stat().st_size // 1024
        sheet_table += f"| {i} | {s.stem} | {size_kb} KB |\n"

    status = "✅ PASS" if not issues else "❌ FAIL"
    issues_text = "\n".join(f"- {i}" for i in issues) if issues else "No issues found."
    fidelity = ""
    if params.get("approximation"):
        fidelity = ("\n> **Fidelity:** approximation — "
                    f"{params.get('fidelity_note', 'engine primitive not implemented')}\n")

    readme = f"""# {params['title']}

**PWD Drawing No.:** {params['id']}  
**Spans:** {params['spans']}  
**Foundation:** {params['foundation_type']}  
**Superstructure:** {params['superstructure_type']}  
**Pier Material:** {params.get('pier_material', 'M25')}  
**Carriageway:** {params['carriageway_width']} m  
**Road RL:** {params['road_level']} m  
**HFL:** {params['hfl_m']} m  
{fidelity}
## Completeness check: {status}

{issues_text}

## Sheets generated

| # | Sheet | Size |
|---|---|---|
{sheet_table}

**Total DXF size:** {dxf_kb} KB

---
*Generated by BridgeCAD Enterprise Suite v0.1.0-rc1 — Maharashtra PWD Booklet*
*IRC 5 / IRC 6 / IRC 21 / IRC 78 / IRC SP:55 / MoRTH 2024-25*
*Parameters resolved from `bridgecad_catalogue` — see `params.resolved.json`.*
"""
    (out_dir / "README.md").write_text(readme, encoding="utf-8")


def _canonicalise(sheets: list[Path]) -> None:
    """Re-serialise each sheet through the deterministic DXF writer.

    An ezdxf ASCII DXF is not byte-stable: every save stamps ``$TDCREATE`` /
    ``$TDUPDATE``, regenerates two GUIDs and writes its own version comment, so
    two renders of the same project differed (W07 DoD — "two renders of the same
    input produce identical bytes").  ``determinism.write_deterministic``
    replaces the volatile values with fixed sentinels.
    """
    import ezdxf

    from bridgecad_draw.determinism import write_deterministic

    for s in sheets:
        write_deterministic(ezdxf.readfile(str(s)), s)


def generate_one(params: dict, out_root: Path,
                 label: str | None = None, *, render_paper: str = "A2",
                 render_orientation: str = "landscape") -> tuple[str, bool, str]:
    """Generate one variant into ``out_root/<label>``.

    Returns ``(label, success, message)``.
    """
    from bridgecad_draw.booklet import generate_package

    label = label or params["id"]
    out_dir = out_root / label
    out_dir.mkdir(parents=True, exist_ok=True)

    # Provenance: the exact resolved set (and the trace that produced it) that
    # the sheets in this folder were drawn from.
    (out_dir / "params.resolved.json").write_text(
        json.dumps({"resolved": params, "trace": params.trace,
                    "warnings": params.warnings}, indent=2, default=str),
        encoding="utf-8",
    )

    try:
        project = _build_project(params)
    except Exception as exc:
        return label, False, f"build failed: {exc}"

    try:
        sheets = generate_package(project, out_dir, prefix=label)
        _canonicalise(sheets)
    except Exception as exc:
        return label, False, f"DXF failed: {type(exc).__name__}: {exc}"

    issues = _check_completeness(sheets)
    import os
    render_issues = []
    skipped = os.getenv("SKIP_PNG") == "1"
    if not skipped:
        render_issues = _render_pngs(sheets, out_dir, render_paper=render_paper, render_orientation=render_orientation)
        issues.extend(render_issues)
    (out_dir / "render-status.json").write_text(
        json.dumps({"png": "skipped" if skipped else ("failed" if render_issues else "nonblank"),
                    "render_issues": render_issues, "render_paper": render_paper,
                    "render_orientation": render_orientation, "reference_fidelity": "not_verified"}, indent=2),
        encoding="utf-8",
    )
    dxf_kb = sum(s.stat().st_size for s in sheets) // 1024
    _write_readme(out_dir, params, sheets, issues, dxf_kb)

    status = "STRUCTURAL PASS (reference fidelity not verified)" if not issues else "FAIL"
    return label, not issues, f"{status} — {len(sheets)} sheets, {dxf_kb} KB, {len(issues)} issue(s)"


def _write_index(root: Path, jobs: list[tuple[dict, str]], failed: set[str]) -> None:
    index = "# Maharashtra PWD Booklet — GAD Packages\n\n"
    index += (f"**{len(jobs) - len(failed)}/{len(jobs)} variants** generated as "
              "9-sheet DXF packages; PNG rendering is optional and must be checked separately.\n\n")
    index += "| # | Folder | PWD Drawing No. | Type | Spans | Status |\n"
    index += "|---|---|---|---|---|---|\n"
    for i, (p, label) in enumerate(jobs, 1):
        ok = label not in failed
        index += (f"| {i:02d} | {label} | {p['id']} | {p['title']} | {p['spans']} | "
                  f"{'✅' if ok else '❌'} |\n")
    index += "\n---\n*BridgeCAD Enterprise Suite v0.1.0-rc1 — BRIDGECAD-OSS-1.0*\n"
    (root / "README.md").write_text(index, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    from bridgecad_catalogue import registry, resolve as R, sweep as S

    ap = argparse.ArgumentParser(
        prog="generate_all_pwd_gads",
        description="Generate Maharashtra PWD booklet GAD packages from the catalogue.",
    )
    ap.add_argument("--type", action="append", metavar="BR-I-2022-00N",
                    help="restrict to one booklet type (repeatable)")
    ap.add_argument("--set", action="append", default=[], metavar="key=value",
                    help="pin one catalogue dial (repeatable) → writes to out/pwd_sweep")
    ap.add_argument("--sweep", action="append", default=[], metavar="key=lo:hi:step",
                    help="vary one catalogue dial (repeatable) → writes to out/pwd_sweep")
    ap.add_argument("--force", action="store_true",
                    help="allow LOCKED (booklet identity) edits")
    ap.add_argument("--dry-run", action="store_true",
                    help="resolve and print the variants, generate nothing")
    ap.add_argument("--render-paper", choices=["A0", "A1", "A2", "A3", "A4"], default="A2",
                    help="PNG output media only; does not change DXF layout/scale")
    ap.add_argument("--render-orientation", choices=["landscape", "portrait"], default="landscape",
                    help="PNG output orientation only")
    a = ap.parse_args(argv)

    cards = registry.load()
    known = {c["id"] for c in cards}
    unknown = [t for t in a.type or [] if t not in known]
    if unknown:
        print(f"  [ERROR] unknown booklet type(s): {', '.join(unknown)}")
        print(f"          known: {', '.join(sorted(known))}")
        return 2

    chosen = [c for c in cards if not a.type or c["id"] in a.type]
    fixed = {k: v for k, v in (s.split("=", 1) for s in a.set)}
    variants = S.matrix(a.sweep) if a.sweep else [{}]

    jobs: list[tuple[dict, str]] = []
    rejected = 0
    for card in chosen:
        for i, var in enumerate(variants):
            ov = {**fixed, **var}
            try:
                p = R.resolve(card, ov, force=a.force)
            except R.Violation as exc:
                rejected += 1
                print(f"  [REJECT] {card['id']} {ov} — {exc}")
                continue
            p["id"] = card["id"]          # resolve() drops the identity key
            for w in p.warnings:
                print(f"  [WARN]   {card['id']} — {w}")
            label = card["id"] if not ov else f"{card['id']}__v{i:02d}"
            jobs.append((p, label))

    if not jobs:
        print("  [ERROR] no buildable variant — every override was rejected")
        return 1

    if a.dry_run:
        for p, label in jobs:
            print(f"  {label:<24} Σ={p['total_length_m']} m  soffit={p['soffit_level']}")
        print(f"\n  dry-run: {len(jobs)} variant(s) resolved, nothing written.")
        return 1 if rejected else 0

    root = SWEEP_ROOT if (a.set or a.sweep or a.render_paper != "A2" or a.render_orientation != "landscape") else OUTPUT_ROOT

    print(f"\n{'='*72}")
    print("  Maharashtra PWD Booklet — GAD Generator")
    print(f"  Variants: {len(jobs)}  |  Output: {root}")
    print(f"{'='*72}\n")

    passed, failed = 0, []
    for p, label in jobs:
        fid, ok, msg = generate_one(p, root, label, render_paper=a.render_paper, render_orientation=a.render_orientation)
        print(f"  [{'DONE' if ok else 'FAIL':4s}] {label:<28} {p['title']:<46} {msg}")
        if ok:
            passed += 1
        else:
            failed.append(fid)

    print(f"\n{'='*72}")
    print(f"  Generated : {passed}/{len(jobs)}")
    print(f"  Failed    : {len(failed)}")
    for f in failed:
        print(f"    ✗ {f}")
    print(f"  Output dir: {root}")
    print(f"{'='*72}\n")

    _write_index(root, jobs, set(failed))
    if rejected:
        print(f"  Rejected variants: {rejected} (partial success is not a successful batch)")
    return 0 if not failed and not rejected else 1


if __name__ == "__main__":
    sys.exit(main())
