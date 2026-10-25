"""Wing-19 — issue state.

The point: "Construction ready" is a conclusion the set is entitled to, or is
not. Test the entitlement, not the string.
"""
from __future__ import annotations

import pytest

from . import contract

pytestmark = pytest.mark.draw

from bridgecad_export.revisions import PURPOSES, blockers_for, load, manifest_label  # noqa: E402


def test_register_is_well_formed():
    reg = load()
    assert reg["purpose"] in PURPOSES
    codes = [r["code"] for r in reg["revisions"]]
    assert codes, "no revisions recorded"
    assert len(codes) == len(set(codes)), "duplicate revision codes"


def test_every_revision_names_sheets_and_a_description():
    for r in load()["revisions"]:
        assert r["sheets"], f"{r['code']}: no sheets"
        assert r["description"], f"{r['code']}: no description"
        assert r["purpose"] in PURPOSES
        for sheet in r["sheets"]:
            assert sheet in contract.SHEET_NAMES, f"{r['code']}: unknown sheet {sheet}"


def test_revisions_are_ordered_and_chain():
    reg = load()
    for prev, cur in zip(reg["revisions"], reg["revisions"][1:]):
        assert prev["date"] <= cur["date"], f"{cur['code']} predates {prev['code']}"
        assert cur.get("supersedes") == prev["code"], (
            f"{cur['code']} does not declare supersedes: {prev['code']}"
        )


def test_current_purpose_is_not_claimed_without_satisfying_it():
    """The central assertion. Flip purpose to FOR_CONSTRUCTION with scaffolds
    outstanding and this must fail."""
    reg = load()
    blockers = blockers_for(reg["purpose"])
    if reg["purpose"] in ("FOR_CONSTRUCTION", "AS_BUILT"):
        assert blockers.ok, f"claims {reg['purpose']} but: {blockers.blockers}"
    else:
        assert blockers.blockers, (
            f"claims {reg['purpose']} but nothing blocks — promote it and say so"
        )


def test_preliminary_never_blocks():
    assert blockers_for("PRELIMINARY").ok


def test_manifest_label_is_derived_from_state():
    reg = load()
    label = manifest_label(reg["purpose"])
    if reg["purpose"] == "PRELIMINARY":
        assert "Preliminary" in label
        assert "Construction" not in label, "preliminary set claiming construction"


def test_for_construction_lists_accepted_gaps_on_the_transmittal():
    blockers = blockers_for("FOR_CONSTRUCTION")
    gaps = [b for b in blockers.blockers if b.startswith("GAP ")]
    for g in gaps:
        assert len(g.split(":", 1)[1].strip()) > 8, f"{g}: gap with no real reason"


def test_transmittal_carries_hashes():
    """A transmittal without hashes cannot prove what was issued."""
    from bridgecad_export.transmittal import build_transmittal
    reg = load()
    t = build_transmittal(contract.make_project("simple_12m"), revision=reg["current"])
    assert t["revision"] == reg["current"]
    for sheet in t["sheets"]:
        assert len(sheet["geometry_sha"]) == 16, f"{sheet['name']}: no geometry hash"
    assert t["purpose"] in PURPOSES


def test_as_built_requires_more_than_for_construction():
    from bridgecad_export.revisions import LADDER
    assert LADDER["AS_BUILT"] > LADDER["FOR_CONSTRUCTION"]
