#!/usr/bin/env python3
"""Pull facts off reference drawings. Propose, never decide.

Extraction output is NOT ground truth. A CAD-exported PDF gives you exploded
text, rotated labels and glyph-encoded fonts. So facts go to `extracted/`
(regenerable, cited) and expectations go to `expected/` with status "proposed".
A human flips them to "verified". Only "verified" expectations are trusted by CI.

Usage:
    python scripts/refs_extract.py                 # all references
    python scripts/refs_extract.py --only gad-borse-sheet5
    python scripts/refs_extract.py --check         # is extracted/ stale?
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

# Self-bootstrap: when launched as `python scripts/refs_extract.py`, sys.path[0]
# is scripts/ and the repo-root sitecustomize.py is NOT imported, so the
# packages/* layout would be invisible. Prepend every packages/<name> directory.
_REPO_ROOT = Path(__file__).resolve().parent.parent
for _pkg in sorted((_REPO_ROOT / "packages").glob("*/")):
    if _pkg.is_dir():
        _entry = str(_pkg)
        if _entry not in sys.path:
            sys.path.insert(0, _entry)

from bridgecad_refs import ocr  # noqa: E402

REPO = _REPO_ROOT
REF = REPO / "references"
EXTRACTOR_VERSION = 1


def sha16(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def words_with_citations(path: Path) -> list[dict]:
    """One record per text line, with the page and bbox that produced it.

    The bbox is what makes a citation checkable: a reviewer can open the page and
    look at that rectangle.
    """
    import pdfplumber
    from bridgecad_refs.parse import parse_lines

    out = []
    with pdfplumber.open(path) as pdf:
        for pno, page in enumerate(pdf.pages, start=1):
            rows: dict[int, list] = {}
            for w in page.extract_words(use_text_flow=False):
                rows.setdefault(round(w["top"]), []).append(w)
            for top in sorted(rows):
                ws = sorted(rows[top], key=lambda w: w["x0"])
                text = " ".join(w["text"] for w in ws)
                facts = parse_lines([text])
                for f in facts:
                    out.append(
                        {
                            "fact": {**asdict(f), "value": str(f.value)},
                            "citation": {
                                "ref": path.stem,
                                "page": pno,
                                "bbox": [
                                    round(min(w["x0"] for w in ws), 1),
                                    round(top, 1),
                                    round(max(w["x1"] for w in ws), 1),
                                    round(max(w["bottom"] for w in ws), 1),
                                ],
                                "quote": text.strip()[:120],
                            },
                        }
                    )
    return out


def extract_ocr(entry: dict) -> dict:
    """OCR route. Facts carry confidence; low-confidence facts are held back as
    needs_manual rather than proposed, because a 60% confident digit is a
    question, not a value."""
    path = REF / entry["path"]
    payload = {
        "id": entry["id"],
        "sha256": sha16(path),
        "extractor_version": EXTRACTOR_VERSION,
        "extraction": "ocr",
        "ocr_pipeline": ocr.OCR_PIPELINE_VERSION,
        "facts": [],
    }
    if not ocr.available():
        payload["note"] = "tesseract not installed — pip install '.[refs-ocr]'"
        return payload

    from bridgecad_refs.parse import parse_lines

    payload["ocr_engine"] = ocr.engine_version()
    for pno, image in enumerate(ocr.rasterise(path), start=1):
        image = ocr.binarise(ocr.deskew(image))
        for text, words in ocr.rows_to_lines(ocr.ocr_page(image)):
            for f in parse_lines([text]):
                conf = sum(w.conf for w in words) / len(words)
                cites = [w for w in words if w.text in f.raw] or words
                payload["facts"].append(
                    {
                        "fact": {**asdict(f), "value": str(f.value)},
                        "citation": {
                            "ref": path.stem,
                            "page": pno,
                            "bbox": [
                                round(min(w.x0 for w in cites), 1),
                                round(min(w.top for w in cites), 1),
                                round(max(w.x1 for w in cites), 1),
                                round(max(w.bottom for w in cites), 1),
                            ],
                            "quote": text.strip()[:120],
                        },
                        "extraction": "ocr",
                        "ocr_conf": round(conf, 1),
                        "ocr_engine": payload["ocr_engine"],
                        "ocr_pipeline": ocr.OCR_PIPELINE_VERSION,
                        "repaired": [w.repaired_from for w in cites if w.repaired_from],
                        "status": "proposed" if conf >= ocr.MIN_WORD_CONF else "needs_manual",
                    }
                )
    return payload


def extract_one(entry: dict) -> dict:
    if entry.get("text_layer") is False:
        return extract_ocr(entry)
    path = REF / entry["path"]
    return {
        "id": entry["id"],
        "sha256": sha16(path),
        "extractor_version": EXTRACTOR_VERSION,
        "extraction": "text",
        "facts": words_with_citations(path),
    }


def write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    index = json.loads((REF / "index.json").read_text(encoding="utf-8"))
    entries = [r for r in index["references"] if not args.only or r["id"] == args.only]

    if args.check:
        stale = []
        for r in entries:
            out = REF / "extracted" / f"{r['id']}.json"
            if not out.exists():
                stale.append(f"{r['id']}: never extracted")
                continue
            got = json.loads(out.read_text(encoding="utf-8"))
            if got.get("sha256") != sha16(REF / r["path"]):
                stale.append(f"{r['id']}: raw changed since extraction")
            if got.get("extractor_version") != EXTRACTOR_VERSION:
                stale.append(
                    f"{r['id']}: extractor v{got.get('extractor_version')} -> v{EXTRACTOR_VERSION}"
                )
            if got.get("extraction") == "ocr":
                if (
                    got.get("ocr_pipeline") != ocr.OCR_PIPELINE_VERSION
                    and got.get("ocr_pipeline") is not None
                ):
                    stale.append(
                        f"{r['id']}: OCR pipeline v{got.get('ocr_pipeline')} -> v{ocr.OCR_PIPELINE_VERSION}"
                    )
                stored_engine = got.get("ocr_engine")
                if stored_engine and ocr.available() and stored_engine != ocr.engine_version():
                    stale.append(f"{r['id']}: tesseract {stored_engine} -> {ocr.engine_version()}")
        for s in stale:
            print(f"  STALE {s}")
        print(f"\n  {len(stale)} stale reference(s)" if stale else "\n  extracted/ is fresh")
        return 1 if stale else 0

    for r in entries:
        payload = extract_one(r)
        write(REF / "extracted" / f"{r['id']}.json", payload)
        print(f"  {r['id']}: {len(payload['facts'])} facts")

    propose_expectations()
    return 0


def propose_expectations() -> None:
    """Group facts by bridge and sheet type into expected/<bridge>_<sheet>.json.

    Expected files are keyed by bridge since Wing-21: a value only means
    something together with the bridge it was read from. Existing verified
    values are carried across; only new or changed ones are marked proposed, so
    re-running extraction does not silently un-verify work.
    """
    index = json.loads((REF / "index.json").read_text(encoding="utf-8"))
    groups: dict[tuple[str, str], list[dict]] = {}
    for r in index["references"]:
        path = REF / "extracted" / f"{r['id']}.json"
        if not path.exists():
            continue
        groups.setdefault((r["bridge_id"], r["sheet_type"]), [])
        for item in json.loads(path.read_text(encoding="utf-8"))["facts"]:
            item["fact"]["source_ref"] = r["id"]
            groups[(r["bridge_id"], r["sheet_type"])].append(item)

    for (bridge_id, sheet_type), items in groups.items():
        target = REF / "expected" / f"{bridge_id}_{sheet_type}.json"
        existing = (
            json.loads(target.read_text(encoding="utf-8")) if target.exists() else {"values": []}
        )
        verified = {v["key"]: v for v in existing["values"] if v["status"] == "verified"}

        values = []
        for item in items:
            key = item["fact"]["key"]
            entry = {
                "key": key,
                "value": item["fact"]["value"],
                "unit": item["fact"]["unit"],
                "precision": item["fact"]["precision"],
                "citation": item["citation"],
                "sheet_type": sheet_type,
                "status": "verified"
                if key in verified and verified[key]["value"] == item["fact"]["value"]
                else "proposed",
            }
            if key in verified and verified[key]["value"] != item["fact"]["value"]:
                entry["was"] = verified[key]["value"]
            values.append(entry)

        write(target, {"bridge_id": bridge_id, "sheet_type": sheet_type, "values": values})
        proposed = sum(1 for v in values if v["status"] == "proposed")
        print(
            f"  expected/{bridge_id}_{sheet_type}.json: {len(values)} values, {proposed} awaiting review"
        )


if __name__ == "__main__":
    raise SystemExit(main())
