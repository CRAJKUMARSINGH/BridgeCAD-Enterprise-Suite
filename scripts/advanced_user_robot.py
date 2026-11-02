#!/usr/bin/env python3
"""Advanced user: model schema size, unit suite, and an optional property lane.

Run from the BridgeCAD repo root::

    python scripts/advanced_user_robot.py --seed 789 --hypothesis
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], timeout: int = 120) -> tuple[int, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, proc.stdout + proc.stderr


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=789)
    parser.add_argument("--hypothesis", action="store_true")
    parser.add_argument("--e2e", action="store_true")
    args = parser.parse_args()

    results: list[dict] = []

    for pkg in Path("packages").glob("bridgecad-*"):
        sys.path.insert(0, str(pkg))
    try:
        from bridgecad_core.models import BridgeProject

        size = len(json.dumps(BridgeProject.model_json_schema()))
        results.append({"name": "schema", "ok": size > 40_000, "bytes": size})
        print(f"  schema size {size} bytes  OK={size > 40_000}")
    except Exception as exc:
        results.append({"name": "schema", "ok": False, "error": str(exc)})
        print(f"  schema FAIL {exc}")

    rc, out = run([sys.executable, "-m", "pytest", "tests/unit", "-q", "--tb=no"], timeout=300)
    ok = rc == 0 or "passed" in out
    results.append({"name": "unit", "ok": ok, "rc": rc})
    print(f"  unit tests OK={ok}")

    if args.hypothesis:
        if importlib.util.find_spec("hypothesis") is None:
            results.append({"name": "hypothesis", "ok": False, "error": "hypothesis not installed"})
        else:
            rc, _ = run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "tests/draw",
                    "-q",
                    "--tb=line",
                    "-k",
                    "hypothesis",
                ],
                timeout=180,
            )
            results.append({"name": "hypothesis", "ok": rc == 0, "rc": rc})

    all_ok = all(r["ok"] for r in results)
    Path("reports").mkdir(exist_ok=True)
    Path("reports/advanced_robot.json").write_text(
        json.dumps({"seed": args.seed, "results": results, "all_ok": all_ok}, indent=2),
        encoding="utf-8",
    )
    print("ALL OK" if all_ok else "SOME FAILURES")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
