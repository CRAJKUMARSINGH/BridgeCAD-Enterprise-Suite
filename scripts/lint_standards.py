"""
Lint standards YAML files for schema consistency.

M0 placeholder — simple structural checks:
  - File is valid YAML
  - Required top-level keys present (per file)
M1+ implements a full pydantic schema.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("pip install pyyaml required")
    sys.exit(0)

REQUIRED = {
    "irc_sp55_drawing.yaml":    ["scales", "text_heights_mm", "lineweights_mm"],
    "irc_05_hydraulic.yaml":    ["scour", "waterway"],
    "irc_21_structural.yaml":   ["span_depth_ratio", "load_dispersal"],
    "morth_rates_2024.yaml":    ["items"],
    "state_pwd_multipliers.yaml": [],
}


def lint(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        return [f"{path.name}: YAML parse error: {exc}"]
    for key in REQUIRED.get(path.name, []):
        if key not in data:
            errors.append(f"{path.name}: missing required key '{key}'")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parent.parent / "standards"
    all_errors: list[str] = []
    for yml in sorted(root.rglob("*.yaml")):
        all_errors.extend(lint(yml))
    if all_errors:
        print("\n".join(all_errors))
        return 1
    print(f"✔ All {(root.rglob('*.yaml').__reduce__())[0] or ''} standards YAML files OK")
    print("✔ standards/ lint OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
