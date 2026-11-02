#!/usr/bin/env python
"""Write the published BridgeProject JSON Schema (W08).

The schema is generated from the Pydantic model, so it can never drift from the
code that validates it. ``docs/interop.md`` documents the format; this script
emits the machine-readable contract that external tools validate against.

Usage
-----
    python scripts/export_project_schema.py            # write the schema
    python scripts/export_project_schema.py --check    # exit 1 if stale (CI gate)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs" / "schema" / "bridgeproject.schema.json"

for _pkg in ("bridgecad-core", "bridgecad-io"):
    _path = str(REPO / "packages" / _pkg)
    if _path not in sys.path:
        sys.path.insert(0, _path)


def render() -> str:
    """Return the canonical schema text (sorted keys, 2-space indent, trailing NL)."""
    from bridgecad_io.json_adapter import project_schema

    return json.dumps(project_schema(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the checked-in schema matches the model instead of writing it",
    )
    args = parser.parse_args(argv)

    text = render()
    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != text:
            print(f"[FAIL] {OUT.relative_to(REPO)} is stale — run this script without --check")
            return 1
        print(f"[PASS] {OUT.relative_to(REPO)} matches the BridgeProject model")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)} ({len(text):,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
