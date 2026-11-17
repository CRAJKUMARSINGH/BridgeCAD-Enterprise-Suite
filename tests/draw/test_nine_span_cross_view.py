"""Nine-span (9 x 10 m) slab GAD — MEASURED cross-view agreement.

WHY THIS FILE EXISTS
    A GAD package is a set of views of ONE physical bridge. If the plan, the
    longitudinal section and the foundation sheet disagree about where a
    support sits or what level a pier cap sits at, the drawing is wrong no
    matter how clean each sheet looks on its own. This module renders the
    nine-span slab card into ``tmp_path`` and then MEASURES the tagged geometry
    back out of the generated DXFs, inverse-mapping sheet coordinates to model
    metres through each sheet's declared scale. Nothing here trusts a label.

WHAT IT FOUND (the "authority" question, answered — and then fixed)
    The catalogue card ``BR-I-2022-002`` carries ``pier_height_m = 6.0`` and an
    OPEN foundation with NO designed footing thickness. As originally wired the
    resolver never received that height, so the record came back LEVEL_CONTROLLED
    / RESOLVED from a fabricated embedment datum and the longitudinal section
    drew the pier base at ``HFL - pier_height_typical_m`` (= 94.0 RL) — 5.0 m
    away from the record's ``shaft_base_rl_m`` of 99.0. Two views, two bridges.

    The contract is now wired honestly and the finding is closed:

      * the model supplies a pier HEIGHT and no supplied founding RL, so the
        authority auto-classifies to HEIGHT_CONTROLLED; the record derives the
        shaft base from that height and PROPOSES the founding RL. With no
        footing thickness it cannot propose one, so it reports
        ``E-MISSING-FOOTING-DEPTH`` and stays UNRESOLVED rather than inventing a
        footing (``test_record_is_height_controlled_and_resolves_the_gap_honestly``);
      * every view that draws the pier base — the long section (Sheet 2) and the
        Side Elevations transverse cut (Sheet 8) — now reads
        ``shaft_base_rl_m`` from the record, so the drawn pier base AGREES with
        the canonical record to the drawing tolerance
        (``test_drawn_pier_base_agrees_with_the_canonical_record``);
      * ``test_spec_fixture_six_metre_shaft_height_is_rejected_as_a_conflict``
        still proves the level-controlled conflict guard is real and fires when a
        supplied height disagrees with a supplied footing.

TOLERANCES
    ``TOL_M = 1e-6`` is the declared pure-resolver tolerance (matches
    ``bridgecad_core.geometry.support_levels.LEVEL_TOLERANCE_M``).
    ``TOL_DRAW_M = 1e-3`` is the drawing-coordinate tolerance: DXF coordinates
    are written in paper millimetres and inverse-mapped to metres, so 1e-3 m
    (= 1 mm at the 1:1 model-space contract) absorbs the paper rounding while
    still catching any real layout error.

SPEC FIXTURE INPUTS ARE ASSUMED, NOT DESIGN GUIDANCE
    The only numbers taken from outside the generated model are the resolver
    fixture used to prove the authority policy (road RL 102.500, wearing 0.075,
    slab 0.500, bearing 0.050 assumed, pedestal 0.150 assumed, cap 0.800,
    footing bottom 97.400, depth 1.000). Every one of those is a *spec fixture
    input, assumed, not design guidance*.
"""

from __future__ import annotations

import importlib.util
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

import ezdxf
import pytest

from bridgecad_catalogue import registry
from bridgecad_catalogue.resolve import resolve
from bridgecad_core.geometry.long_section import (
    compute_long_section_geometry,
    typical_pier_support_level,
)
from bridgecad_core.geometry.support_levels import (
    AuthorityMode,
    BearingTopology,
    FieldSource,
    ResolutionStatus,
    SupportLevelInput,
    resolve_support_levels,
)
from bridgecad_draw import layout_audit
from bridgecad_draw.booklet import generate_package

pytestmark = pytest.mark.draw

REPO = Path(__file__).resolve().parents[2]

#: Declared pure-resolver tolerance (metres) — see support_levels.LEVEL_TOLERANCE_M.
TOL_M = 1e-6
#: Declared drawing-coordinate tolerance (metres); DXF coords are paper mm.
TOL_DRAW_M = 1e-3

#: A1 landscape, matching titleblocks/layout_audit.
_FRAME = (10.0, 10.0, 831.0, 584.0)

#: Layers that carry drawn STRUCTURE (a "view"), as opposed to the border,
#: title block, dimensions and notes. Used to prove a view stays in the frame.
_VIEW_PREFIXES = ("STRUC", "SUPER", "SUB-", "CIVIL", "FOUND", "ABUT")

CARD_ID = "BR-I-2022-002"
SPAN_COUNT = 9
SPAN_LENGTH_M = 10


# ---------------------------------------------------------------------------
# Generator loading (same pattern as tests/pwd/test_booklet_oracle.py)
# ---------------------------------------------------------------------------
def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "_nine_span_pwd_generator", REPO / "scripts" / "generate_all_pwd_gads.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# DXF extraction helpers
# ---------------------------------------------------------------------------
def _read(path: Path):
    return ezdxf.readfile(str(path)).modelspace()


def _lwp_rects(space, layer: str):
    """Axis-aligned bboxes of every LWPOLYLINE on *layer*.

    The ``rectangle`` primitive emits a 4-vertex closed LWPOLYLINE, so the
    min/max of its vertices is the rectangle.
    """
    out = []
    for e in space:
        if e.dxftype() == "LWPOLYLINE" and e.dxf.layer == layer:
            pts = e.get_points("xy")
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            out.append((min(xs), min(ys), max(xs), max(ys)))
    return out


def _horizontal_lines(space, layer: str):
    out = []
    for e in space:
        if e.dxftype() == "LINE" and e.dxf.layer == layer:
            s, en = e.dxf.start, e.dxf.end
            if abs(s.y - en.y) < 1e-9:
                out.append((min(s.x, en.x), s.y, max(s.x, en.x)))
    return out


def _union_bbox(space, prefixes):
    x0 = y0 = float("inf")
    x1 = y1 = float("-inf")
    seen = False
    for e in space:
        if not str(e.dxf.layer).startswith(prefixes):
            continue
        try:
            pts = e.get_points("xy")
        except Exception:  # non-polyline entity
            pts = []
        if not pts:
            p = getattr(e.dxf, "insert", None) or getattr(e.dxf, "start", None)
            pts = [(p[0], p[1])] if p else []
        for (x, y) in pts:
            seen = True
            x0, y0, x1, y1 = min(x0, x), min(y0, y), max(x1, x), max(y1, y)
    return (x0, y0, x1, y1) if seen else None


def _sheet_path(paths, stem: str) -> Path:
    for p in paths:
        if p.stem.endswith(stem):
            return p
    raise AssertionError(f"sheet {stem!r} not generated: {[p.name for p in paths]}")


def _pier_groups(space):
    """[(centre_x, [rects sorted by y0])] for the section's SUB-PIER piers."""
    groups = defaultdict(list)
    for r in _lwp_rects(space, "SUB-PIER"):
        groups[round((r[0] + r[2]) / 2.0, 6)].append(r)
    return [(cx, sorted(rs, key=lambda r: r[1])) for cx, rs in sorted(groups.items())]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def package(tmp_path_factory):
    """Resolve the nine-span slab card and render the full 9-sheet package.

    Everything lands in a pytest-managed tmp directory — the evidence folder
    under ``artifacts/`` is deliberately NOT a dependency.
    """
    gen = _load_generator()
    card = registry.by_id(CARD_ID)
    params = resolve(
        card, {"span_count": str(SPAN_COUNT), "span_length_m": str(SPAN_LENGTH_M)}
    )
    params["id"] = card["id"]
    project = gen._build_project(params)

    out_dir = tmp_path_factory.mktemp("nine_span_cross_view")
    paths = generate_package(project, out_dir, prefix="NINE")
    return {"project": project, "params": params, "out_dir": out_dir, "paths": paths}


@pytest.fixture(scope="module")
def section_model(package):
    """Scales + inverse mappers measured back out of Sheet 2."""
    project = package["project"]
    total_m = float(package["params"]["total_length_m"])
    ls = compute_long_section_geometry(project)
    rec = typical_pier_support_level(project)

    space = _read(_sheet_path(package["paths"], "Sheet2_LongSection"))
    deck = _horizontal_lines(space, "SUPER-DECK")
    sfx0 = min(d[0] for d in deck)
    sfx1 = max(d[2] for d in deck)
    h_mm_per_m = (sfx1 - sfx0) / total_m

    y_soffit = min(d[1] for d in deck)
    hfl_line = _horizontal_lines(space, "CIVIL-HFL")
    assert hfl_line, "long section lost its CIVIL-HFL datum line"
    y_hfl = hfl_line[0][1]
    hfl_rl = float(ls.hfl_rl)
    soffit_rl = float(rec.structural_soffit_rl_m)
    v_mm_per_m = (y_soffit - y_hfl) / (soffit_rl - hfl_rl)

    return {
        "space": space,
        "ls": ls,
        "record": rec,
        "sfx0": sfx0,
        "sfx1": sfx1,
        "h_mm_per_m": h_mm_per_m,
        "v_mm_per_m": v_mm_per_m,
        "y_hfl": y_hfl,
        "hfl_rl": hfl_rl,
        "soffit_rl": soffit_rl,
        "chainage": lambda x: (x - sfx0) / h_mm_per_m,
        "rl": lambda y: hfl_rl + (y - y_hfl) / v_mm_per_m,
    }


# ---------------------------------------------------------------------------
# (a) resolution + generation
# ---------------------------------------------------------------------------
def test_resolved_card_is_nine_spans_of_ten_metres(package):
    p = package["params"]
    assert p["id"] == CARD_ID
    assert p["span_count"] == 9
    assert len(p["span_lengths"]) == 9
    assert all(Decimal(str(v)) == Decimal("10") for v in p["span_lengths"])
    assert p["spans"] == "9×10 m"
    assert float(p["total_length_m"]) == 90.0
    assert p["pier_count"] == 8
    assert p["foundation_type"] == "OPEN"
    assert p["pier_height_m"] == 6.0
    assert not p.get("warnings")


def test_package_renders_all_nine_sheets(package):
    paths = package["paths"]
    assert len(paths) == 9
    for p in paths:
        assert p.exists() and p.stat().st_size > 0


# ---------------------------------------------------------------------------
# (b) MEASURED cross-view agreement
# ---------------------------------------------------------------------------
def test_plan_and_section_support_chainages_agree(package, section_model):
    """The support chainage SET is identical in plan and long section.

    Plan supports are read from the SUB-PIER / SUB-ABUT footprints (rect
    centres, inverse-mapped through ``scale = 1000/denom``). Section supports
    are read from the SUB-PIER rect centres and the abutment front faces.
    """
    project = package["project"]
    total_m = float(package["params"]["total_length_m"])

    # -- plan -----------------------------------------------------------------
    plan = _read(_sheet_path(package["paths"], "Sheet1_Plan"))
    outline = _lwp_rects(plan, "STRUC-OUTLINE")
    assert len(outline) == 1, "plan deck outline should be a single rectangle"
    ox0, ox1 = outline[0][0], outline[0][2]
    plan_mm_per_m = (ox1 - ox0) / total_m

    def plan_ch(x):
        return (x - ox0) / plan_mm_per_m

    plan_piers = sorted(round(plan_ch((r[0] + r[2]) / 2), 6) for r in _lwp_rects(plan, "SUB-PIER"))
    plan_abuts = sorted(round(plan_ch((r[0] + r[2]) / 2), 6) for r in _lwp_rects(plan, "SUB-ABUT"))
    assert len(plan_piers) == 8
    assert len(plan_abuts) == 2

    # -- long section ---------------------------------------------------------
    ch = section_model["chainage"]
    sec_piers = sorted(round(ch(cx), 6) for cx, _ in _pier_groups(section_model["space"]))

    # Abutment support chainage = the FACE nearest the deck (the abutment body
    # extends outward, so its rect centre sits ~0.6 m off the support axis).
    deck_mid = (section_model["sfx0"] + section_model["sfx1"]) / 2.0
    abut_rects = _lwp_rects(section_model["space"], "SUB-ABUT")
    left = [r for r in abut_rects if (r[0] + r[2]) / 2.0 < deck_mid]
    right = [r for r in abut_rects if (r[0] + r[2]) / 2.0 >= deck_mid]

    def _shaft(rs):
        return max(rs, key=lambda r: r[3] - r[1])

    sec_abuts = sorted(round(v, 6) for v in (ch(_shaft(left)[2]), ch(_shaft(right)[0])))
    assert len(sec_piers) == 8

    # -- the assertion --------------------------------------------------------
    expected_piers = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0]
    for a, b in zip(plan_piers, expected_piers):
        assert a == pytest.approx(b, abs=TOL_DRAW_M)
    for a, b in zip(sec_piers, expected_piers):
        assert a == pytest.approx(b, abs=TOL_DRAW_M)
    for a, b in zip(plan_piers, sec_piers):
        assert a == pytest.approx(b, abs=TOL_DRAW_M), f"plan {plan_piers} vs section {sec_piers}"

    # abutments: plan footprint centres and section front faces share {0, 90}
    for a, b in zip(plan_abuts, (0.0, 90.0)):
        assert a == pytest.approx(b, abs=TOL_DRAW_M)
    for a, b in zip(sec_abuts, (0.0, 90.0)):
        assert a == pytest.approx(b, abs=TOL_DRAW_M)

    # the whole support set, measured, is {0, 10, ..., 90}
    expected_supports = [0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0]
    plan_supports = sorted(round(v, 6) for v in (plan_piers + plan_abuts))
    sec_supports = sorted(round(v, 6) for v in (sec_piers + sec_abuts))
    for a, b in zip(plan_supports, expected_supports):
        assert a == pytest.approx(b, abs=TOL_DRAW_M)
    for a, b in zip(sec_supports, expected_supports):
        assert a == pytest.approx(b, abs=TOL_DRAW_M)


def test_measured_span_count_and_total_length(package):
    """Plan supports imply 9 spans of 10 m over 90 m — measured, not labelled."""
    total_m = float(package["params"]["total_length_m"])
    plan = _read(_sheet_path(package["paths"], "Sheet1_Plan"))
    outline = _lwp_rects(plan, "STRUC-OUTLINE")[0]
    plan_mm_per_m = (outline[2] - outline[0]) / total_m

    piers = sorted((r[0] + r[2]) / 2.0 for r in _lwp_rects(plan, "SUB-PIER"))
    abuts = sorted((r[0] + r[2]) / 2.0 for r in _lwp_rects(plan, "SUB-ABUT"))
    supports = sorted(piers + abuts)
    chainages = [(x - outline[0]) / plan_mm_per_m for x in supports]
    spans = [b - a for a, b in zip(chainages, chainages[1:])]

    assert len(spans) == 9
    for s in spans:
        assert s == pytest.approx(SPAN_LENGTH_M, abs=TOL_DRAW_M)
    assert sum(spans) == pytest.approx(90.0, abs=TOL_DRAW_M)


def test_cap_bottom_equals_shaft_top_across_the_views(package, section_model):
    """cap bottom (record + drawn cap rect) == shaft top (record + drawn shaft).

    The value is carried by Sheet 2's ``SUB-PIER`` rectangles: the cap rectangle
    is the widest of the three stacked rects (shaft / cap / seat); its bottom
    edge and the shaft rectangle's top edge are one and the same DXF y.
    """
    space = section_model["space"]
    sec_rl = section_model["rl"]
    record = section_model["record"]

    # pure-resolver equality (exact assignment inside the resolver)
    assert abs(record.cap_bottom_rl_m - record.shaft_top_rl_m) <= Decimal(str(TOL_M))

    groups = _pier_groups(space)
    assert len(groups) == 8
    for _cx, rects in groups:
        assert len(rects) == 3, "each pier should draw shaft + cap + seat"
        shaft, cap = rects[0], rects[1]
        # drawn cap-bottom and drawn shaft-top share one coordinate
        assert cap[1] == pytest.approx(shaft[3], abs=1e-6)
        # and that coordinate is the record's cap bottom / shaft top
        assert sec_rl(cap[1]) == pytest.approx(float(record.cap_bottom_rl_m), abs=TOL_DRAW_M)
        assert sec_rl(shaft[3]) == pytest.approx(float(record.shaft_top_rl_m), abs=TOL_DRAW_M)

    # each drawn cap TOP agrees with its own canonical record's cap top
    ls = section_model["ls"]
    for (_cx, rects), rec, toc in zip(
        groups, ls.support_level_records, ls.pier_top_of_cap_rl_m
    ):
        cap = rects[1]
        assert sec_rl(cap[3]) == pytest.approx(float(rec.cap_top_rl_m), abs=TOL_DRAW_M)
        assert sec_rl(cap[3]) == pytest.approx(float(toc), abs=TOL_DRAW_M)


def test_footing_top_equals_shaft_base_in_the_record(package, section_model):
    """footing top = shaft base — from the canonical record.

    This card's foundation is ``OPEN`` with no designed footing thickness, so the
    contract CANNOT resolve a footing: the record keeps ``footing_top`` equal to
    ``shaft_base`` (the one surface it did resolve) and reports the missing
    thickness instead of inventing a depth. Sheet 4 (foundation) therefore
    renders NO pier-footing geometry at all — the layers ``FOUND-CAP``,
    ``FOUND-PILE``, ``SUB-PIER`` and ``TEXT-LEVEL`` are absent (verified below) —
    and no sheet carries a drawn pier footing from which to re-measure the
    equality. The negative finding on Sheet 4 is asserted explicitly.
    """
    record = section_model["record"]
    assert abs(record.footing_top_rl_m - record.shaft_base_rl_m) <= Decimal(str(TOL_M))
    # The footing CHAIN is fail-closed: bottom and depth stay None, never guessed.
    assert record.footing_bottom_rl_m is None
    assert record.footing_depth_m is None
    assert record.provenance["shaft_base_rl_m"] is FieldSource.DERIVED
    assert record.provenance["footing_bottom_rl_m"] is FieldSource.UNRESOLVED
    assert any(i.code == "E-MISSING-FOOTING-DEPTH" for i in record.issues)

    # Sheet 4 carries no tagged pier-footing content for an OPEN foundation.
    s4 = _read(_sheet_path(package["paths"], "Sheet4_Foundation"))
    present = {e.dxf.layer for e in s4}
    for missing in ("FOUND-CAP", "FOUND-PILE", "SUB-PIER", "TEXT-LEVEL"):
        assert missing not in present, (
            f"unexpected {missing!r} content on Sheet 4 for an OPEN foundation"
        )


# ---------------------------------------------------------------------------
# The authority question — answered, and the gap reported not hidden
# ---------------------------------------------------------------------------
def test_record_is_height_controlled_and_resolves_the_gap_honestly(package):
    """The project build yields an honest HEIGHT_CONTROLLED record, crucially
    UNRESOLVED — not a silent RESOLVED/LEVEL_CONTROLLED one.

    The card supplies ``pier_height_m = 6.0`` and NO supplied founding RL or
    footing thickness. The resolver now receives that height, so it classifies
    the authority as HEIGHT_CONTROLLED, derives the shaft base from the height,
    and — because a footing bottom cannot be proposed without a thickness —
    reports ``E-MISSING-FOOTING-DEPTH`` and keeps the footing chain UNRESOLVED.
    That UNRESOLVED status is the honest flag: the project genuinely lacks a
    designed founding level.
    """
    ls = compute_long_section_geometry(package["project"])
    assert len(ls.support_level_records) == 8
    for rec in ls.support_level_records:
        assert rec.status is ResolutionStatus.UNRESOLVED
        assert rec.authority is AuthorityMode.HEIGHT_CONTROLLED
        assert rec.topology is BearingTopology.SEPARATE_BEARING_PEDESTAL
        assert any(i.code == "E-MISSING-FOOTING-DEPTH" for i in rec.issues)
        assert rec.provenance["shaft_height_m"] is FieldSource.SUPPLIED
        assert rec.provenance["shaft_base_rl_m"] is FieldSource.DERIVED

    rec = typical_pier_support_level(package["project"])
    assert rec.support_id == "P1"
    assert rec.shaft_height_m == Decimal("6.0")
    assert rec.structural_soffit_rl_m == Decimal("101.925")
    assert rec.cap_top_rl_m == Decimal("101.775")
    assert rec.cap_bottom_rl_m == Decimal("100.975")
    assert rec.shaft_base_rl_m == Decimal("94.975")  # cap bottom − the 6 m height
    assert rec.footing_top_rl_m == Decimal("94.975")
    assert rec.footing_bottom_rl_m is None
    assert rec.footing_depth_m is None


def test_spec_fixture_six_metre_shaft_height_is_rejected_as_a_conflict():
    """The authority guard is real: a 6 m supplied shaft height CONFLICTS.

    Fixture inputs are the specification's illustrative fixture — SPEC FIXTURE
    INPUT, ASSUMED, NOT DESIGN GUIDANCE. This proves the only reason the card's
    6.0 m did not conflict above is that it never entered the resolver as a
    shaft height.
    """
    base = dict(
        support_id="P1",
        road_rl_m=Decimal("102.500"),
        wearing_depth_m=Decimal("0.075"),
        structural_depth_m=Decimal("0.500"),
        bearing_depth_m=Decimal("0.050"),
        bearing_depth_assumed=True,
        pedestal_height_m=Decimal("0.150"),
        pedestal_height_assumed=True,
        cap_depth_m=Decimal("0.800"),
        footing_bottom_rl_m=Decimal("97.400"),
        footing_depth_m=Decimal("1.000"),
    )
    ok = resolve_support_levels(SupportLevelInput(**base))
    assert ok.status is ResolutionStatus.RESOLVED
    assert ok.shaft_height_m == Decimal("2.525")

    conflict = resolve_support_levels(
        SupportLevelInput(**base, shaft_height_m=Decimal("6.000"))
    )
    assert conflict.status is ResolutionStatus.CONFLICT
    assert conflict.shaft_height_m == Decimal("2.525")  # derived value survives
    assert any(i.code == "E-CONFLICT-SHAFT-HEIGHT" for i in conflict.issues)


def test_drawn_pier_base_agrees_with_the_canonical_record(package, section_model):
    """FINDING CLOSED: the drawn pier base IS the canonical record's shaft base.

    Sheet 2 now draws the pier base at the record's ``shaft_base_rl_m``
    (94.975 RL = cap bottom − the card's supplied 6.0 m height), NOT at
    ``HFL - pier_height_typical_m`` (the old 94.0 RL datum derived from the
    hydraulic level). The drawn shaft height therefore equals the record's
    supplied height, and the previous 5.0 m view-to-view divergence is gone.
    """
    project = package["project"]
    pier_height = float(project.substructure.pier_height_typical_m)
    assert pier_height == pytest.approx(6.0)

    sec_rl = section_model["rl"]
    groups = _pier_groups(section_model["space"])
    assert groups
    record = section_model["record"]
    record_base_rl = float(record.shaft_base_rl_m)

    last_shaft = None
    for _cx, rects in groups:
        shaft = rects[0]
        last_shaft = shaft
        drawn_base_rl = sec_rl(shaft[1])
        # the drawn base agrees with the canonical record …
        assert drawn_base_rl == pytest.approx(record_base_rl, abs=TOL_DRAW_M)
        # … and is NOT the old HFL − pier_height hydraulic datum
        assert drawn_base_rl != pytest.approx(
            section_model["hfl_rl"] - pier_height, abs=0.05
        )

    # drawn shaft height (base -> cap bottom) equals the record's shaft height
    drawn_height = sec_rl(last_shaft[3]) - sec_rl(last_shaft[1])
    assert drawn_height == pytest.approx(float(record.shaft_height_m), abs=TOL_DRAW_M)
    assert drawn_height == pytest.approx(pier_height, abs=TOL_DRAW_M)
    assert float(record.shaft_base_rl_m) == pytest.approx(94.975, abs=TOL_M)


# ---------------------------------------------------------------------------
# (c) LAYOUT COLLISION CHECKS via bridgecad_draw.layout_audit
# ---------------------------------------------------------------------------
def test_layout_audit_frame_scales_and_text_floor(package):
    project = package["project"]
    layout_audit.set_enabled(True)
    try:
        audit = layout_audit.collect(project)
    finally:
        # Never leave the audit forced on for the rest of the session.
        layout_audit.set_enabled(None)

    assert audit.rendered, audit.error
    assert audit.error == ""

    # 1. no entity outside the printable frame, on ANY rendered sheet
    assert audit.outside_frame == []

    # 2. every printed scale is a rung of the standard ladder (ISO 5455)
    assert audit.printed_scales, "no declared scale found on any sheet"
    for sheet, denom in audit.printed_scales:
        assert layout_audit.scale_on_ladder(denom), f"{sheet} printed 1:{denom}"

    # 3. text-size floor (IRC hard floor 1.8 mm)
    heights = [b.height for b in audit.text_boxes if b.height > 0]
    assert heights
    assert min(heights) >= 1.8 - 1e-6

    # 4. every text box sits inside the printable frame
    x0, y0, x1, y1 = _FRAME
    for b in audit.text_boxes:
        assert b.x0 >= x0 - 1.0, (b.sheet, b.text, b.x0)
        assert b.y0 >= y0 - 1.0, (b.sheet, b.text, b.y0)
        assert b.x1 <= x1 + 1.0, (b.sheet, b.text, b.x1)
        assert b.y1 <= y1 + 1.0, (b.sheet, b.text, b.y1)


def test_layout_view_rectangles_stay_inside_the_frame(package):
    """Every drawn view (structure layers) is inside the printable frame."""
    x0, y0, x1, y1 = _FRAME
    for path in package["paths"]:
        space = _read(path)
        view = _union_bbox(space, _VIEW_PREFIXES)
        if view is None:  # BOQ / reinforcement sheets carry no structural view
            continue
        vx0, vy0, vx1, vy1 = view
        assert vx0 >= x0 - 1.0, (path.name, vx0)
        assert vy0 >= y0 - 1.0, (path.name, vy0)
        assert vx1 <= x1 + 1.0, (path.name, vx1)
        assert vy1 <= y1 + 1.0, (path.name, vy1)


def test_layout_detected_text_overlaps_stay_within_the_estimator_bound(package):
    """Honest reporting of ``BBox`` text collisions.

    ``layout_audit.BBox`` ESTIMATES a text width as ``0.6 * height * len(text)``
    which over-estimates for short labels with wide gaps, so a handful of false
    collisions is expected and a zero-overlap assertion would be dishonest.
    We therefore assert the detected set stays a small fraction of all text
    pairs (so a genuinely broken layout still fails) and record the count.
    NOTE / MISSING CONTENT: ``layout_audit`` exposes TEXT boxes only — it does
    not surface separate "view", "title-block" or "notes" rectangles, so the
    region-level check is done from the rendered DXFs
    (``test_layout_view_rectangles_stay_inside_the_frame``).
    """
    project = package["project"]
    layout_audit.set_enabled(True)
    try:
        audit = layout_audit.collect(project)
    finally:
        layout_audit.set_enabled(None)

    by_sheet = defaultdict(list)
    for b in audit.text_boxes:
        by_sheet[b.sheet].append(b)

    for sheet in sorted(by_sheet):
        boxes = by_sheet[sheet]
        total_pairs = len(boxes) * (len(boxes) - 1) // 2
        overlaps = sum(
            1
            for i in range(len(boxes))
            for j in range(i + 1, len(boxes))
            if boxes[i].overlaps(boxes[j])
        )
        ceiling = max(2, int(0.05 * total_pairs))
        assert overlaps <= ceiling, (
            f"{sheet}: {overlaps} text collisions of {total_pairs} pairs "
            f"(ceiling {ceiling})"
        )
