"""Bump all __version__ strings to 0.1.0-rc1 across the Enterprise Suite."""
import re
import sys
from pathlib import Path

SUITE = Path(__file__).parent.parent
NEW_VER = "0.1.0-rc1"

changed = []
for p in SUITE.rglob("__init__.py"):
    if any(skip in str(p) for skip in [".git", "__pycache__", "vendor", ".deps"]):
        continue
    try:
        txt = p.read_text(encoding="utf-8")
    except Exception:
        continue
    if "__version__" not in txt:
        continue
    new = re.sub(
        r'__version__\s*=\s*["\'][\w.\-]+["\']',
        f'__version__ = "{NEW_VER}"',
        txt,
    )
    if new != txt:
        p.write_text(new, encoding="utf-8")
        rel = str(p.relative_to(SUITE))
        changed.append(rel)
        print(f"  Updated: {rel}")

print(f"\n  {len(changed)} files updated to v{NEW_VER}")
