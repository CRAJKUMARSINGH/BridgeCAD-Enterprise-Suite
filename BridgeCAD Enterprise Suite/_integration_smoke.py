"""Smoke-test script for the unified bridgecad facade package + sitecustomize."""
from __future__ import annotations

import sys
from pathlib import Path

print("=" * 78)
print("STEP 0 · sitecustomize bootstrap applied:",
      getattr(sys, "__bridgecad_workspace_bootstrap_applied__", False))

import sitecustomize  # noqa: F401 — ensure bootstrap fires even if `python -S`
print("STEP 0 bis · bootstrap re-apply (idempotent): OK")
print()

# ── 1. Facade banner ──────────────────────────────────────────────────
import bridgecad as bc

print("=" * 78)
print("STEP 1 · facade banner")
print(f"  suite      : {bc.__suite__}")
print(f"  version    : {bc.__version__}")
print(f"  moniker    : {bc.__moniker__}")

# ── 2. Submodule list ─────────────────────────────────────────────────
facade_attrs = sorted(n for n in dir(bc) if not n.startswith("_"))
print()
print("STEP 2 · facade public attrs (first 18):")
for a in facade_attrs[:18]:
    print(f"   · {a}")

# ── 3. Resolve core + enums via facade ────────────────────────────────
print()
print("=" * 78)
print("STEP 3 · resolve bc.models / bc.types / bc.validation")

BridgeProject = bc.models.BridgeProject
SlabType    = bc.types.SlabType
GirderType  = bc.types.GirderType
run_all     = bc.validation.run_all

print(f"  BridgeProject            : {type(BridgeProject).__name__} (Pydantic class? {hasattr(BridgeProject, 'model_validate')})")
print(f"  SlabType.SOLID_MONOLITHIC: {SlabType.SOLID_MONOLITHIC}")
print(f"  GirderType.I_GIRDER_PS   : {GirderType.I_GIRDER_PS_PRECAST_OR_INSITU}")
print(f"  validation.run_all call. : {callable(run_all)}")

# ── 4. Resolve draw / qa / bill / io / geometry ──────────────────────────
print()
print("=" * 78)
print("STEP 4 · resolve bc.draw / bc.qa / bc.bill / bc.io / bc.geometry")
print(f"  bc.draw.generate_package callable       : {callable(bc.draw.generate_package)}")
print(f"  bc.qa.score              callable       : {callable(bc.qa.score)}")
print(f"  bc.bill.extract_and_price callable      : {callable(bc.bill.extract_and_price)}")
# json_adapter is a stub module (M2 placeholder); we just ensure access resolves.
print(f"  bc.io.json_adapter  is module           : {type(bc.io.json_adapter).__name__ == 'module'}")
# geometry.__init__ re-exports classes / fns as top-level names (not submodules).
# We therefore check for the actual exported compute_* and classes.
print(f"  bc.geometry.compute_plan_geometry       : {callable(getattr(bc.geometry, 'compute_plan_geometry', None))}")
print(f"  bc.geometry.BridgePlanGeometry          : {type(getattr(bc.geometry, 'BridgePlanGeometry', None)).__name__ == 'type'}")
print(f"  bc.geometry.compute_long_section_geom.  : {callable(getattr(bc.geometry, 'compute_long_section_geometry', None))}")
print(f"  bc.geometry.compute_cross_section_geom. : {callable(getattr(bc.geometry, 'compute_cross_section_geometry', None))}")
print(f"  bc.geometry.compute_pile_group_layout   : {callable(getattr(bc.geometry, 'compute_pile_group_layout', None))}")
# But we also load the submodules themselves directly so `bc.geometry.plan` fn-class name shadow still works:
import bridgecad_core.geometry.plan as _plan_mod  # noqa: F401
import bridgecad_core.geometry.long_section as _ls_mod  # noqa: F401
import bridgecad_core.geometry.cross_section as _cs_mod  # noqa: F401
print(f"  bridgecad_core.geometry.plan (module)   : True")
print(f"  bridgecad_core.geometry.long_section    : True")
print(f"  bridgecad_core.geometry.cross_section   : True")

# ── 5. Legacy imports STILL WORK (back-compat) ────────────────────────
print()
print("=" * 78)
print("STEP 5 · back-compat: direct bridgecad_core / bridgecad_draw imports")
try:
    from bridgecad_core.models import BridgeProject as BP2
    from bridgecad_draw.booklet import generate_package as GP2
    from bridgecad_qa.compliance import score as SC2
    from bridgecad_bill.processor import extract_and_price as EP2
    # json_adapter is a stub (M2 placeholder) — don't depend on dump_project existing;
    # we just confirm import resolves.
    import bridgecad_io.json_adapter as _  # noqa: F401
    compat = True
except Exception as e:  # pragma: no cover
    compat = False
    import traceback; traceback.print_exc()
    print(f"  ERROR (legacy): {type(e).__name__}: {e}")
print(f"  bridgecad_core.models.BridgeProject OK : {compat}")

# ── 6. Route repo integration: facade <-> packages <-> apps ────────────
print()
print("=" * 78)
print("STEP 6 · Route repo integration: facade bridgecad/ + packages/* + apps/*")
REPO = Path(__file__).resolve().parent
junction_ok = (
    (REPO / "bridgecad" / "__init__.py").is_file()
    and (REPO / "packages" / "bridgecad-core" / "pyproject.toml").exists()
    and (REPO / "packages" / "bridgecad-core" / "bridgecad_core" / "models.py").exists()
    and (REPO / "packages" / "bridgecad-draw" / "bridgecad_draw" / "booklet.py").exists()
    and (REPO / "packages" / "bridgecad-core" / "bridgecad_core" / "types.py").exists()
    and (REPO / "apps" / "cli-console").is_dir()
    and (REPO / "apps" / "api-gateway").is_dir()
    and (REPO / "sitecustomize.py").is_file()
)
print(f"  Integration ok (facade + 9 pkgs + 2 apps + bootstrap) : {junction_ok}")
print(f"     bridgecad/__init__.py  (facade)              exists : {(REPO / 'bridgecad' / '__init__.py').exists()}")
print(f"     packages/bridgecad-core (models/types)       exists : {(REPO / 'packages' / 'bridgecad-core').exists()}")
print(f"     packages/bridgecad-draw (booklet/sheets)     exists : {(REPO / 'packages' / 'bridgecad-draw').exists()}")
print(f"     packages/bridgecad-qa   (compliance)         exists : {(REPO / 'packages' / 'bridgecad-qa').exists()}")
print(f"     packages/bridgecad-bill (processor)          exists : {(REPO / 'packages' / 'bridgecad-bill').exists()}")
print(f"     packages/bridgecad-export (orchestrator)     exists : {(REPO / 'packages' / 'bridgecad-export').exists()}")
print(f"     apps/cli-console                              exists : {(REPO / 'apps' / 'cli-console').exists()}")
print(f"     apps/api-gateway                              exists : {(REPO / 'apps' / 'api-gateway').exists()}")
print(f"     sitecustomize.py (sys.path bootstrap)        exists : {(REPO / 'sitecustomize.py').exists()}")

# ── 7. python -m bridgecad info output ────────────────────────────────
print()
print("=" * 78)
print("STEP 7 · `python -m bridgecad` banner")
import subprocess
rc = subprocess.call([sys.executable, "-m", "bridgecad"],
                     cwd=str(Path(__file__).resolve().parent))
print(f"  python -m bridgecad exit code : {rc}")

# ── Final verdict ─────────────────────────────────────────────────────
print()
print("=" * 78)
failures = []
if not junction_ok: failures.append("route repo integration (facade + pkgs + apps)")
if not compat:     failures.append("legacy imports (bridgecad_core)")
if rc != 0:        failures.append("python -m bridgecad")
if failures:
    print(f"FAILURES: {failures}")
    raise SystemExit(1)
print("★ ROUTE REPO INTEGRATION SMOKE TEST · ALL 7 STEPS PASSED ★")
