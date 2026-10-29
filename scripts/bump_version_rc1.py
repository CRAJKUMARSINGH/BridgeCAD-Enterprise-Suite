"""Bump the release version across the whole Enterprise Suite — one source.

Sets every ``__version__`` to the human form (``0.1.0-rc1``) and every
``[project].version`` (root + members) to the PEP 440 form (``0.1.0rc1``).
Run ``scripts/check_version_consistency.py`` afterwards to prove they agree.
"""

import re
from pathlib import Path

SUITE = Path(__file__).parent.parent
NEW_VER = "0.1.0-rc1"

try:
    from packaging.version import Version

    PEP440_VER = str(Version(NEW_VER))  # "0.1.0-rc1" -> "0.1.0rc1"
except ModuleNotFoundError:  # pragma: no cover - packaging ships with pip
    PEP440_VER = NEW_VER

_RE_DUNDER = re.compile(r'__version__\s*=\s*["\'][\w.\-]+["\']')
_RE_PYPROJECT = re.compile(r'(?m)^(\s*version\s*=\s*["\'])[\w.\-]+(["\'])')

changed = []

# ── __init__ / main __version__ -> human form ────────────────────────────────
for p in SUITE.rglob("__init__.py"):
    if any(skip in p.parts for skip in (".git", "__pycache__", "vendor", ".deps")):
        continue
    try:
        txt = p.read_text(encoding="utf-8")
    except OSError:
        continue
    if "__version__" not in txt:
        continue
    new = _RE_DUNDER.sub(f'__version__ = "{NEW_VER}"', txt)
    if new != txt:
        p.write_text(new, encoding="utf-8")
        changed.append(p.relative_to(SUITE).as_posix())
        print(f"  __version__: {p.relative_to(SUITE).as_posix()}")

# ── pyproject [project].version -> PEP 440 form ───────────────────────────────
_manifests = [SUITE / "pyproject.toml"]
_manifests += sorted(SUITE.glob("packages/*/pyproject.toml"))
_manifests += sorted(SUITE.glob("apps/*/pyproject.toml"))
for p in _manifests:
    try:
        txt = p.read_text(encoding="utf-8")
    except OSError:
        continue
    new = _RE_PYPROJECT.sub(rf"\g<1>{PEP440_VER}\g<2>", txt, count=1)
    if new != txt:
        p.write_text(new, encoding="utf-8")
        changed.append(p.relative_to(SUITE).as_posix())
        print(f"  pyproject  : {p.relative_to(SUITE).as_posix()}")

print(f"\n  {len(changed)} files updated to v{NEW_VER} (PEP 440: {PEP440_VER})")
