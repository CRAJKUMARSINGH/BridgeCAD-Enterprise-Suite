#!/usr/bin/env python3
"""Remove stale git lock files left behind by an interrupted git command.

A lock file that survives a crashed or killed git process blocks every later
write: ``git add`` fails, ``git commit`` fails, and on Windows a shell ``rm``
can be silently ignored, leaving the lock in place for days. This clears the
names git uses and re-checks each one afterwards, because a delete that reports
success is not evidence that the file is gone.

    python scripts/clear_stale_locks.py --dry-run
    python scripts/clear_stale_locks.py

Run it as the first step of any commit script.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

#: Fixed lock names git creates, relative to the git directory.
LOCK_NAMES = (
    "index.lock",
    "HEAD.lock",
    "AUTO_MERGE.lock",
    "packed-refs.lock",
    "ORIG_HEAD.lock",
)
#: Lock names git creates with a process id appended.
LOCK_GLOBS = ("next-index-*.lock",)


def _git_dir(root: Path) -> Path | None:
    """The git directory for *root*, or None when *root* is not a repository."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    path = Path(out)
    return path if path.is_absolute() else (root / path)


def _git_is_running() -> bool:
    """True when a git process is alive. A live git may legitimately hold a lock."""
    pgrep = shutil.which("pgrep")
    if pgrep:
        return (
            subprocess.run(
                [pgrep, "-x", "git"],
                capture_output=True,
                check=False,
            ).returncode
            == 0
        )
    if os.name == "nt":
        try:
            out = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq git.exe"],
                capture_output=True,
                text=True,
                check=False,
            ).stdout
        except OSError:
            return False
        return "git.exe" in out
    return False


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".", help="repo root (default: cwd)")
    ap.add_argument("--dry-run", action="store_true", help="report only")
    ap.add_argument(
        "--force", action="store_true", help="clear locks even when a git process is running"
    )
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    gitdir = _git_dir(root)
    if gitdir is None:
        print(f"not a git repository: {root}", file=sys.stderr)
        return 1

    if _git_is_running() and not args.force:
        print("a git process is running; skipping (use --force to override)")
        return 0

    targets = [gitdir / name for name in LOCK_NAMES]
    for pattern in LOCK_GLOBS:
        targets.extend(sorted(gitdir.glob(pattern)))

    cleared = 0
    for lock in targets:
        if not lock.exists():
            continue
        if args.dry_run:
            print(f"would remove {lock}")
            cleared += 1
            continue
        try:
            lock.unlink()
        except OSError as exc:
            print(f"FAILED to remove {lock}: {exc}", file=sys.stderr)
            continue
        if lock.exists():
            print(f"FAILED to remove {lock} — still present after unlink", file=sys.stderr)
            continue
        print(f"removed {lock}")
        cleared += 1

    verb = "would clear" if args.dry_run else "cleared"
    print(f"{verb} {cleared} lock file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
