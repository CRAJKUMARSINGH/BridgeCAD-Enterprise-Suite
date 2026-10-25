#!/usr/bin/env python3
"""Enforce performance budgets against a pytest-benchmark JSON report.

Budget file schema (JSON):

    {
      "defaults": { "metric": "median", "warn_ratio": 0.85, "max_seconds": null },
      "budgets": {
        "test_gad_generation": {
          "max_seconds": 5.0,
          "max_peak_mb": 512,
          "note": "30 m span, 4-lane, single render"
        },
        "tests/benchmarks/*::test_hundred_sheet_project": { "max_seconds": 60.0 }
      }
    }

Keys match a benchmark's `name` or `fullname` exactly, or as an fnmatch glob.

Usage:
    python scripts/check_perf_budgets.py bench.json
    python scripts/check_perf_budgets.py bench.json --budgets tests/benchmarks/budgets.json
    python scripts/check_perf_budgets.py bench.json --strict --json-out perf-report.json

Exit codes:
    0  every measured benchmark is within budget
    1  one or more budgets breached (or --strict and a benchmark is unbudgeted)
    2  bad input or bad configuration
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import sys
from pathlib import Path

VALID_METRICS = ("min", "median", "mean", "max")
DEFAULT_WARN_RATIO = 0.85
BYTES_PER_MB = 1024 * 1024


# --------------------------------------------------------------------- utils
def fail(msg: str) -> SystemExit:
    print(f"error: {msg}", file=sys.stderr)
    return SystemExit(2)


def fmt_seconds(value: float) -> str:
    if value < 1:
        return f"{value * 1000:.1f} ms"
    return f"{value:.3f} s"


def fmt_mb(value_bytes: float) -> str:
    return f"{value_bytes / BYTES_PER_MB:.1f} MB"


def read_json(path: Path, what: str) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise fail(f"{what} not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise fail(f"{what} is not valid JSON ({path}): {exc}") from exc


# ------------------------------------------------------------------- budgets
def load_budgets(path: Path) -> tuple[dict, dict[str, dict]]:
    data = read_json(path, "budget file")
    if not isinstance(data, dict):
        raise fail(f"budget file must be a JSON object: {path}")

    defaults = data.get("defaults") or {}
    if not isinstance(defaults, dict):
        raise fail("'defaults' must be an object")

    metric = defaults.get("metric", "median")
    if metric not in VALID_METRICS:
        raise fail(f"defaults.metric must be one of {VALID_METRICS}, got {metric!r}")

    warn_ratio = defaults.get("warn_ratio", DEFAULT_WARN_RATIO)
    if not isinstance(warn_ratio, int | float) or not 0 < warn_ratio < 1:
        raise fail("defaults.warn_ratio must be a number strictly between 0 and 1")

    budgets = data.get("budgets") or {}
    if not isinstance(budgets, dict) or not budgets:
        raise fail("budget file has no 'budgets' entries")

    for key, spec in budgets.items():
        if not isinstance(spec, dict):
            raise fail(f"budget for {key!r} must be an object")
        if "max_seconds" not in spec and "max_peak_mb" not in spec:
            raise fail(f"budget for {key!r} needs max_seconds and/or max_peak_mb")
        if spec.get("metric", metric) not in VALID_METRICS:
            raise fail(f"budget for {key!r} has an invalid metric")

    return defaults, budgets


def resolve(budgets: dict[str, dict], name: str, fullname: str) -> tuple[str, dict] | None:
    """Exact name, exact fullname, then glob — most specific first."""
    if name in budgets:
        return name, budgets[name]
    if fullname in budgets:
        return fullname, budgets[fullname]
    for key, spec in budgets.items():
        if fnmatch.fnmatchcase(fullname, key) or fnmatch.fnmatchcase(name, key):
            return key, spec
    return None


# --------------------------------------------------------------------- input
def load_benchmarks(path: Path) -> list[dict]:
    data = read_json(path, "benchmark report")
    if not isinstance(data, dict) or not isinstance(data.get("benchmarks"), list):
        raise fail(f"{path} is not a pytest-benchmark report (no 'benchmarks' array)")
    return [b for b in data["benchmarks"] if isinstance(b, dict)]


def measured_seconds(entry: dict, metric: str) -> float | None:
    stats = entry.get("stats") or {}
    value = stats.get(metric)
    if value is None and metric != "median":
        value = stats.get("median")
    return float(value) if isinstance(value, int | float) else None


def measured_peak_bytes(entry: dict) -> float | None:
    for source in (entry.get("memory") or {}, entry.get("stats") or {}):
        for key in ("max_peak", "peak", "max_size", "max"):
            value = source.get(key)
            if isinstance(value, int | float) and value > 0:
                return float(value)
    return None


# -------------------------------------------------------------------- report
def evaluate(entries, budgets, defaults, cli_metric) -> tuple[list[dict], list[dict], list[str]]:
    rows: list[dict] = []
    unbudgeted: list[str] = []
    errors: list[str] = []

    for entry in entries:
        name = str(entry.get("name") or "<unnamed>")
        fullname = str(entry.get("fullname") or name)

        match = resolve(budgets, name, fullname)
        if match is None:
            unbudgeted.append(fullname)
            continue

        key, spec = match
        metric = cli_metric or spec.get("metric") or defaults.get("metric", "median")
        warn_ratio = float(spec.get("warn_ratio", defaults.get("warn_ratio", DEFAULT_WARN_RATIO)))

        row = {
            "name": name,
            "fullname": fullname,
            "budget_key": key,
            "metric": metric,
            "note": spec.get("note", ""),
            "status": "pass",
        }

        seconds = measured_seconds(entry, metric)
        if "max_seconds" in spec:
            if seconds is None:
                errors.append(f"{fullname}: no '{metric}' in report but max_seconds is set")
            else:
                limit = float(spec["max_seconds"])
                row["seconds"] = seconds
                row["seconds_limit"] = limit
                ratio = seconds / limit if limit else 0.0
                row["seconds_ratio"] = ratio
                if ratio > 1.0:
                    row["status"] = "fail"
                elif ratio >= warn_ratio:
                    row["status"] = "warn"

        peak = measured_peak_bytes(entry)
        if "max_peak_mb" in spec:
            if peak is None:
                row["memory_unmeasured"] = True
            else:
                limit_bytes = float(spec["max_peak_mb"]) * BYTES_PER_MB
                row["peak_bytes"] = peak
                row["peak_limit_bytes"] = limit_bytes
                ratio = peak / limit_bytes if limit_bytes else 0.0
                row["peak_ratio"] = ratio
                if ratio > 1.0:
                    row["status"] = "fail"
                elif ratio >= warn_ratio and row["status"] == "pass":
                    row["status"] = "warn"

        rows.append(row)

    return rows, [{"fullname": n} for n in unbudgeted], errors


def render(
    rows: list[dict], unbudgeted: list[dict], errors: list[str], budget_path: Path, strict: bool
) -> tuple[str, int]:
    out: list[str] = ["Performance budgets", f"budgets: {budget_path}", ""]

    for row in sorted(rows, key=lambda r: r["fullname"]):
        label = {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}[row["status"]]
        out.append(f"[{label}] {row['fullname']}")
        if "seconds" in row:
            ratio = row["seconds_ratio"]
            out.append(
                f"        {row['metric']}: {fmt_seconds(row['seconds'])} "
                f"/ {fmt_seconds(row['seconds_limit'])}  ({ratio:.0%} of budget)"
            )
        if "peak_bytes" in row:
            ratio = row["peak_ratio"]
            out.append(
                f"        peak memory: {fmt_mb(row['peak_bytes'])} "
                f"/ {fmt_mb(row['peak_limit_bytes'])}  ({ratio:.0%} of budget)"
            )
        if row.get("memory_unmeasured"):
            out.append("        peak memory: not measured (report has no memory data)")
        if row["note"]:
            out.append(f"        note: {row['note']}")
        out.append("")

    if unbudgeted:
        header = "FAIL" if strict else "WARN"
        out.append(f"[{header}] {len(unbudgeted)} benchmark(s) have no budget entry:")
        for item in sorted(unbudgeted, key=lambda u: u["fullname"]):
            out.append(f"        {item['fullname']}")
        out.append("")

    if errors:
        for err in errors:
            out.append(f"[FAIL] {err}")
        out.append("")

    failed = [r for r in rows if r["status"] == "fail"]
    warned = [r for r in rows if r["status"] == "warn"]

    if failed or errors:
        out.append(
            f"Result: {len(failed)} breached, {len(warned)} warning(s), "
            f"{len(rows) - len(failed) - len(warned)} clean."
        )
        code = 1
    elif unbudgeted and strict:
        out.append(
            f"Result: all budgets met, but {len(unbudgeted)} benchmark(s) unbudgeted (--strict)."
        )
        code = 1
    else:
        out.append(
            f"Result: all {len(rows)} budgeted benchmark(s) within limits"
            + (f", {len(warned)} approaching." if warned else ".")
        )
        code = 0

    return "\n".join(out) + "\n", code


# ---------------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("report", help="path to a pytest-benchmark JSON report")
    parser.add_argument(
        "--budgets",
        default="tests/benchmarks/budgets.json",
        help="budget file (default: tests/benchmarks/budgets.json)",
    )
    parser.add_argument(
        "--metric",
        choices=VALID_METRICS,
        default=None,
        help="override the metric for all benchmarks",
    )
    parser.add_argument(
        "--strict", action="store_true", help="fail if any benchmark has no budget entry"
    )
    parser.add_argument("--json-out", help="write a machine-readable report here")
    args = parser.parse_args(argv)

    report_path = Path(args.report)
    budget_path = Path(args.budgets)

    if not report_path.exists():
        raise fail(f"benchmark report not found: {report_path}")

    defaults, budgets = load_budgets(budget_path)
    entries = load_benchmarks(report_path)

    if not entries:
        print("warn: benchmark report contains no benchmarks", file=sys.stderr)

    rows, unbudgeted, errors = evaluate(entries, budgets, defaults, args.metric)
    text, code = render(rows, unbudgeted, errors, budget_path, args.strict)

    sys.stdout.write(text)

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        try:
            with Path(summary).open("a", encoding="utf-8") as fh:
                fh.write("```\n" + text + "```\n")
        except OSError:
            pass

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(
                {
                    "status": "fail" if code else "pass",
                    "budgets_file": str(budget_path),
                    "results": rows,
                    "unbudgeted": [u["fullname"] for u in unbudgeted],
                    "errors": errors,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    return code


if __name__ == "__main__":
    raise SystemExit(main())
