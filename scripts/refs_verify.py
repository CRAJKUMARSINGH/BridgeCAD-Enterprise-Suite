#!/usr/bin/env python3
"""Show proposed values with their citations, so the human decides with the
drawing open.

Usage:
    python scripts/refs_verify.py                 # print proposed values
    python scripts/refs_verify.py --crop          # write bbox crops for a ref
    python scripts/refs_verify.py --crop gad-set-d-sheet5
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REF = REPO / "references"
index = json.loads((REF / "index.json").read_text(encoding="utf-8"))


def main() -> int:
    for path in sorted((REF / "expected").glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        proposed = [v for v in doc["values"] if v["status"] == "proposed"]
        if not proposed:
            continue
        print(f"\n  {doc['sheet_type']} — {len(proposed)} to review\n")
        for v in proposed:
            print(f"    {v['key']:<22} {v['value']} {v['unit']}  ({v['precision']} dp)")
            print(
                f"      from {v['citation']['ref']} p{v['citation']['page']} "
                f"bbox {v['citation']['bbox']}"
            )
            print(f"      reads: {v['citation']['quote']!r}")
            if "was" in v:
                print(f"      CHANGED from {v['was']!r}")
            print()
        print(f'  edit {path} and set status to "verified" for each you have checked')
    return 0


def write_crops(ref_id: str) -> int:
    """A reviewer verifying OCR must look at the pixels. A bbox plus a quoted
    string is the extractor's own opinion of what the drawing says."""
    from bridgecad_refs import ocr

    entry = next(r for r in index["references"] if r["id"] == ref_id)
    out = REF / "extracted" / "_crops"
    out.mkdir(parents=True, exist_ok=True)
    pages = list(ocr.rasterise(REF / entry["path"]))
    n = 0
    for item in json.loads((REF / "extracted" / f"{ref_id}.json").read_text(encoding="utf-8"))[
        "facts"
    ]:
        if item.get("status") != "proposed":
            continue
        x0, top, x1, bottom = item["citation"]["bbox"]
        page = pages[item["citation"]["page"] - 1]
        pad = 12
        crop = page.crop((int(x0) - pad, int(top) - pad, int(x1) + pad, int(bottom) + pad))
        crop = crop.resize((crop.width * 3, crop.height * 3))
        name = f"{ref_id}_p{item['citation']['page']}_{item['fact']['key']}.png"
        crop.save(out / name)
        n += 1
    print(f"  {n} crop(s) written to references/extracted/_crops/")
    return n


def _crop_targets() -> list[str]:
    return [r["id"] for r in index["references"] if r.get("text_layer") is False]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--crop",
        nargs="?",
        const=True,
        metavar="REF_ID",
        help="write bbox crops for OCR verification (all scanned refs if no id)",
    )
    args = ap.parse_args()
    if args.crop:
        targets = [args.crop] if isinstance(args.crop, str) else _crop_targets()
        for ref_id in targets:
            write_crops(ref_id)
        sys.exit(0)
    sys.exit(main())
