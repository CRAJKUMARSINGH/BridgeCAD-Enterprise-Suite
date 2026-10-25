"""Wing-03 — every sheet, every golden case, must satisfy the DXF contract.

These run before any geometry assertion. If a sheet is a scaffold with a title
block and nothing else, assert_non_empty fails and you find out immediately.
"""
from __future__ import annotations

import json

import pytest

from . import contract, dxf_assert

pytestmark = pytest.mark.draw

SHEET_INDEX = {
    "sheet1_plan": 1, "sheet2_long_section": 2, "sheet3_cross_section": 3,
    "sheet4_foundation": 4, "sheet5_pier_abutment_details": 5,
    "sheet6_bearings_joints": 6, "sheet7_bill_of_quantities": 7,
}

SPEC = json.loads((contract.REPO / "tests" / "draw" / "sheets.spec.json").read_text(encoding="utf-8"))
SCAFFOLD_SHEETS = {s for s, v in SPEC["sheets"].items() if v["status"] == "scaffold"}


def _min_entities(sheet: str) -> int:
    return 20 if sheet in SCAFFOLD_SHEETS else 50


@pytest.mark.parametrize("slug", contract.golden_slugs())
@pytest.mark.parametrize("sheet", sorted(SHEET_INDEX))
def test_sheet_satisfies_structural_contract(slug: str, sheet: str):
    project = contract.make_project(slug)
    doc = contract.build_sheet(project, sheet)

    dxf_assert.assert_finite_extents(doc, sheet)
    dxf_assert.assert_non_empty(doc, sheet, minimum=_min_entities(sheet))
    dxf_assert.assert_no_degenerate_geometry(doc, sheet)
    dxf_assert.assert_layers_known(doc, contract.layer_registry(), sheet)
    dxf_assert.assert_nothing_on_layer_zero(doc, sheet)
    dxf_assert.assert_title_block_filled(doc, sheet)
    dxf_assert.assert_sheet_annotation(doc, sheet, index=SHEET_INDEX[sheet])


@pytest.mark.parametrize("sheet", sorted(SHEET_INDEX))
def test_non_scaffold_sheets_are_dimensioned(sheet: str):
    if sheet in SCAFFOLD_SHEETS:
        pytest.xfail(f"{sheet} is a documented scaffold — no dimensions yet")
    project = contract.make_project("simple_12m")
    doc = contract.build_sheet(project, sheet)
    dxf_assert.assert_min_dimensions(doc, sheet, minimum=8)


@pytest.mark.parametrize("sheet", sorted(SHEET_INDEX))
def test_text_is_legible(sheet: str):
    project = contract.make_project("simple_12m")
    doc = contract.build_sheet(project, sheet)
    dxf_assert.assert_min_text_height(doc, sheet)


def test_no_sheet_is_a_pure_title_block():
    """The failure mode from 2 OCT PROGRAM.MD: title block text and nothing else."""
    project = contract.make_project("simple_12m")
    for sheet in SHEET_INDEX:
        doc = contract.build_sheet(project, sheet)
        non_text = sum(1 for e in doc.modelspace()
                       if e.dxftype() not in ("TEXT", "MTEXT", "DIMENSION"))
        assert non_text >= 10, (
            f"{sheet} has {non_text} non-text entities — title block only, "
            "geometry never drawn"
        )
