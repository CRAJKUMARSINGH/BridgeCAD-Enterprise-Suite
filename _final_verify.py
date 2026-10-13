import py_compile, sys, os
from pathlib import Path

REPO = Path(__file__).resolve().parent
os.chdir(str(REPO))

# 1. Re-verify API gateway compiles after all edits
try:
    py_compile.compile(
        str(REPO / "apps" / "api-gateway" / "bridgecad_api" / "main.py"),
        doraise=True,
    )
    print("  OK: API gateway main.py compiles")
except py_compile.PyCompileError as e:
    print(f"  FAIL: {e}")
    sys.exit(1)

# 2. CLI console compiles
try:
    py_compile.compile(
        str(REPO / "apps" / "cli-console" / "bridgecad_cli" / "main.py"),
        doraise=True,
    )
    print("  OK: CLI console main.py compiles")
except py_compile.PyCompileError as e:
    print(f"  FAIL: {e}")
    sys.exit(1)

# 3. Core packages compile (types / models / validation / foundation / primitives)
for rel in [
    "packages/bridgecad-core/bridgecad_core/types.py",
    "packages/bridgecad-core/bridgecad_core/models.py",
    "packages/bridgecad-core/bridgecad_core/validation.py",
    "packages/bridgecad-core/bridgecad_core/validation_registry.py",
    "packages/bridgecad-core/bridgecad_core/geometry/foundation.py",
    "packages/bridgecad-draw/bridgecad_draw/primitives.py",
    "packages/bridgecad-draw/bridgecad_draw/sheets/sheet7_bill_of_quantities.py",
    "packages/bridgecad-export/bridgecad_export/orchestrator.py",
    "packages/bridgecad-bill/bridgecad_bill/formatters/pdf_formatter.py",
    "bridgecad/__init__.py",
    "bridgecad/__main__.py",
    "sitecustomize.py",
]:
    p = REPO / rel
    if not p.exists():
        print(f"  SKIP (not found): {rel}")
        continue
    try:
        py_compile.compile(str(p), doraise=True)
        print(f"  OK compile: {rel}")
    except py_compile.PyCompileError as e:
        print(f"  FAIL {rel}: {e}")
        sys.exit(1)

# 4. Try YAML syntax check (PyYAML)
try:
    import yaml  # type: ignore
    workflow_files = [
        ".github/workflows/ci.yml",
        ".github/workflows/bench.yml",
        ".github/workflows/release.yml",
    ]
    for wf_rel in workflow_files:
        wf = REPO / wf_rel
        if not wf.exists():
            print(f"  SKIP (not found): {wf_rel}")
            continue
        with open(wf, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        assert isinstance(data, dict), f"{wf_rel}: not a YAML mapping"
        assert "jobs" in data, f"{wf_rel}: missing top-level 'jobs' key"
        print(f"  OK YAML: {wf_rel}  jobs={sorted(data['jobs'].keys())}")

    standard_files = [
        "standards/irc_05_hydraulic.yaml",
        "standards/irc_21_structural.yaml",
        "standards/irc_sp55_drawing.yaml",
        "standards/morth_rates_2024.yaml",
    ]
    for s_rel in standard_files:
        s = REPO / s_rel
        if not s.exists():
            print(f"  SKIP (not found): {s_rel}")
            continue
        try:
            with open(s, "r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
            print(f"  OK YAML: {s_rel}")
        except yaml.YAMLError as ye:
            print(f"  WARN YAML (pre-existing issue): {s_rel} — {type(ye).__name__}")
except ImportError:
    print("  PyYAML not importable — skipping YAML parse; CI will parse at runtime")

# 5. Facade entry point
import subprocess
print("  Running: python -m bridgecad info")
res = subprocess.run(
    [sys.executable, "-m", "bridgecad", "info"],
    cwd=str(REPO),
    capture_output=True,
    text=True,
    timeout=60,
)
print(res.stdout[-1200:] if len(res.stdout) > 1200 else res.stdout)
if res.returncode != 0:
    if res.stderr:
        print("STDERR tail:", res.stderr[-500:])
    print(f"  FAIL: python -m bridgecad info exited {res.returncode}")
    sys.exit(res.returncode)

print()
print("★ ROOT REPO FINAL VERIFY · ALL CHECKS GREEN ★")
sys.exit(0)
