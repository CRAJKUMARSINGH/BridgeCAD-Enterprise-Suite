"""M1 Week 1 Final Sign-Off — runs Days 1..5 and import smoke."""
from __future__ import annotations

import datetime
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

SEP = "─" * 72

def run_import_smoke() -> int:
    print(SEP)
    print("  TOP-LEVEL IMPORT SMOKE  (bridgecad_core.*)  —",
          datetime.datetime.now().strftime("%Y-%m-%d %H:%M IST"))
    print(SEP)
    import bridgecad_core as bc
    checks = [
        ("mod", "types"), ("mod", "models"), ("mod", "validation"),
        ("mod", "quantities"), ("mod", "costs"), ("mod", "geometry"),
        ("mod", "standards"), ("mod", "validation_registry"),
        ("type", "BridgeCategory"), ("type", "BridgeSelectionCriterion"),
        ("type", "BearingType"), ("type", "ExpansionJointType"),
        ("type", "SuperstructureType"), ("type", "PierType"),
        ("type", "AbutmentType"), ("type", "FoundationType"),
        ("type", "ConcreteGrade"), ("type", "SteelGrade"),
        ("cls",  "BridgeProject"), ("cls", "ValidationModel"),
        ("cls",  "ProjectMaster"), ("cls", "BridgePlanGeometry"),
        ("cls",  "LongSectionGeometry"), ("cls", "CrossSectionGeometry"),
        ("cls",  "PileGroupLayout"),
        ("fn",   "compute_plan_geometry"), ("fn", "compute_long_section_geometry"),
        ("fn",   "compute_cross_section_geometry"), ("fn", "compute_pile_group_layout"),
        ("fn",   "preferred_scale"), ("fn", "text_height"),
        ("fn",   "lineweight_for_layer"), ("fn", "hatch_for_material"),
        ("fn",   "dimension_style"),
    ]
    ok = fail = 0
    for kind, name in checks:
        try:
            getattr(bc, name)
            print(f"  OK  {name:<40} {kind}")
            ok += 1
        except AttributeError as e:
            print(f"  FAIL {name:<40} {kind}  {e}")
            fail += 1
    print()
    print(f"  IMPORT SUMMARY: {ok} OK  {fail} FAIL  "
          f"→  {'PASS' if fail == 0 else 'FAIL'}")
    return 0 if fail == 0 else 1


def run_day_scripts() -> int:
    print()
    print(SEP)
    print("  M1 WEEK 1 — DAYS 1 .. 5 RUN  (5 DAYS, AC-1..AC-12 AGGREGATED)")
    print(SEP)
    days = [
        ("day1_verify.py",  "Day 1  Types (184 Enums, LabeledEnum mixins)"),
        ("day2_summary.py", "Day 2  Enum audit + ENUM_REGISTRY wiring"),
        ("day3_verify.py",  "Day 3  Pydantic models — 14 sheets, 439 fields"),
        ("day4_verify.py",  "Day 4  Geometry (4 modules) + validation stubs"),
        ("day5_verify.py",  "Day 5  Standards wiring + WEEK 1 SIGN-OFF"),
    ]
    total_rc = 0
    for fname, title in days:
        print()
        print(f">>>  {title}")
        p = ROOT / fname
        if not p.exists():
            print(f"     SKIPPED  (file missing: {fname})")
            continue
        r = subprocess.run([sys.executable, str(p)],
                           capture_output=True, text=True, cwd=str(ROOT))
        verdict_lines = [l.strip() for l in r.stdout.splitlines()
                         if "VERDICT" in l or "ACCEPTED" in l or "SIGN-OFF" in l]
        for v in verdict_lines:
            print(f"     {v}")
        rc_icon = "OK" if r.returncode == 0 else "FAIL"
        print(f"     {rc_icon}  exit_code={r.returncode}")
        if r.returncode != 0:
            total_rc += 1
            tail = [l for l in r.stdout.splitlines() if l.strip()][-10:]
            for l in tail:
                print(f"       | {l}")
    return total_rc


def main() -> int:
    import_rc = run_import_smoke()
    days_rc   = run_day_scripts()
    total_fail = import_rc + days_rc

    print()
    print(SEP)
    print(f"  M1 WEEK-1 FINAL SIGN-OFF  —  {datetime.date.today()}")
    print(f"  Import smoke  : { 'PASS' if import_rc == 0 else 'FAIL' }  "
          f"(geometry + standards top-level exports)")
    print(f"  Days 1..5 run : { 'PASS' if days_rc == 0 else f'{days_rc} FAIL' }")
    print(f"  Overall       : { '★ ACCEPTED ★' if total_fail == 0 else 'REJECTED' }")
    print(SEP)
    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
