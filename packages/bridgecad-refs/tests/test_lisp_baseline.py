"""Tests for bridgecad_refs.lisp_baseline against the stub fixture."""

from pathlib import Path

from bridgecad_refs.lisp_baseline import inventory

REPO = Path(__file__).resolve().parents[3]
STUB = REPO / "references" / "lisp" / "fixture_min.lsp"


def test_defun_and_entities_found():
    inv = inventory(STUB)
    assert "c:gad-deck" in inv.defuns
    assert inv.entity_counts.get("LINE") == 1
    assert inv.entity_counts.get("HATCH") == 1


def test_setq_symbols_captured():
    inv = inventory(STUB)
    assert "dtop" in inv.setq_names and "halfw" in inv.setq_names


def test_numeric_literals_counted():
    assert inventory(STUB).numeric_literal_count >= 3
