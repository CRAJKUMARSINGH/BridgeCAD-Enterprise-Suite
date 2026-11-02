#!/usr/bin/env python3
"""Merge gate. Reads artifacts/TRIAGE_LOG.md — the only source of truth.

Exit codes:  0 pass · 1 blocked · 2 log unreadable/malformed

  python scripts/robot/gate.py                     # full gate, every open S1/S2
  python scripts/robot/gate.py --changed           # gate only entries in the diff
  python scripts/robot/gate.py --changed-file-list f1 f2
  python scripts/robot/gate.py --allow-s2          # S2 warns instead of blocking
  python scripts/robot/gate.py --budget 25         # ratchet on total open count
  python scripts/robot/gate.py --max-age 14        # stale-entry check
  python scripts/robot/gate.py --json              # machine output for CI

Out-of-scope is conservative: an entry with no recorded file path always blocks.
Silence is not permission.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import pathlib
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date

LOG = pathlib.Path("artifacts/TRIAGE_LOG.md")
BLOCKING = {"S1", "S2"}
SEV_ORDER = {"S1": 0, "S2": 1, "S3": 2, "S4": 3}

ROW = re.compile(r"^\|\s*(BCAD-\d{4})\s*\|\s*(S[1-4])\s*\|(.*)$")
BLOCK_HDR = re.compile(r"^###\s+(BCAD-\d{4})\s+—\s*(.*)$")
# Repo-relative paths in a detail block. Flat-repo aware: no packages/apps
# prefix required, so scripts/robot/*.py, docs/*.md and pyproject.toml are all
# recorded as blast-radius paths.
PATH = re.compile(r"(?:^|[\s`(])((?:[\w.\-]+/)*[\w.\-]+\.(?:py|js|ts|tsx|yml|yaml|toml|json|md))")
OPENED = re.compile(r"Opened:\s*(\d{4}-\d{2}-\d{2})")


@dataclass
class Entry:
    id: str
    sev: str
    persona: str
    symptom: str
    status: str
    cls: str = "?"
    paths: list[str] = field(default_factory=list)
    opened: date | None = None


class LogError(Exception):
    pass


def _sections(text: str) -> tuple[str, str]:
    try:
        open_block = text.split("## Open", 1)[1].split("## In progress")[0]
        prog_block = text.split("## In progress", 1)[1].split("## Closed")[0]
    except IndexError as exc:
        raise LogError("missing '## Open' / '## In progress' / '## Closed' headers") from exc
    return open_block, prog_block


def parse(text: str) -> list[Entry]:
    open_block, prog_block = _sections(text)
    entries: dict[str, Entry] = {}

    for block, default_status in ((open_block, "OPEN"), (prog_block, "IN_PROGRESS")):
        for line in block.splitlines():
            m = ROW.match(line.strip())
            if not m:
                continue
            tid, sev, rest = m.groups()
            cells = [c.strip() for c in rest.split("|")]
            if default_status == "OPEN":
                # columns: persona | symptom | class | patch | owner | status
                status = cells[5].upper() if len(cells) > 5 else "OPEN"
                if status != "OPEN":
                    continue  # predicted / UNCONFIRMED rows are not yet findings
            else:
                status = "IN_PROGRESS"
            entries[tid] = Entry(
                id=tid,
                sev=sev,
                persona=cells[0] if cells else "?",
                symptom=cells[1] if len(cells) > 1 else "",
                status=status,
                cls=cells[2] if len(cells) > 2 else "?",
            )

    # detail blocks enrich entries with blast radius + open date
    for block in re.split(r"^###\s+", text, flags=re.M)[1:]:
        m = BLOCK_HDR.match("### " + block.split("\n", 1)[0])
        if not m or m.group(1) not in entries:
            continue
        e = entries[m.group(1)]
        e.paths = sorted({m.group(1) for m in PATH.finditer(block)})
        if d := OPENED.search(block):
            with contextlib.suppress(ValueError):
                e.opened = date.fromisoformat(d.group(1))

    return sorted(entries.values(), key=lambda e: (SEV_ORDER[e.sev], e.id))


def changed_paths(args) -> set[str]:
    if args.changed_file_list:
        return set(args.changed_file_list)
    if not args.changed:
        return set()
    base = args.base or _default_base()
    try:
        out = subprocess.run(
            ["git", "diff", "--name-only", f"{base}..HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except subprocess.CalledProcessError:
        print(f"gate: could not diff against {base}; gating everything", file=sys.stderr)
        return set()
    return {ln for ln in out.splitlines() if ln}


def _default_base() -> str:
    for cand in ("origin/main", "origin/master", "main"):
        if (
            subprocess.run(
                ["git", "rev-parse", "--verify", "--quiet", cand], capture_output=True
            ).returncode
            == 0
        ):
            return cand
    return "HEAD~1"


def in_scope(entry: Entry, changed: set[str]) -> bool:
    if not changed:
        return True
    if not entry.paths:
        return True  # unknown blast radius → assume global
    return any(p in changed for p in entry.paths)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--changed", action="store_true")
    ap.add_argument("--changed-file-list", nargs="*")
    ap.add_argument("--base")
    ap.add_argument("--allow-s2", action="store_true")
    ap.add_argument("--budget", type=int)
    ap.add_argument("--max-age", type=int)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not LOG.exists():
        print(f"gate: {LOG} missing", file=sys.stderr)
        return 2

    try:
        entries = parse(LOG.read_text(encoding="utf-8"))
    except LogError as exc:
        print(f"gate: {exc}", file=sys.stderr)
        return 2

    changed = changed_paths(args) if (args.changed or args.changed_file_list) else set()

    blockers: list[Entry] = []
    skipped: list[Entry] = []
    warnings: list[str] = []

    for e in entries:
        if e.sev not in BLOCKING:
            continue
        if e.sev == "S2" and args.allow_s2:
            warnings.append(f"{e.id} S2 open (allowed): {e.symptom}")
            continue
        if not in_scope(e, changed):
            skipped.append(e)
            continue
        blockers.append(e)
        if args.max_age and e.opened and (date.today() - e.opened).days > args.max_age:
            warnings.append(
                f"{e.id} stale: open {(date.today() - e.opened).days}d (limit {args.max_age})"
            )

    total_open = len([e for e in entries if e.status == "OPEN"])

    if args.json:
        print(
            json.dumps(
                {
                    "blocked": bool(blockers),
                    "blockers": [
                        {"id": e.id, "sev": e.sev, "symptom": e.symptom} for e in blockers
                    ],
                    "out_of_scope": [e.id for e in skipped],
                    "warnings": warnings,
                    "total_open": total_open,
                },
                indent=2,
            )
        )
    else:
        if blockers:
            print(f"\n\033[31mBLOCKED\033[0m — {len(blockers)} open defect(s) in scope\n")
            for e in blockers:
                where = e.paths[0] if e.paths else "no path recorded"
                print(f"  {e.sev}  {e.id}  {where}\n       {e.symptom}")
            print("\n  close them, or: git push --no-verify\n")
        for e in skipped:
            print(f"  out of scope: {e.id} ({e.sev})")
        for w in warnings:
            print(f"  \033[33mwarn\033[0m {w}")

    if args.budget is not None and total_open > args.budget:
        print(f"\n  budget exceeded: {total_open} open > {args.budget}", file=sys.stderr)
        return 1

    return 1 if blockers else 0


if __name__ == "__main__":
    sys.exit(main())
