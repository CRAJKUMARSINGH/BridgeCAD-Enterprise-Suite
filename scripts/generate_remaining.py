"""
scripts/generate_remaining.py — generate only the fixtures not yet in EXAMPLES/.
Run from repo root: python scripts/generate_remaining.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SUITE = Path(__file__).parents[1]
for _pkg in [
    "bridgecad-core",
    "bridgecad-io",
    "bridgecad-draw",
    "bridgecad-bill",
    "bridgecad-qa",
    "bridgecad-export",
    "bridgecad-plugins",
]:
    _p = _SUITE / "packages" / _pkg
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
sys.path.insert(0, str(_SUITE / "tests" / "e2e"))
from generate_examples import (  # type: ignore[import]
    EXAMPLES_DIR,
    FIXTURES_DIR,
    LABELS,
    _write_index_readme,
    generate_fixture,
)

done = {d.name for d in EXAMPLES_DIR.iterdir() if d.is_dir()}
fixtures = sorted(FIXTURES_DIR.glob("*.json"))
remaining = [f for f in fixtures if f.stem not in done]

print(f"\n  Remaining: {len(remaining)}  |  Already done: {len(done)}")
passed, failed = 0, []
for fp in remaining:
    fid, ok, msg = generate_fixture(fp)
    label = LABELS.get(fid, fid)
    print(f"  [{'DONE' if ok else 'FAIL'}] {label:<45}  {msg}")
    if ok:
        passed += 1
    else:
        failed.append(fid)

print(f"\n  Done: {passed}/{len(remaining)}  Failed: {len(failed)}")
if failed:
    for f in failed:
        print(f"    x {f}")

# Regenerate index README to include all
_write_index_readme(fixtures, len(done) + passed, len(fixtures))
print("  Index README updated.")
