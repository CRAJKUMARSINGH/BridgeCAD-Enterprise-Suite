"""
sitecustomize.py — workspace bootstrap for the ROUTE REPO ROOT.

Placed at the repo-root (which is the first sys.path entry when running
`python <script.py>` from that folder, and therefore automatically loaded by
CPython's `site` module at interpreter startup).

WHAT IT DOES
------------
1. Locates the `packages/*` and `apps/*` folders relative to the repo root.
2. Prepends each individual package folder (bridgecad-core/ , bridgecad-io/, …)
   to sys.path so `import bridgecad_core, bridgecad_io, …` works immediately.
3. Prepends the repo-root itself (already first item in script mode; explicit
   for REPL/interactive sessions).

This file is idempotent.  It also avoids mutation when the workspace is
installed via `pip install -e .` (setuptools already took care of paths then).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_BOOTSTRAP_MARKER = "__bridgecad_workspace_bootstrap_applied__"


def _apply() -> None:
    if getattr(sys, _BOOTSTRAP_MARKER, False):
        return  # idempotent

    repo_root = Path(__file__).resolve().parent
    repo_root_candidates: list[Path] = [repo_root]
    try:
        repo_root_candidates.append(Path(os.getcwd()).resolve())
    except Exception:  # pragma: no cover
        pass
    try:
        if sys.argv and sys.argv[0]:
            script_path = Path(sys.argv[0]).resolve()
            if script_path.is_file():
                repo_root_candidates.append(script_path.parent)
    except Exception:  # pragma: no cover
        pass
    for p in sys.path:
        try:
            pp = Path(p)
            if pp.is_dir() and (pp / "sitecustomize.py").is_file():
                repo_root_candidates.append(pp.resolve())
        except Exception:
            continue

    base_dir: Path | None = None
    seen: set[str] = set()
    for cand in repo_root_candidates:
        key = os.path.normcase(str(cand))
        if key in seen:
            continue
        seen.add(key)
        if (cand / "packages").is_dir() and (cand / "apps").is_dir():
            base_dir = cand
            break

    if base_dir is None:  # pragma: no cover - can't detect, skip
        return

    packages_dir = base_dir / "packages"
    apps_dir     = base_dir / "apps"

    new_paths: list[str] = []
    if packages_dir.is_dir():
        for pkg_meta in [
            ("bridgecad-core",    "bridgecad_core"),
            ("bridgecad-io",      "bridgecad_io"),
            ("bridgecad-draw",    "bridgecad_draw"),
            ("bridgecad-bill",    "bridgecad_bill"),
            ("bridgecad-qa",      "bridgecad_qa"),
            ("bridgecad-export",  "bridgecad_export"),
            ("bridgecad-plugins", "bridgecad_plugins"),
            ("bridgecad-ai",      "bridgecad_ai"),
            ("bridgecad-infra",   "bridgecad_infra"),
        ]:
            pkg_dir = packages_dir / pkg_meta[0]
            if pkg_dir.is_dir():
                new_paths.append(str(pkg_dir))

    if apps_dir.is_dir():
        for app_dir_name, _py_name in [
            ("api-gateway",  "bridgecad_api"),
            ("cli-console",  "bridgecad_cli"),
        ]:
            app_dir = apps_dir / app_dir_name
            if app_dir.is_dir():
                new_paths.append(str(app_dir))

    new_paths.append(str(base_dir))

    existing = set(os.path.normcase(p) for p in sys.path if isinstance(p, str))
    prepend: list[str] = []
    for p in new_paths:
        np = os.path.normcase(p)
        if np in existing:
            continue
        existing.add(np)
        prepend.append(p)

    if prepend:
        sys.path[:0] = prepend

    setattr(sys, _BOOTSTRAP_MARKER, True)


_apply()
