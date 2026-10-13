# M2 — BridgeCAD IO Layer — Implementation Plan

## Task 1: Exception hierarchy + package public surface (bridgecad_io/__init__.py + exceptions.py)
- **Status**: `pending`
- **Priority**: high
- **Depends On**: None (foundational)
- **Description**:
  - Create `bridgecad_io/exceptions.py` defining:
    ```
    BridgeCADError(Exception)                           # root marker (keep same package so imports work)
      └── IOError(BridgeCADError)
            ├── ExcelParseError(IOError)
            ├── JsonParseError(IOError)
            └── CsvParseError(IOError)
    ```
    Each subclass takes `(message, *, file=None, sheet=None, field=None, line=None, suggestion=None)` and formats `__str__` with all context fields aligned to AC-6's "actionable hint" pattern.
  - Update `bridgecad_io/__init__.py` to:
    - Lazy import core inside each public function.
    - Re-export `read_excel`, `write_excel`, `generate_template`, `to_json`, `from_json`, `to_csv`, `from_csv` proxies plus the `exceptions` module reference.
    - Declare `__version__ = "0.2.0-m2"` (bump from `0.1.0-rc1`).
- **Acceptance Criteria Addressed**: AC-6 (part: introduces the classes), AC-7 (8-name surface, lazy import requirement for (b))
- **Test Requirements**:
  - `rule` TR-1.1: `import bridgecad_io` succeeds with `bridgecad_core` removed from sys.path; 8 names present.
  - `rule` TR-1.2: `ExcelParseError(msg, file="a.xlsx", sheet="PROJECT_MASTER", field="road_level_rl_m", suggestion="numeric RL in metres")` includes all 4 context items in its string representation.

## Task 2: Excel Reader — harden 4 weak areas (aliases, BearingsJoints schedule, coerce Decimal precision, structured errors)
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 1
- **Description**:
  1. Add `"parameters": "S03"` / `"sheet1": "S01"` fallback aliases to `_SHEET_ALIASES` so legacy 1-sheet V1 layout `Parameters` or `Sheet1` tiles don't raise `ValueError: No recognised BridgeCAD sheets found`; log a `WARNING: legacy single-sheet layout detected — field mapping may be partial` instead.
  2. Fix `_parse_bearings_joints` S10 sentinel blocks: the existing regex search for `bearing_schedule:` / `expansion_joint_schedule:` rows → next-row header → iterate table rows until blank; convert each row to `BearingScheduleRow` / `ExpansionJointScheduleRow` using field-name match against header columns (case-insensitive, aliases like `"bearing type"` → `"type"`).
  3. `_coerce(value, Decimal)` — keep 3 decimal places for metre RL fields, 2 for currency — done by preserving original string precision from Excel via `Decimal(str(v))` (already present), but add a `quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)` fallback for float cells to prevent 12.0 → 11.999999999999 drift.
  4. Every `_parse_*` helper wraps its body in `try: ... except Exception as exc: raise ExcelParseError(..., sheet=Sx, suggestion=...) from exc`.
- **Acceptance Criteria Addressed**: AC-1 (decimal precision enum parse affects 95 % field match), AC-6 (structured parse errors), FR-1
- **Test Requirements**:
  - `rule` TR-2.1: `read_excel(generate_template(SIMPLE_12M_14sheet))` returns a `BridgeProject` with `len(model_dump(exclude_none=True)) ≥ 300` fields populated.
  - `rule` TR-2.2: Reading a workbook containing a single sheet `Parameters` raises no ValueError (emits WARNING only) and returns a BridgeProject with at least ProjectMaster + GeometryInput populated from matching column headers.
  - `rule` TR-2.3: BearingsJoints S10 sheet populated with 2 `BearingScheduleRow` items → they appear in `bp.bearings_joints.bearing_schedule[0/1]` with correct c/c spacing & type.
  - `rule` TR-2.4: A deliberately corrupt `road_level_rl_m = "not_a_number"` cell raises `ExcelParseError` having `.field == "road_level_rl_m"` and `.suggestion != None`.

## Task 3: Excel Writer — implement excel_writer.py (equivalent to prefilled template, 14 sheets, cell-value parity)
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 1 (uses ExcelParseError for errors)
- **Description**:
  - File `bridgecad_io/excel_writer.py` exports `write_excel(project: BridgeProject, output_path) -> Path`.
  - Implementation: call `excel_template.generate_template(output_path, project=project)` but with `_fast_mode=True` (add a private kwarg to generate_template that skips dropdowns/conditional-formatting; keeps sheet-name, row order, cell-value = prefilled project data).
  - Explicitly guarantee cell-value parity with `generate_template(path, project=project)` by sharing the same S01..S14 field-lists from a single `_FIELD_LAYOUT = {...S04: [(fname, unit, desc), ...]}` dict extracted out of excel_template.py into an internal `_layouts.py` module so both readers and writers never drift.
  - Final row: add `SUMMARY` sheet at the end listing `Sheet | Field Count | Last Updated | Project Code` if a project is present; not required for AC-3 diff because it's excluded when comparing sheets S01..S14.
- **Acceptance Criteria Addressed**: AC-3 (cell-value parity), FR-3
- **Test Requirements**:
  - `rule` TR-3.1: For S01..S14, every sheet `(row,col)` cell value in `generate_template(prefilled)` == `write_excel()`; compare via `for ws_name in ws_names[:14]: for row in ws.iter_rows(values_only=True): for cell in row: assert a_cell == b_cell or (a_cell is None and b_cell is None)`.
  - `rule` TR-3.2: Writing a BridgeProject where `bearings_joints.bearing_schedule = [row1,row2]` → `S10 BEARINGS_JOINTS` sheet has the 2 rows after the `bearing_schedule:` sentinel.

## Task 4: JSON Adapter — implement json_adapter.py (Decimal→str, Enum→value, idempotent)
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 1 (uses JsonParseError)
- **Description**:
  - File `bridgecad_io/json_adapter.py`:
    - `to_json(project, path=None, indent=2, exclude: set[str] | None = None) -> str` — calls `project.model_dump_json(indent=indent, round_trip=True, exclude=EXCLUDE_ALWAYS | (exclude or set()))`.
    - `from_json(s: str | Path) -> BridgeProject` — reads string/Path contents, calls `BridgeProject.model_validate_json(s)`.
    - Define `EXCLUDE_ALWAYS = {"project_master": {"creation_date", "last_modified_date"}, "validation": {"report_signature", "validation_run_date"}}` as the auto-fields excluded for AC-1 diff (so 20-field allowance is only for semantic drift, not metadata).
  - Wrap `ValidationError` → `JsonParseError` with `.field = e["loc"][-1]` extracted from the first error item.
- **Acceptance Criteria Addressed**: AC-1 (provides the diff mechanism), AC-4 (Decimal/enum/3-way stability), FR-4
- **Test Requirements**:
  - `rule` TR-4.1: JSON text for SIMPLE_12M contains the substring `"12.000"` (span length Decimal-with-string) AND substring `"RCC_TBEAM"` (enum value, not class repr).
  - `rule` TR-4.2: `to_json(from_json(to_json(fixture))) == to_json(fixture)` (text-identical, 3-way idempotence; compare SHA-256 of text).

## Task 5: CSV Adapter — implement csv_adapter.py (16 files, from_csv/to_csv round-trip)
- **Status**: `pending`
- **Priority**: medium
- **Depends On**: Task 4 (uses same EXCLUDE_ALWAYS list)
- **Description**:
  - File `bridgecad_io/csv_adapter.py`:
    - `to_csv(project, out_dir: Path) -> list[Path]`: one file per key in `_MODEL_KEYS` (14 sub-models) + 2 schedule CSVs:
      - `S10_bearing_schedule.csv` (from `bearings_joints.bearing_schedule[]`)
      - `S10_expansion_joint_schedule.csv` (from `bearings_joints.expansion_joint_schedule[]`)
    - For each sub-model dict, flatten field→value; field order == `sub_model.model_fields.keys()` exactly so column order is stable.
    - `from_csv(in_dir: Path) -> BridgeProject`: loads each CSV → dict → construct sub-model from dict → feed into BridgeProject kwargs.
    - Wrap `csv.Error` / `KeyError` → `CsvParseError` with `.file`, `.line` from CSV reader line number.
- **Acceptance Criteria Addressed**: AC-5, FR-5
- **Test Requirements**:
  - `rule` TR-5.1: `len(to_csv(fixture, tmp)) == 16` — 14 sub-models + 2 schedule.
  - `rule` TR-5.2: `from_csv(to_csv(fixture, tmp))` round-trips to a JSON-identical project (exclude EXCLUDE_ALWAYS set).

## Task 6: Upgrade excel_template.py (4 styling tiers; 120+ enum dropdowns; numeric validation)
- **Status**: `pending`
- **Priority**: medium
- **Depends On**: Task 2 (shared layouts module)
- **Description**:
  - Pull 14-sheet field-list arrays out of excel_template.py's body and into shared `bridgecad_io/_layouts.py` (reused by excel_reader.py TR field mapping).
  - In `_build_generic_sheet(ws, sheet_code, rows, types_mod)`:
    - Detect enum fields heuristically: any row whose "default value" is a string matching an enum `.value` or if the matching BridgeProject sub-model field's annotation is an Enum subclass → attach a DataValidation dropdown list of all `.value` members.
    - Dimensional rows: `field_name` in `_MM_FIELDS` or `"_mm"` / `"_m"` suffix or unit in `("mm","m","cm","°","kN/m³","kPa")` → add numeric data-validation `between(min,max)` if the core ValidationModel defines min/max bounds (e.g. `deck_thickness_mm 50..600`).
  - Add a `COVER` sheet (sheet index 0) with project_title + logo placeholder + "BridgeCAD Enterprise" banner when `project is not None`.
  - Keep generating 22–30 KB `.xlsx` output; not larger than 60 KB.
- **Acceptance Criteria Addressed**: AC-2 (rubric — enum dropdown count ≥ 120, 4 styling tiers, numeric validation active), FR-2
- **Test Requirements**:
  - `rubric` TR-6.1: AC-2 rubric score directly mapped (≥ 2 to pass); evidence = workbook openpyxl sheet count + DataValidation count + count of validations with formula1 containing ≥ 8 comma-separated values (heuristic for enum dropdowns).
  - `rule` TR-6.2: 14 sheet-names present (sheetnames list has ≥ 14 unique non-COVER entries)
  - `rule` TR-6.3: `COVER` sheet cell (1,1) contains project_title string when template generated with project.

## Task 7: Build m2_verify.py acceptance suite (AC-1..AC-8 runs + 28-fixture batch timing)
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Tasks 1–6 (runs the full implementation)
- **Description**:
  - File `packages/bridgecad-io/m2_verify.py`.
  - Pattern follows `m1w2_verify.py` + `day5_verify.py`.
  - Imports/uses:
    - SIMPLE_12M from `smoke_test_m3.py` (copy payload or import sys.path add bridgecad-draw).
    - Four additional typed fixtures built from dict-literal variants of SIMPLE_12M (continuous_3x12m, box_culvert_8m, girder_4x18m, arch_24m).
  - Run ACs in order AC-1..AC-8; tally rule passes (need 5/5 rules: AC-1,3,4,5,7 = 5 rules all pass); rubric AC-2 ≥ 2, AC-6 ≥ 2, AC-8 ≥ 2.
  - Output `★ M2 IO ACCEPTED ★` and exit 0 iff all rule ACs PASS AND all rubric ACs meet threshold.
- **Acceptance Criteria Addressed**: AC-1 through AC-8 aggregator / runner
- **Test Requirements**:
  - `rule` TR-7.1: Exit 0 when all pass; exit 1 if any rule AC fails.
  - `rubric` TR-7.2: The console output has 8 explicit lines `✅ PASS AC-1 … AC-8` or for rubrics `[2/3] AC-2` with explicit scale denominator.

## Task 8: Backwards-compat + path-resolution audit (NFR-1 + NFR-3)
- **Status**: `pending`
- **Priority**: low
- **Depends On**: Tasks 1, 2
- **Description**:
  - Run existing `bridgecad-io/tests/__init__.py` (create a basic empty conftest import smoke if none).
  - Confirm no import of pandas/numpy occurs inside `read_excel/write_excel/to_json/from_json` hot paths via a runtime sys.modules check (monkey-patch pandas import to raise Exception).
  - NFR-1: alias-map `_SHEET_ALIASES` supports both `"s01 project_master"` (old) and `"01 — PROJECT MASTER"` (space-separated display title) variants.
- **Acceptance Criteria Addressed**: NFR-1, NFR-3. Indirect evidence for AC-1.
- **Test Requirements**:
  - `rule` TR-8.1: Alias `"01 — PROJECT MASTER"` → resolves to S01 via lookup; alias `"SHEET1"` → resolves to S01 with WARNING logged.
  - `rule` TR-8.2: `pandas` not in `sys.modules` after `from bridgecad_io import read_excel, to_json`.
