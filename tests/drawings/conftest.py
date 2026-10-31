"""W07 drawing-output regression lane — local fixtures.

The verification command is ``pytest -q tests/drawings --regression``; the
``--regression`` option itself lives in ``tests/conftest.py`` because pytest
only honours ``pytest_addoption`` in the tests-root conftest.

``tests/`` is put on ``sys.path`` so this lane reuses the product-facade
adapters (``draw.contract``) instead of duplicating sheet construction.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
_TESTS = REPO / "tests"
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))
