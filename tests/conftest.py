"""
pytest top-level configuration.
M0: empty. M1 populates fixtures, markers, plugins.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure packages & apps are importable without install.
# This file lives in tests/, so parents[1] is the repo root — `.parent` pointed
# at tests/packages and tests/apps, neither of which exists.
ROOT = Path(__file__).resolve().parents[1]
for sub in ("packages", "apps"):
    p = str(ROOT / sub)
    if p not in sys.path:
        sys.path.insert(0, p)
