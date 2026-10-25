#!/usr/bin/env python3
"""Generate one Sphinx stub per workspace package.

Idempotent — safe to re-run. Regenerate after adding a package or a public
module so the reference never falls behind the code.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "api" / "packages"
OUT.mkdir(parents=True, exist_ok=True)

TEMPLATE = """{title}
{underline}

.. automodule:: {module}
   :members:
   :show-inheritance:
"""


def main() -> int:
    count = 0
    for pkg_dir in sorted((ROOT / "packages").iterdir()):
        if not pkg_dir.is_dir():
            continue
        module = pkg_dir.name.replace("-", "_")
        if not (pkg_dir / module).is_dir():
            continue

        title = pkg_dir.name
        body = TEMPLATE.format(title=title, underline="=" * len(title), module=module)
        (OUT / f"{module}.rst").write_text(body, encoding="utf-8")
        print(f"  wrote {OUT.relative_to(ROOT)}/{module}.rst")
        count += 1

    print(f"{count} stub(s) generated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
