"""
bridgecad.__main__ — thin CLI shim for `python -m bridgecad`.

Delegates to the richer Typer CLI in bridgecad_cli.main (apps/cli-console) if
available; otherwise falls back to a minimal "suite info" banner + the three
most-used entry points (verify / generate / qa).
"""
from __future__ import annotations

import json as _json
import subprocess
import sys
from pathlib import Path

# Self-bootstrap: when python -m bridgecad is executed via runpy, sys.path[0]
# might be the `bridgecad/` package dir itself (not the repo root containing
# sitecustomize.py).  Ensure sitecustomize fires once so bridgecad_core, …
# are all importable regardless of cwd.
try:
    import sitecustomize as _sitecustomize  # noqa: F401
except Exception:  # pragma: no cover
    _repo_root = Path(__file__).resolve().parent.parent
    if str(_repo_root) not in sys.path:
        sys.path.insert(0, str(_repo_root))


def app() -> int:
    # Make sure the facade banner is always printed first on `python -m bridgecad`.
    import bridgecad as bc

    lines = [
        "",
        f"  {bc.__suite__}  v{bc.__version__}",
        f"  milestone : {bc.__moniker__}",
        "",
        "  Usage:",
        "    python -m bridgecad verify              # Run Day3 + Day4 acceptance verifiers",
        "    python -m bridgecad generate 11span     # Generate the 11-span RCC Solid Slab GAD",
        "    python -m bridgecad qa  <project.json>  # Score QA Grade on a saved project",
        "    python -m bridgecad info                # Print Python / import layout",
        "",
        "  To invoke the full CLI (apps/cli-console):",
        "    pip install -e apps/cli-console && bridgecad-cli ...",
        "",
    ]
    banner = "\n".join(lines)

    argv = sys.argv[1:]
    if not argv:
        print(banner)
        return 0

    cmd = argv[0].strip().lower()

    # ── verify ────────────────────────────────────────────────────────
    if cmd == "verify":
        root = Path(__file__).resolve().parent.parent
        suites = root / "packages" / "bridgecad-core"
        print("[bridgecad] verify :: day3_verify.py + day4_verify.py")
        # Execute both scripts in-process so sitecustomize.paths stays intact.
        import subprocess
        py = sys.executable
        rc3 = subprocess.call([py, str(suites / "day3_verify.py")])
        rc4 = subprocess.call([py, str(suites / "day4_verify.py")])
        return 0 if (rc3 == 0 and rc4 == 0) else 1

    # ── generate ──────────────────────────────────────────────────────
    if cmd == "generate":
        variant = (argv[1] if len(argv) > 1 else "11span").lower()
        root = Path(__file__).resolve().parent.parent
        mapping = {
            "11span": "_generate_11span_gad.py",
            "elegant": "_enhance_elegant_pdf.py",
        }
        script = root / mapping.get(variant, mapping["11span"])
        if not script.exists():
            print(f"[bridgecad] generate :: unknown variant {variant!r}")
            return 2
        print(f"[bridgecad] generate :: {script.name}")
        import subprocess
        return subprocess.call([sys.executable, str(script), *argv[2:]])

    # ── qa ────────────────────────────────────────────────────────────
    if cmd == "qa":
        project_json = argv[1] if len(argv) > 1 else None
        if not project_json:
            print("Usage: python -m bridgecad qa <project.json>")
            return 2
        path = Path(project_json).resolve()
        if not path.exists():
            print(f"[bridgecad] qa :: project file not found: {path}")
            return 3
        # Prefer io.json_adapter.load_project if available; else use
        # pydantic's JSON loader via BridgeProject.model_validate_json.
        project = None
        try:
            from bridgecad_io.json_adapter import load_project  # type: ignore
            project = load_project(path)
        except Exception:
            raw = path.read_text(encoding="utf-8")
            from bridgecad_core.models import BridgeProject
            try:
                project = BridgeProject.model_validate_json(raw, context={"ignore_computed": True})
            except Exception:
                data = _json.loads(raw)
                # strip known computed-field extras if strict roundtrip fails
                def _strip_extras(obj: dict) -> dict:
                    EXTRA_KEYS = {
                        "total_length_m", "overall_width_m", "freeboard_actual_m",
                        "total_deck_thickness_mm", "total_bearings_quantity",
                        "total_joints_quantity", "total_bridge_length_m",
                        "overall_bridge_width_m", "span_count_propagated",
                        "agg_total_length",
                    }
                    if isinstance(obj, dict):
                        return {k: _strip_extras(v) for k, v in obj.items()
                                if k not in EXTRA_KEYS and not (
                                    isinstance(v, dict) and any(x in str(k) for x in ["agg_", "_propagated"])
                                )}
                    if isinstance(obj, list):
                        return [_strip_extras(i) for i in obj]
                    return obj
                data_clean = _strip_extras(data)
                try:
                    project = BridgeProject.model_validate(data_clean)
                except Exception:
                    # Final fallback: validation engine's run_all takes project dict
                    project = BridgeProject.model_construct(**{
                        k: v for k, v in data_clean.items()
                        if k in {"project_metadata", "geometry_input", "superstructure",
                                  "substructure", "foundation_details", "approaches",
                                  "hydraulic_data", "materials", "bearings_joints",
                                  "components_lib", "drawing_control", "spans",
                                  "piers", "abutments", "soils", "standards",
                                  "loads", "validation_model", "project_id", "revision"}
                    })
        from bridgecad_qa.compliance import score            # type: ignore
        grade, score_num, notes = score(project)
        print(f"[bridgecad] qa :: {path.name}")
        print(f"  Grade    : {grade}")
        print(f"  Score    : {score_num}/100")
        if isinstance(notes, list):
            for n in notes:
                print(f"  Note     : {n}")
        else:
            print(f"  Notes    : {notes}")
        return 0

    # ── info ──────────────────────────────────────────────────────────
    if cmd == "info":
        import os
        info_lines = [
            banner,
            f"  interpreter : {sys.executable}",
            f"  version     : {sys.version}",
            f"  repo root   : {Path(__file__).resolve().parent.parent}",
            "",
            "  sys.path workspace roots (bridgecad auto-loaded):",
        ]
        for p in sys.path:
            if any(tok in p for tok in [os.sep + "packages" + os.sep + "bridgecad", os.sep + "apps" + os.sep, os.sep + "bridgecad"]):
                info_lines.append(f"    + {p}")
        info_lines.append("")
        print("\n".join(info_lines))
        return 0

    print(banner)
    print(f"  Unknown command: {cmd!r}")
    return 2


if __name__ == "__main__":
    raise SystemExit(app())
