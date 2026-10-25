#!/usr/bin/env python3
"""Fail if a repo path referenced inside a fenced code block does not exist.

A URL checker only sees markdown links. It is blind to:

    cd BridgeCAD Enterprise Suite      <- phantom directory
    pip install -r requirements_lean.txt   <- missing file

Both of those shipped. This closes that gap.

Usage:
    python scripts/check_doc_paths.py            # exit 1 on any missing path
    python scripts/check_doc_paths.py --verbose
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# archive/ is historical and unmaintained — lychee excludes it for the same
# reason (.lychee.toml), so the code-block audit skips it too.
SCAN_GLOBS = ("*.md", "docs/**/*.md")

FENCE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)

# A `cd <dir>` instruction. Captures quoted or bare targets; an unquoted target
# may contain spaces (the phantom "BridgeCAD Enterprise Suite") so it runs to
# the first shell separator or comment.
CD_TARGET = re.compile(
    r"^\s*cd\s+(?:\"([^\"]+)\"|'([^']+)'|([^;&|#\n]+))",
    re.MULTILINE,
)

# Tokens that look like paths worth verifying. Only tokens carrying a known
# file extension, so prose like "I/T" or a ratio like "30/150" is not a path.
# The trailing (?![\w]) stops "bridgecad_draw.sheets" matching as "*.sh".
PATH_TOKEN = re.compile(
    r"(?<![\w/.-])("
    r"(?:\./|\.\./)?(?:[\w.-]+/)*[\w.-]+\.(?:py|md|txt|toml|yml|yaml|json|cfg|ini|sh|rst|lock)"
    r")(?![\w])"
)

# Filenames that legitimately do not exist in the tree.
ALLOW = {
    ".env",
    ".env.example",
    "bridge.xlsx",
    "gad.dxf",
    "qa.html",
    "boq.xlsx",
    "project.json",
    "manifest.json",
    "out/",
    "output_directory",
    "output_dir",
    "bridgecad",
    "python",
    "pip",
    "make",
    "docker",
    "packages/*",
    "apps/*",
    "site/",
    "site-api/",
    # The directory you land in after `git clone` — the repo's own name.
    "BridgeCAD-Enterprise-Suite",
}

# Substrings that mean "generated, may not exist yet".
SOFT_SUFFIXES = (".dxf", ".xlsx", ".pdf", ".zip", ".html")

SKIP_PREFIXES = ("http://", "https://", "$", "-", "--")


def repo_files() -> set[str]:
    out = set()
    for p in ROOT.rglob("*"):
        if any(part in {".git", "node_modules", ".venv", "__pycache__"} for part in p.parts):
            continue
        out.add(str(p.relative_to(ROOT)))
    return out


def basenames(files: set[str]) -> set[str]:
    """Every filename in the tree, so a bare `irc_sp55.py` reference resolves."""
    return {Path(f).name for f in files}


def path_tails(files: set[str]) -> set[str]:
    """Every trailing path fragment, so a package-relative tree entry like
    `tests/__init__.py` resolves against `packages/*/tests/__init__.py`."""
    tails = set()
    for f in files:
        parts = Path(f).parts
        for i in range(len(parts)):
            tails.add("/".join(parts[i:]))
    return tails


def iter_markdown():
    for g in SCAN_GLOBS:
        yield from sorted(ROOT.glob(g))


def check_cd_targets(path: Path, text: str) -> list[str]:
    """`cd` into a directory that does not exist is the headline defect."""
    problems: list[str] = []
    for m in CD_TARGET.finditer(text):
        target = (m.group(1) or m.group(2) or m.group(3) or "").strip()
        if not target or target in ALLOW:
            continue
        if target.startswith(SKIP_PREFIXES) or "*" in target or "<" in target:
            continue
        if target.startswith("~") or target.startswith("/"):
            continue
        normalised = target.rstrip("/")
        if (ROOT / normalised).exists() or (path.parent / normalised).exists():
            continue
        problems.append(f"{path.relative_to(ROOT)}: missing path -> {target}")
    return problems


def check(
    path: Path, files: set[str], names: set[str], tails: set[str], verbose: bool
) -> list[str]:
    problems: list[str] = []
    text = path.read_text(encoding="utf-8", errors="replace")

    problems.extend(check_cd_targets(path, text))

    for block in FENCE.findall(text):
        for raw in PATH_TOKEN.findall(block):
            tok = raw.strip().strip("'\"`,;:()")

            if not tok or tok in ALLOW or tok.startswith(SKIP_PREFIXES):
                continue
            if "*" in tok or "<" in tok or ">" in tok:
                continue
            if tok.endswith(SOFT_SUFFIXES):
                continue  # generated artifacts
            if tok.startswith("~") or tok.startswith("/"):
                continue

            normalised = tok.rstrip("/")
            if normalised in files or tok in files:
                continue
            # bare filename: accept if that file exists anywhere in the tree
            if "/" not in normalised and normalised in names:
                continue
            # package-relative tree entry: accept if any file ends with it
            if normalised in tails:
                continue
            # try resolving relative to the doc's own directory
            if (path.parent / normalised).exists():
                continue
            if (ROOT / normalised).exists():
                continue

            problems.append(f"{path.relative_to(ROOT)}: missing path -> {tok}")

    if verbose:
        print(f"  scanned {path.relative_to(ROOT)}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument(
        "--root", default=None, help="Repo root to audit. Defaults to the script's parent."
    )
    args = ap.parse_args()

    global ROOT
    if args.root:
        ROOT = Path(args.root).resolve()
    files = repo_files()
    names = basenames(files)
    tails = path_tails(files)
    all_problems: list[str] = []

    for md in iter_markdown():
        all_problems.extend(check(md, files, names, tails, args.verbose))

    if all_problems:
        print(f"\n{len(all_problems)} broken path reference(s):\n")
        for p in all_problems:
            print(f"  ::error::{p}")
        return 1

    print("OK — every path referenced in a code block exists.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
