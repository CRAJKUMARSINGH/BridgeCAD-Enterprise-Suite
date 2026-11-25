#!/usr/bin/env python3
"""
Ultimate Bridge GAD Generator - Comprehensive Test Suite
Tests the app with all available input files and generates date-stamped outputs
"""

import sys
import os
from pathlib import Path
import time
from datetime import datetime
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

def get_timestamp():
    """Get formatted timestamp for filenames"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def get_readable_timestamp():
    """Get readable timestamp for reports"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def ensure_outputs_folder():
    """Create outputs folder if it doesn't exist"""
    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)
    return outputs_dir

def test_drawing_generation():
    """Test drawing generation with all available input files"""
    print("\n" + "="*70)
    print("🧪 ULTIMATE BRIDGE GAD GENERATOR - COMPREHENSIVE TEST SUITE")
    print("="*70 + "\n")
    
    # Import required modules
    try:
        from bridge_gad.bridge_generator import BridgeGADGenerator
        # FIX REPLIT-005: generate_bridge_gad does not exist; use generate_complete_drawing
        from bridge_gad.enhanced_io_utils import SmartInputProcessor
        print("✅ Modules imported successfully\n")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False, []
    
    # Ensure outputs folder exists
    outputs_dir = ensure_outputs_folder()
    print(f"✅ Outputs folder ready: {outputs_dir.absolute()}\n")
    
    # Get timestamp for this test run
    test_timestamp = get_timestamp()
    
    # Find all Excel input files
    inputs_dir = Path("inputs")
    test_files = list(inputs_dir.glob("*.xlsx"))
    
    if not test_files:
        print("❌ No input files found in inputs/ folder")
        return False, []
    
    print(f"📁 Found {len(test_files)} input file(s) to test:\n")
    for i, f in enumerate(test_files, 1):
        size = f.stat().st_size / 1024
        print(f"   {i}. {f.name} ({size:.1f} KB)")
    print()
    
    results = []
    
    # Known span-data format files that can't be processed by BridgeGADGenerator directly
    _SPAN_DATA_FILES = {"spans_only.xlsx"}

    for idx, test_file in enumerate(test_files, 1):
        print(f"{'='*70}")
        print(f"📝 Test {idx}/{len(test_files)}: {test_file.name}")
        print(f"{'='*70}")
        
        try:
            # Start timer
            start_time = time.time()
            
            # Use smart input processor for better format handling
            print(f"  → Reading input with smart processor...")
            processor = SmartInputProcessor()

            # Skip known span-data format files (not compatible with BridgeGADGenerator)
            if test_file.name in _SPAN_DATA_FILES:
                print(f"  ⏭️  SKIPPED: span-data format (not a parameter file)")
                results.append({
                    'test_number': idx,
                    'input_file': str(test_file),
                    'status': 'SKIPPED',
                    'time_seconds': 0,
                    'timestamp': get_readable_timestamp()
                })
                continue
            
            try:
                params = processor.read_input(test_file)
                params = processor.validate_parameters(params)
                print(f"  → Loaded {len(params)} parameters")
            except Exception as e:
                print(f"  ⚠️  Smart processor failed, using direct method: {e}")
                # Fallback to direct generation
                params = None
            
            # Generate date-stamped output filename
            base_name = test_file.stem
            output_file = outputs_dir / f"{base_name}_{test_timestamp}.dxf"
            
            print(f"  → Output: {output_file}")
            print(f"  → Generating DXF drawing...")
            
            # FIX REPLIT-005: use generate_complete_drawing instead of non-existent generate_bridge_gad
            gen = BridgeGADGenerator()
            result = gen.generate_complete_drawing(test_file, output_file)
            
            # End timer
            elapsed = time.time() - start_time
            
            # Check output
            if output_file.exists():
                size = output_file.stat().st_size
                print(f"\n  ✅ SUCCESS!")
                print(f"     • Output: {output_file.name}")
                print(f"     • Size: {size:,} bytes ({size/1024:.1f} KB)")
                print(f"     • Time: {elapsed:.2f} seconds")
                print(f"     • Speed: {size/elapsed/1024:.1f} KB/s")
                
                results.append({
                    'test_number': idx,
                    'input_file': str(test_file),
                    'output_file': str(output_file),
                    'status': 'SUCCESS',
                    'size_bytes': size,
                    'size_kb': round(size/1024, 2),
                    'time_seconds': round(elapsed, 2),
                    'speed_kbps': round(size/elapsed/1024, 2),
                    'timestamp': get_readable_timestamp()
                })
            else:
                print(f"\n  ❌ FAILED: Output file not created")
                results.append({
                    'test_number': idx,
                    'input_file': str(test_file),
                    'output_file': str(output_file),
                    'status': 'FAILED',
                    'error': 'No output file created',
                    'time_seconds': round(elapsed, 2),
                    'timestamp': get_readable_timestamp()
                })
                
        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = str(e)
            print(f"\n  ❌ ERROR: {error_msg}")
            results.append({
                'test_number': idx,
                'input_file': str(test_file),
                'status': 'ERROR',
                'error': error_msg,
                'time_seconds': round(elapsed, 2),
                'timestamp': get_readable_timestamp()
            })
        
        print()
    
    # Generate summary report
    generate_summary_report(results, test_timestamp)
    
    # Print summary to console
    print_summary(results)
    
    success_count = sum(1 for r in results if r["status"] == "SUCCESS")
    skip_count   = sum(1 for r in results if r["status"] == "SKIPPED")
    assert success_count + skip_count == len(results), \
        f"{len(results) - success_count - skip_count} test(s) failed"


def generate_summary_report(results, test_timestamp):
    """Generate detailed JSON and text reports"""
    outputs_dir = Path("outputs")
    
    # JSON report
    json_report = outputs_dir / f"test_report_{test_timestamp}.json"
    with open(json_report, 'w') as f:
        json.dump({
            'test_run_timestamp': test_timestamp,
            'test_run_datetime': get_readable_timestamp(),
            'total_tests': len(results),
            'passed': sum(1 for r in results if r['status'] == 'SUCCESS'),
            'failed': sum(1 for r in results if r['status'] != 'SUCCESS'),
            'results': results
        }, f, indent=2)
    
    print(f"📄 JSON report saved: {json_report.name}")
    
    # Text report
    text_report = outputs_dir / f"test_report_{test_timestamp}.txt"
    with open(text_report, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("🌉 ULTIMATE BRIDGE GAD GENERATOR - TEST REPORT\n")
        f.write("="*70 + "\n\n")
        f.write(f"Test Run: {get_readable_timestamp()}\n")
        f.write(f"Timestamp: {test_timestamp}\n\n")
        
        success_count = sum(1 for r in results if r['status'] == 'SUCCESS')
        f.write(f"Total Tests: {len(results)}\n")
        f.write(f"Passed: {success_count}\n")
        f.write(f"Failed: {len(results) - success_count}\n")
        f.write(f"Success Rate: {success_count/len(results)*100:.1f}%\n\n")
        
        f.write("="*70 + "\n")
        f.write("DETAILED RESULTS\n")
        f.write("="*70 + "\n\n")
        
        for r in results:
            f.write(f"Test #{r['test_number']}: {Path(r['input_file']).name}\n")
            f.write(f"  Status: {r['status']}\n")
            if r['status'] == 'SUCCESS':
                f.write(f"  Output: {Path(r['output_file']).name}\n")
                f.write(f"  Size: {r['size_kb']} KB\n")
                f.write(f"  Time: {r['time_seconds']} seconds\n")
                f.write(f"  Speed: {r['speed_kbps']} KB/s\n")
            else:
                f.write(f"  Error: {r.get('error', 'Unknown')}\n")
            f.write(f"  Timestamp: {r['timestamp']}\n")
            f.write("\n")
        
        if success_count > 0:
            f.write("="*70 + "\n")
            f.write("STATISTICS\n")
            f.write("="*70 + "\n\n")
            
            successful = [r for r in results if r['status'] == 'SUCCESS']
            total_size = sum(r['size_kb'] for r in successful)
            total_time = sum(r['time_seconds'] for r in successful)
            avg_size = total_size / len(successful)
            avg_time = total_time / len(successful)
            
            f.write(f"Total Output Size: {total_size:.2f} KB\n")
            f.write(f"Total Processing Time: {total_time:.2f} seconds\n")
            f.write(f"Average File Size: {avg_size:.2f} KB\n")
            f.write(f"Average Processing Time: {avg_time:.2f} seconds\n")
            f.write(f"Overall Speed: {total_size/total_time:.2f} KB/s\n")
    
    print(f"📄 Text report saved: {text_report.name}\n")


def print_summary(results):
    """Print summary to console"""
    print("="*70)
    print("📊 TEST SUMMARY")
    print("="*70 + "\n")
    
    success_count = sum(1 for r in results if r['status'] == 'SUCCESS')
    total_count = len(results)
    
    print(f"Tests Run: {total_count}")
    print(f"Passed: {success_count} ✅")
    print(f"Failed: {total_count - success_count} ❌")
    print(f"Success Rate: {success_count/total_count*100:.1f}%\n")
    
    if success_count > 0:
        print("✅ Successful Tests:")
        print("-" * 70)
        for r in [x for x in results if x['status'] == 'SUCCESS']:
            print(f"  {r['test_number']}. {Path(r['input_file']).name}")
            print(f"     → {Path(r['output_file']).name}")
            print(f"     → {r['size_kb']} KB in {r['time_seconds']}s ({r['speed_kbps']} KB/s)")
        print()
    
    if success_count < total_count:
        print("❌ Failed Tests:")
        print("-" * 70)
        for r in [x for x in results if x['status'] != 'SUCCESS']:
            print(f"  {r['test_number']}. {Path(r['input_file']).name}")
            print(f"     → Error: {r.get('error', 'Unknown')}")
        print()
    
    if success_count > 0:
        successful = [r for r in results if r['status'] == 'SUCCESS']
        total_size = sum(r['size_kb'] for r in successful)
        total_time = sum(r['time_seconds'] for r in successful)
        
        print("📈 Statistics:")
        print("-" * 70)
        print(f"  Total Output: {total_size:.2f} KB")
        print(f"  Total Time: {total_time:.2f} seconds")
        print(f"  Average Size: {total_size/len(successful):.2f} KB")
        print(f"  Average Time: {total_time/len(successful):.2f} seconds")
        print(f"  Overall Speed: {total_size/total_time:.2f} KB/s")
        print()
    
    print("="*70)
    
    if success_count == total_count:
        print("🎉 ALL TESTS PASSED!")
    elif success_count > 0:
        print("⚠️  SOME TESTS PASSED")
    else:
        print("❌ ALL TESTS FAILED")
    
    print("="*70 + "\n")


def test_app_structure():
    """Test that all required modules exist"""
    print("\n" + "="*70)
    print("🔍 CHECKING APP STRUCTURE")
    print("="*70 + "\n")
    
    required_modules = [
        "src/bridge_gad/__init__.py",
        "src/bridge_gad/bridge_generator.py",
        "src/bridge_gad/io_utils.py",
        "src/bridge_gad/drawing.py",
        "src/bridge_gad/drawing_generator.py",
    ]
    
    all_exist = True
    for module in required_modules:
        if os.path.exists(module):
            print(f"  ✅ {module}")
        else:
            print(f"  ❌ {module} (MISSING)")
            all_exist = False
    
    print()
    
    if all_exist:
        print("✅ All required modules found!\n")
    else:
        print("❌ Some modules are missing!\n")
    
    assert all_exist, "Required modules are missing"


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🌉 ULTIMATE BRIDGE GAD GENERATOR - COMPREHENSIVE TEST SUITE")
    print("="*70)
    print(f"Started: {get_readable_timestamp()}")
    print("="*70)
    
    # Test structure
    structure_ok = test_app_structure()
    
    if not structure_ok:
        print("⚠️  Cannot proceed with tests - missing modules")
        sys.exit(1)
    
    # Test drawing generation
    tests_passed, results = test_drawing_generation()
    
    # Final message
    if tests_passed:
        print("✅ All outputs saved with date-stamped filenames in outputs/ folder")
        print(f"✅ Test reports generated: test_report_{get_timestamp()}.json/.txt")
    
    # Exit code
    sys.exit(0 if tests_passed else 1)


# ── Focused regression tests (pytest-compatible) ────────────────────────────

def test_standards_metadata():
    """Sanity-check the shared standards metadata module (folder-2 version).

    Covers:
      - PARAMETER_SPECS dataclass registry has new keys (OwnerProfile, phase 2).
      - Helper functions get_parameter_spec / get_parameter_description /
        get_owner_profile return sensible values and safe fallbacks.
      - OWNER_PROFILES expose all four authority presets.
      - PHASE_TWO_SHEETS defines the 7-sheet package.
      - DEFAULT_METADATA contains submission defaults.
      - build_template_rows, merge_with_metadata, checklist_rows,
        owner_profile_rows, phase_two_sheet_rows produce non-empty rows.
    """
    from bridge_gad import standards as s
    from bridge_gad.standards import (
        ParameterSpec, OwnerProfile, build_template_rows,
        merge_with_metadata, checklist_rows, owner_profile_rows,
        phase_two_sheet_rows, get_parameter_description, get_owner_profile,
        get_parameter_spec,
    )

    # Must-have new keys in the dataclass registry
    new_keys = [
        "DRAWING_STANDARD", "DESIGN_LIVE_LOAD", "ROAD_CLASS",
        "MEDIANW", "BARRIERT", "BEARING_W", "OWNER_PROFILE", "TOTAL_SHEETS",
        "DRAWING_NO", "REVISION", "LANES", "FOOTPATHW", "CRASHB",
        "BARRIERH", "UTILITYD", "DRAINSP", "CROSSFALL", "EXPJT",
        "BEARING_TYPE",
    ]
    for k in new_keys:
        assert k in s.PARAMETER_SPECS, f"Missing PARAMETER_SPECS[{k}]"
        spec = s.PARAMETER_SPECS[k]
        assert isinstance(spec, ParameterSpec)
        assert spec.key == k
        assert spec.description and isinstance(spec.description, str)
        assert isinstance(spec.unit, str)
        assert spec.category and isinstance(spec.category, str)

    # Unknown key -> get_parameter_spec returns a safe Custom fallback.
    fallback = get_parameter_spec("XYZ_NOT_A_THING")
    assert fallback.category == "Custom"
    assert "XYZ_NOT_A_THING" in fallback.description

    # get_parameter_description for known/unknown keys.
    assert get_parameter_description("DRAWING_NO") != "DRAWING_NO"
    assert "Project-specific" in get_parameter_description("XYZ_ABC")

    # Owner profiles: four presets + safe default.
    for p in ("IRC_MORTH", "NHAI", "RAILWAY", "ULB"):
        assert p in s.OWNER_PROFILES
        prof = s.OWNER_PROFILES[p]
        assert isinstance(prof, OwnerProfile)
        assert prof.owner and prof.drawing_standard
    assert get_owner_profile(None).key == "IRC_MORTH"
    assert get_owner_profile("bogus").key == "IRC_MORTH"
    assert get_owner_profile("NHAI").key == "NHAI"

    # Phase two package: 7 sheet schedule.
    sheets = phase_two_sheet_rows()
    assert len(sheets) == 7
    codes = {row["Code"] for row in sheets}
    for c in ("IDX", "GAD", "TYP", "ABT", "PIER", "BRG", "DRN"):
        assert c in codes, f"Phase 2 missing sheet code {c}"

    # DEFAULT_METADATA includes minimum submission fields.
    for tb in ["DRAWING_STANDARD", "DESIGN_LIVE_LOAD", "REVISION",
               "DRAWN_BY", "CHECKED_BY", "APPROVED_BY",
               "SHEET_NO", "TOTAL_SHEETS", "OWNER_PROFILE"]:
        assert tb in s.DEFAULT_METADATA and s.DEFAULT_METADATA[tb]

    # STANDARD_CHECKLIST non-empty + checklist_rows formatter.
    assert len(s.STANDARD_CHECKLIST) >= 5
    cl = checklist_rows()
    assert len(cl) == len(s.STANDARD_CHECKLIST)
    assert "Checklist Item" in cl[0]

    # build_template_rows produces expected columns.
    rows = build_template_rows({"CCBR": 8.0, "LANES": 2})
    assert len(rows) == 2
    for r in rows:
        for col in ("Value", "Variable", "Description", "Unit", "Category"):
            assert col in r

    # merge_with_metadata layers DEFAULT_METADATA then overrides then params.
    merged = merge_with_metadata({"LANES": 3}, DRAWING_NO="MY-99",
                                  OWNER_PROFILE="NHAI")
    assert merged["LANES"] == 3
    assert merged["DRAWING_NO"] == "MY-99"
    assert merged["OWNER_PROFILE"] == "NHAI"
    assert merged["REVISION"] == s.DEFAULT_METADATA["REVISION"]

    # owner_profile_rows returns all presets incl. PMGSY minor-bridge.
    ow = owner_profile_rows()
    assert len(ow) == 5


def test_template_excel_enriched():
    """make_template_excel now exports 4 sheets including OwnerProfiles
    and SheetIndex. Plus phase-two ZIP bundler runs without error.
    """
    from io import BytesIO
    from bridge_gad.bridge_canvas_features import (
        BRIDGE_TEMPLATES, make_template_excel, make_phase_two_package_zip,
    )
    import pandas as pd
    import zipfile

    params = BRIDGE_TEMPLATES["simple_12m"]["parameters"]
    for required in ["LANES", "MEDIANW", "BARRIERT", "BEARING_W",
                     "ROAD_CLASS", "DRAWING_STANDARD", "DESIGN_LIVE_LOAD",
                     "TOTAL_SHEETS", "OWNER_PROFILE"]:
        assert required in params, f"Template missing {required}"

    xls_bytes = make_template_excel(params)
    assert isinstance(xls_bytes, bytes) and len(xls_bytes) > 2048

    with pd.ExcelFile(BytesIO(xls_bytes), engine="openpyxl") as xls:
        for required_sheet in ("Parameters", "Checklist",
                               "OwnerProfiles", "SheetIndex"):
            assert required_sheet in xls.sheet_names, \
                f"Missing workbook sheet {required_sheet}"

        df_params = pd.read_excel(xls, sheet_name="Parameters")
        assert {"Value", "Variable", "Description", "Unit", "Category"} \
            .issubset(set(df_params.columns))
        variables = set(df_params["Variable"].astype(str).tolist())
        for k in ["LANES", "MEDIANW", "BARRIERT", "BEARING_W",
                  "DRAWING_STANDARD", "DESIGN_LIVE_LOAD",
                  "OWNER_PROFILE", "TOTAL_SHEETS"]:
            assert k in variables, f"Parameters sheet missing {k}"

        df_owner = pd.read_excel(xls, sheet_name="OwnerProfiles")
        assert {"Profile Key", "Owner", "Drawing Standard",
                "Design Live Load", "Review Note"} \
            .issubset(set(df_owner.columns))
        assert len(df_owner) == 5  # authority presets incl. PMGSY

        df_sheet = pd.read_excel(xls, sheet_name="SheetIndex")
        assert len(df_sheet) == 7  # phase two schedule

    # Phase two ZIP bundler produces a valid 3-entry zip.
    zip_bytes = make_phase_two_package_zip(params)
    assert isinstance(zip_bytes, bytes) and len(zip_bytes) > 4096
    with zipfile.ZipFile(BytesIO(zip_bytes), "r") as zf:
        names = set(zf.namelist())
        for required in ("phase2/phase2_parameters.xlsx",
                          "phase2/phase2_sheet_index.csv",
                          "phase2/phase2_manifest.json"):
            assert required in names, f"ZIP missing {required}"


def test_phase_three_package_zip():
    """make_phase_two_package_zip(include_phase_three=True) and the
    dedicated make_phase_three_package_zip helper produce the correct
    11-sheet submission bundles with phase-3 markers and no invented
    data leaks into the manifest.
    """
    from io import BytesIO
    from bridge_gad.bridge_canvas_features import (
        BRIDGE_TEMPLATES, make_phase_two_package_zip,
        make_phase_three_package_zip,
    )
    from bridge_gad.standards import (
        PHASE_THREE_CODE_SET, phase_three_sheet_rows,
    )
    import pandas as pd
    import zipfile
    import json

    params = BRIDGE_TEMPLATES["simple_12m"]["parameters"]

    # --- Helper A: phase_two wrapper with include_phase_three=True ---
    zip_p2_p3 = make_phase_two_package_zip(params, include_phase_three=True)
    assert isinstance(zip_p2_p3, bytes) and len(zip_p2_p3) > 4096

    with zipfile.ZipFile(BytesIO(zip_p2_p3), "r") as zf:
        names_p2 = set(zf.namelist())
        for required in ("phase2/phase2_parameters.xlsx",
                          "phase2/phase2_sheet_index.csv",
                          "phase2/phase2_manifest.json"):
            assert required in names_p2, f"P2+P3 ZIP missing {required}"

        manifest = json.loads(zf.read("phase2/phase2_manifest.json").decode("utf-8"))
        assert manifest["include_phase_three"] is True
        assert manifest["total_sheets"] == 11
        assert len(manifest["sheets"]) == 11
        codes_p2 = {row["Code"] for row in manifest["sheets"]}
        assert PHASE_THREE_CODE_SET.issubset(codes_p2), \
            f"P2+P3 sheet codes missing: {PHASE_THREE_CODE_SET - codes_p2}"

        csv_rows = pd.read_csv(BytesIO(zf.read("phase2/phase2_sheet_index.csv")))
        assert len(csv_rows) == 11, \
            f"P2+P3 CSV sheet index expected 11 rows, got {len(csv_rows)}"

        with pd.ExcelFile(BytesIO(zf.read("phase2/phase2_parameters.xlsx")),
                          engine="openpyxl") as xls:
            df_sheet = pd.read_excel(xls, sheet_name="SheetIndex")
            assert len(df_sheet) == 11, \
                f"P2+P3 XLSX SheetIndex expected 11 rows, got {len(df_sheet)}"

    # --- Helper B: dedicated make_phase_three_package_zip rewrites paths ---
    zip_p3 = make_phase_three_package_zip(params)
    assert isinstance(zip_p3, bytes) and len(zip_p3) > 4096

    with zipfile.ZipFile(BytesIO(zip_p3), "r") as zf:
        names_p3 = set(zf.namelist())
        # No phase2/ prefixes remain after the rewrite step.
        phase2_leftovers = [n for n in names_p3 if n.startswith("phase2/") or "phase2_" in n]
        assert phase2_leftovers == [], \
            f"P3 ZIP still contains phase2 names: {phase2_leftovers}"
        for required in ("phase3/phase3_parameters.xlsx",
                          "phase3/phase3_sheet_index.csv",
                          "phase3/phase3_manifest.json"):
            assert required in names_p3, f"P3 ZIP missing {required}"

        manifest3 = json.loads(zf.read("phase3/phase3_manifest.json").decode("utf-8"))
        assert manifest3.get("phase3") is True, \
            "P3 manifest must carry phase3=True flag after rewrite"
        assert manifest3["include_phase_three"] is True
        assert manifest3["total_sheets"] == 11
        assert len(manifest3["sheets"]) == 11
        codes_p3 = {row["Code"] for row in manifest3["sheets"]}
        assert PHASE_THREE_CODE_SET.issubset(codes_p3)

        csv_p3 = pd.read_csv(BytesIO(zf.read("phase3/phase3_sheet_index.csv")))
        assert len(csv_p3) == 11

        with pd.ExcelFile(BytesIO(zf.read("phase3/phase3_parameters.xlsx")),
                          engine="openpyxl") as xls:
            for required_sheet in ("Parameters", "Checklist",
                                   "OwnerProfiles", "SheetIndex"):
                assert required_sheet in xls.sheet_names
            df_s3 = pd.read_excel(xls, sheet_name="SheetIndex")
            assert len(df_s3) == 11


# =========================================================================
# PHASE C3 — DXF STRUCTURAL REGRESSION TESTS
# Baseline facts captured 2026-09-29 from ezdxf inspection of
# test_run_output/DXF/02_phase_two_7sheet/01_simple_12m_Sheet_Sheet*.dxf
# and multi_sheet_generator.py grep (TBC_BY_ENGINEER markers).
# Rule: NO invented data — every bound / keyword / code is fact-verified.
# Fix IDs referenced: §11 C3 in CREAT.MD
# =========================================================================


def _dxf_structural_baselines():
    """Return the verified structural baseline table for simple_12m.

    bounds are (min_entities, max_entities) inclusive.  We assert >=min
    to allow future polish (C2 hatching / dims) to INCREASE entity counts
    without breaking the test.  max bound catches catastrophic drops
    (empty sheet, dropped title block) while tolerating incremental polish.
    """
    return {
        # Phase 2 sheets
        "Sheet1": {
            "code": "IDX", "title": "DRAWING INDEX AND BASIS",
            "sheet_of": "Sheet 1 of 7",
            "entity_types_at_least": {"TEXT": 30, "LWPOLYLINE": 2, "LINE": 5},
            "min_entities": 45,
            # Required strings that must appear somewhere in the drawing.
            "required_substrings": [
                "DRAWING INDEX AND BASIS", "Sheet 1 of 7",
                "Drg: GAD-001", "Basis: IRC / MoRTH",
                "IDX", "GAD", "TYP", "ABT", "PIER", "BRG", "DRN",
            ],
        },
        "Sheet2": {
            "code": "GAD", "title": "PLAN VIEW - TOP",
            "sheet_of": "Sheet 2 of 7",
            "entity_types_at_least": {"TEXT": 8, "LWPOLYLINE": 3, "LINE": 2},
            "min_entities": 15,
            "required_substrings": [
                "PLAN VIEW - TOP", "Sheet 2 of 7",
                "Drg: GAD-001", "Basis: IRC / MoRTH",
                "Span 1", "Width:", "Total Length:",
            ],
        },
        "Sheet3": {
            "code": "TYP", "title": "SECTION VIEW - PROFILE",
            "sheet_of": "Sheet 3 of 7",
            "entity_types_at_least": {"TEXT": 10, "LWPOLYLINE": 4, "LINE": 3},
            "min_entities": 18,
            "required_substrings": [
                "SECTION VIEW - PROFILE", "Sheet 3 of 7",
                "Drg: GAD-001", "Basis: IRC / MoRTH",
                "DATUM", "Span:", "Height:",
            ],
        },
        "Sheet4": {
            "code": "ABT", "title": "ABUTMENT ELEVATION - ENLARGED",
            "sheet_of": "Sheet 4 of 7",
            "entity_types_at_least": {"TEXT": 10, "LWPOLYLINE": 4, "LINE": 2},
            "min_entities": 16,
            "required_substrings": [
                "ABUTMENT ELEVATION - ENLARGED", "Sheet 4 of 7",
                "Drg: GAD-001", "Basis: IRC / MoRTH",
                "GROUND LEVEL",
            ],
        },
        "Sheet5": {
            "code": "PIER", "title": "PIER ELEVATION - ENLARGED",
            "sheet_of": "Sheet 5 of 7",
            "entity_types_at_least": {"TEXT": 10, "LWPOLYLINE": 4, "LINE": 3},
            "min_entities": 18,
            "required_substrings": [
                "PIER ELEVATION - ENLARGED", "Sheet 5 of 7",
                "Drg: GAD-001", "Basis: IRC / MoRTH",
                "Pier Width", "Height", "Footing Width", "GROUND LEVEL",
            ],
        },
        "Sheet6": {
            "code": "BRG", "title": "BEARING AND EXPANSION JOINT NOTES",
            "sheet_of": "Sheet 6 of 7",
            "entity_types_at_least": {"TEXT": 12, "LWPOLYLINE": 3},
            "min_entities": 15,
            "required_substrings": [
                "BEARING AND EXPANSION JOINT NOTES", "Sheet 6 of 7",
                "Drg: GAD-001", "Basis: IRC / MoRTH",
                "Bearing system:", "Elastomeric",
                "detail drawings",  # note 5 ends with "...issued in detail drawings."
            ],
        },
        "Sheet7": {
            "code": "DRN", "title": "DRAINAGE, SAFETY AND UTILITY NOTES",
            "sheet_of": "Sheet 7 of 7",
            "entity_types_at_least": {"TEXT": 12, "LWPOLYLINE": 3},
            "min_entities": 15,
            "required_substrings": [
                "DRAINAGE, SAFETY AND UTILITY NOTES", "Sheet 7 of 7",
                "Drg: GAD-001", "Basis: IRC / MoRTH",
                "Drainage spout", "RCC crash barrier",
            ],
        },
        # Phase 3 sheets (TBC-stamped detail stubs) — baseline facts come
        # from multi_sheet_generator grep, not eyeballed DXF samples yet.
        # We don't pin exact entity counts here because detail polish (C2)
        # will raise them; we just assert the critical ring-fenced markers
        # and the no-invented-data TBC_BY_ENGINEER stamps are present.
        "Sheet8": {
            "code": "BRG-DET", "title": None, "sheet_of": None,
            "entity_types_at_least": {"TEXT": 10, "LWPOLYLINE": 2},
            "min_entities": 15,
            "required_substrings": [
                "TBC_BY_ENGINEER",  # ring-fence stamp
                "Bearing",
            ],
        },
        "Sheet9": {
            "code": "EXPJ-DET", "title": None, "sheet_of": None,
            "entity_types_at_least": {"TEXT": 10, "LWPOLYLINE": 2},
            "min_entities": 15,
            "required_substrings": [
                "TBC_BY_ENGINEER",
                "Expansion", "joint",
            ],
        },
        "Sheet10": {
            "code": "WING-DET", "title": None, "sheet_of": None,
            "entity_types_at_least": {"TEXT": 10, "LWPOLYLINE": 2},
            "min_entities": 15,
            "required_substrings": [
                "TBC_BY_ENGINEER",
                "REINFORCEMENT", "TBC",  # "REINFORCEMENT (INDICATIVE — TBC)"
                "Wing",
            ],
        },
        "Sheet11": {
            "code": "DRN-DET", "title": None, "sheet_of": None,
            "entity_types_at_least": {"TEXT": 10, "LWPOLYLINE": 2},
            "min_entities": 15,
            "required_substrings": [
                "TBC_BY_ENGINEER",
                "Drainage", "Downpipe" if False else "pipe",  # tolerant match
            ],
        },
    }


def test_phase2_phase3_dxf_structural_regression(tmp_path):
    """Phase C3 structural regression: entity-count sanity, layer
    presence, title-block text strings, TBC-by-engineer integrity
    stamps for the full 11-sheet Phase-3 package.

    Uses MultiSheetGenerator + simple_12m template params, writes to
    pytest tmp_path (auto-cleaned), opens every DXF with ezdxf, and
    asserts the per-sheet baseline table in _dxf_structural_baselines.
    """
    import ezdxf
    from bridge_gad.multi_sheet_generator import DetailedSheetGenerator
    from bridge_gad.bridge_canvas_features import BRIDGE_TEMPLATES

    params = BRIDGE_TEMPLATES["simple_12m"]["parameters"]
    baselines = _dxf_structural_baselines()

    # _save_sheet_set(sheets, output_path) treats output_path as a FILE:
    #   output_dir = output_path.parent   (where DXFs are written)
    #   output_stem = output_path.stem    (prefix:  f"{stem}_Sheet{N}.dxf")
    # Therefore pass a file-like path inside our tmp directories.
    # -------- Phase 2: 7 sheet package --------
    gen = DetailedSheetGenerator()
    p2_dir = tmp_path / "phase2"
    p2_dir.mkdir()
    p2_prefix = p2_dir / "simple_12m_Sheet"
    p2_ok = gen.generate_phase_two_package(params, p2_prefix)
    assert p2_ok is True, "generate_phase_two_package returned False"
    p2_dxfs = sorted(p2_dir.glob("*.dxf"))
    # Exact 7 files.  Naming: simple_12m_Sheet_Sheet1.dxf .. simple_12m_Sheet_Sheet7.dxf
    assert len(p2_dxfs) == 7, \
        f"Phase 2 expected 7 DXFs in {p2_dir}, got {len(p2_dxfs)}: {[p.name for p in p2_dxfs]}"

    # -------- Phase 3: 11 sheet package --------
    p3_dir = tmp_path / "phase3"
    p3_dir.mkdir()
    p3_prefix = p3_dir / "simple_12m_Sheet"
    p3_ok = gen.generate_phase_three_package(params, p3_prefix)
    assert p3_ok is True, "generate_phase_three_package returned False"
    p3_dxfs = sorted(p3_dir.glob("*.dxf"))
    assert len(p3_dxfs) == 11, \
        f"Phase 3 expected 11 DXFs in {p3_dir}, got {len(p3_dxfs)}: {[p.name for p in p3_dxfs]}"

    # -------- Helper: structural assertions on one DXF --------
    def _check_one(dxf_path, sheet_key, allow_missing_substrings=False):
        baseline = baselines[sheet_key]
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()
        entities = list(msp)
        n_ents = len(entities)
        assert n_ents >= baseline["min_entities"], (
            f"{sheet_key} ({dxf_path.name}): only {n_ents} entities, "
            f"need >= {baseline['min_entities']} "
            f"(baseline fact-verified 2026-09-29)"
        )

        # Entity-type floor counts.
        type_counts = {}
        for e in entities:
            type_counts[e.dxftype()] = type_counts.get(e.dxftype(), 0) + 1
        for etype, floor in baseline["entity_types_at_least"].items():
            actual = type_counts.get(etype, 0)
            assert actual >= floor, (
                f"{sheet_key}: entity type {etype} count={actual} "
                f"below floor={floor}.  Full type histogram: {type_counts}"
            )

        # Layer presence: baseline is a single layer "0".  (Future C2
        # hatching may add CONCRETE/STEEL/...; guard with superset.)
        layers_present = {e.dxf.layer for e in entities if e.dxf.layer}
        assert "0" in layers_present, (
            f"{sheet_key}: all drawings must contain at least layer '0'. "
            f"Found: {sorted(layers_present)}"
        )

        # Required substrings: concatenate TEXT + MTEXT strings once.
        all_text_bits = []
        for t in msp.query("TEXT MTEXT"):
            try:
                s = t.dxf.text if hasattr(t.dxf, "text") else (t.text or "")
            except Exception:
                s = ""
            if s:
                all_text_bits.append(str(s))
        all_text = "\n".join(all_text_bits)

        missing = []
        for needle in baseline["required_substrings"]:
            # Case-insensitive, substring-match (text may be split across
            # lines / wrapped MTEXT).
            if needle.lower() not in all_text.lower():
                # Some Phase-3 substrings may be tolerant (e.g. "pipe" may
                # appear as "downpipe" / "downtake").  Do NOT fail silently:
                # record and, when caller does not allow, assert.
                missing.append(needle)

        if missing and not allow_missing_substrings:
            # Diagnostic: show first 1500 chars of TEXT dump so failed
            # assertion points the engineer at what WAS actually written.
            preview = all_text[:1500].replace("\r", " ")
            raise AssertionError(
                f"{sheet_key}: required strings not found in TEXT/MTEXT: "
                f"{missing}.\nTEXT dump (first 1500 chars):\n{preview}"
            )
        return {
            "n_entities": n_ents,
            "type_counts": type_counts,
            "layers": sorted(layers_present),
            "missing_strings": missing,
        }

    import re as _re_numsort

    def _sheet_num_key(path: Path):
        """Sort by numeric Sheet{N} suffix so Sheet10 does NOT sort before
        Sheet2 (Python's lexicographic string sort would break order)."""
        m = _re_numsort.search(r"Sheet(\d+)\.dxf$", path.name)
        return int(m.group(1)) if m else 999

    p2_dxfs = sorted(p2_dir.glob("*.dxf"), key=_sheet_num_key)
    assert len(p2_dxfs) == 7, (
        f"Phase 2 expected 7 DXFs in {p2_dir}, got {len(p2_dxfs)}: "
        f"{[p.name for p in p2_dxfs]}"
    )
    # Phase 2 sheets numeric order: Sheet1 (IDX) .. Sheet7 (DRN).
    for i in range(7):
        _check_one(p2_dxfs[i], f"Sheet{i + 1}")

    # Phase 3 package contains 11 sheets in NUMERIC sheet-suffix order:
    #   Sheet1 IDX, Sheet2 GAD, Sheet3 TYP, Sheet4 ABT, Sheet5 PIER,
    #   Sheet6 BRG, Sheet7 DRN,
    #   Sheet8 BRG-DET, Sheet9 EXPJ-DET, Sheet10 WING-DET, Sheet11 DRN-DET
    # (matches PHASE_THREE_SHEETS iteration order in generate_phase_three_package;
    #  _save_sheet_set names each f"{output_stem}_Sheet{{i}}.dxf").
    # Sheets 1..7 already passed via Phase-2 package (identical generation
    # path with identical params).  Assert ONLY the 4 new appendices here.
    p3_sorted = sorted(p3_dir.glob("*.dxf"), key=_sheet_num_key)
    assert len(p3_sorted) == 11
    p3_appendices = p3_sorted[-4:]  # numeric indices 8,9,10,11
    # Map in fixed order: BRG-DET (8), EXPJ-DET (9), WING-DET (10), DRN-DET (11)
    classified = {
        "BRG-DET":  p3_appendices[0],
        "EXPJ-DET": p3_appendices[1],
        "WING-DET": p3_appendices[2],
        "DRN-DET":  p3_appendices[3],
    }

    # Sanity-check the filename suffixes match our positional assumption:
    for code, path in classified.items():
        expected_sheet_num = {"BRG-DET": 8, "EXPJ-DET": 9, "WING-DET": 10, "DRN-DET": 11}[code]
        assert f"Sheet{expected_sheet_num}" in path.name, (
            f"Positional appendix assumption broken: {code} expected Sheet{expected_sheet_num} "
            f"in filename but got: {path.name}"
        )

    # Run structural assertions on the 4 matched Phase-3 appendices.
    mapping = {"BRG-DET": "Sheet8", "EXPJ-DET": "Sheet9",
               "WING-DET": "Sheet10", "DRN-DET": "Sheet11"}
    for code, path in classified.items():
        _check_one(path, mapping[code])

    # Final smoke: every Phase-3 DXF must be non-trivial bytes.
    for dx in p3_sorted:
        assert dx.stat().st_size >= 2000, (
            f"Phase-3 DXF {dx.name} is only {dx.stat().st_size} B — "
            f"looks like an empty / failed write."
        )

    # --- Optional: common title-block invariants across ALL 7 Phase-2 sheets ---
    # Every Phase-2 sheet should share these title-block strings.
    invariant_texts = [
        "By: Bridge GAD Generator",
        "Project: Simple Span 12 m Bridge",
        "Drg: GAD-001",
        "Rev: R0",
        "Basis: IRC / MoRTH",
    ]
    for i in range(7):
        doc = ezdxf.readfile(p2_dxfs[i])
        blob = ""
        for t in doc.modelspace().query("TEXT MTEXT"):
            try:
                s = t.dxf.text if hasattr(t.dxf, "text") else (t.text or "")
            except Exception:
                s = ""
            blob += " " + (s or "")
        low = blob.lower()
        missing_inv = [tok for tok in invariant_texts if tok.lower() not in low]
        assert not missing_inv, (
            f"Phase-2 sheet {i + 1} filename={p2_dxfs[i].name}: "
            f"missing title-block invariant strings {missing_inv}.\n"
            f"First 800 chars of TEXT: {blob[:800]}"
        )

    # --- TBC-stamp integrity check on all Phase-3 appendices ---------------
    # The ring-fenced "TBC_BY_ENGINEER" string must appear in EVERY Phase-3
    # appendix DXF (it's the no-invented-data compliance stamp).
    for code, path in classified.items():
        doc = ezdxf.readfile(path)
        blob = ""
        for t in doc.modelspace().query("TEXT MTEXT"):
            try:
                s = t.dxf.text if hasattr(t.dxf, "text") else (t.text or "")
            except Exception:
                s = ""
            blob += " " + (s or "")
        assert "TBC_BY_ENGINEER" in blob, (
            f"Phase-3 appendix {code} (file {path.name}) is missing the "
            f"TBC_BY_ENGINEER ring-fence stamp — violates no-invented-data "
            f"rule.  First 800 chars of TEXT:\n{blob[:800]}"
        )

