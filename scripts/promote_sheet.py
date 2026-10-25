#!/usr/bin/env python3
"""Promote a drawing sheet from `scaffold` to `promoted` — or say why not.

THE RULE
    A sheet's status lives in exactly one place: tests/draw/sheets.spec.json.
    Promotion is one word in that file plus making the full-spec assertions pass.
    There is no third path. This script is the one command that does it, so a
    failed promotion leaves the spec byte-identical to how it started.

WHAT IT PRINTS
    `--status` prints the promotion board — the count the CI summary shows.
    `--sheet NAME` flips the spec, runs that sheet's assertions, then either
    keeps the promotion (PROMOTED, new spec sha) or restores the file exactly
    (REVERTED, spec sha unchanged).

Usage:
    python scripts/promote_sheet.py --status
    python scripts/promote_sheet.py --sheet sheet4_foundation
    python scripts/promote_sheet.py --sheet sheet4_foundation --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "tests" / "draw" / "sheets.spec.json"
LOG = ROOT / "tests" / "draw" / "_artifacts" / "promotions.log"


def sha8(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:8]


def load() -> tuple[bytes, dict]:
    raw = SPEC.read_bytes()
    return raw, json.loads(raw.decode("utf-8"))


def board(spec: dict) -> str:
    sheets: dict = spec["sheets"]
    rows = sorted(sheets.items())
    width = max(len(name) for name, _ in rows)
    lines = [f"{'sheet'.ljust(width)}  status", f"{'-' * width}  ------"]
    lines += [f"{name.ljust(width)}  {body['status']}" for name, body in rows]
    promoted = sum(1 for _, body in rows if body["status"] == "promoted")
    lines += ["", f"{promoted}/{len(rows)} promoted"]
    return "\n".join(lines)


def run_assertions(sheet: str) -> subprocess.CompletedProcess:
    """Every test that mentions the sheet, plus the full-spec gate for it."""
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/draw",
            "-m",
            "draw",
            "-q",
            "--no-header",
            "--tb=line",
            "-k",
            sheet,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def failures(output: str) -> list[str]:
    """pytest's short summary: FAILED for a failed test, ERROR for a collection
    error — a sheet that cannot even be collected has not been promoted either."""
    return [line.strip() for line in output.splitlines() if line.startswith(("FAILED", "ERROR"))]


def log(record: dict) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


def promote(sheet: str, *, dry_run: bool) -> int:
    original, spec = load()
    sheets = spec["sheets"]

    if sheet not in sheets:
        print(f"unknown sheet {sheet!r}; known: {', '.join(sorted(sheets))}", file=sys.stderr)
        return 2

    if sheets[sheet]["status"] == "promoted":
        print(f"{sheet} is already promoted — nothing to do.")
        return 0

    before = sha8(original)
    if dry_run:
        print(f"would promote {sheet} (spec sha {before}) — no change written")
        return 0

    print(f"promoting {sheet} — running full-spec assertions ...", flush=True)

    sheets[sheet]["status"] = "promoted"
    SPEC.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")

    started = time.monotonic()
    proc = run_assertions(sheet)
    elapsed = round(time.monotonic() - started, 1)

    if proc.returncode == 0:
        after = sha8(SPEC.read_bytes())
        print(f"PROMOTED {sheet} (spec sha {before} -> {after}, {elapsed}s)")
        log(
            {
                "sheet": sheet,
                "result": "promoted",
                "spec_sha_before": before,
                "spec_sha_after": after,
                "seconds": elapsed,
            }
        )
        print()
        print(board(json.loads(SPEC.read_text(encoding="utf-8"))))
        return 0

    SPEC.write_bytes(original)
    print(f"REVERTED — {sheet} stays scaffold (spec sha {before} unchanged)")
    missing = failures(proc.stdout + proc.stderr)
    if missing:
        print("what is missing:")
        for line in missing:
            print(f"  {line}")
    log(
        {
            "sheet": sheet,
            "result": "reverted",
            "spec_sha_before": before,
            "spec_sha_after": before,
            "seconds": elapsed,
            "failures": missing,
        }
    )
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--status", action="store_true", help="print the promotion board and exit")
    ap.add_argument("--sheet", default=None, help="sheet to promote")
    ap.add_argument(
        "--dry-run", action="store_true", help="show what a promotion would change, write nothing"
    )
    args = ap.parse_args()

    if args.status:
        _, spec = load()
        print(board(spec))
        return 0

    if not args.sheet:
        ap.error("give --status or --sheet NAME")

    return promote(args.sheet, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
