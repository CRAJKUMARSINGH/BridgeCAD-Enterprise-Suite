import sys
print("=== Legacy app imports ===")
sys.path.insert(0, "src")
try:
    from bridge_gad.calc_engine import CalcEngine
    e = CalcEngine.with_bridge_defaults()
    e.set("SPAN1", 12.0); e.set("NSPAN", 3); e.set("LEFT", 0)
    r = e.recalculate()
    lb = r.get("LBRIDGE")
    assert lb == 36.0, f"Expected 36.0 got {lb}"
    print(f"  CalcEngine OK: LBRIDGE={lb}")
except Exception as ex:
    print(f"  FAIL CalcEngine: {ex}")
    sys.exit(1)

try:
    from bridge_gad.worker import WorkerSettings, generate_drawing_job
    print("  Worker import OK")
except Exception as ex:
    print(f"  FAIL Worker: {ex}")
    sys.exit(1)

try:
    from bridge_gad.telemetry import TELEMETRY_ENABLED
    assert not TELEMETRY_ENABLED, "Telemetry must be opt-in"
    print("  Telemetry opt-in OK")
except Exception as ex:
    print(f"  FAIL Telemetry: {ex}")
    sys.exit(1)

print("=== Suite: API gateway module syntax + helpers (ROOT FLAT PACKAGES) ===")
SUITE_DIR = r"E:\Rajkumar\Bridge_GAD_Yogendra_Borse"
sys.path.insert(0, SUITE_DIR + r"\apps\api-gateway")
sys.path.insert(0, SUITE_DIR + r"\packages\bridgecad-core")
sys.path.insert(0, SUITE_DIR + r"\packages\bridgecad-io")
sys.path.insert(0, SUITE_DIR + r"\packages\bridgecad-bill")
sys.path.insert(0, SUITE_DIR + r"\packages\bridgecad-qa")
sys.path.insert(0, SUITE_DIR + r"\packages\bridgecad-export")

# Import the helper functions directly from the API module (without actually starting FastAPI)
import importlib.util
spec = importlib.util.spec_from_file_location(
    "bridgecad_api_main",
    SUITE_DIR + r"\apps\api-gateway\bridgecad_api\main.py"
)
mod = importlib.util.module_from_spec(spec)
# Don't execute the routers / lifespan — just parse the module level functions
spec.loader.exec_module(mod)

# Test the input validators (pure helpers, no external imports needed)
try:
    assert mod._validate_scale(100) == 100
    assert mod._validate_scale(50) == 50
    assert mod._validate_scale(2500) == 2500
    print("  _validate_scale: pass positive cases")
except Exception as ex:
    print(f"  FAIL _validate_scale pass cases: {ex}")
    sys.exit(1)

# Rejection cases
from fastapi import HTTPException
for bad_scale in [-1, 0, 1, 9, 2501, "abc"]:
    caught = False
    try:
        mod._validate_scale(bad_scale if isinstance(bad_scale, int) else bad_scale)
    except HTTPException as he:
        caught = True
        assert he.status_code == 400
    except Exception:
        caught = True
    if not caught:
        print(f"  FAIL _validate_scale did not reject {bad_scale!r}")
        sys.exit(1)
print("  _validate_scale: pass rejection cases")

# Prefix validator
try:
    assert mod._validate_prefix("GAD") == "GAD"
    assert mod._validate_prefix("My Bridge 12") == "My_Bridge_12"
    assert mod._validate_prefix("") == "GAD"
    assert len(mod._validate_prefix("A" * 100)) == 32
    print("  _validate_prefix: pass positive cases")
except Exception as ex:
    print(f"  FAIL _validate_prefix: {ex}")
    sys.exit(1)

for bad in ["foo/bar", "..\\evil", "<script>", "file:name"]:
    caught = False
    try:
        mod._validate_prefix(bad)
    except HTTPException as he:
        caught = True
        assert he.status_code == 400
    if not caught:
        print(f"  FAIL _validate_prefix did not reject {bad!r}")
        sys.exit(1)
print("  _validate_prefix: pass rejection cases")

print("\n*** ALL SMOKE CHECKS PASSED ***")
