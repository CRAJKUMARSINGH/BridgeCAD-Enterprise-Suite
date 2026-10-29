#!/usr/bin/env python3
"""Week-2 tool: select golden fixtures, copy them, pin their input hashes.

    python scripts/freeze_golden.py            # dry run, lists matches
    python scripts/freeze_golden.py --write    # copy + write PINNED block
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "tests" / "e2e" / "fixtures"
GOLDEN = ROOT / "tests" / "draw" / "golden"
FROZEN_TEST = ROOT / "tests" / "draw" / "test_golden_frozen.py"

#: fixture_id -> substring that identifies the source file, plus why it is here.
SELECT = {
    "simple_12m": ("simple_12m", "single-span RCC slab"),
    "continuous_3x12m": ("continuous_3x12m", "continuous slab"),
    "girder_4x18m": ("girder_4x18m", "PSC girder"),
    "box_culvert_8m": ("box_culvert_8m", "box culvert"),
    "skew_15deg": ("skew", "15 degree skew"),
}


def _input_hash(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    data.pop("_meta", None)
    data.pop("expected", None)
    blob = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()


def _locate(needle: str) -> Path:
    hits = [p for p in sorted(FIXTURES.glob("*.json")) if needle in p.name.lower()]
    if not hits:
        raise FileNotFoundError(f"no fixture filename contains {needle!r}")
    if len(hits) > 1:
        raise SystemExit(
            f"{needle!r} is ambiguous: {[h.name for h in hits]}\n"
            "narrow the needle in SELECT."
        )
    return hits[0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    resolved: dict[str, Path] = {}
    for fid, (needle, why) in SELECT.items():
        try:
            src = _locate(needle)
        except (FileNotFoundError, SystemExit) as exc:
            print(f"  [!] {fid}: {exc}")
            continue
        data = json.loads(src.read_text(encoding="utf-8"))
        data.setdefault("_meta", {})["fixture_id"] = fid
        data["_meta"]["golden_reason"] = why
        resolved[fid] = src
        print(f"  [ok] {fid:18s} <- {src.name}  ({why})")

    if len(resolved) != len(SELECT):
        print(f"\n  {len(resolved)}/{len(SELECT)} resolved — fix the needles first.")
        return 1
    if not args.write:
        print("\n  dry run; re-run with --write")
        return 0

    GOLDEN.mkdir(parents=True, exist_ok=True)
    pins = {}
    for fid, src in resolved.items():
        data = json.loads(src.read_text(encoding="utf-8"))
        data.setdefault("_meta", {})["fixture_id"] = fid
        data["_meta"]["golden_reason"] = SELECT[fid][1]
        dest = GOLDEN / f"{fid}.json"
        dest.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        pins[fid] = _input_hash(dest)

    text = FROZEN_TEST.read_text(encoding="utf-8")
    block = "PINNED: dict[str, str] = {\n" + "".join(
        f'    "{k}": "{v}",\n' for k, v in sorted(pins.items())
    ) + "}"
    text = re.sub(r"PINNED: dict\[str, str\] = \{.*?\n\}", block, text, flags=re.S)
    FROZEN_TEST.write_text(text, encoding="utf-8")

    print(f"\n  wrote {len(pins)} golden fixtures and pinned their hashes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
