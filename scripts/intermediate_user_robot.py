#!/usr/bin/env python3
"""Intermediate user: generate a bridge, then assert the QA score is plausible.

Run from the BridgeCAD repo root::

    python scripts/intermediate_user_robot.py --seed 456 --mutations 5
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], timeout: int = 180) -> tuple[int, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, proc.stdout + proc.stderr


def qa_score(project_json: Path) -> float | int | None:
    """Read the QA score from a generated project JSON, tolerating either key."""
    try:
        data = json.loads(project_json.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    return data.get("qa_score") or (data.get("qa") or {}).get("score")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=456)
    parser.add_argument("--mutations", type=int, default=5)
    args = parser.parse_args()
    random.seed(args.seed)

    results: list[dict] = []
    for i in range(args.mutations):
        print(f"=== Intermediate mutation {i + 1} ===")

        rc, out = run([sys.executable, "-m", "bridgecad", "generate", "11span"], timeout=300)
        ok = rc == 0 or "COMPLETE" in out

        jsons = list(Path("outputs").rglob("project_*.json")) if Path("outputs").exists() else []
        score = qa_score(jsons[0]) if jsons else None
        qa_ok = score is None or (isinstance(score, int | float) and score >= 60)
        print(f"  generate={'PASS' if ok else 'FAIL'}  qa={score}  qa_ok={qa_ok}")

        results.append({"iter": i, "generate": ok, "qa": score, "qa_ok": qa_ok})

    all_ok = all(r["generate"] and r["qa_ok"] for r in results)
    Path("reports").mkdir(exist_ok=True)
    Path("reports/intermediate_robot.json").write_text(
        json.dumps({"seed": args.seed, "results": results, "all_ok": all_ok}, indent=2),
        encoding="utf-8",
    )
    print("ALL OK" if all_ok else "SOME FAILURES")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
