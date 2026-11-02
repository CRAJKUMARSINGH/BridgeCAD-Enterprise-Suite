"""Turn robot failures into triage entries. IDs assigned only here.

Ported from the Venice-patch robotic test plan. Run from the repo root:

    python scripts/robot/triage.py --ingest artifacts/robot
    python scripts/robot/triage.py --ingest artifacts/robot --gh --repo OWNER/REPO
    python scripts/robot/triage.py --metrics
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys

LOG = pathlib.Path("artifacts/TRIAGE_LOG.md")
OPEN_HDR = "## Open"
ID_RE = re.compile(r"BCAD-(\d{4})")

SEV_BY_TIER = {"P1_basic": "S1", "P2_intermediate": "S2", "P3_advanced": "S2"}
CLASS_HINT = {
    "ZeroDivisionError": ("VAL", "§1"),
    "nan": ("VAL", "§1"),
    "Traceback": ("UX", "§7"),
    "UnicodeEncodeError": ("ENC", "§10"),
    "PermissionError": ("RACE", "§3"),
    "TimeoutError": ("PERF", "§8"),
}


def next_id(text: str) -> str:
    nums = [int(m) for m in ID_RE.findall(text)] or [0]
    return f"BCAD-{max(nums) + 1:04d}"


def classify(blob: str) -> tuple[str, str]:
    for needle, pair in CLASS_HINT.items():
        if needle.lower() in blob.lower():
            return pair
    return ("UX", "—")


def insert_row(text: str, row: str) -> str:
    """Insert after the Open table header, keeping the separator row intact."""
    lines = text.splitlines()
    start = lines.index(OPEN_HDR)
    for i in range(start, len(lines)):
        if lines[i].startswith("|---"):
            lines.insert(i + 1, row)
            return "\n".join(lines) + "\n"
    raise SystemExit("Open table not found — restore the header in TRIAGE_LOG.md")


def ingest(path: pathlib.Path, gh: bool, repo: str | None) -> int:
    text = LOG.read_text(encoding="utf-8")
    created = 0
    for report in sorted(path.glob("*_report.json")):
        data = json.loads(report.read_text(encoding="utf-8"))
        if not data.get("failures"):
            continue
        persona = data["persona"]
        for fail in data["failures"]:
            blob = fail.get("text") or json.dumps(fail.get("js_errors", []))
            cls, patch = classify(blob)
            tid = next_id(text)
            first = blob.strip().splitlines()[0][:110].replace("|", "\\|")
            row = (
                f"| {tid} | {SEV_BY_TIER.get(persona, 'S3')} | {persona} | "
                f"{first} | {cls} | {patch} | — | OPEN |"
            )
            text = insert_row(text, row)
            created += 1
            if gh and repo:
                _gh_issue(repo, tid, persona, data["seed"], fail, cls)
    LOG.write_text(text, encoding="utf-8")
    print(f"{created} entr{'y' if created == 1 else 'ies'} opened in {LOG}")
    return 1 if created else 0


def _gh_issue(repo, tid, persona, seed, fail, cls):
    body = (
        f"Triage: {tid}\nPersona: {persona} seed {seed}\n"
        f"Class: {cls}\n\n```\n{fail.get('text', '')[:3000]}\n```\n"
        f"Artifact: {fail.get('shot', 'n/a')}"
    )
    subprocess.run(
        [
            "gh",
            "issue",
            "create",
            "--repo",
            repo,
            "--title",
            f"[{tid}] {persona} failure",
            "--body",
            body,
            "--label",
            "defect",
        ],
        check=False,
    )


def metrics() -> int:
    """Count only rows whose Status cell is OPEN — predictions do not block."""
    text = LOG.read_text(encoding="utf-8")
    open_block = text.split(OPEN_HDR, 1)[1].split("## In progress")[0]
    s1 = s2 = 0
    for line in open_block.splitlines():
        stripped = line.strip()
        if not stripped.startswith("| BCAD-"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 3 or cells[-1].upper() != "OPEN":
            continue
        s1 += cells[1] == "S1"
        s2 += cells[1] == "S2"
    print(f"open S1={s1} S2={s2}")
    return 1 if s1 or s2 else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ingest", type=pathlib.Path)
    ap.add_argument("--gh", action="store_true")
    ap.add_argument("--repo")
    ap.add_argument("--metrics", action="store_true")
    a = ap.parse_args()
    if a.metrics:
        sys.exit(metrics())
    if not a.ingest:
        ap.print_help()
        sys.exit(2)
    sys.exit(ingest(a.ingest, a.gh, a.repo))
