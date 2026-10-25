#!/usr/bin/env python3
"""Single verification entry point for the documentation system.

Runs every available check, emits machine-readable JSON, exits 0 or 1.
Safe to run locally, in CI, or from an agent loop.

Missing optional tools (lychee, mkdocs, sphinx) report as `skip`, never `fail`
— an absent binary is not a broken repo.

Usage:
    python scripts/verify_docs.py            # human-readable
    python scripts/verify_docs.py --json     # machine-readable
    python scripts/verify_docs.py --only paths,integrity
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PASS, FAIL, SKIP = "pass", "fail", "skip"


class Result(dict):
    def __init__(self, name: str, status: str, detail: str = "", ms: int = 0):
        super().__init__(name=name, status=status, detail=detail, duration_ms=ms)


def _run(name: str, cmd: list[str], *, needs: str | None = None) -> Result:
    if needs and shutil.which(needs) is None:
        return Result(name, SKIP, f"{needs} not installed")

    started = time.monotonic()
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    ms = int((time.monotonic() - started) * 1000)

    if proc.returncode == 0:
        return Result(name, PASS, "", ms)

    tail = (proc.stdout + proc.stderr).strip().splitlines()[-25:]
    return Result(name, FAIL, "\n".join(tail), ms)


def check_paths() -> Result:
    return _run("code-block paths", [sys.executable, "scripts/check_doc_paths.py"])


def check_integrity() -> Result:
    return _run(
        "doc integrity tests",
        [sys.executable, "-m", "pytest", "tests/docs/test_doc_integrity.py", "-q", "--no-header"],
    )


def check_selftest() -> Result:
    return _run(
        "gate self-tests",
        [sys.executable, "-m", "pytest", "tests/docs/test_gates_selfcheck.py", "-q", "--no-header"],
    )


def check_links() -> Result:
    if shutil.which("lychee") is None:
        return Result("external + internal links", SKIP, "lychee not installed")
    return _run(
        "external + internal links",
        ["lychee", "--config", ".lychee.toml", "--no-progress", "**/*.md"],
    )


def check_mkdocs() -> Result:
    if shutil.which("mkdocs") is None:
        return Result("mkdocs strict build", SKIP, "mkdocs not installed")
    return _run("mkdocs strict build", ["mkdocs", "build", "--strict", "-q"])


def check_sphinx() -> Result:
    if shutil.which("sphinx-build") is None:
        return Result("sphinx api build", SKIP, "sphinx-build not installed")
    _run("api stubs", [sys.executable, "scripts/gen_api_stubs.py"])
    return _run(
        "sphinx api build",
        [
            "sphinx-build",
            "-W",
            "--keep-going",
            "-q",
            "-b",
            "html",
            "docs/api",
            "docs/api/_build/html",
        ],
    )


CHECKS = {
    "paths": check_paths,
    "integrity": check_integrity,
    "selftest": check_selftest,
    "links": check_links,
    "mkdocs": check_mkdocs,
    "sphinx": check_sphinx,
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--only", default=None, help=f"comma-separated subset of: {','.join(CHECKS)}")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    names = args.only.split(",") if args.only else list(CHECKS)
    unknown = [n for n in names if n not in CHECKS]
    if unknown:
        print(f"unknown check(s): {unknown}", file=sys.stderr)
        return 2

    results: list[Result] = []
    for name in names:
        if not args.quiet and not args.json:
            print(f"  running {name} ...", file=sys.stderr, flush=True)
        results.append(CHECKS[name]())

    summary = {
        PASS: sum(1 for r in results if r["status"] == PASS),
        FAIL: sum(1 for r in results if r["status"] == FAIL),
        SKIP: sum(1 for r in results if r["status"] == SKIP),
    }
    ok = summary[FAIL] == 0

    if args.json:
        print(json.dumps({"ok": ok, "checks": results, "summary": summary}, indent=2))
    else:
        for r in results:
            mark = {PASS: "PASS", FAIL: "FAIL", SKIP: "SKIP"}[r["status"]]
            print(f"  [{mark}] {r['name']}  ({r['duration_ms']}ms)")
            if r["detail"]:
                for line in r["detail"].splitlines():
                    print(f"         {line}")
        print(f"\n  {summary[PASS]} passed, {summary[FAIL]} failed, {summary[SKIP]} skipped")
        print("  documentation verification OK" if ok else "  documentation verification FAILED")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
