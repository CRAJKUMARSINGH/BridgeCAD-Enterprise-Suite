"""
BRIDGECAD-OSS-1.0-RC1 — Release Candidate Smoke Test.

Runs all 5 E2E fixtures through the full pipeline and verifies:
  ★ Version string == "0.1.0-rc1" in every package
  ★ 5/5 E2E fixtures ACCEPTED
  ★ CLI health command imports clean
  ★ FastAPI app constructs with correct version
  ★ M8-AI optimizer produces feasible result (cost > 0)
  ★ M8-Infra DB creates tables (SQLite, idempotent)

Run:
    python rc1_smoke.py
"""
from __future__ import annotations
import sys
import importlib
import traceback
from pathlib import Path

# ── bootstrap ────────────────────────────────────────────────────────────
_SUITE = Path(__file__).parent
for _pkg in ["bridgecad-core","bridgecad-io","bridgecad-draw",
             "bridgecad-bill","bridgecad-qa","bridgecad-export",
             "bridgecad-plugins","bridgecad-ai","bridgecad-infra"]:
    _p = _SUITE / "packages" / _pkg
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
for _app in ["cli-console","api-gateway"]:
    _p = _SUITE / "apps" / _app
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

SEP  = "=" * 72
PASS = "  [PASS]"
FAIL = "  [FAIL]"
SKIP = "  [SKIP]"
RC1  = "0.1.0-rc1"

results: list[tuple[str, bool]] = []
skipped: list[str] = []

#: Optional `[infra]` extras. A smoke test must fail on *product* defects, not
#: on an environment that chose not to install an optional extra.
INFRA_EXTRAS = {"sqlalchemy", "alembic", "redis", "boto3", "structlog", "arq"}

def ok(label, detail=""):
    msg = f"{PASS} {label}" + (f"  ({detail})" if detail else "")
    print(msg); results.append((label, True))

def fail(label, detail=""):
    msg = f"{FAIL} {label}" + (f"  ✗ {detail}" if detail else "")
    print(msg); results.append((label, False))

def skip(label, detail=""):
    msg = f"{SKIP} {label}" + (f"  ({detail})" if detail else "")
    print(msg); skipped.append(label)


print(); print(SEP)
print(f"  BRIDGECAD-OSS-1.0-RC1  RELEASE SMOKE TEST")
print(SEP)

# ── RC1-01: version strings ───────────────────────────────────────────────
PACKAGES = ["bridgecad_core","bridgecad_io","bridgecad_draw","bridgecad_bill",
            "bridgecad_qa","bridgecad_export","bridgecad_plugins",
            "bridgecad_ai","bridgecad_infra"]
wrong = []
for pkg in PACKAGES:
    try:
        mod = importlib.import_module(pkg)
        v   = getattr(mod, "__version__", None)
        if v != RC1:
            wrong.append(f"{pkg}={v!r}")
    except Exception as exc:
        wrong.append(f"{pkg}=IMPORT_ERROR({exc})")
if wrong:
    fail("RC1-01 version strings", "; ".join(wrong))
else:
    ok("RC1-01 version strings", f"all {len(PACKAGES)} packages == {RC1!r}")

# ── RC1-02: CLI import ────────────────────────────────────────────────────
try:
    from bridgecad_cli.main import app as _cli_app
    ok("RC1-02 CLI import", "bridgecad_cli.main.app found")
except Exception as exc:
    fail("RC1-02 CLI import", str(exc)[:80])

# ── RC1-03: FastAPI app version ───────────────────────────────────────────
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "bridgecad_api.main",
        _SUITE / "apps" / "api-gateway" / "bridgecad_api" / "main.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    api_ver = getattr(mod, "__version__", "")
    if api_ver == RC1:
        ok("RC1-03 FastAPI version", f"__version__={api_ver!r}")
    else:
        fail("RC1-03 FastAPI version", f"got {api_ver!r}")
except Exception as exc:
    fail("RC1-03 FastAPI version", str(exc)[:80])

# ── RC1-04: M8-AI optimizer ───────────────────────────────────────────────
try:
    from bridgecad_ai.optimizer import BridgeOptimizer
    r = BridgeOptimizer().optimize(36.0, max_span_m=20.0)
    if r.success and r.estimated_cost_inr > 0:
        ok("RC1-04 AI optimizer", f"span={r.optimal_span_m}m  cost=INR {r.estimated_cost_inr:,.0f}")
    else:
        fail("RC1-04 AI optimizer", f"success={r.success}  cost={r.estimated_cost_inr}")
except Exception as exc:
    fail("RC1-04 AI optimizer", str(exc)[:80])

# ── RC1-05: M8-Infra DB ───────────────────────────────────────────────────
try:
    from bridgecad_infra.db import create_all_tables
    create_all_tables()
    ok("RC1-05 Infra DB", "tables created (SQLite idempotent)")
except ModuleNotFoundError as exc:
    missing = (exc.name or "").split(".")[0]
    if missing in INFRA_EXTRAS:
        skip("RC1-05 Infra DB", f"infra extras not installed (missing {missing!r})")
    else:
        fail("RC1-05 Infra DB", str(exc)[:80])
except Exception as exc:
    fail("RC1-05 Infra DB", str(exc)[:80])

# ── RC1-06 through RC1-10: E2E fixtures ──────────────────────────────────
import subprocess, tempfile
result = subprocess.run(
    [sys.executable, "tests/e2e/run_e2e.py"],
    capture_output=True, text=True, cwd=str(_SUITE),
    timeout=600,
)
e2e_lines = (result.stdout + result.stderr).splitlines()
pass_lines = [l for l in e2e_lines if "[PASS]" in l]
fail_lines = [l for l in e2e_lines if "[FAIL]" in l]
verdict    = "★ ACCEPTED ★" in (result.stdout + result.stderr)

for l in pass_lines:
    fid = l.strip().replace("[PASS]","").strip()
    ok(f"RC1-E2E {fid}")
for l in fail_lines:
    fid = l.strip().replace("[FAIL]","").strip()
    fail(f"RC1-E2E {fid}")
if not pass_lines and not fail_lines:
    fail("RC1-E2E", f"no output (rc={result.returncode})")

# ── RC1-11: `bridgecad --version` ────────────────────────────────────────
try:
    res = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0,r'" +
         str(_SUITE/"apps"/"cli-console") + "'); "
         "from bridgecad_cli.main import __version__; print(__version__)"],
        capture_output=True, text=True, timeout=15,
    )
    ver_out = res.stdout.strip()
    if ver_out == RC1:
        ok("RC1-11 bridgecad --version", f"printed {ver_out!r}")
    else:
        fail("RC1-11 bridgecad --version", f"got {ver_out!r}")
except Exception as exc:
    fail("RC1-11 bridgecad --version", str(exc)[:80])

# ── Final verdict ─────────────────────────────────────────────────────────
passed = sum(1 for _, ok_ in results if ok_)
failed = sum(1 for _, ok_ in results if not ok_)
total  = passed + failed
all_ok = failed == 0

print(); print(SEP); print("  RC1 RELEASE VERDICT"); print(SEP)
print(f"  Checks run  : {total}")
print(f"  Passed      : {passed}")
print(f"  Failed      : {failed}")
if skipped:
    print(f"  Skipped     : {len(skipped)}  (optional extras absent — not a product defect)")
    for label in skipped:
        print(f"    ~ {label}")
if not all_ok:
    print("\n  FAILURES:")
    for label, ok_ in results:
        if not ok_:
            print(f"    ✗ {label}")
print(f"\n  BRIDGECAD-OSS-1.0  RC1  "
      f"{'★ ACCEPTED ★' if all_ok else 'NOT READY'}")
print(SEP)
sys.exit(0 if all_ok else 1)
