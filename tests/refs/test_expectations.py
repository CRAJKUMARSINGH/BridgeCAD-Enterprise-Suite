"""Wing-20 — what the corpus is allowed to assert.

Only `verified` expectations reach a tolerance-sensitive assertion. A `proposed`
value is reported and skipped, because an unreviewed OCR value failing a test
teaches you nothing except that extraction is imperfect.
"""
from __future__ import annotations

import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

import pytest

from bridgecad_refs.parse import agree

pytestmark = pytest.mark.refs

REF = Path(__file__).resolve().parents[2] / "references"


def all_expected() -> list[tuple[str, dict]]:
    out = []
    for f in (REF / "expected").glob("*.json"):
        doc = json.loads(f.read_text(encoding="utf-8"))
        for v in doc["values"]:
            out.append((doc["sheet_type"], v))
    return out


def by_bridge() -> dict[str, list[dict]]:
    """Expected files are keyed by bridge since Wing-21. Group values by bridge."""
    out: dict[str, list[dict]] = {}
    for f in (REF / "expected").glob("*.json"):
        doc = json.loads(f.read_text(encoding="utf-8"))
        out.setdefault(doc["bridge_id"], []).extend(doc["values"])
    return out


EXPECTED = all_expected()
VERIFIED = [(t, v) for t, v in EXPECTED if v["status"] == "verified"]


def test_there_are_verified_expectations():
    assert VERIFIED, "nothing verified — the corpus is not yet load-bearing"


def test_every_expectation_cites_a_source():
    for sheet_type, v in EXPECTED:
        c = v["citation"]
        assert c["ref"] and c["page"] >= 1, f"{sheet_type}/{v['key']}: no citation"
        assert c["bbox"] and len(c["bbox"]) == 4, f"{sheet_type}/{v['key']}: no bbox"
        assert c["quote"].strip(), f"{sheet_type}/{v['key']}: no quoted text"


def test_citations_point_at_indexed_references():
    index = {r["id"] for r in json.loads((REF / "index.json").read_text(encoding="utf-8"))["references"]}
    for sheet_type, v in EXPECTED:
        assert v["citation"]["ref"] in index, f"{sheet_type}: cites unknown ref {v['citation']['ref']!r}"


def test_verified_values_meet_a_precision_floor():
    """A 1 dp value cannot justify a 1 mm assertion — the source does not say."""
    for sheet_type, v in VERIFIED:
        if v["key"] in ("abtl", "wing_face_run", "wing_return", "carriageway"):
            assert v["precision"] >= 2, (
                f"{sheet_type}/{v['key']}: only {v['precision']} dp on the drawing"
            )


def test_values_agree_within_a_bridge():
    """A single bridge stating the same key twice must agree. THIS is the
    consistency claim. The old test asserted it across bridges, which is wrong
    for n > 1."""
    for bridge, values in by_bridge().items():
        seen: dict[tuple, list] = defaultdict(list)
        for v in values:
            seen[(v["sheet_type"], v["key"])].append(v)
        for (sheet_type, key), items in seen.items():
            vals = [Decimal(i["value"]) for i in items]
            for a in vals:
                for b in vals:
                    assert agree(a, b), (
                        f"{bridge}/{sheet_type}/{key}: one bridge disagrees with "
                        f"itself — {vals} "
                        f"({[i['citation']['ref'] for i in items]})"
                    )


def test_values_differ_across_bridges_where_parameters_differ():
    """The other half, and the one that would have caught the schema bug: two
    bridges with different parameters MUST state different ABTLs. If they do not,
    one case file was copy-pasted and never edited."""
    for key in ("abtl", "carriageway"):
        by_bridge_vals = {
            b: {v["value"] for v in vals if v["key"] == key}
            for b, vals in by_bridge().items()
        }
        for b, vals in by_bridge_vals.items():
            if not vals:
                continue
            assert len(vals) == 1, f"{b}/{key}: {len(vals)} distinct values on one bridge"
        flat = [next(iter(v)) for v in by_bridge_vals.values() if v]
        assert len(set(flat)) >= 3, (
            f"{key}: only {len(set(flat))} distinct values across {len(flat)} bridges "
            f"— the cases are not actually different bridges"
        )


def test_extraction_is_reproducible():
    """Same bytes in, same facts out. Extraction that drifts run to run cannot
    be diffed, so a reviewer cannot see what changed."""
    from scripts.refs_extract import extract_one
    entry = json.loads((REF / "index.json").read_text(encoding="utf-8"))["references"][0]
    a = json.dumps(extract_one(entry), sort_keys=True)
    b = json.dumps(extract_one(entry), sort_keys=True)
    assert a == b


def test_extracted_is_fresh():
    import subprocess, sys
    proc = subprocess.run([sys.executable, "scripts/refs_extract.py", "--check"],
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout
