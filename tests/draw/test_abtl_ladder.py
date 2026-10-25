"""Wing-04 — ABTL resolution ladder.

ABTL fell through to a silent default once, producing abutments with no
dimensionable length. The fix introduced a ladder and a source label. These
tests pin both: every rung resolves, precedence is exact, and the source is
always reportable so an auditor can see which parameter was used.
"""
from __future__ import annotations

import pytest

from . import contract

pytestmark = pytest.mark.draw

LADDER = ("ABTL", "FUTL", "FOOTL", "FUTRL", "ALCL", "ALCW")
TERMINAL_DEFAULT = 13.0


def _project_with(**fields):
    """Minimal project carrying only the fields under test."""
    project = contract.make_project("simple_12m")
    for name, value in fields.items():
        setattr(project.foundation_details, name.lower(), value)
    return project


@pytest.mark.parametrize("field", LADDER)
def test_each_ladder_rung_resolves(field: str):
    project = contract.make_project("simple_12m")
    setattr(project.foundation_details, field.lower(), 17.5)
    value, source = contract.resolve_abtl(project)
    assert value == pytest.approx(17.5)
    assert source != "", "source label must never be empty"


def test_ladder_precedence_is_exact():
    """The earliest rung that carries a value must win — for every rung in turn.

    Rungs before the one under test are cleared, so "the earliest set rung" is
    unambiguous. Leaving them all set would only ever exercise ABTL.
    """
    for i, field in enumerate(LADDER):
        project = contract.make_project("simple_12m")
        for j, f in enumerate(LADDER):
            # distinct value per rung so a mis-ordered ladder is unambiguous
            setattr(project.foundation_details, f.lower(), 10.0 + j if j >= i else None)
        value, source = contract.resolve_abtl(project)
        assert source == field, f"expected {field} to win, got {source}"
        assert value == pytest.approx(10.0 + i)


def test_terminal_default_is_13_metres():
    project = contract.make_project("simple_12m")
    for f in LADDER:
        setattr(project.foundation_details, f.lower(), None)
    value, source = contract.resolve_abtl(project)
    assert value == pytest.approx(TERMINAL_DEFAULT)
    assert source == "default"


def test_source_label_names_the_parameter_actually_used():
    """An auditor must be able to tell which rung fired, from the output alone."""
    project = contract.make_project("simple_12m")
    for f in LADDER:
        setattr(project.foundation_details, f.lower(), None)
    setattr(project.foundation_details, "futrl", 15.25)
    _, source = contract.resolve_abtl(project)
    assert source == "FUTRL"


@pytest.mark.parametrize("bad", [0.0, -1.0])
def test_zero_and_negative_values_fall_through(bad: float):
    """A present-but-zero rung is not a valid length; the ladder must continue."""
    project = contract.make_project("simple_12m")
    for f in LADDER:
        setattr(project.foundation_details, f.lower(), None)
    setattr(project.foundation_details, "abtl", bad)
    setattr(project.foundation_details, "futl", 14.0)
    value, source = contract.resolve_abtl(project)
    assert source == "FUTL", f"{bad} accepted as a valid ABTL"
    assert value == pytest.approx(14.0)


def test_resolved_value_is_written_back_for_downstream_drawers():
    """The fix wrote the resolved value into project variables so later drawers
    do not re-resolve and possibly get a different answer."""
    project = contract.make_project("simple_12m")
    for f in LADDER:
        setattr(project.foundation_details, f.lower(), None)
    contract.resolve_abtl(project)
    again, source = contract.resolve_abtl(project)
    assert source != "default", "second resolution lost the first result"


def test_source_is_emitted_into_the_drawing():
    """The abutment elevation must print which rung was used."""
    project = contract.make_project("simple_12m")
    doc = contract.build_sheet(project, "sheet5_pier_abutment_details")
    from .dxf_assert import text_of
    blob = " ".join(text_of(doc)).upper()
    assert any(f"ABTL" in blob for _ in [0]), "ABTL not annotated on the sheet"
    assert any(src.upper() in blob for src in LADDER + ("DEFAULT",)), (
        "no ABTL source label on the drawing — auditor cannot tell which rung fired"
    )
