"""The required-content manifest must credit nothing it cannot see.

The acceptance spec (§4) defines completeness by *required content*, not sheet
count: nine DXF files of non-trivial size, a matching named RL chain and a clean
layout-zone check do not prove the details, dimensions and schedules are on the
sheets.  These tests pin the three properties that make the ``REQUIRED_CONTENT``
gate honest:

* double credit — a requirement counts only when it is declared ``IMPLEMENTED``
  *and* measured present, so a declared-but-unbuilt feature fails;
* scope separation — drawing text and title-block boilerplate are measured
  separately, so a project name in the title block cannot satisfy a requirement
  for a detail on the sheet (the false positive this module previously had);
* applicability — a requirement whose ``when`` condition does not match the
  resolved parameters is reported ``applicable=false`` and excluded, and an
  empty applicable set is never a pass.
"""
from __future__ import annotations

import pytest

from bridgecad_qa.required_content import (
    DRAWING,
    TITLE_BLOCK,
    ContentReport,
    Requirement,
    RequirementKind,
    RequirementResult,
    SheetContent,
    annotate_family,
    evaluate,
    load_manifest,
)

# ── the shipped manifest ─────────────────────────────────────────────────────

def test_shipped_manifest_loads_with_unique_ids_and_declared_statuses():
    raw, reqs = load_manifest()
    assert raw["manifest_version"]
    ids = [r.id for r in reqs]
    assert len(ids) == len(set(ids))
    assert reqs, "the shipped manifest must not be empty"
    for r in reqs:
        assert r.status in ("IMPLEMENTED", "PARTIAL", "MISSING")
        assert r.kind in RequirementKind
        assert r.sheet, r.id


def test_shipped_manifest_covers_every_spec_drawing_area():
    _, reqs = load_manifest()
    areas = {r.area for r in reqs}
    # The ten areas of spec §4's table. Missing one would silently narrow the
    # acceptance check.
    assert {
        "Plan",
        "Longitudinal section",
        "Cross section",
        "Foundation",
        "Cantilever abutment",
        "Battered abutment",
        "Bearings/joints",
        "Reinforcement",
        "BOQ/schedules",
        "Title/notes",
    } <= areas


def test_every_gated_requirement_names_a_resolvable_parameter():
    _, reqs = load_manifest()
    gated = [r for r in reqs if r.when]
    assert gated, "the manifest must scope at least some requirements"
    for r in gated:
        assert isinstance(r.when, dict) and r.when


def test_an_unknown_declared_status_is_rejected():
    with pytest.raises(ValueError):
        Requirement.from_json(
            {"id": "X", "area": "Plan", "kind": "layer", "sheet": "S", "status": "MAYBE"}
        )


def test_an_unknown_scope_is_rejected():
    with pytest.raises(ValueError):
        Requirement.from_json(
            {
                "id": "X",
                "area": "Plan",
                "kind": "text",
                "sheet": "S",
                "status": "IMPLEMENTED",
                "scope": "everywhere",
            }
        )


# ── verdict arithmetic ───────────────────────────────────────────────────────

def _result(**kw) -> RequirementResult:
    base = dict(
        id="R", area="Plan", declared_status="IMPLEMENTED", applicable=True,
        measured=1, required_count=1, detail="",
    )
    base.update(kw)
    return RequirementResult(**base)


def test_ok_requires_declared_implemented_and_measured_present():
    assert _result().ok is True
    assert _result(declared_status="PARTIAL").ok is False
    assert _result(declared_status="MISSING").ok is False
    assert _result(measured=0).ok is False
    assert _result(applicable=False).ok is False


def test_an_empty_applicable_set_is_not_a_pass():
    report = ContentReport(manifest_version="1.0.0")
    assert report.applicable == []
    assert report.failures == []
    assert report.passed is False
    assert "0/0" in report.summary()


def test_report_passes_only_with_no_failures():
    report = ContentReport(
        manifest_version="1.0.0",
        requirements=[_result(id="A"), _result(id="B")],
    )
    assert report.passed is True
    report.requirements.append(_result(id="C", declared_status="MISSING"))
    assert report.passed is False
    assert [r.id for r in report.failures] == ["C"]


def test_report_json_carries_the_counts_and_every_requirement():
    report = ContentReport(
        manifest_version="1.0.0",
        requirements=[_result(id="A"), _result(id="B", applicable=False, measured=0)],
        sheets_found=["Sheet1_Plan"],
    )
    payload = report.to_json()
    assert payload["applicable"] == 1
    assert payload["not_applicable"] == 1
    assert payload["failures"] == 0
    assert payload["passed"] is True
    assert [r["id"] for r in payload["requirements"]] == ["A", "B"]


# ── applicability ────────────────────────────────────────────────────────────

def test_annotate_family_uses_the_renderers_own_classifier():
    # "OPEN" is not a wall-shape name; family_for deliberately falls through to
    # the plain rectangle family the renderers draw for it.
    assert annotate_family({"abutment_type": "OPEN"})["abutment_shape_family"] == "battered"
    assert annotate_family({"abutment_type": "CANTILEVER"})["abutment_shape_family"] == "cantilever"
    # An explicit value wins.
    assert annotate_family(
        {"abutment_type": "OPEN", "abutment_shape_family": "cantilever"}
    )["abutment_shape_family"] == "cantilever"


# ── measurement against a real DXF ───────────────────────────────────────────

def _write_dxf(path, texts):
    """Write a minimal DXF with the given ``(layer, text)`` modelspace texts."""
    ezdxf = pytest.importorskip("ezdxf")
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    for layer, text in texts:
        msp.add_text(text).set_dxf_attrib("layer", layer)
    doc.saveas(str(path))


def _manifest(reqs):
    return {"manifest_version": "test"}, [Requirement.from_json(r) for r in reqs]


def test_title_block_text_cannot_satisfy_a_drawing_content_requirement(tmp_path):
    """The regression this module was fixed for.

    The title block prints ``PROJECT: Open Footing ...``.  A requirement for an
    open-footing label on the sheet must not be satisfied by it — "FOOTING"
    inside "Open Footing" in the title block is not an open-footing drawing.
    """
    _write_dxf(
        tmp_path / "tt_Sheet1_Plan.dxf",
        [("TITLEBLK-TEXT", "PROJECT: Open Footing + RCC Pier"),
         ("TEXT-TITLE", "DRAWING TITLE: PLAN VIEW"),
         ("TEXT-GENERAL", "PLAN VIEW")],
    )
    manifest = _manifest([
        {"id": "DRAW", "area": "Foundation", "kind": "text_regex",
         "sheet": "Sheet1_Plan", "value": "FOOTING", "status": "IMPLEMENTED"},
        {"id": "TITLE", "area": "Title/notes", "kind": "text_regex",
         "sheet": "Sheet1_Plan", "value": "^PROJECT: ", "scope": TITLE_BLOCK,
         "status": "IMPLEMENTED"},
    ])
    report = evaluate(tmp_path, {}, manifest=manifest)
    by_id = {r.id: r for r in report.requirements}
    # Drawing scope sees only the drawing text — no FOOTING there.
    assert by_id["DRAW"].measured == 0
    assert by_id["DRAW"].ok is False
    # Title-block scope sees the boilerplate.
    assert by_id["TITLE"].measured == 1
    assert by_id["TITLE"].ok is True
    assert report.passed is False


def test_drawing_text_is_not_credited_to_a_title_block_requirement(tmp_path):
    _write_dxf(
        tmp_path / "tt_Sheet1_Plan.dxf",
        [("TEXT-GENERAL", "DRG: 9999"), ("TITLEBLK-TEXT", "DRG: BR-I-2022-002")],
    )
    manifest = _manifest([
        {"id": "T", "area": "Title/notes", "kind": "text_regex",
         "sheet": "Sheet1_Plan", "value": "^DRG: ", "scope": TITLE_BLOCK,
         "status": "IMPLEMENTED"},
    ])
    report = evaluate(tmp_path, {}, manifest=manifest)
    assert report.requirements[0].measured == 1
    assert "BR-I-2022-002" not in report.requirements[0].detail


def test_a_declared_partial_requirement_fails_even_when_measured_present(tmp_path):
    _write_dxf(tmp_path / "tt_Sheet1_Plan.dxf", [("TEXT-GENERAL", "WING SPLAY")])
    manifest = _manifest([
        {"id": "P", "area": "Plan", "kind": "text_regex",
         "sheet": "Sheet1_Plan", "value": "SPLAY", "status": "PARTIAL"},
    ])
    report = evaluate(tmp_path, {}, manifest=manifest)
    r = report.requirements[0]
    assert r.measured == 1 and r.present is True
    # Measured, but only declared PARTIAL -> not credited, gate fails.
    assert r.ok is False
    assert report.passed is False


def test_a_non_matching_when_condition_is_reported_not_applicable(tmp_path):
    _write_dxf(tmp_path / "tt_Sheet1_Plan.dxf", [])
    manifest = _manifest([
        {"id": "PILE", "area": "Foundation", "kind": "text_regex",
         "sheet": "Sheet1_Plan", "value": "PILE SCHEDULE", "status": "IMPLEMENTED",
         "when": {"foundation_type": ["PILE"]}},
    ])
    report = evaluate(tmp_path, {"foundation_type": "OPEN"}, manifest=manifest)
    r = report.requirements[0]
    assert r.applicable is False
    assert r.ok is False
    assert report.applicable == []
    assert report.passed is False  # an empty applicable set is not a pass


def test_numeric_when_bounds_scope_a_requirement(tmp_path):
    _write_dxf(tmp_path / "tt_Sheet1_Plan.dxf", [("TEXT-GENERAL", "FOOTPATH 1.5m")])
    manifest = _manifest([
        {"id": "FP", "area": "Cross section", "kind": "text_regex",
         "sheet": "Sheet1_Plan", "value": "FOOTPATH", "status": "IMPLEMENTED",
         "when": {"footpath_width": {"min": 0.1}}},
    ])
    absent = evaluate(tmp_path, {"footpath_width": None}, manifest=manifest)
    assert absent.requirements[0].applicable is False
    present = evaluate(tmp_path, {"footpath_width": 1.5}, manifest=manifest)
    assert present.requirements[0].applicable is True
    assert present.requirements[0].measured == 1


def test_a_missing_sheet_fails_rather_than_silently_passing(tmp_path):
    manifest = _manifest([
        {"id": "S", "area": "Plan", "kind": "layer", "sheet": "Sheet1_Plan",
         "value": "SUB-PIER", "status": "IMPLEMENTED"},
    ])
    report = evaluate(tmp_path, {}, manifest=manifest)
    assert report.requirements[0].measured == 0
    assert report.sheets_found == []
    assert report.passed is False


def test_geometry_kind_counts_drawn_layers_only(tmp_path):
    _write_dxf(
        tmp_path / "tt_Sheet9.dxf",
        [("TEXT-HEADER", "MARK"), ("TITLEBLK-TEXT", "DRG: X")],
    )
    manifest = _manifest([
        {"id": "G", "area": "Reinforcement", "kind": "geometry",
         "sheet": "Sheet9", "status": "IMPLEMENTED"},
    ])
    report = evaluate(tmp_path, {}, manifest=manifest)
    # Only annotation layers are present -> no drawn geometry -> the
    # "a table alone is not detailing" requirement fails, as it should.
    assert report.requirements[0].measured == 0
    assert report.requirements[0].ok is False


def test_drawing_and_title_block_text_pools_are_disjoint():
    content = SheetContent(
        stem="Sheet1_Plan", path=None,  # type: ignore[arg-type]
        layers={"TEXT-GENERAL": 1, "TITLEBLK-TEXT": 2, "TEXT-TITLE": 1},
        texts=[("TEXT-GENERAL", "A"), ("TITLEBLK-TEXT", "B"),
               ("TITLEBLK-TEXT", "C"), ("TEXT-TITLE", "D")],
    )
    assert content.drawing_texts == ["A"]
    assert content.title_block_texts == ["B", "C", "D"]
    assert content.texts[0][0] in (DRAWING, TITLE_BLOCK, "TEXT-GENERAL")
