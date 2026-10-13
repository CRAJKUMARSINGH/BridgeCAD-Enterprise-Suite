"""
E2E regression test runner — M0 placeholder.
M9: Run every fixture in tests/e2e/fixtures/ (28 Scribd-reference pairs).
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    fixtures = Path(__file__).resolve().parent.parent / "tests" / "e2e" / "fixtures"
    count = len(list(fixtures.glob("*.xlsx"))) + len(list(fixtures.glob("*.expected.json")))
    if count == 0:
        print("[M0 scaffold] No E2E fixtures yet. M9 populates 28 Scribd-reference fixtures.")
        return 0
    print(f"Found {count} fixture files. M9 will run: pytest tests/e2e -v")
    return 0


if __name__ == "__main__":
    sys.exit(main())
