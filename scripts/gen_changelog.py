#!/usr/bin/env python3
"""Build CHANGELOG.md from the defect ledger and the commit log.

Closures come from the ledger, not from guessing at commit messages. Commits
appear only where they name a defect ID.

    python scripts/gen_changelog.py            # write
    python scripts/gen_changelog.py --check    # exit 1 if stale
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parents[1]
LEDGER = ROOT / "DEFECT-LEDGER.md"
OUT = ROOT / "CHANGELOG.md"

ROW = re.compile(r"^\|\s*(D-\d+)\s*\|\s*(\w+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|", re.M)
HEADER = """# Changelog

Generated from `DEFECT-LEDGER.md` by `scripts/gen_changelog.py`. Do not edit by
hand — edit the ledger and regenerate.

"""
SECTION = {"closed": "Fixed", "wontfix": "Won't fix", "open": "Open"}


def _ledger() -> dict[str, list[tuple[str, str, str]]]:
    out: dict[str, list[tuple[str, str, str]]] = {k: [] for k in SECTION}
    for did, sev, desc, _file in ROW.findall(LEDGER.read_text(encoding="utf-8")):
        status = "closed" if "closed" in desc.lower() else "open"
        out.setdefault(status, []).append((did, sev, desc.strip("* ").strip()))
    return out


def _commits() -> dict[str, str]:
    try:
        log = subprocess.run(
            ["git", "log", "--pretty=%H%x00%s"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {}
    out: dict[str, str] = {}
    for line in log.splitlines():
        if "\x00" not in line:
            continue
        sha, subject = line.split("\x00", 1)
        for did in re.findall(r"D-\d+", subject):
            out.setdefault(did, sha[:7])
    return out


def render() -> str:
    data = _ledger()
    commits = _commits()
    parts = [HEADER, f"## {date.today().isoformat()}\n\n"]
    for key, title in SECTION.items():
        rows = data.get(key) or []
        if not rows:
            continue
        parts.append(f"### {title}\n\n")
        for did, sev, desc in sorted(rows, key=lambda r: int(r[0][2:])):
            sha = commits.get(did)
            parts.append(f"- **{did}** ({sev}) {desc}" + (f" — {sha}" if sha else "") + "\n")
        parts.append("\n")
    return "".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    new = render()
    old = OUT.read_text(encoding="utf-8") if OUT.is_file() else ""

    if args.check:
        if new != old:
            print("  changelog: STALE — run python scripts/gen_changelog.py")
            return 1
        print("  changelog: up to date")
        return 0

    OUT.write_text(new, encoding="utf-8")
    print(f"  wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
