"""CLI: inventory LISP baseline sources into a markdown report.

Usage:
    python scripts/refs_lisp.py references/lisp/*.lsp
    python scripts/refs_lisp.py references/lisp/fixture_min.lsp -o artifacts/lisp_inventory.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "packages" / "bridgecad-refs"))

from bridgecad_refs.lisp_baseline import inventory, report  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Inventory AutoLISP GAD sources")
    ap.add_argument("sources", nargs="+", help=".lsp files to inventory")
    ap.add_argument("-o", "--output", default=None, help="write report here (default: stdout)")
    args = ap.parse_args()

    invs = [inventory(Path(s)) for s in args.sources]
    text = report(invs)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"wrote {out}", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
