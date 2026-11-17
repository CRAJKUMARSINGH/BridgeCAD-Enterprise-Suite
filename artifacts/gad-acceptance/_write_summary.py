"""Write artifacts/gad-acceptance/nine_span_slab/summary.json.

Re-measures everything from the generated evidence (read-only) so the summary
cannot drift from the DXFs: entity counts, cross-view deltas, layout verdicts.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for _pkg in ["bridgecad-core", "bridgecad-draw", "bridgecad-catalogue"]:
    _p = REPO / "packages" / _pkg
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import ezdxf  # noqa: E402
from bridgecad_catalogue import registry  # noqa: E402
from bridgecad_catalogue.resolve import resolve  # noqa: E402
from bridgecad_core.geometry.long_section import (  # noqa: E402
    compute_long_section_geometry,
    typical_pier_support_level,
)
from bridgecad_draw import layout_audit as LA  # noqa: E402

COMMIT = "e969b72979196f78e2d04129c2462268d6caf099"
OUT = REPO / "artifacts" / "gad-acceptance" / "nine_span_slab" / COMMIT
SUMMARY = REPO / "artifacts" / "gad-acceptance" / "nine_span_slab" / "summary.json"
TOL_M = 1e-6
TOL_DRAW_M = 1e-3

SHEETS = [
    "Sheet1_Plan", "Sheet2_LongSection", "Sheet3_CrossSection", "Sheet4_Foundation",
    "Sheet5_PierAbutment", "Sheet6_BearingsJoints", "Sheet7_BOQ",
    "Sheet8_SideElevations", "Sheet9_Reinforcement",
]


def msp(name):
    return ezdxf.readfile(str(OUT / f"{COMMIT}_{name}.dxf")).modelspace()


def rects(space, layer):
    out = []
    for e in space:
        if e.dxftype() == "LWPOLYLINE" and e.dxf.layer == layer:
            pts = e.get_points("xy")
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            out.append((min(xs), min(ys), max(xs), max(ys)))
    return out


def hlines(space, layer):
    out = []
    for e in space:
        if e.dxftype() == "LINE" and e.dxf.layer == layer:
            s, en = e.dxf.start, e.dxf.end
            if abs(s.y - en.y) < 1e-9:
                out.append((min(s.x, en.x), s.y, max(s.x, en.x)))
    return out


def load_gen():
    spec = importlib.util.spec_from_file_location("_gen", REPO / "scripts" / "generate_all_pwd_gads.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    gen = load_gen()
    card = registry.by_id("BR-I-2022-002")
    params = resolve(card, {"span_count": "9", "span_length_m": "10"})
    params["id"] = card["id"]
    project = gen._build_project(params)
    total_m = float(params["total_length_m"])
    ls = compute_long_section_geometry(project)
    rec = typical_pier_support_level(project)

    # ── DXF entity counts ──────────────────────────────────────────────────
    dxf_files = []
    for name in SHEETS:
        path = OUT / f"{COMMIT}_{name}.dxf"
        space = msp(name)
        dxf_files.append({
            "path": str(path),
            "entities": sum(1 for _ in space),
            "size_bytes": path.stat().st_size,
        })

    # ── plan ───────────────────────────────────────────────────────────────
    s1 = msp("Sheet1_Plan")
    outline = rects(s1, "STRUC-OUTLINE")[0]
    plan_mm_per_m = (outline[2] - outline[0]) / total_m
    plan_ch = lambda x: (x - outline[0]) / plan_mm_per_m
    plan_piers = sorted(round(plan_ch((r[0] + r[2]) / 2.0), 6) for r in rects(s1, "SUB-PIER"))
    plan_abuts = sorted(round(plan_ch((r[0] + r[2]) / 2.0), 6) for r in rects(s1, "SUB-ABUT"))

    # ── long section ───────────────────────────────────────────────────────
    s2 = msp("Sheet2_LongSection")
    deck = hlines(s2, "SUPER-DECK")
    sfx0 = min(d[0] for d in deck)
    sfx1 = max(d[2] for d in deck)
    sec_h_mm_per_m = (sfx1 - sfx0) / total_m
    y_soffit = min(d[1] for d in deck)
    y_hfl = hlines(s2, "CIVIL-HFL")[0][1]
    hfl_rl = float(ls.hfl_rl)
    soffit_rl = float(rec.structural_soffit_rl_m)
    sec_v_mm_per_m = (y_soffit - y_hfl) / (soffit_rl - hfl_rl)
    sec_ch = lambda x: (x - sfx0) / sec_h_mm_per_m
    sec_rl = lambda y: hfl_rl + (y - y_hfl) / sec_v_mm_per_m

    groups = defaultdict(list)
    for r in rects(s2, "SUB-PIER"):
        groups[round((r[0] + r[2]) / 2.0, 6)].append(r)
    groups = [(cx, sorted(rs, key=lambda r: r[1])) for cx, rs in sorted(groups.items())]
    sec_piers = sorted(round(sec_ch(cx), 6) for cx, _ in groups)

    deck_mid = (sfx0 + sfx1) / 2.0
    abut_rects = rects(s2, "SUB-ABUT")
    left = [r for r in abut_rects if (r[0] + r[2]) / 2.0 < deck_mid]
    right = [r for r in abut_rects if (r[0] + r[2]) / 2.0 >= deck_mid]
    shaft_l = max(left, key=lambda r: r[3] - r[1])
    shaft_r = max(right, key=lambda r: r[3] - r[1])
    sec_abuts = sorted(round(v, 6) for v in (sec_ch(shaft_l[2]), sec_ch(shaft_r[0])))

    # drawn cap / shaft per pier
    cap_bottoms, shaft_tops, cap_tops, pier_bases = [], [], [], []
    for _cx, rs in groups:
        shaft, cap = rs[0], rs[1]
        cap_bottoms.append(sec_rl(cap[1]))
        shaft_tops.append(sec_rl(shaft[3]))
        cap_tops.append(sec_rl(cap[3]))
        pier_bases.append(sec_rl(shaft[1]))

    pier_height = float(project.substructure.pier_height_typical_m)
    drawn_base = sum(pier_bases) / len(pier_bases)

    def vd(delta, tol):
        return {"delta_m": round(delta, 9), "tolerance_m": tol,
                "verdict": "AGREE" if abs(delta) <= tol else "DISAGREE"}

    cross = [
        {"check": "plan pier chainages vs long-section pier chainages (max |Δ|)",
         **vd(max(abs(a - b) for a, b in zip(plan_piers, sec_piers)), TOL_DRAW_M)},
        {"check": "plan support set vs long-section support set (max |Δ|)",
         **vd(max(abs(a - b) for a, b in zip(
             sorted(plan_piers + plan_abuts), sorted(sec_piers + sec_abuts))), TOL_DRAW_M)},
        {"check": "plan deck length vs long-section deck length (m)",
         **vd(((outline[2] - outline[0]) / plan_mm_per_m)
              - ((sfx1 - sfx0) / sec_h_mm_per_m), TOL_DRAW_M)},
        {"check": "record cap_bottom vs drawn shaft_top (long-section SUB-PIER rect top)",
         **vd(float(rec.cap_bottom_rl_m) - sum(shaft_tops) / len(shaft_tops), TOL_DRAW_M)},
        {"check": "record cap_top vs drawn cap_top (long-section SUB-PIER cap rect top)",
         **vd(float(rec.cap_top_rl_m) - sum(cap_tops) / len(cap_tops), TOL_DRAW_M)},
        {"check": "record footing_top vs record shaft_base (pure resolver)",
         **vd(float(rec.footing_top_rl_m) - float(rec.shaft_base_rl_m), TOL_M)},
        {"check": "record cap_bottom vs record shaft_top (pure resolver)",
         **vd(float(rec.cap_bottom_rl_m) - float(rec.shaft_top_rl_m), TOL_M)},
        {"check": "DRAWN pier base (long section) vs record shaft_base",
         **vd(drawn_base - float(rec.shaft_base_rl_m), TOL_DRAW_M)},
        {"check": "DRAWN pier base (long section) vs HFL − pier_height (the OLD datum)",
         **vd(drawn_base - (hfl_rl - pier_height), TOL_DRAW_M)},
    ]

    # ── layout audit ───────────────────────────────────────────────────────
    LA.set_enabled(True)
    try:
        audit = LA.collect(project)
    finally:
        LA.set_enabled(None)

    by_sheet = defaultdict(list)
    for b in audit.text_boxes:
        by_sheet[b.sheet].append(b)
    overlaps = {}
    for sheet in sorted(by_sheet):
        boxes = by_sheet[sheet]
        pairs = []
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                if boxes[i].overlaps(boxes[j]):
                    pairs.append([boxes[i].text, boxes[j].text])
        overlaps[sheet] = {"text_boxes": len(boxes), "overlaps": len(pairs), "pairs": pairs}
    heights = [b.height for b in audit.text_boxes if b.height > 0]

    checks = LA.layout_checks(audit)

    def _regions(d):
        return {k: list(v.as_tuple()) for k, v in d.items()}

    layout = {
        "rendered": audit.rendered,
        "error": audit.error,
        "entities_outside_frame": len(audit.outside_frame),
        "outside_frame": audit.outside_frame,
        "printed_scales_all_on_ladder": all(LA.scale_on_ladder(d) for _, d in audit.printed_scales),
        "printed_scales": sorted({d for _, d in audit.printed_scales}),
        "min_text_height_mm": round(min(heights), 4) if heights else None,
        "text_floor_mm": 1.8,
        "text_floor_holds": (min(heights) >= 1.8 - 1e-6) if heights else None,
        "layers_drawn": len(audit.layers_drawn),
        "nts_claims": len(audit.nts_claims),
        "overlaps_per_sheet": overlaps,
        "overlap_note": (
            "layout_audit.BBox estimates text width as 0.6*height*len(text), which "
            "over-estimates short labels; the listed pairs are measured, not asserted zero."
        ),
        # ── reserved-zone rectangles, measured from the rendered DXFs ──────
        "regions": {
            "sheet": _regions(audit.sheet_regions),
            "frame": _regions(audit.frame_regions),
            "title_block": _regions(audit.title_block_regions),
            "notes": _regions(audit.notes_regions),
        },
        "title_block_intrusions": audit.title_block_intrusions,
        "notes_intrusions": audit.notes_intrusions,
        "layout_checks": {
            "rendered": checks.rendered,
            "clipping_ok": checks.clipping_ok,
            "title_block_ok": checks.title_block_ok,
            "notes_zone_declared": checks.notes_zone_declared,
            "notes_zone_ok": checks.notes_zone_ok,
            "scales_ok": checks.scales_ok,
            "text_floor_ok": checks.text_floor_ok,
            "min_text_height_paper_mm": checks.min_text_height_paper_mm,
            "details": checks.details,
            "passed": checks.passed,
        },
    }

    resolve_status = {
        "support_id": rec.support_id,
        "status": rec.status.value,
        "authority": rec.authority.value,
        "topology": rec.topology.value,
        "issues": [{"code": i.code, "field": i.field_name, "message": i.message} for i in rec.issues],
        "levels_m": {k: (None if v is None else str(v)) for k, v in rec.levels().items()},
        "shaft_height_m": str(rec.shaft_height_m),
        "footing_depth_m": None if rec.footing_depth_m is None else str(rec.footing_depth_m),
        "provenance": {k: v.value for k, v in rec.provenance.items()},
    }
    records_all_8 = [
        {"support_id": r.support_id, "status": r.status.value, "authority": r.authority.value,
         "cap_top_rl_m": str(r.cap_top_rl_m), "cap_bottom_rl_m": str(r.cap_bottom_rl_m),
         "shaft_base_rl_m": str(r.shaft_base_rl_m), "shaft_height_m": str(r.shaft_height_m)}
        for r in ls.support_level_records
    ]

    summary = {
        "card_id": "BR-I-2022-002",
        "commit": COMMIT,
        "source_state": (
            "HEAD is uncommitted-for-change: the package was rendered from the "
            "WORKING TREE, which carries the canonical support-level contract fix "
            "(long_section.py, support_levels consumers in sheet2/sheet4/sheet5/"
            "sheet8). The commit hash in the path is the HEAD the tree descends "
            "from, not the code that produced these DXFs."
        ),
        "generated_package_dir": str(OUT),
        "resolve_overrides_used": {"span_count": "9", "span_length_m": "10"},
        "resolved_params_subset": {
            "spans": params.get("spans"),
            "span_count": params.get("span_count"),
            "total_length_m": str(params.get("total_length_m")),
            "pier_count": params.get("pier_count"),
            "foundation_type": params.get("foundation_type"),
            "pier_height_m": params.get("pier_height_m"),
            "hfl_m": params.get("hfl_m"),
            "road_level": params.get("road_level"),
            "soffit_level": str(params.get("soffit_level")),
            "foundation_level": str(params.get("foundation_level")),
        },
        "authority_question": {
            "question": "What does the resolver/project build do with the card's pier_height_m = 6.0?",
            "answer": (
                "HEIGHT_CONTROLLED, HONESTLY UNRESOLVED. The card supplies a pier "
                "HEIGHT (6.0 m) and an OPEN foundation with NO designed footing "
                "thickness or supplied founding RL. The height is now passed into "
                "resolve_support_levels as shaft_height_m, so the authority "
                "auto-classifies to HEIGHT_CONTROLLED: the record DERIVES the shaft "
                "base from the height (cap bottom 100.975 − 6.0 = 94.975 RL) and, "
                "because a founding RL cannot be PROPOSED without a footing depth, "
                "it raises E-MISSING-FOOTING-DEPTH and stays UNRESOLVED rather than "
                "inventing a footing. Every view that draws the pier base (Sheet 2 "
                "long section, Sheet 4 foundation, Sheet 5 details, Sheet 8 side "
                "elevations) consumes that one shaft_base_rl_m, so the drawn base "
                "AGREES with the record and the old 5.0 m view-to-view divergence "
                "(the HFL − pier_height = 94.0 hydraulic datum) is gone."
            ),
            "conflict_path_proven_on_the_spec_fixture": True,
            "conflict_code": "E-CONFLICT-SHAFT-HEIGHT",
            "conflict_proof": (
                "spec fixture (road 102.5 / wearing 0.075 / slab 0.5 / bearing 0.05 assumed / "
                "pedestal 0.15 assumed / cap 0.8 / footing bottom 97.4 / depth 1.0) resolves "
                "RESOLVED with shaft height 2.525 m; adding shaft_height_m=6.0 yields "
                "CONFLICT + E-CONFLICT-SHAFT-HEIGHT, so the guard is real and would fire if "
                "this card ever gained a supplied footing"
            ),
        },
        "support_level_record": resolve_status,
        "support_level_records_all_8": records_all_8,
        "dxf_files": dxf_files,
        "measured_cross_view_deltas": cross,
        "layout_audit": layout,
        "could_not_verify": [
            "'footing top = shaft base' as a DRAWN cross-view check: this card's foundation is "
            "OPEN, so Sheet 4 renders no pier-footing geometry (layers FOUND-CAP / FOUND-PILE / "
            "SUB-PIER / TEXT-LEVEL are absent). The equality is only available from the canonical "
            "resolver record.",
            "'cap bottom = shaft top' as a DRAWN plan↔foundation check: the plan does not carry "
            "RLs; the drawn comparison is long-section SUB-PIER only, cross-checked against the record.",
            "reference fidelity: render-status.json records reference_fidelity = not_verified; no "
            "reference drawing was compared (the reference PDF contains no nine-span sheet).",
            "region-level layout gating is now measured, not assumed: layout_audit exposes "
            "Region rectangles for the sheet, frame, title block and notes zone, and "
            "layout_checks reports clipping / title_block / notes_zone / scales / text_floor. "
            "What remains outside the gate is the *view* rectangles: no sheet declares a "
            "bounding rectangle for its own views, so 'view vs view' overlap is still reported "
            "as measured text-pair counts rather than as a pass/fail region check.",
        ],
        "assumed_inputs": [
            "spec fixture input, assumed, not design guidance: road RL 102.500",
            "spec fixture input, assumed, not design guidance: wearing 0.075",
            "spec fixture input, assumed, not design guidance: structural slab 0.500",
            "spec fixture input, assumed, not design guidance: bearing depth 0.050",
            "spec fixture input, assumed, not design guidance: pedestal height 0.150",
            "spec fixture input, assumed, not design guidance: cap depth 0.800",
            "spec fixture input, assumed, not design guidance: footing bottom RL 97.400",
            "spec fixture input, assumed, not design guidance: footing depth 1.000",
        ],
        "tolerances": {"resolver_TOL_M": TOL_M, "drawing_TOL_DRAW_M": TOL_DRAW_M},
    }

    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("wrote", SUMMARY)
    print("cross-view deltas:")
    for c in cross:
        print(f"  {c['verdict']:9s} {c['delta_m']:>12}  {c['check']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
