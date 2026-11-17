"""Task driver: generate the nine-span (9x10 m) slab GAD evidence.

A bare run reproduces the honest-default fixture at
``artifacts/gad-acceptance/nine_span_slab/<HEAD>/``.  ``--fixture`` / ``--set``
re-resolve the same card with explicit inputs, and ``--all-variants`` writes the
whole variant-validation matrix plus a ``variant-validation.json`` roll-up.

For every generated package this driver also emits the machine-checkable
evidence the acceptance spec asks for:

* ``params.resolved.json``  — the resolved dial set plus the canonical named RL
  chain (written by ``generate_all_pwd_gads.generate_one``);
* ``layout-audit.json``     — measured regions, zones, text floor and the
  pass/fail of every layout sub-check;
* ``quality.json``          — the fail-closed gate manifest (bridgecad_qa).

Allowed writer: artifacts under artifacts/gad-acceptance/. Read-only elsewhere.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
os.environ["SKIP_PNG"] = "1"

for _pkg in ["bridgecad-catalogue", "bridgecad-core", "bridgecad-draw",
             "bridgecad-qa"]:
    _p = REPO / "packages" / _pkg
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

CARD_ID = "BR-I-2022-002"

#: Explicitly supplied inputs for the foundation stack.
#:
#: ``footing_bottom_rl_m`` is the EXPLICITLY SUPPLIED founding RL; arithmetic
#: consistency has been verified by the owner (see review note dated 2026-11-15:
#: footing top = 93.425 + 1.500 = 94.925 m, shaft top = 94.925 + 6.000 =
#: 100.925 m, cap top = 100.925 + 0.800 = 101.725 m, soffit = 101.725 + 0.150
#: + 0.050 = 101.925 m, road = 101.925 + 0.500 + 0.075 = 102.500 m).
#: This is **not** an engineering approval — it is an explicitly supplied,
#: geometrically consistent foundation stack.  Structural adequacy is a separate
#: human verdict recorded via Gate.ENGINEERING_REVIEW.
#:
#: ``pile_cap_thickness_mm`` is the (open) footing thickness.  Together with
#: ``footing_bottom_rl_m`` they switch the canonical §3 contract to
#: LEVEL_CONTROLLED and the shaft height is DERIVED.  The supplied founding RL
#: is chosen so the derived height equals the card's own 6.0 m pier height,
#: i.e. the two declared inputs AGREE — that is what makes the stack resolved
#: rather than conflicted.  The remaining dials are declared so no level in the
#: chain is left ASSUMED:
#:   wearing 75 mm   → matches the catalogue resolver's own WEARING_COAT_M
#:                     (0.075 m), so derived soffit == supplied soffit
#:   bearing 50 mm   → a real elastomeric unit, not an implicit zero
#:   pedestal 150 mm → the model default, declared
#:   cap depth 800 mm→ the model default, declared
#:   footing 1500 mm → the open-footing thickness
SUPPLIED_STACK = {
    "wearing_coat_thickness_mm": "75",
    "bearing_depth_mm": "50",
    "pier_pedestal_height_m": "0.15",
    "pier_cap_depth_m": "0.8",
    "pile_cap_thickness_mm": "1500",
    "footing_bottom_rl_m": "93.425",
}

BASE = {"span_count": "9", "span_length_m": "10"}

#: name → (overrides, what the fixture is for)
VARIANTS: list[tuple[str, dict, str]] = [
    ("nine_span_slab", {},
     "HONEST DEFAULT: the card supplies only a 6.0 m pier HEIGHT; no supplied "
     "founding RL and no footing thickness exist, so the contract stays "
     "HEIGHT_CONTROLLED / UNRESOLVED with E-MISSING-FOOTING-DEPTH."),
    ("nine_span_slab_resolved", dict(SUPPLIED_STACK),
     "DELIVERABLE: explicitly supplied, geometrically consistent founding RL + "
     "footing thickness consistent with the card's 6.0 m pier ⇒ "
     "LEVEL_CONTROLLED / RESOLVED; every level SUPPLIED or DERIVED, none ASSUMED. "
     "Structural adequacy is a separate engineering verdict."),
    ("nine_span_slab_conflict", {**SUPPLIED_STACK, "pier_height_m": "8.0"},
     "NEGATIVE CONTROL: the same founding RL with a conflicting 8.0 m pier "
     "height must be rejected (E-CONFLICT-SHAFT-HEIGHT), never forced. "
     "Generation is aborted before any sheets are written — partial output "
     "from a rejected run must not appear as a deliverable package."),
    ("seven_span_slab_resolved", {"span_count": "7", **SUPPLIED_STACK},
     "SPAN VARIANT: the resolved stack must not depend on the span count."),
    ("nine_span_slab_skew15_resolved", {"skew_deg": "15", **SUPPLIED_STACK},
     "SKEW VARIANT: the resolved stack must survive a 15° skew."),
]


def _load_generator():
    path = REPO / "scripts" / "generate_all_pwd_gads.py"
    spec = importlib.util.spec_from_file_location("gen_all_pwd", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _parse_sets(items: list[str]) -> dict:
    return {k: v for k, v in (s.split("=", 1) for s in items)}


def _head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(REPO), text=True).strip()


def _count_annotation_overlaps(audit: "object") -> int:
    """Count label-label, dimension-geometry and schedule text-pair overlaps.

    Reserved-zone checks (clipping, title-block intrusion, notes intrusion) do
    not detect these; they require comparing text boxes against each other and
    against drawn geometry.  The count is reported in the manifest so a reviewer
    sees the number; it is *not* yet a gate pass/fail because per-view bounding
    rectangles are not declared, which means the estimator may flag adjacent
    labels in different views as colliding.

    Returns the number of overlapping text-box pairs across all sheets, or -1
    if the audit did not render.
    """
    from bridgecad_draw.layout_audit import BBox

    if not getattr(audit, "rendered", False):
        return -1
    boxes = getattr(audit, "text_boxes", [])
    count = 0
    for i, a in enumerate(boxes):
        for b in boxes[i + 1 :]:
            if a.sheet == b.sheet and a.overlaps(b):
                count += 1
    return count


def _layout_payload(project) -> tuple[dict, object]:
    """Measure the layout and return (json, LayoutChecks)."""
    from bridgecad_draw import layout_audit as LA

    LA.set_enabled(True)
    try:
        audit = LA.collect(project)
    finally:
        LA.set_enabled(None)
    checks = LA.layout_checks(audit)
    overlap_count = _count_annotation_overlaps(audit)

    def _regions(d):
        return {k: list(v.as_tuple()) for k, v in d.items()}

    payload = {
        "rendered": audit.rendered,
        "error": audit.error,
        "entities_outside_frame": len(audit.outside_frame),
        "outside_frame": audit.outside_frame,
        "printed_scales": sorted({d for _, d in audit.printed_scales}),
        "sheet_regions": _regions(audit.sheet_regions),
        "frame_regions": _regions(audit.frame_regions),
        "title_block_regions": _regions(audit.title_block_regions),
        "notes_regions": _regions(audit.notes_regions),
        "title_block_intrusions": audit.title_block_intrusions,
        "notes_intrusions": audit.notes_intrusions,
        # Annotation-overlap count: label-label / dimension-geometry / schedule.
        # Not yet a gate — view rectangles are not declared, so the estimator
        # may flag cross-view adjacency.  Present for reviewer inspection.
        "annotation_overlap_count": overlap_count,
        "annotation_overlap_note": (
            "measured label-label text-box pairs; not a gate pass/fail until "
            "per-view bounding rectangles are declared"
        ),
        "checks": {
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
    return payload, checks, overlap_count


def _content_report(dxf_dir, params, project) -> "object":
    """Measure the required-content manifest against the published package.

    The manifest (``bridgecad_qa/required_content.json``) is the reviewed
    statement of what each drawing area must contain; a requirement is credited
    only when it is declared IMPLEMENTED *and* measured present in the DXF, so a
    declared-but-unbuilt feature fails the gate rather than passing on a
    declaration.

    ``abutment_shape_family`` is taken from the **resolved** ``AbutmentType`` on
    the built project — the very object the renderers read (``sheet5`` opens with
    ``sub = project.substructure``).  Deriving it from the registry's raw
    abutment token instead would hand ``family_for()`` a value the draw path
    never passes: the registry token ``"OPEN"`` is not a shape-family name and
    falls through to ``battered``, which would declare the battered area
    applicable to a sheet that was drawn as a cantilever abutment — and would
    hide the cantilever area's own requirements.
    """
    from bridgecad_core.geometry.abutment_profiles import family_for
    from bridgecad_qa.required_content import evaluate

    p = dict(params)
    abutment_type = getattr(getattr(project, "substructure", None),
                            "abutment_type", None)
    if abutment_type is not None:
        p["abutment_shape_family"] = family_for(abutment_type)
    return evaluate(dxf_dir, p)


def _quality(*, gen, fixture: str, commit: str, sheets, checks, records,
             generated: bool, overlap_count: int = -1,
             content: "object" = None) -> "object":
    """Build the fail-closed gate manifest from the measured evidence."""
    from bridgecad_qa.quality_manifest import Gate, QualityManifest, Verdict

    m = QualityManifest(fixture=fixture, commit=commit,
                        annotation_overlap_count=overlap_count)

    statuses = {r.status.value for r in records}
    authorities = {r.authority.value for r in records}

    m.set(Gate.GENERATION, Verdict.SUCCEEDED if generated else Verdict.FAILED,
          "" if generated else "the package did not generate")

    if records and statuses <= {"RESOLVED"}:
        m.set(Gate.MODEL_VALIDATION, Verdict.PASSED,
              f"all {len(records)} supports RESOLVED ({'/'.join(sorted(authorities))})")
    elif "CONFLICT" in statuses:
        m.set(Gate.MODEL_VALIDATION, Verdict.FAILED, "at least one support CONFLICT")
    else:
        m.set(Gate.MODEL_VALIDATION, Verdict.UNRESOLVED,
              f"support statuses: {sorted(statuses) or ['none resolved']}")
    for r in records:
        for i in r.issues:
            m.add_issue(Gate.MODEL_VALIDATION, i.code, i.message, r.support_id)

    # The pure-resolver interfaces must connect on every support.
    defects = []
    for r in records:
        if r.shaft_top_rl_m is not None and r.cap_bottom_rl_m != r.shaft_top_rl_m:
            defects.append(f"{r.support_id}: cap_bottom != shaft_top")
        if (r.footing_top_rl_m is not None and r.shaft_base_rl_m is not None
                and r.footing_top_rl_m != r.shaft_base_rl_m):
            defects.append(f"{r.support_id}: footing_top != shaft_base")
        if (r.footing_bottom_rl_m is not None and r.footing_depth_m is not None
                and r.footing_top_rl_m != r.footing_bottom_rl_m + r.footing_depth_m):
            defects.append(f"{r.support_id}: footing_top != footing_bottom + depth")
    if defects:
        m.set(Gate.GEOMETRY_CONTRACT, Verdict.FAILED, "; ".join(defects))
        for d in defects:
            m.add_issue(Gate.GEOMETRY_CONTRACT, "E-CHAIN-BREAK", d)
    else:
        m.set(Gate.GEOMETRY_CONTRACT, Verdict.PASSED,
              f"{len(records)} supports: cap_bottom=shaft_top, footing_top=shaft_base, "
              "footing_top=footing_bottom+depth")

    # Required content is decided by the versioned manifest, not by sheet count:
    # nine non-trivial DXF files cannot establish that the details, dimensions
    # and schedules each drawing area requires are actually present.  The
    # entity-count completeness check is retained as a precondition and both
    # must hold before the gate passes.
    content_issues = gen._check_completeness(sheets)
    if not generated:
        m.set(Gate.REQUIRED_CONTENT, Verdict.FAILED,
              "package is incomplete: generation failed")
    else:
        reasons = []
        if content_issues:
            reasons.append(f"{len(content_issues)} completeness issue(s)")
            for i in content_issues:
                m.add_issue(Gate.REQUIRED_CONTENT, "E-SHEET-CONTENT", i)
        if content is None:
            reasons.append("required-content manifest was not measured")
        elif not content.passed:
            reasons.append(content.summary())
            for f in content.failures:
                m.add_issue(
                    Gate.REQUIRED_CONTENT, "E-REQUIRED-CONTENT",
                    f"{f.id} declared {f.declared_status}: {f.detail}", f.area)
        if reasons:
            m.set(Gate.REQUIRED_CONTENT, Verdict.FAILED, "; ".join(reasons))
        else:
            m.set(Gate.REQUIRED_CONTENT, Verdict.PASSED,
                  f"{content.summary()}; {len(sheets)} sheets each "
                  f">= {gen.MIN_ENTITIES} entities")

    m.set(Gate.LAYOUT, Verdict.PASSED if checks.passed else Verdict.FAILED,
          "title-block/notes zones clear, frame, scale ladder and text floor all hold"
          if checks.passed else "a layout sub-check failed")
    if not checks.passed:
        m.add_issue(Gate.LAYOUT, "E-LAYOUT", "layout_checks.passed is False",
                    json.dumps(checks.details, default=str))

    # The reference booklet contains no nine-span sheet, so an exact nine-span
    # reproduction claim cannot be made.  That limitation does NOT prevent
    # checking the applicable booklet conventions and details alongside the
    # independently verified nine-span geometry — that comparison is PARTIAL
    # (artifacts/reference-overlay/comparison.json).  What is still missing is
    # the calibrated per-reference-page comparison of spec §6 (PDF filename and
    # hash, page, sheet/drawing number, revision, drawing family), which needs
    # the approved reference PDF.  The required-content manifest
    # (bridgecad_qa/required_content.json) is measured against the *generated*
    # package by the REQUIRED_CONTENT gate above; it is not a substitute for
    # that reference comparison.
    m.set(Gate.REFERENCE_FIDELITY, Verdict.BLOCKED,
          "reference booklet contains no nine-span sheet — exact nine-span "
          "reproduction claim not possible; booklet convention + independently "
          "verified geometry comparison is PARTIAL and the calibrated "
          "per-reference-page comparison (§6) awaits the approved reference PDF "
          "(artifacts/reference-overlay/comparison.json)")
    m.add_issue(Gate.REFERENCE_FIDELITY, "E-NO-NINE-SPAN-REFERENCE",
                "reference booklet contains no nine-span sheet; "
                "convention/geometry comparison is PARTIAL")

    m.set(Gate.ENGINEERING_REVIEW, Verdict.PENDING,
          "structural/geotechnical adequacy is a human verdict; not claimed here")
    return m


def _top_of_deck_rl(project) -> float:
    """The road RL the §3 contract anchors every derived level to.

    Mirrors ``compute_long_section_geometry``: the project master's road level
    when declared, otherwise the soffit plus the declared deck build-up.
    """
    pm = project.project_master
    hd = project.hydraulic_data
    ss = project.superstructure
    if pm.road_level_rl_m is not None:
        return float(pm.road_level_rl_m)
    soffit_rl = (
        float(hd.actual_soffit_level_m) if hd.actual_soffit_level_m is not None else 0.0
    )
    return (
        soffit_rl
        + (float(ss.girder_depth_mm) / 1000.0 if ss.girder_depth_mm else 0.0)
        + (float(ss.deck_thickness_mm) / 1000.0 if ss.deck_thickness_mm else 0.0)
        + (float(ss.wearing_coat_thickness_mm) / 1000.0
           if ss.wearing_coat_thickness_mm else 0.0)
    )


def _support_records(project) -> list:
    """The canonical per-support records, recovered even from a CONFLICT.

    ``compute_long_section_geometry`` raises on a CONFLICT so the DRAWING path
    fails closed — two views can never disagree. The evidence driver still
    needs the rejected record itself: rejecting the fixture is the negative
    control's *result*, not a driver crash. So a CONFLICT is caught and the
    per-support resolver is re-run directly to recover the records for
    reporting. Nothing about this fallback reaches a rendering sheet.
    """
    from bridgecad_core.geometry.long_section import (
        _pier_support_level_input,
        compute_long_section_geometry,
    )
    from bridgecad_core.geometry.support_levels import resolve_support_levels

    try:
        return list(compute_long_section_geometry(project).support_level_records)
    except ValueError:
        gi = project.geometry_input
        hd = project.hydraulic_data
        top_of_deck_rl = _top_of_deck_rl(project)
        soffit = (
            float(hd.actual_soffit_level_m)
            if hd.actual_soffit_level_m is not None
            else None
        )
        n_piers = max(len(gi.span_lengths_m) - 1, 0)
        return [
            resolve_support_levels(
                _pier_support_level_input(
                    project,
                    support_id=f"P{i + 1}",
                    top_of_deck_rl=top_of_deck_rl,
                    soffit_rl=soffit,
                )
            )
            for i in range(n_piers)
        ]


def _generate(fixture: str, overrides: dict, commit: str, *, verbose=True) -> dict:
    """Generate one fixture and write its package + evidence. Returns a summary.

    Generation is transactional: for a fixture that the conflict guard rejects,
    no DXF files reach the final output directory.  Instead a ``FAILED-RUN/``
    sub-directory is created with a ``failure-report.json`` that records what
    was rejected and why.  This prevents partial output from a failed run mixing
    with a previous successful package, and prevents it appearing as a
    deliverable without an explicit label.
    """
    import tempfile
    import shutil
    from bridgecad_catalogue import registry
    from bridgecad_catalogue import resolve as R

    gen = _load_generator()
    card = registry.by_id(CARD_ID)
    ov = {**BASE, **overrides}
    p = R.resolve(card, ov)
    p["id"] = card["id"]
    for w in p.warnings:
        if verbose:
            print(f"  [WARN] {w}")

    out_root = REPO / "artifacts" / "gad-acceptance" / fixture
    out_root.mkdir(parents=True, exist_ok=True)

    # Validate before generation: build the project and resolve all support
    # records.  A CONFLICT here means the resolver has already rejected the
    # inputs — abort before writing any DXF to the destination.
    project = gen._build_project(p)
    records = _support_records(project)
    statuses = {r.status.value for r in records}

    if "CONFLICT" in statuses:
        # Write evidence to a clearly labelled failed-run directory; nothing
        # goes to the commit-keyed directory that a downstream reader might
        # mistake for a successful package.  The directory is cleared first so
        # evidence from an earlier run can never be mistaken for this one's.
        failed_dir = out_root / "FAILED-RUN"
        if failed_dir.exists():
            shutil.rmtree(failed_dir)
        failed_dir.mkdir(parents=True, exist_ok=True)
        # A rejected run must not leave a package-looking directory behind: an
        # earlier run that died mid-generation could otherwise leave partial
        # sheets in a commit-keyed directory that reads as a success.
        stale = out_root / commit
        if stale.exists():
            shutil.rmtree(stale)
        failure = {
            "fixture": fixture,
            "commit": commit,
            "overrides": ov,
            "generated": False,
            "message": "REJECTED — conflict in support records; no DXF written",
            "failed_run_label": (
                "FAILED-RUN: this directory contains evidence from a rejected "
                "generation attempt.  It is not a deliverable package."
            ),
            "statuses": sorted({r.status.value for r in records}),
            "authorities": sorted({r.authority.value for r in records}),
            "sheets": [],
            "supports": [
                {"support_id": r.support_id, "status": r.status.value,
                 "authority": r.authority.value,
                 "issue_codes": sorted({i.code for i in r.issues})}
                for r in records
            ],
        }
        (failed_dir / "failure-report.json").write_text(
            json.dumps(failure, indent=2, default=str), encoding="utf-8")
        if verbose:
            print(f"  REJECTED — conflict; evidence written to {failed_dir}")
            for r in records:
                print(f"    {r.support_id}: {r.status.value} "
                      f"{sorted({i.code for i in r.issues})}")
        # Build a minimal quality manifest for the invariant-check roll-up.
        from bridgecad_qa.quality_manifest import Gate, QualityManifest, Verdict
        m = QualityManifest(fixture=fixture, commit=commit)
        m.set(Gate.GENERATION, Verdict.FAILED,
              "conflict in support records; generation aborted before any DXF written")
        m.set(Gate.MODEL_VALIDATION, Verdict.FAILED,
              "at least one support CONFLICT")
        for r in records:
            for i in r.issues:
                m.add_issue(Gate.MODEL_VALIDATION, i.code, i.message, r.support_id)
        m.set(Gate.REFERENCE_FIDELITY, Verdict.BLOCKED,
              "reference booklet contains no nine-span sheet")
        m.set(Gate.ENGINEERING_REVIEW, Verdict.PENDING,
              "structural/geotechnical adequacy is a human verdict; not claimed here")
        (failed_dir / "quality.json").write_text(
            json.dumps(m.to_json(), indent=2), encoding="utf-8")
        failure["quality"] = m.to_json()
        return failure

    # Generation path: use a temporary directory and publish only on success.
    tmp_root = Path(tempfile.mkdtemp(prefix="bridgecad_gen_"))
    try:
        label, ok, msg = gen.generate_one(p, tmp_root, commit)
        tmp_dir = tmp_root / commit
        if verbose:
            print(f"  generate_one -> {msg}")

        if ok:
            # Publish: move from temp to the final destination.
            out_dir = out_root / commit
            if out_dir.exists():
                shutil.rmtree(out_dir)
            shutil.copytree(tmp_dir, out_dir)
        else:
            # Generation failed mid-way (some sheets may exist in tmp_dir).
            # Publish only as clearly labelled failed-run evidence.
            failed_dir = out_root / "FAILED-RUN"
            if failed_dir.exists():
                shutil.rmtree(failed_dir)
            shutil.copytree(tmp_dir, failed_dir)
            (failed_dir / "FAILED-RUN.txt").write_text(
                "FAILED-RUN: this directory contains partial output from a "
                "generation that did not complete.  It is not a deliverable "
                f"package.\nfixture={fixture}\ncommit={commit}\nmessage={msg}\n",
                encoding="utf-8",
            )
            if verbose:
                print(f"  FAILED — partial output labelled at {failed_dir}")
            out_dir = failed_dir
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)

    layout_json, checks, overlap_count = _layout_payload(project)
    (out_dir / "layout-audit.json").write_text(
        json.dumps(layout_json, indent=2, default=str), encoding="utf-8")

    sheets = sorted(out_dir.glob("*.dxf"))
    content = _content_report(out_dir, p, project)
    (out_dir / "required-content.json").write_text(
        json.dumps(content.to_json(), indent=2, default=str), encoding="utf-8")
    manifest = _quality(gen=gen, fixture=fixture, commit=commit, sheets=sheets,
                        checks=checks, records=records, generated=ok,
                        overlap_count=overlap_count, content=content)
    (out_dir / "quality.json").write_text(
        json.dumps(manifest.to_json(), indent=2), encoding="utf-8")

    result = {
        "fixture": fixture,
        "commit": commit,
        "overrides": ov,
        "generated": ok,
        "message": msg,
        "package_dir": str(out_dir),
        "supports": [
            {"support_id": r.support_id, "status": r.status.value,
             "authority": r.authority.value,
             "cap_top_rl_m": str(r.cap_top_rl_m),
             "cap_bottom_rl_m": str(r.cap_bottom_rl_m),
             "shaft_base_rl_m": str(r.shaft_base_rl_m),
             "shaft_height_m": str(r.shaft_height_m),
             "issue_codes": sorted({i.code for i in r.issues})}
            for r in records
        ],
        "statuses": sorted({r.status.value for r in records}),
        "authorities": sorted({r.authority.value for r in records}),
        "sheets": [s.name for s in sheets],
        "layout_checks_passed": checks.passed,
        "required_content": content.to_json(),
        "required_content_failures": [f.to_json() for f in content.failures],
        "quality": manifest.to_json(),
    }
    if verbose:
        for r in records:
            print(f"  {r.support_id}: {r.status.value}/{r.authority.value} "
                  f"cap_bottom={r.cap_bottom_rl_m} shaft_base={r.shaft_base_rl_m} "
                  f"h={r.shaft_height_m} {sorted({i.code for i in r.issues})}")
        print(f"  layout_checks.passed = {checks.passed}")
        print(f"  annotation_overlap_count = {overlap_count}")
        print(f"  {content.summary()}")
        print(f"  quality: generation_gates_passed={manifest.generation_gates_passed} "
              f"quality_and_layout_passed={manifest.quality_and_layout_passed} "
              f"accepted={manifest.accepted}")
        print(f"  quality.json -> {out_dir / 'quality.json'}")
    return result


def _run_variants(commit: str) -> int:
    results = []
    for name, ov, why in VARIANTS:
        print(f"\n=== {name} ===\n  {why}")
        results.append(_generate(name, ov, commit))

    # ── invariant checks across the matrix ──────────────────────────────────
    checks = []
    by_name = {r["fixture"]: r for r in results}

    def _chk(name, condition, detail):
        checks.append({"check": name, "passed": bool(condition), "detail": detail})

    resolved = by_name["nine_span_slab_resolved"]
    _chk("deliverable: every support RESOLVED",
         resolved["statuses"] == ["RESOLVED"], f"statuses={resolved['statuses']}")
    _chk("deliverable: quality/layout gates pass",
         resolved["quality"]["generation_gates_passed"] is True,
         f"quality={resolved['quality']['status']}")
    _chk("deliverable: layout gate passes",
         resolved["layout_checks_passed"] is True, "layout_checks.passed")
    _chk("deliverable: level-controlled authority",
         resolved["authorities"] == ["LEVEL_CONTROLLED"],
         f"authorities={resolved['authorities']}")

    # Required content is measured against the versioned manifest.  Every
    # applicable requirement is now declared IMPLEMENTED *and* measured present
    # — the last declared gap (RC-RFT-05, the bar-arrangement geometry on
    # Sheet 9) has been built and is measured as drawn linework — so the
    # REQUIRED_CONTENT gate passes.  Two things are still asserted, because a
    # package that "passes" the content gate is not thereby accepted:
    #
    #  * every applicable requirement is credited, so a requirement quietly
    #    dropped from a sheet fails here rather than reading as a pass;
    #  * acceptance is still withheld — reference fidelity is BLOCKED (the
    #    booklet carries no nine-span sheet) and the engineering review is
    #    PENDING — so `accepted` must remain False.
    rc = resolved["required_content"]
    _chk("deliverable: required-content manifest measured",
         rc["manifest_version"] == "1.0.0" and rc["applicable"] > 0,
         f"applicable={rc['applicable']} of {rc['applicable'] + rc['not_applicable']}")
    _chk("deliverable: every applicable requirement is credited",
         not resolved["required_content_failures"] and rc["passed"] is True,
         "unmet: " + ", ".join(
             f"{f['id']}({f['declared_status']})"
             for f in resolved["required_content_failures"]))
    _chk("deliverable: required-content gate passes",
         resolved["quality"]["required_content"] == "PASSED"
         and resolved["quality"]["quality_and_layout_passed"] is True,
         f"unmet={rc['failures']} gate={resolved['quality']['required_content']} "
         f"quality_and_layout_passed="
         f"{resolved['quality']['quality_and_layout_passed']}")
    _chk("deliverable: acceptance withheld pending reference + review",
         resolved["quality"]["accepted"] is False
         and resolved["quality"]["reference_fidelity"] == "BLOCKED"
         and resolved["quality"]["engineering_review"] == "PENDING",
         f"accepted={resolved['quality']['accepted']} "
         f"reference_fidelity={resolved['quality']['reference_fidelity']} "
         f"engineering_review={resolved['quality']['engineering_review']}")

    default = by_name["nine_span_slab"]
    _chk("default stays honestly UNRESOLVED",
         default["statuses"] == ["UNRESOLVED"]
         and "E-MISSING-FOOTING-DEPTH" in {
             c for s in default["supports"] for c in s["issue_codes"]},
         f"statuses={default['statuses']}")

    conflict = by_name["nine_span_slab_conflict"]
    _chk("conflicting founding RL / pier height is rejected",
         conflict["statuses"] == ["CONFLICT"]
         and all("E-CONFLICT-SHAFT-HEIGHT" in s["issue_codes"]
                 for s in conflict["supports"]),
         f"statuses={conflict['statuses']} codes="
         f"{sorted({c for s in conflict['supports'] for c in s['issue_codes']})}")

    for name in ("seven_span_slab_resolved", "nine_span_slab_skew15_resolved"):
        r = by_name[name]
        _chk(f"{name}: every support RESOLVED, gates pass",
             r["statuses"] == ["RESOLVED"]
             and r["quality"]["generation_gates_passed"] is True,
             f"statuses={r['statuses']} layout={r['layout_checks_passed']}")

    # the resolved chain must be span-invariant
    base_supports = {s["cap_bottom_rl_m"] for s in resolved["supports"]}
    span_supports = {s["cap_bottom_rl_m"] for s in by_name["seven_span_slab_resolved"]["supports"]}
    _chk("cap_bottom RL is span-invariant",
         base_supports == span_supports,
         f"9-span={sorted(base_supports)} 7-span={sorted(span_supports)}")

    payload = {
        "commit": commit,
        "card_id": CARD_ID,
        "base_overrides": BASE,
        "supplied_stack": SUPPLIED_STACK,
        "variants": results,
        "invariant_checks": checks,
        "all_checks_passed": all(c["passed"] for c in checks),
    }
    out = REPO / "artifacts" / "gad-acceptance" / "variant-validation.json"
    out.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"\nwrote {out}")
    print("invariant checks:")
    for c in checks:
        print(f"  {'PASS' if c['passed'] else 'FAIL':4s} {c['check']} — {c['detail']}")
    return 0 if payload["all_checks_passed"] else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="_gen_nine_span")
    ap.add_argument("--fixture", default="nine_span_slab")
    ap.add_argument("--set", action="append", default=[], metavar="key=value")
    ap.add_argument("--all-variants", action="store_true")
    ap.add_argument("--diagnostics", action="store_true",
                    help="also print the spec-fixture conflict proof")
    a = ap.parse_args(argv)

    head = _head()
    print("HEAD =", head)

    if a.all_variants:
        return _run_variants(head)

    result = _generate(a.fixture, _parse_sets(a.set), head)

    if a.diagnostics:
        from bridgecad_core.geometry.support_levels import (
            AuthorityMode, SupportLevelInput, resolve_support_levels,
        )
        fixture = SupportLevelInput(
            support_id="fixture", road_rl_m=Decimal("102.500"),
            wearing_depth_m=Decimal("0.075"), structural_depth_m=Decimal("0.500"),
            bearing_depth_m=Decimal("0.050"), bearing_depth_assumed=True,
            pedestal_height_m=Decimal("0.150"), pedestal_height_assumed=True,
            cap_depth_m=Decimal("0.800"), footing_bottom_rl_m=Decimal("97.400"),
            footing_depth_m=Decimal("1.000"), authority=AuthorityMode.LEVEL_CONTROLLED,
        )
        ok = resolve_support_levels(fixture)
        print("FIXTURE (no height) status=%s" % ok.status.value)
        conflict = resolve_support_levels(
            SupportLevelInput(**{**fixture.__dict__, "shaft_height_m": Decimal("6.000")}))
        print("FIXTURE (+6.0 m supplied) status=%s issues=%s" % (
            conflict.status.value, [(i.code, i.message) for i in conflict.issues]))

    return 0 if result["generated"] else 1


if __name__ == "__main__":
    sys.exit(main())
