"""Wing-21 — the OCR route.

OCR is worse than a text layer, not equivalent, and the tests have to encode
that difference rather than hide it behind the same interface.
"""
from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from bridgecad_refs import ocr

pytestmark = pytest.mark.refs

requires_tesseract = pytest.mark.skipif(not ocr.available(), reason="tesseract not installed")

REF = Path(__file__).resolve().parents[2] / "references"
OCR_REFS = [r for r in json.loads((REF / "index.json").read_text(encoding="utf-8"))["references"]
            if r.get("text_layer") is False]


def test_ocr_references_exist():
    """If nothing is scanned, this whole path is untested. One scanned set is the
    minimum for the route to be real."""
    assert OCR_REFS, "no reference is marked text_layer: false"


def test_no_text_layer_flag_is_a_claim_not_a_guess():
    """text_layer: false must mean extraction produced nothing, not that someone
    assumed a scan. A mislabelled reference takes the wrong route silently."""
    for r in OCR_REFS:
        out = REF / "extracted" / f"{r['id']}.json"
        if out.exists():
            doc = json.loads(out.read_text(encoding="utf-8"))
            assert doc.get("extraction") == "ocr", (
                f"{r['id']} is flagged scanned but was extracted as text"
            )


@requires_tesseract
def test_numeric_repair_only_fires_in_numeric_context():
    """The rule that stops SOFFIT becoming 50FFIT."""
    assert ocr.repair_token("SOFFIT") == ("SOFFIT", None)
    assert ocr.repair_token("BRIDGE") == ("BRIDGE", None)
    assert ocr.repair_token("1O4.5OO") == ("104.500", "1O4.5OO")
    assert ocr.repair_token("l3.OOO") == ("13.000", "l3.OOO")


@requires_tesseract
def test_repair_is_recorded_on_the_fact():
    doc = json.loads((REF / "extracted" / f"{OCR_REFS[0]['id']}.json").read_text(encoding="utf-8"))
    for item in doc["facts"]:
        if item["repaired"]:
            assert all(r for r in item["repaired"]), "empty repair record"


@requires_tesseract
def test_every_ocr_fact_carries_confidence_and_engine():
    doc = json.loads((REF / "extracted" / f"{OCR_REFS[0]['id']}.json").read_text(encoding="utf-8"))
    for item in doc["facts"]:
        assert 0 <= item["ocr_conf"] <= 100, item["fact"]["key"]
        assert item["ocr_engine"], "no engine version — OCR is not reproducible"
        assert item["ocr_pipeline"] == ocr.OCR_PIPELINE_VERSION


@requires_tesseract
def test_low_confidence_facts_are_held_back_not_proposed():
    """A 60% confident digit is a question. It must not reach a proposed
    expectation, where it would look like an answer."""
    doc = json.loads((REF / "extracted" / f"{OCR_REFS[0]['id']}.json").read_text(encoding="utf-8"))
    for item in doc["facts"]:
        if item["ocr_conf"] < ocr.MIN_WORD_CONF:
            assert item["status"] == "needs_manual", (
                f"{item['fact']['key']} at {item['ocr_conf']}% was proposed"
            )


@requires_tesseract
def test_ocr_values_asserted_at_1mm_meet_the_confidence_floor():
    """Precision and confidence together decide the tolerance. A 3 dp value at
    85% confidence cannot justify a 1 mm assertion."""
    for case in (REF / "cases").glob("*.json"):
        doc = json.loads(case.read_text(encoding="utf-8"))
        for key, sv in doc["stated_values"].items():
            if sv.get("status") != "verified":
                continue
            if not sv["citation"]["ref"].startswith("gad-set-d"):
                continue
            extracted = json.loads((REF / "extracted" / f"{sv['citation']['ref']}.json").read_text(encoding="utf-8"))
            conf = max((f["ocr_conf"] for f in extracted["facts"] if f["fact"]["key"] == key), default=0)
            assert conf >= ocr.ASSERT_CONF_FLOOR, (
                f"{sv['citation']['ref']}/{key}: verified at 1 mm on {conf}% confidence"
            )


@requires_tesseract
def test_crops_exist_for_verified_ocr_values():
    """Verification without the pixels is the extractor agreeing with itself."""
    crops = REF / "extracted" / "_crops"
    if not crops.exists():
        pytest.skip("crops not generated — run `make refs-verify-crops`")
    for case in (REF / "cases").glob("*.json"):
        doc = json.loads(case.read_text(encoding="utf-8"))
        for key, sv in doc["stated_values"].items():
            if sv.get("status") == "verified" and sv["citation"]["ref"].startswith("gad-set-d"):
                assert list(crops.glob(f"{sv['citation']['ref']}_*_{key}.png")), (
                    f"no crop for verified OCR value {key}"
                )
