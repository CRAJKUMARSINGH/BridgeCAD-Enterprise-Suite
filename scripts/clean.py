#!/usr/bin/env python3
"""Selectable workspace cleaner for BridgeCAD Enterprise Suite.

Removes only regenerable artifacts — build output, caches, test dumps, stale
git locks, old temp files and AI-IDE cache directories. Every category is
listed up front and can be unticked before anything is deleted, so a run never
takes more than the user approved.

Standing rule: cleaning never stops running processes. Browser binaries under
``.playwright-browsers/`` and AI/tooling state are never touched, no process
is killed, and outside-the-repo cleaning is limited to whitelisted cache
subdirectories and aged temp files — IDE settings, sign-ins, Local Storage
and profiles are never deleted. Locked files are skipped.

    python scripts/clean.py                    # interactive: untick what to skip
    python scripts/clean.py --list             # show categories, remove nothing
    python scripts/clean.py --dry-run          # show what would be removed
    python scripts/clean.py --yes              # clean everything, no prompts
    python scripts/clean.py --skip pytest,mypy # everything except these
    python scripts/clean.py --only dist,pycache
    python scripts/clean.py --stats            # pre/post stats report for this PC

Every real run records pre- and post-clean statistics (free space before and
after, bytes freed overall and per category, paths removed, duration) to a
per-machine file under the user profile — ``~/.bridgecad/clean_stats.json`` —
so the counter works on any PC. On every 50th run a full statistics report is
printed automatically, including a per-category breakdown that highlights the
AI-tools/machine categories (``os-temp``, ``ide-caches``);
``python scripts/clean.py --stats`` prints it on demand, ``--no-stats`` opts
out.

Or via make::

    make clean                      # all categories (non-interactive)
    make clean SKIP=pytest,mypy     # untick equivalent
    make clean-select               # interactive picker
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

#: Per-machine run statistics live under the user profile so the counter and
#: reports work on any PC without touching the repository or git history.
STATS_DIR = Path.home() / ".bridgecad"
STATS_FILE = STATS_DIR / "clean_stats.json"
#: Print the full pre/post statistics report on every Nth recorded run.
STATS_EVERY = 50

#: Names that must never be deleted, anywhere in the tree.
PROTECTED_NAMES = {
    ".git",
    ".github",
    ".agents",
    ".env",
    ".env.example",
    ".playwright-browsers",
    "ATTACHED ASSETS",
    "CODE-JUNCTION",
    "node_modules",
}

#: Directories pruned while searching for ``__pycache__`` — keeps the walk
#: fast and guarantees dependency trees are never entered.
WALK_PRUNE = PROTECTED_NAMES | {".venv", "venv", "dist", "build"}


@dataclass(frozen=True)
class CleanItem:
    """One selectable cleanup category."""

    id: str
    label: str
    description: str
    # (glob, is_dir) pairs relative to the repo root; "**" globs match
    # recursively. Dirs are removed with shutil.rmtree, files with unlink.
    targets: tuple[tuple[str, bool], ...] = field(default_factory=tuple)
    # Optional callable run instead of path deletion (e.g. stale git locks).
    runner: object = None
    # Optional callable returning concrete paths outside the glob model
    # (dynamic discovery, absolute paths, age filters).
    resolver: object = None
    # Skip files locked by running apps instead of reporting failures.
    ignore_errors: bool = False


def _git_locks(root: Path, dry_run: bool) -> list[str]:
    """Clear stale git locks via scripts/clear_stale_locks.py (never --force)."""
    script = root / "scripts" / "clear_stale_locks.py"
    cmd = [sys.executable, str(script), "--root", str(root)]
    if dry_run:
        cmd.append("--dry-run")
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    out = (proc.stdout or "") + (proc.stderr or "")
    return [line for line in out.splitlines() if line.strip()]


def _pycache_dirs(root: Path) -> list[Path]:
    """All __pycache__ dirs, pruning protected and dependency trees."""
    found: list[Path] = []
    for dirpath, dirnames, _ in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in WALK_PRUNE]
        if Path(dirpath).name == "__pycache__":
            found.append(Path(dirpath))
            dirnames[:] = []
    return found


def _node_modules_dirs(root: Path) -> list[Path]:
    """All node_modules dirs, never descending inside them."""
    found: list[Path] = []
    for dirpath, dirnames, _ in os.walk(root):
        dirnames[:] = [
            d for d in dirnames if d not in WALK_PRUNE or d == "node_modules"
        ]
        if Path(dirpath).name == "node_modules":
            found.append(Path(dirpath))
            dirnames[:] = []
    return found


#: Temp files younger than this are left alone — they may belong to running
#: installers or the tools the user is working in right now.
TEMP_MAX_AGE_DAYS = 7


def _old_temp_files(_root: Path) -> list[Path]:
    """Files in the system temp dir older than TEMP_MAX_AGE_DAYS.

    Files only — old temp *directories* may still contain files a running
    program is using, so they are never removed wholesale.
    """
    temp = Path(tempfile.gettempdir())
    cutoff = time.time() - TEMP_MAX_AGE_DAYS * 86400
    try:
        entries = list(temp.iterdir())
    except OSError:
        return []
    out: list[Path] = []
    for entry in entries:
        try:
            if entry.is_file() and entry.stat().st_mtime < cutoff:
                out.append(entry)
        except OSError:
            continue
    return out


#: AI IDE / editor folders under %APPDATA% whose *caches* may be cleaned.
#: Only whitelisted cache subdirectories are ever touched — settings,
#: sign-ins, Local Storage, IndexedDB, Preferences and User profiles stay.
IDE_DIR_NAMES = (
    "Antigravity IDE",
    "Cursor",
    "Kiro",
    "Qoder",
    "Replit",
    "Trae",
    "devin",
    "Windsurf",
)

#: Cache-only subdirectory names probed inside each IDE folder. Anything not
#: listed here (Local Storage, Session Storage, IndexedDB, Network,
#: Preferences, User, Backups, Local State, ...) is never deleted.
IDE_CACHE_SUBDIRS = (
    "Cache",
    "Code Cache",
    "CachedData",
    "CachedConfigurations",
    "CachedProfilesData",
    "CachedExtensionVSIXs",
    "GPUCache",
    "DawnGraphiteCache",
    "DawnWebGPUCache",
    "Crashpad",
    "logs",
    "blob_storage",
)
IDE_SERVICE_WORKER_CACHES = ("CacheStorage", "ScriptCache")


def _ide_cache_dirs(_root: Path) -> list[Path]:
    """Cache directories inside each known AI IDE's %APPDATA% folder."""
    roaming = Path.home() / "AppData" / "Roaming"
    out: list[Path] = []
    for ide in IDE_DIR_NAMES:
        base = roaming / ide
        if not base.is_dir():
            continue
        for name in IDE_CACHE_SUBDIRS:
            candidate = base / name
            if candidate.is_dir():
                out.append(candidate)
        service_worker = base / "Service Worker"
        for name in IDE_SERVICE_WORKER_CACHES:
            candidate = service_worker / name
            if candidate.is_dir():
                out.append(candidate)
    return out


ITEMS: tuple[CleanItem, ...] = (
    CleanItem(
        id="dist",
        label="Build artifacts",
        description="build/, dist/ and *.egg-info — regenerated by `make build` / pip install",
        targets=(
            ("build", True),
            ("dist", True),
            ("*.egg-info", True),
            ("**/*.egg-info", True),
        ),
    ),
    CleanItem(
        id="pycache",
        label="Python bytecode caches",
        description="every __pycache__/ directory outside dependency trees",
        resolver=_pycache_dirs,
    ),
    CleanItem(
        id="pytest",
        label="pytest cache",
        description=".pytest_cache/ — last-run state for pytest",
        targets=((".pytest_cache", True),),
    ),
    CleanItem(
        id="mypy",
        label="mypy cache",
        description=".mypy_cache/ — incremental type-check state",
        targets=((".mypy_cache", True),),
    ),
    CleanItem(
        id="ruff",
        label="ruff cache",
        description=".ruff_cache/ — linter cache",
        targets=((".ruff_cache", True),),
    ),
    CleanItem(
        id="hypothesis",
        label="Hypothesis cache",
        description=".hypothesis/ — property-test example database",
        targets=((".hypothesis", True),),
    ),
    CleanItem(
        id="coverage",
        label="Coverage output",
        description=".coverage, coverage.xml, htmlcov/ — regenerated by `make cov`",
        targets=(
            (".coverage", False),
            ("coverage.xml", False),
            ("htmlcov", True),
        ),
    ),
    CleanItem(
        id="robot-artifacts",
        label="Robot run dumps",
        description="artifacts/robot/ and artifacts/browser_check/ — per-run screenshots/traces "
        "(tracked artifacts/TRIAGE_LOG.md is kept)",
        targets=(
            ("artifacts/robot", True),
            ("artifacts/browser_check", True),
            (".screenshots", True),
        ),
    ),
    CleanItem(
        id="draw-baselines",
        label="Draw baseline hashes",
        description="tests/draw/baselines/*.hash — forces PNG baseline re-verification "
        "(see `make wing-rebaseline`)",
        targets=(("tests/draw/baselines/*.hash", False),),
    ),
    CleanItem(
        id="node-modules",
        label="Node dependencies",
        description="node_modules/ trees — reinstalled by `npm ci`; large but fully regenerable",
        resolver=_node_modules_dirs,
    ),
    CleanItem(
        id="os-temp",
        label="Old temp files",
        description=f"files in the system temp dir older than {TEMP_MAX_AGE_DAYS} days "
        "(temp dirs and in-use files are never touched)",
        resolver=_old_temp_files,
        ignore_errors=True,
    ),
    CleanItem(
        id="ide-caches",
        label="AI IDE caches",
        description="cache dirs (Cache, Code Cache, GPUCache, Crashpad, Service Worker "
        "caches, ...) inside %APPDATA% folders of Antigravity IDE, Cursor, Kiro, Qoder, "
        "Replit, Trae, devin and Windsurf — settings and sign-ins are never touched; "
        "close the IDEs for a complete clean",
        resolver=_ide_cache_dirs,
        ignore_errors=True,
    ),
    CleanItem(
        id="git-locks",
        label="Stale git locks",
        description="index.lock/HEAD.lock etc. left by interrupted git commands "
        "(via scripts/clear_stale_locks.py, skipped while git is running)",
        targets=(),
        runner=_git_locks,
    ),
)


def _protected(path: Path, root: Path) -> bool:
    """True when *path* or any component under root is a protected name."""
    try:
        rel = path.relative_to(root)
    except ValueError:
        return True
    return any(part in PROTECTED_NAMES for part in rel.parts)


def _resolve_targets(item: CleanItem, root: Path) -> list[Path]:
    """Expand an item into concrete paths via its resolver or globs."""
    if item.resolver is not None:
        return sorted(set(item.resolver(root)))
    paths: list[Path] = []
    for pattern, is_dir in item.targets:
        for match in root.glob(pattern):
            if _protected(match, root):
                continue
            if (is_dir and match.is_dir()) or (not is_dir and match.is_file()):
                paths.append(match)
    return sorted(set(paths))


def _remove(path: Path, dry_run: bool, ignore_errors: bool = False) -> str:
    if dry_run:
        return f"would remove {path}"
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path, ignore_errors=ignore_errors)
    else:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            if not ignore_errors:
                raise
    return f"removed {path}"


def _parse_list(value: str) -> set[str]:
    return {part.strip() for part in value.split(",") if part.strip()}


# ---------------------------------------------------------------------------
# Run statistics — recorded locally per machine, reported every STATS_EVERY runs
# ---------------------------------------------------------------------------


def _load_stats() -> dict:
    try:
        return json.loads(STATS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"runs": 0, "total_freed_bytes": 0, "by_category_totals": {}, "recent": []}


def _save_stats(stats: dict) -> None:
    try:
        STATS_DIR.mkdir(parents=True, exist_ok=True)
        STATS_FILE.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    except OSError as exc:
        print(f"  [stats] could not save {STATS_FILE}: {exc}", file=sys.stderr)


def _fmt_bytes(num: float) -> str:
    value = float(num)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(value) < 1024 or unit == "TiB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{value:.1f} TiB"


def _record_run(
    stats: dict,
    *,
    categories: list[str],
    seconds: float,
    free_before: int,
    free_after: int,
    paths_removed: int,
    failures: int,
    by_category: dict[str, int],
) -> int:
    """Append one run record and return the new run number."""
    run_number = stats.get("runs", 0) + 1
    freed = max(free_after - free_before, 0)
    stats["runs"] = run_number
    stats["total_freed_bytes"] = stats.get("total_freed_bytes", 0) + freed
    totals = stats.setdefault("by_category_totals", {})
    for cat, cat_freed in by_category.items():
        totals[cat] = totals.get(cat, 0) + cat_freed
    record = {
        "run": run_number,
        "ts": datetime.now(UTC).isoformat(timespec="seconds"),
        "categories": categories,
        "by_category": by_category,
        "seconds": round(seconds, 2),
        "free_before": free_before,
        "free_after": free_after,
        "freed_bytes": freed,
        "paths_removed": paths_removed,
        "failures": failures,
    }
    recent = stats.setdefault("recent", [])
    recent.append(record)
    del recent[:-10]  # keep the last 10 runs for the report
    _save_stats(stats)
    return run_number


def _print_stats_report(stats: dict, current: dict | None = None) -> None:
    """Pre/post cleaning statistics for this PC."""
    print("\n" + "=" * 64)
    print("  CLEAN STATISTICS REPORT")
    print("=" * 64)
    runs = stats.get("runs", 0)
    total_freed = stats.get("total_freed_bytes", 0)
    print(f"  Machine stats file : {STATS_FILE}")
    print(f"  Total clean runs   : {runs}")
    print(f"  Total space freed  : {_fmt_bytes(total_freed)}")
    if runs:
        print(f"  Average freed/run  : {_fmt_bytes(total_freed / runs)}")
    if current is not None:
        print("-" * 64)
        print(f"  This run #{current['run']} ({current['ts']})")
        print(f"    Categories       : {', '.join(current['categories'])}")
        print(f"    Duration         : {current['seconds']:.1f} s")
        print(f"    Paths removed    : {current['paths_removed']}"
              + (f" ({current['failures']} failed)" if current["failures"] else ""))
        print(f"    Free space before: {_fmt_bytes(current['free_before'])}")
        print(f"    Free space after : {_fmt_bytes(current['free_after'])}")
        print(f"    Freed this run   : {_fmt_bytes(current['freed_bytes'])}")
        by_cat = current.get("by_category") or {}
        if by_cat:
            parts = ", ".join(
                f"{cat} {_fmt_bytes(b)}" for cat, b in sorted(by_cat.items()) if b
            )
            if parts:
                print(f"    Freed by category: {parts}")
    totals = stats.get("by_category_totals") or {}
    if totals:
        print("-" * 64)
        print("  Space freed by category (all recorded runs on this PC):")
        for cat, cat_total in sorted(totals.items(), key=lambda kv: -kv[1]):
            marker = "  <- AI tools / machine" if cat in ("os-temp", "ide-caches") else ""
            print(f"    {cat:<16} {_fmt_bytes(cat_total):>12}{marker}")
    recent = stats.get("recent", [])
    if len(recent) > 1:
        print("-" * 64)
        print("  Recent runs:")
        for rec in recent[-5:]:
            print(f"    #{rec['run']:<4} {rec['ts'][:10]}  "
                  f"freed {_fmt_bytes(rec['freed_bytes']):>10}  "
                  f"{rec['paths_removed']:>5} paths  {rec['seconds']:>7.1f}s")
    print("=" * 64)


def _choose_interactive(items: list[CleanItem]) -> set[str]:
    """Show every category checked; the user unticks by number."""
    selected = {item.id for item in items}
    print("Select cleanup categories — untick by entering numbers.\n")
    for i, item in enumerate(items, 1):
        mark = "[x]" if item.id in selected else "[ ]"
        print(f"  {i:>2}. {mark} {item.label:<24} {item.description}")
    print("\nEnter numbers to EXCLUDE (comma-separated), or Enter to clean all:\n")
    answer = input("> ").strip()
    if not answer:
        return selected
    try:
        excluded = {items[int(tok) - 1].id for tok in answer.split(",") if tok.strip()}
    except (ValueError, IndexError):
        print("unrecognized selection — cleaning everything", file=sys.stderr)
        return selected
    return selected - excluded


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=str(REPO_ROOT), help="repo root (default: script location)")
    ap.add_argument("--list", action="store_true", help="list categories and exit")
    ap.add_argument("--dry-run", action="store_true", help="report only, remove nothing")
    ap.add_argument("-y", "--yes", action="store_true", help="clean all selected, no prompts")
    ap.add_argument("--only", help="comma-separated category ids to clean")
    ap.add_argument("--skip", help="comma-separated category ids to exclude")
    ap.add_argument("--stats", action="store_true",
                    help="print the run-statistics report for this PC and exit")
    ap.add_argument("--no-stats", action="store_true",
                    help="do not record this run in the statistics file")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    known = {item.id: item for item in ITEMS}

    if args.stats:
        _print_stats_report(_load_stats())
        return 0

    if args.list:
        for item in ITEMS:
            print(f"{item.id:<16} {item.label} — {item.description}")
        return 0

    if args.only:
        wanted = _parse_list(args.only)
        unknown = wanted - set(known)
        if unknown:
            print(f"unknown categories: {', '.join(sorted(unknown))}", file=sys.stderr)
            print(f"available: {', '.join(item.id for item in ITEMS)}", file=sys.stderr)
            return 2
        items = [known[i] for i in known if i in wanted]
    else:
        items = list(ITEMS)

    skipped = _parse_list(args.skip or "")
    items = [item for item in items if item.id not in skipped]

    if args.yes or args.dry_run or not sys.stdin.isatty():
        selected = {item.id for item in items}
    else:
        selected = _choose_interactive(items)

    started = time.monotonic()
    free_before = shutil.disk_usage(root).free
    paths_removed = 0
    failures = 0
    ran_categories: list[str] = []
    by_category: dict[str, int] = {}
    for item in items:
        if item.id not in selected:
            continue
        ran_categories.append(item.id)
        cat_before = shutil.disk_usage(root).free
        if item.runner is not None:
            for line in item.runner(root, args.dry_run):
                print(f"  [{item.id}] {line}")
        else:
            targets = _resolve_targets(item, root)
            if not targets:
                print(f"  [{item.id}] nothing to clean")
            else:
                for path in targets:
                    try:
                        print(f"  [{item.id}] {_remove(path, args.dry_run, item.ignore_errors)}")
                        paths_removed += 1
                    except OSError as exc:
                        failures += 1
                        print(f"  [{item.id}] FAILED {path}: {exc}", file=sys.stderr)
        by_category[item.id] = max(shutil.disk_usage(root).free - cat_before, 0)

    verb = "would clean" if args.dry_run else "cleaned"
    print(f"\n{verb} {len(ran_categories)} categor{'y' if len(ran_categories) == 1 else 'ies'}"
          + (f" ({failures} failure(s))" if failures else ""))

    if not args.dry_run and not args.no_stats:
        stats = _load_stats()
        seconds = time.monotonic() - started
        free_after = shutil.disk_usage(root).free
        run_number = _record_run(
            stats,
            categories=ran_categories,
            seconds=seconds,
            free_before=free_before,
            free_after=free_after,
            paths_removed=paths_removed,
            failures=failures,
            by_category=by_category,
        )
        if run_number % STATS_EVERY == 0:
            _print_stats_report(stats, stats["recent"][-1])

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
