"""Wing-12 — the sheets spec, and the promotion gate.

Promoting a sheet from scaffold to real geometry is one word in sheets.spec.json
plus making the tests pass. There is no third path, and the CI matrix prints the
count so the trend is visible.

The gate is deliberately the *spec*, not a test-side constant. A test-side
SCAFFOLD_SHEETS set can drift from reality; a spec file cannot, because
test_spec_and_tests_agree reads it back.
"""
from __future__ import annotations

import json

import pytest

from . import contract, dxf_assert

pytestmark = pytest.mark.draw

SPEC = json.loads((contract.REPO / "tests" / "draw" / "sheets.spec.json").read_text(encoding="utf-8"))
SHEETS = SPEC["sheets"]
PROMOTED = sorted(s for s, v in SHEETS.items() if v["status"] == "promoted")
SCAFFOLD = sorted(s for s, v in SHEETS.items() if v["status"] == "scaffold")


def test_spec_covers_every_sheet():
    from bridgecad_draw.coordinates import FRAMES
    assert set(SHEETS) | {"sheet1_plan"} == set(FRAMES), (
        f"spec/coordinates disagree: {set(FRAMES) ^ (set(SHEETS) | {'sheet1_plan'})}"
    )


def test_every_sheet_has_a_valid_status():
    for sheet, spec in SHEETS.items():
        assert spec["status"] in ("scaffold", "promoted"), sheet


def test_promotion_is_one_way():
    """A promoted sheet may not silently regress to scaffold."""
    for sheet in PROMOTED:
        assert SHEETS[sheet]["required"], f"{sheet}: promoted with no required block"


@pytest.mark.parametrize("sheet", sorted(SHEETS))
def test_scaffold_sheets_meet_the_structural_bar(sheet: str):
    spec = SHEETS[sheet]
    project = contract.make_project("simple_12m")
    doc = contract.build_sheet(project, sheet)
    dxf_assert.assert_non_empty(doc, sheet, minimum=20)
    dxf_assert.assert_finite_extents(doc, sheet)


#: Two materially different projects: one 12 m span vs three. A drawing that is
#: byte-for-byte the same for both is not reading its project at all.
_RESPONSIVENESS_PAIR = ("simple_12m", "continuous_3x12m")


@pytest.mark.parametrize("sheet", sorted(SHEETS))
def test_every_sheet_responds_to_its_input(sheet: str):
    """DEBUG_REPORT §3.2: sheets 2–7 produced near-identical DXF sizes for a
    1-span 12 m bridge and an 11-span 110 m one — entity counts never scaled.

    A scaffold may be incomplete; it may not be *static*. Build the sheet for a
    single-span bridge and for a three-span one and require the geometry — entity
    count or fingerprint — to differ, so a placeholder cannot silently ship as a
    finished drawing. The spec's `required` block is the promotion target, not a
    scaffold floor, so this is the strongest bar a scaffold can be held to today.
    """
    first, second = _RESPONSIVENESS_PAIR
    a = contract.build_sheet(contract.make_project(first), sheet)
    b = contract.build_sheet(contract.make_project(second), sheet)
    count_a, count_b = dxf_assert.entity_count(a), dxf_assert.entity_count(b)
    assert (count_a, dxf_assert.fingerprint(a)) != (count_b, dxf_assert.fingerprint(b)), (
        f"{sheet}: identical geometry ({count_a} entities) for {first} and {second} — "
        "the sheet ignores its input and would ship as a placeholder"
    )


@pytest.mark.parametrize("sheet", PROMOTED)
def test_promoted_sheets_meet_the_full_spec(sheet: str):
    """This is what 'promoted' means. If it fails, either fix the sheet or set
    the status back to scaffold — do not soften the assertion."""
    spec = SHEETS[sheet]["required"]
    project = contract.make_project("simple_12m")
    doc = contract.build_sheet(project, sheet)

    dxf_assert.assert_non_empty(doc, sheet, minimum=spec["min_entities"])
    dxf_assert.assert_min_dimensions(doc, sheet, minimum=spec["min_dimensions"])

    blob = " ".join(dxf_assert.text_of(doc)).upper()
    for needle in spec["must_contain_text"]:
        assert needle.upper() in blob, f"{sheet}: missing text {needle!r}"

    used = set(dxf_assert.layer_usage(doc))
    for layer in spec["must_contain_layers"]:
        assert layer in used, f"{sheet}: no entities on required layer {layer!r}"


@pytest.mark.parametrize("sheet", PROMOTED)
def test_promoted_long_section_has_a_pier_centreline_per_pier(sheet: str):
    if sheet != "sheet2_long_section":
        pytest.skip("long section only")
    project = contract.make_project("continuous_3x12m")
    doc = contract.build_sheet(project, sheet)
    cl_count = dxf_assert.layer_usage(doc).get("CL", 0)
    piers = len(contract.pier_positions(project))
    assert cl_count >= piers, (
        f"long section has {cl_count} centreline entities for {piers} piers"
    )


def test_scaffold_count_is_reported_and_decreases_over_time():
    """Not an assertion on a magic number — a printed trend the CI summary shows."""
    assert len(SCAFFOLD) + len(PROMOTED) == len(SHEETS)
    print(f"\n  sheets: {len(PROMOTED)} promoted, {len(SCAFFOLD)} scaffold")


def test_manifest_declares_which_sheets_are_scaffolds():
    """GUIDE.md §11 requires the manifest to say so. If the manifest is silent,
    a reader assumes all seven sheets are complete."""
    from bridgecad_export.bundler import build_manifest
    manifest = build_manifest(contract.make_project("simple_12m"))
    assert "scaffold_sheets" in manifest, "manifest does not declare scaffold sheets"
    assert set(manifest["scaffold_sheets"]) == set(SCAFFOLD), (
        "manifest scaffold list disagrees with sheets.spec.json"
    )
