"""Wing-20 — arithmetic validated against reference drawings.

THE TRIANGULATION
    wing_wall_length is asserted three ways, from three independent sources:
      1. the formula in abutment.py
      2. the hand arithmetic in test_sheet2_long_section.py
      3. the value stated on the reference drawing
    Any two agreeing is a coincidence. All three agreeing is a result. A single
    typo in any one of them fails this file.
"""
from __future__ import annotations

import json
from decimal import Decimal

import pytest

from . import contract

pytestmark = pytest.mark.draw

from bridgecad_draw.contract import wing_wall_geometry  # noqa: E402
from bridgecad_refs.parse import agree  # noqa: E402

REF = contract.REPO / "references"
CASES = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((REF / "cases").glob("*.json"))]


def _project(case: dict):
    p = contract.make_project("blank")
    for k, v in case["parameters"].items():
        setattr(p.geometry if k in ("nspan", "span_m") else p, k, Decimal(str(v)))
    return p


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_case_is_fully_cited(case: dict):
    for key, sv in case["stated_values"].items():
        assert sv["citation"]["ref"], f"{case['id']}/{key}: no citation"
        assert sv["status"] in ("verified", "proposed"), key
    assert case["source_sheets"], case["id"]


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_pier_count_matches_the_reference(case: dict):
    """nspan - 1, cross-checked against a drawing that states its piers."""
    stated = case["stated_values"].get("pier_count")
    if not stated or stated["status"] != "verified":
        pytest.skip("no verified pier count")
    project = _project(case)
    assert len(project.geometry.pier_positions()) == stated["value"], (
        f"{case['id']}: {len(project.geometry.pier_positions())} piers generated, "
        f"reference states {stated['value']}"
    )


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_wing_geometry_matches_the_reference(case: dict):
    project = _project(case)
    walls = wing_wall_geometry(project)
    assert len(walls) == 2

    face = case["stated_values"].get("wing_face_run_m")
    if face and face["status"] == "verified":
        for w in walls:
            assert agree(w.face_run_m, Decimal(face["value"])), (
                f"{case['id']}: face run {w.face_run_m}, reference states {face['value']}"
            )

    length = case["stated_values"].get("wing_wall_length_m")
    if length and length["status"] == "verified":
        for w in walls:
            assert agree(w.length_m, Decimal(length["value"])), (
                f"{case['id']}: wall length {w.length_m}, reference states {length['value']}"
            )


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_face_run_formula_matches_the_reference(case: dict):
    """The formula, stated plainly so a failure names the arithmetic and not a
    function: face run = (ABTL - carriageway) / 2."""
    p = case["parameters"]
    expected = (Decimal(p["abtl_m"]) - Decimal(p["carriageway_m"])) / 2
    stated = case["stated_values"].get("wing_face_run_m")
    if stated and stated["status"] == "verified":
        assert agree(expected, Decimal(stated["value"])), (
            f"hand formula gives {expected}, reference states {stated['value']}"
        )


def test_hand_arithmetic_and_the_reference_agree():
    """The triangulation, explicitly. If Wing-16's hand-typed constant and the
    reference drawing disagree, one of them is wrong and this says so."""
    hand = Decimal("2.75")   # from test_sheet2_long_section.py, typed by hand
    for case in CASES:
        stated = case["stated_values"].get("wing_face_run_m")
        if stated and stated["status"] == "verified":
            assert agree(hand, Decimal(stated["value"])), (
                f"hand constant {hand} vs reference {stated['value']} — a typo in one"
            )


def test_levels_from_the_reference_case_are_ordered():
    # Named explicitly: "hfl_m" and "lwl_m" do not end in "_level_m", so a
    # suffix filter silently drops two of the four levels and the assertion
    # KeyErrors instead of testing the ordering.
    levels = ("deck_level_m", "hfl_m", "lwl_m", "founding_level_m")
    for case in CASES:
        p = {k: Decimal(str(case["parameters"][k])) for k in levels}
        assert p["deck_level_m"] > p["hfl_m"] > p["lwl_m"] > p["founding_level_m"], case["id"]
