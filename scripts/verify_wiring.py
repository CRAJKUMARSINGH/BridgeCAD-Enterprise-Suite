#!/usr/bin/env python3
"""Fail the build when code exists but nothing can reach it.

Checks
------
1. No plugin directory relies on a stray marker file instead of a real manifest.
2. Every plugin directory has manifest.json, defaults.yaml, draw_overrides.py.
3. Every manifest parses, validates, declares a sane span range, and its
   ``bridge_types`` are real ``SuperstructureType`` members.
4. Plugin ids are unique and bridge_types are not claimed twice.
5. Every plugin's draw_overrides exposes describe / get_typical_values /
   apply_defaults.
6. Every name in every package ``__all__`` resolves.
7. Every public name defined by a ``standards`` module is exported by the
   ``standards`` package.
8. No bare ``tuple`` / ``list`` / ``dict`` / ``set`` annotation under
   ``bridgecad_core/standards`` (mypy --strict type-arg).

Exit code 0 = wired, 1 = at least one violation.

    python scripts/verify_wiring.py
"""

from __future__ import annotations

import ast
import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGINS = ROOT / "packages/bridgecad-plugins/bridgecad_plugins/plugins"
STANDARDS = ROOT / "packages/bridgecad-core/bridgecad_core/standards"

BRACKET = "['manifest.json', 'draw_overrides.py', 'defaults.yaml']"
REQUIRED_PLUGIN_FILES = ("manifest.json", "defaults.yaml", "draw_overrides.py")
OVERRIDES_REQUIRED = ("describe", "get_typical_values", "apply_defaults")
BARE = {"tuple", "list", "dict", "set", "frozenset"}

problems: list[str] = []


def fail(msg: str) -> None:
    problems.append(msg)


def _add_paths() -> None:
    sys.path[:0] = [
        str(ROOT),
        str(ROOT / "packages/bridgecad-core"),
        str(ROOT / "packages/bridgecad-plugins"),
    ]
    # Every suite package ships its distribution folder under packages/, so make
    # each one importable without an editable install.
    for pkg_dir in sorted((ROOT / "packages").glob("bridgecad-*")):
        sys.path.insert(0, str(pkg_dir))


def check_plugin_markers() -> None:
    for entry in sorted(PLUGINS.iterdir()):
        if entry.name == BRACKET:
            fail(f"stray marker file at plugins/{entry.name}")
            continue
        if not entry.is_dir():
            continue
        for name in REQUIRED_PLUGIN_FILES:
            if not (entry / name).exists():
                fail(f"plugins/{entry.name}: missing {name}")
        if (entry / BRACKET).exists():
            fail(f"plugins/{entry.name}: still contains the marker file {BRACKET}")


def check_manifests() -> list[str]:
    from bridgecad_core.types import SuperstructureType

    valid_types = {member.value for member in SuperstructureType}
    ids: list[str] = []
    type_owner: dict[str, str] = {}

    for entry in sorted(PLUGINS.iterdir()):
        manifest = entry / "manifest.json"
        if not manifest.exists():
            continue
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(f"plugins/{entry.name}/manifest.json: invalid JSON ({exc})")
            continue

        pid = data.get("plugin_id", "")
        if pid != entry.name:
            fail(f"plugins/{entry.name}: plugin_id {pid!r} != directory name")
        if pid in ids:
            fail(f"duplicate plugin_id {pid!r}")
        ids.append(pid)

        rng = data.get("span_range_m", [])
        if len(rng) != 2 or rng[0] >= rng[1]:
            fail(f"plugins/{entry.name}: span_range_m must be [min, max] with min < max")

        types = data.get("bridge_types", [])
        if not types:
            fail(f"plugins/{entry.name}: bridge_types is empty")
        for bt in types:
            if bt not in valid_types:
                fail(f"plugins/{entry.name}: bridge_type {bt!r} is not a SuperstructureType member")
            if bt in type_owner:
                fail(f"bridge_type {bt} claimed by both {type_owner[bt]} and {pid}")
            type_owner[bt] = pid

        overrides = entry / "draw_overrides.py"
        if overrides.exists():
            tree = ast.parse(overrides.read_text(encoding="utf-8"))
            defined = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
            for fn in OVERRIDES_REQUIRED:
                if fn not in defined:
                    fail(f"plugins/{entry.name}/draw_overrides.py: no {fn}()")

    return ids


def check_all_resolves() -> None:
    for pkg_dir in sorted((ROOT / "packages").glob("bridgecad-*")):
        init = next(pkg_dir.glob("*/__init__.py"), None)
        if init is None:
            continue
        module_name = init.parent.name
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:  # report, do not crash the run
            fail(f"{module_name}: import failed ({exc})")
            continue
        for name in getattr(module, "__all__", ()):
            if not hasattr(module, name):
                fail(f"{module_name}.__all__ lists {name!r} which does not resolve")


def check_standards_exports() -> None:
    package = importlib.import_module("bridgecad_core.standards")
    exported = set(getattr(package, "__all__", ()))
    for module_path in sorted(STANDARDS.glob("*.py")):
        if module_path.name == "__init__.py":
            continue
        module = importlib.import_module(f"bridgecad_core.standards.{module_path.stem}")
        for name in getattr(module, "__all__", ()):
            if name not in exported:
                fail(f"standards.{module_path.stem}.{name} is defined but not exported")


def check_no_bare_generics() -> None:
    for module_path in sorted(STANDARDS.glob("*.py")):
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.AnnAssign)
                and isinstance(node.annotation, ast.Name)
                and node.annotation.id in BARE
            ):
                fail(
                    f"{module_path.name}:{node.lineno}: bare "
                    f"{node.annotation.id!r} annotation (needs type arguments)"
                )


def main() -> int:
    _add_paths()
    check_plugin_markers()
    ids = check_manifests()
    check_all_resolves()
    check_standards_exports()
    check_no_bare_generics()

    if problems:
        print(f"WIRING FAILED — {len(problems)} problem(s):\n")
        for p in problems:
            print(f"  x {p}")
        return 1

    print(f"WIRING OK — {len(ids)} plugins wired, standards fully exported, " "no bare generics.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
