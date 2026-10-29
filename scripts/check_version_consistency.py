"""Single-source version guard for the BridgeCAD Enterprise Suite.

The release version lives in exactly one place — ``[project].version`` in the
root ``pyproject.toml``. Everything else that declares a version must normalise
to the same PEP 440 release:

  * every member ``pyproject.toml`` under ``packages/`` and ``apps/``
  * every ``__version__`` in a package ``__init__.py`` or app ``main.py``
  * the root ``bridgecad`` shim

Normalisation is deliberate: a pyproject says ``0.1.0rc1`` (PEP 440) while a
human-facing ``__version__`` says ``0.1.0-rc1``. Those are the same release and
must not be flagged; ``0.1.0`` (the *final* release) is a genuine divergence.

Run:
    python scripts/check_version_consistency.py
Exit 0 when consistent, 1 otherwise. Wired into pre-commit and suite-ci.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:  # packaging ships with pip/setuptools; fall back to a regex if absent
    from packaging.version import InvalidVersion, Version
except ModuleNotFoundError:  # pragma: no cover - exercised only without pip
    Version = None  # type: ignore[assignment]
    InvalidVersion = ValueError  # type: ignore[assignment,misc]

SUITE = Path(__file__).resolve().parent.parent

_RE_PYPROJECT_VERSION = re.compile(r'^\s*version\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)
_RE_DUNDER_VERSION = re.compile(r'^__version__\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)

# Directories that never carry the product version.
_SKIP = (".git", "__pycache__", ".venv", "build", "dist", "site", "node_modules")


def normalise(raw: str) -> str:
    """Canonical PEP 440 string, so ``0.1.0-rc1`` and ``0.1.0rc1`` compare equal."""
    text = raw.strip()
    if Version is not None:
        try:
            return str(Version(text))
        except InvalidVersion:
            return text
    return re.sub(r"-?rc(\d+)$", r"rc\1", text)  # pragma: no cover


def _read(path: Path, pattern: re.Pattern[str]) -> str | None:
    try:
        match = pattern.search(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return None
    return match.group(1) if match else None


def collect() -> tuple[str | None, list[tuple[str, str]]]:
    """Return (source_version, [(label, raw_version), ...]) for every declaration."""
    source = _read(SUITE / "pyproject.toml", _RE_PYPROJECT_VERSION)
    found: list[tuple[str, str]] = []

    for manifest in sorted(SUITE.glob("packages/*/pyproject.toml")) + sorted(
        SUITE.glob("apps/*/pyproject.toml")
    ):
        raw = _read(manifest, _RE_PYPROJECT_VERSION)
        if raw is not None:
            found.append((manifest.relative_to(SUITE).as_posix(), raw))

    for init in sorted(SUITE.rglob("__init__.py")) + sorted(SUITE.rglob("main.py")):
        if any(part in _SKIP for part in init.parts):
            continue
        rel = init.relative_to(SUITE).as_posix()
        if not (
            rel.startswith("packages/") or rel.startswith("apps/") or rel == "bridgecad/__init__.py"
        ):
            continue
        raw = _read(init, _RE_DUNDER_VERSION)
        if raw is not None:
            found.append((rel, raw))

    return source, found


def main() -> int:
    source, found = collect()
    if source is None:
        print("  [FAIL] could not read [project].version from the root pyproject.toml")
        return 1

    canonical = normalise(source)
    print(f"  source of truth  : pyproject.toml -> {source!r}  (normalised: {canonical})")

    mismatches = [
        (label, raw, normalise(raw)) for label, raw in found if normalise(raw) != canonical
    ]

    for label, raw in found:
        mark = "ok " if normalise(raw) == canonical else "BAD"
        print(f"    [{mark}] {label:<58} {raw!r}")

    if mismatches:
        print(f"\n  [FAIL] {len(mismatches)} version declaration(s) diverge from {canonical}:")
        for label, raw, norm in mismatches:
            print(f"    - {label}: {raw!r} (normalised {norm})")
        return 1

    print(f"\n  [PASS] {len(found)} declarations all resolve to {canonical}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
