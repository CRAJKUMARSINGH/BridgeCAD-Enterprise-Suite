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


def pytest_addoption(parser) -> None:
    """`pytest -q tests/drawings --regression` — the W07 verification command.

    Defined here, not in tests/drawings/conftest.py: pytest only honours
    pytest_addoption in the tests-root conftest, and a subdirectory conftest is
    loaded too late for its option to be registered.
    """
    parser.addoption(
        "--regression",
        action="store_true",
        default=False,
        help="run only the drawing-output regression lane (W07)",
    )


def pytest_configure(config) -> None:
    if config.getoption("regression"):
        existing = config.option.markexpr or ""
        config.option.markexpr = f"({existing}) and regression" if existing else "regression"
