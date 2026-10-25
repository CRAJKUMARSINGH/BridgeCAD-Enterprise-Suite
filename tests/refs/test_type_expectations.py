"""Wing-20 — Class A: the spec's required text must trace to a real reference.

Class A expectations say what a sheet must contain. Without a reference to check
them against, `must_contain_text` accumulates plausible-sounding labels that no
real drawing uses.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.refs

REPO = Path(__file__).resolve().parents[2]
REF = REPO / "references"
SPEC = json.loads((REPO / "tests" / "draw" / "sheets.spec.json").read_text(encoding="utf-8"))
index = json.loads((REF / "index.json").read_text(encoding="utf-8"))


def quotes_from(ref: dict) -> list[str]:
    """Every quoted text line extraction pulled off a reference sheet."""
    out = REF / "extracted" / f"{ref['id']}.json"
    if not out.exists():
        return []
    doc = json.loads(out.read_text(encoding="utf-8"))
    return [item["citation"]["quote"] for item in doc["facts"]]


def test_spec_required_text_is_supported_by_a_reference():
    """Every must_contain_text entry on a promoted sheet must trace to a string
    that actually appears on a reference sheet of that type."""
    ...
    for sheet, entry in SPEC["sheets"].items():
        if entry["status"] != "promoted":
            continue
        refs = [r for r in index["references"] if r["sheet_type"] == sheet]
        assert refs, f"{sheet} is promoted with no reference to have checked it against"
        blob = " ".join(quote for r in refs for quote in quotes_from(r)).upper()
        for needle in entry["required"]["must_contain_text"]:
            assert needle.upper() in blob, (
                f"{sheet}: spec requires {needle!r} but no reference sheet of this "
                f"type states it — is the spec inventing a requirement?"
            )
