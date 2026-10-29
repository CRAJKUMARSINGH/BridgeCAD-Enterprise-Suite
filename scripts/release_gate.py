#!/usr/bin/env python3
"""Week-48 release gate.

Refuses unless every condition in MASTER-PLAN §Q4 holds. Writes
build/release-gate.json, which bridgecad_export reads to decide whether the
manifest may say `construction_ready`.

    python scripts/release_gate.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).parents[1]
LEDGER = ROOT / "docs" / "upgrade" / "DEFECT-LEDGER.md"
SIGNOFF = ROOT / "docs" / "upgrade" / "SIGNOFF.md"
REPORT = ROOT / "build" / "release-gate.json"

MIN_ASSERTIONS = 90
MIN_TRACEABILITY_PCT = 90.0
MIN_SIGNED_FAMILIES = 5


def _run(cmd: list[str]) -> tuple[bool, str]:
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return p.returncode == 0, (p.stdout + p.stderr).strip().splitlines()[-1:] and (
        p.stdout + p.stderr
    ).strip()[-400:]


def check_open_blockers() -> tuple[bool, str]:
    if not LEDGER.is_file():
        return False, "ledger missing"
    open_rows = re.findall(r"^\|\s*(D-\d+)\s*\|\s*blocker\s*\|.*\|\s*open\s*\|", LEDGER, re.M)
    if open_rows:
        return False, f"{len(open_rows)} open blocker(s): {open_rows[:5]}"
    return True, "no open blockers"


def check_signed_families() -> tuple[bool, str]:
    if not SIGNOFF.is_file():
        return False, "no SIGNOFF.md"
    signed = len(re.findall(r"^\|\s*(simple_12m|continuous_3x12m|girder_4x18m|box_culvert_8m|skew_15deg)\s*\|.*\|\s*☑\s*\|", SIGNOFF.read_text(), re.M))
    if signed < MIN_SIGNED_FAMILIES:
        return False, f"{signed}/{MIN_SIGNED_FAMILIES} families signed"
    return True, f"{signed} families signed"


def check_harness() -> tuple[bool, str]:
    ok, out = _run([sys.executable, "-m", "pytest", "tests/draw", "-q", "--tb=no", "-p", "no:cacheprovider"])
    if not ok:
        return False, "assertion harness failed"
    passed = re.search(r"(\d+) passed", out)
    n = int(passed.group(1)) if passed else 0
    if n < MIN_ASSERTIONS:
        return False, f"{n} assertions, need {MIN_ASSERTIONS}"
    return True, f"{n} assertions green"


def check_visual() -> tuple[bool, str]:
    ok, out = _run([sys.executable, "-m", "pytest", "tests/visual", "-q", "--tb=no", "-p", "no:cacheprovider"])
    return (True, "visual regression green") if ok else (False, "visual regression failed")


def check_traceability() -> tuple[bool, str]:
    ok, out = _run([sys.executable, "scripts/check_traceability.py"])
    if ok:
        return True, "traceability >= gate"
    m = re.search(r"coverage: \d+/\d+ layers \((\d+)%\)", out)
    return False, f"traceability {m.group(1) + '%' if m else 'below gate'}"


def check_text_heights() -> tuple[bool, str]:
    ok, _ = _run([sys.executable, "scripts/check_text_heights.py"])
    return (True, "text heights derived") if ok else (False, "numeric text heights remain")


def check_boq_provenance() -> tuple[bool, str]:
    ok, out = _run([sys.executable, "scripts/check_boq_provenance.py"])
    return (True, "BOQ provenance clean") if ok else (False, out or "provenance audit failed")


CHECKS = [
    ("open_blockers", check_open_blockers),
    ("signed_families", check_signed_families),
    ("harness", check_harness),
    ("visual_regression", check_visual),
    ("traceability", check_traceability),
    ("text_heights", check_text_heights),
    ("boq_provenance", check_boq_provenance),
]


def main() -> int:
    results = []
    for name, fn in CHECKS:
        try:
            ok, detail = fn()
        except Exception as exc:
            ok, detail = False, f"check crashed: {exc}"
        results.append({"check": name, "ok": ok, "detail": detail})
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")

    overall = all(r["ok"] for r in results)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({
        "schema": "release-gate/1",
        "generated_at": datetime.now(UTC).isoformat(),
        "overall": "pass" if overall else "fail",
        "checks": results,
    }, indent=2))

    print()
    print(f"  gate: {'*** PASS ***' if overall else 'FAIL'}")
    print(f"  report: {REPORT.relative_to(ROOT)}")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
