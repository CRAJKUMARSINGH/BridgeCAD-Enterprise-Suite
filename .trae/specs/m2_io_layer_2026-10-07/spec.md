# M2 — BridgeCAD IO Layer — Product Requirements Document

## Overview
- **Summary**: BridgeCAD Enterprise IO package (`bridgecad-io`) delivers a lossless, round-trippable, bidirectional adapter layer between Excel / CSV / JSON files and the M1 core-domain Pydantic model `BridgeProject` (14 sub-models, 439 fields). M2 is the "bridge" between human-authored workbooks (PWD engineer input, 28 fixture templates in `public/samples/`) and the downstream M3 drawing engine + M5 bill engine.
- **Purpose**:
  - Remove Excel-specific parsing from M3 drawing code (previously inlined in `src/bridge_gad/bridge_generator.py:2100`).
  - Guarantee byte-identical workbook structure for `read → modify → write` so engineer-authored templates can be re-opened without layout drift.
  - Provide JSON `to_json`/`from_json` for REST API transport and CSV exports for bulk audit / import by bridge-maintenance ERP systems.
- **Target Users**:
  1. **PWD Field Engineers** — fill in `template_simple_12m.xlsx` (or variants) and run CLI → generate 8-sheet DXF booklet.
  2. **API Gateway (M7 FastAPI)** — accept `.json` bridge-project payloads via `/v1/projects` endpoints.
  3. **Bridge Inventory ERP** — consume CSV exports of M5 bill-of-quantities summaries, or import 200+ bridge CSV rosters in batch.

## Goals
1. Round-trip lossless: `read_excel → BridgeProject → write_excel` preserves ≥ 95 % of 439 field values across 28 templates (no coercion drift).
2. Templates ship with correct 14-sheet sheet-names so `read_excel()` matches `_SHEET_ALIASES` out-of-the-box.
3. Top-level package `bridgecad_io.__init__.py` exposes a clean public surface (no `from bridgecad_io.excel_reader import read_excel` required for CLI callers).
4. All adapters handle bad input with structured, user-friendly error messages — never `AttributeError` / `KeyError` / uncaught `pydantic.ValidationError` in normal usage.
5. JSON schema is stable (field order preserved, Decimal serialised as string to avoid float drift, Enum values serialised to their `.value`).

## Non-Goals
1. **Not** a custom Excel formula engine — formulas in input workbooks are read via `data_only=True`; if a workbook has never been opened in Excel, computed cells can be `None`, and we inject documented fallbacks (M1 defaults).
2. **Not** a generic Pandas DataFrame IO — Pandas is listed in pyproject.toml only for optional CSV column-type inference; primary adapters use `openpyxl`/stdlib `csv`/`json`.
3. **Not** the legacy single-sheet `Parameters` layout parser (the 4 failing `public/samples/*.xlsx` files are legacy V1 layouts; M2 supports 14-sheet V2 layout only; a single legacy-adapter shim is stretch goal, not in ACs).
4. **Not** Excel macro (.xlsm) or .xls (pre-2007) binary support.
5. **Not** encryption / password-protected workbooks.

## Background & Context
- M1 Week-1 Sign-off delivered 184 Enum types, 439-field `BridgeProject` Pydantic aggregate (14 sub-models: ProjectMaster, BridgeSelection, GeometryInput, Superstructure, Substructure, FoundationDetails, Approaches, HydraulicData, Materials, BearingsJoints, ComponentsLib, DrawingControl, Calculations, Validation).
- M2 IO package scaffold was created in M0 with 5 file stubs: `excel_reader.py`, `excel_template.py`, `excel_writer.py`, `json_adapter.py`, `csv_adapter.py`. Of these:
  - `excel_reader.py` (690 lines) — 90 % complete: `_SHEET_ALIASES`, 14 `_parse_*` helpers, `read_excel()` public API. Open problem: BearingsJoints schedules and legacy single-sheet files are not tested.
  - `excel_template.py` (480 lines) — 90 % complete: `generate_template(output_path, project=None)` creates 14 sheets with styled rows, dropdowns, data validation. Verified blank-template round-trip produces 22 KB workbook with 14 matching sheet-titles.
  - `excel_writer.py` — 1 line stub (docstring only); missing.
  - `json_adapter.py` — 1 line stub (docstring only); missing.
  - `csv_adapter.py` — 1 line stub (docstring only); missing.
- 28 E2E fixtures exist at `public/samples/`:
  - 4 typed templates: `template_simple_12m`, `template_continuous_3x12m`, `template_box_culvert_8m`, `template_girder_4x18m`, `template_arch_24m` (all 1-sheet legacy `Parameters` layout today).
  - 2 project inputs: `bridge_simple_12m.xlsx`, `bridge_comprehensive.xlsx`, `bridge_large.xlsx`, `bridge_23span.xlsx`, `sample_input.xlsx` (sheet titles are `"Sheet1"` / `"Sheet2"`).
- Per the **Plan Adjustment (Honest Review 2026-10-07)**, M2 and M3 are being executed in parallel order; M3 re-uses `bridge_generator.py:2100` as its base (already kicked off in prior session as M1W2). M2 must deliver stable `BridgeProject` loaders so that the M3 refactor does not regress on input handling.

## Functional Requirements
- **FR-1 (Excel Reader)**: `bridgecad_io.read_excel(path) -> BridgeProject` accepts a 14-sheet canonical layout workbook, parses every sheet via the 3-col Field/Value/Notes pattern, coerces Decimals / Enums / Bools / dates, falls back to documented M1 defaults when cells are blank (empty → not 0), parses S10 BearingsJoints tabular `bearing_schedule:` / `expansion_joint_schedule:` sentinel blocks into list models.
- **FR-2 (Excel Template)**: `bridgecad_io.generate_template(path, project=None) -> Path` writes a 14-sheet workbook with: navy section headers; light-yellow input cells (unlocked); grey calc cells (locked/italic); Enum dropdowns via `openpyxl DataValidation` on every enum field; dimensional numeric validation on fields tagged `mm` / `m`; matching column widths; and a COVER / SUMMARY page if `project is not None`.
- **FR-3 (Excel Writer — non-template)**: `bridgecad_io.write_excel(project, path) -> Path` is functionally equivalent to `generate_template(path, project=project)` but with template styling skipped for speed; guarantees sheet-name + column parity with template so any template `read_excel` output can `write_excel` and re-`read_excel` byte-identically for fields.
- **FR-4 (JSON Adapter)**: `bridgecad_io.to_json(project, path=None, indent=2) -> str` and `bridgecad_io.from_json(s | path) -> BridgeProject` preserve: `Decimal` → JSON string (no float drift), `Enum` → `.value`, `date` → ISO 8601, empty fields excluded.
- **FR-5 (CSV Adapter)**: `bridgecad_io.to_csv(project, out_dir) -> list[Path]` writes one `.csv` per sub-model (14 files + 2 schedule files for bearing / expansion joint rows); fields are in same order as Pydantic definition; `bridgecad_io.from_csv(in_dir) -> BridgeProject` reads them back.
- **FR-6 (Structured errors)**: A public exception hierarchy `BridgeCADError -> IOError -> {ExcelParseError, JSONParseError, CSVParseError}` wraps every underlying exception (openpyxl, json, pydantic) with: 1) failed file, 2) sheet / column name, 3) human-readable suggestion, 4) optional `line: int` / `field: str`; raised instead of raw Python errors for all documented public functions.
- **FR-7 (Package surface)**: `bridgecad_io.__init__.py` re-exports `read_excel`, `write_excel`, `generate_template`, `to_json`, `from_json`, `to_csv`, `from_csv`, `exceptions` namespace.

## Non-Functional Requirements
- **NFR-1 (Backward compat.)**: `read_excel()` still accepts missing sheets (uses empty defaults) + tolerates `ws.title` with whitespace / case variants.
- **NFR-2 (Performance)**:
  - 439-field round-trip (read → model → write → read → diff) completes in ≤ 0.5 s on a 1.5 GHz 2-core laptop.
  - 28-fixture batch run (CSV output + JSON output) finishes in ≤ 10 s total.
- **NFR-3 (Zero new heavy deps)**: Depends on `openpyxl>=3.1` (already listed in `pyproject.toml`). Uses stdlib `csv` + `json` + `decimal`; never imports numpy/pandas in hot paths of `read_excel/write_excel/to_json/from_json`.
- **NFR-4 (Logging)**: Structured logger `bridgecad_io` at level WARNING by default; INFO-level messages contain (sheet_name, n_rows_parsed, fallback_count); DEBUG-level logs each coerced field.
- **NFR-5 (Test harness)**: `m2_verify.py` at package-root same pattern as M1's `day5_verify.py` / M1W2's `m1w2_verify.py`.

## Constraints
- **Technical**:
  - Python ≥ 3.11 (per `bridgecad-io/pyproject.toml:9`).
  - Must not import `bridgecad_core` at package top-level; use lazy-import pattern already present in `excel_reader.py:_core()` so `import bridgecad_io` does not fail in environments where core is not installed (important for `m0_scaffold_packages.py` smoke scripts).
  - Sheet-name 1:1 mapping to `_SHEET_ALIASES` — V1 single-sheet `Parameters` layout out of scope, but alias table must include `"parameters": "S03" | None` fallback path for future legacy shim.
- **Business**:
  - Output templates are shared with PWD engineers; no proprietary fonts; Arial 11 default only.
- **Dependencies**:
  - Upstream: `bridgecad-core @ file://../bridgecad-core` (peer-dependency; we just finished M1 week-1 sign-off; 184 enums + 439 fields are stable).
  - Test fixtures: `public/samples/*.xlsx` — they are V1 layout so won't parse, but we use `generate_template(SIMPLE_12M)` + `generate_template(CONTINUOUS_3X12M)` + `generate_template(CULVERT_8M)` + `generate_template(GIRDER_4X18M)` + `generate_template(ARCH_24M)` as M2 fixtures.

## Assumptions
1. `BridgeProject(**kwargs)` default injection for empty required fields is acceptable (the excel_reader stub already injects `project_title = "BRIDGE PROJECT"` fallback).
2. Users opening templates in LibreOffice Calc will lose advanced Excel data-validation styling — acceptable because dropdowns still render as literal cell value, round-trip remains correct.
3. 439-field round-trip "≥ 95 % match" tolerates 20 fields intentionally excluded: `project_master.creation_date` (auto-set each call), `validation.report_signature` (auto-hash) etc.
4. The 28 E2E fixtures in `scripts/generate_all_28_fixtures.py` include 5 primary bridge-type models (Simple/Continuous/Girder/Culvert/Arch); we copy those fixture payloads into a `_fixtures.py` under `bridgecad_io/tests` or pull from bridgecad-core `tests/fixtures_projects.py` if it has them.

## Acceptance Criteria

### AC-1: Excel Reader round-trip — 439 field ≥ 95 % match
- **Type**: `rule`
- **Given**: The four generate_template-produced "typed fixture" workbooks (simple_12m, continuous_3x12m, box_culvert_8m, girder_4x18m) exist on disk.
- **When**: `bp_orig = FixtureProject; generate_template(xlsx, bp_orig); bp_rt = read_excel(xlsx); compare_by_json_sha256(to_json(bp_orig, exclude_auto_fields), to_json(bp_rt, exclude_auto_fields))`.
- **Then**: Number of differing fields ≤ 20 / 439 = 95.4 % match.
- **Pass Condition**: All 4 fixtures differ in ≤ 20 fields (no mismatched enums / decimals beyond round-off).
- **Evidence**: `m2_verify.py` section AC-1 output with explicit diff list for any diverging field.

### AC-2: Excel Template — 14 sheets named correctly + enum dropdown coverage ≥ 120 Enum fields
- **Type**: `rubric`
- **Dimension**: Template correctness / usefulness to a PWD engineer.
- **Scale**: 1–3
- **Anchors**:
  - 1 = ≤ 10 sheets present, no data validation, unstyled.
  - 2 = 14 sheets named, ≥ 40 enum dropdowns, 2 styling tiers (header + input).
  - 3 = 14 sheets, ≥ 120 distinct enum dropdowns, 4 styling tiers (header/sub/input/calc), numeric validation active.
- **Pass Threshold**: ≥ 2
- **Evidence**: `m2_verify.py` openpyxl workbook introspection: sheetnames set, count of `DataValidation` objects with formula1 length ≥ 8 enum-choices.

### AC-3: Excel Writer equivalence to Template(prefilled)
- **Type**: `rule`
- **Given**: A `SIMPLE_12M` BridgeProject fixture.
- **When**: We write two files: `p1=generate_template(path1, project=fixture)` and `p2=write_excel(fixture, path2)`.
- **Then**: For every sheet, for every cell `(row,col)` that belongs to a 3-column layout row, the typed value (not formatting) of `p1` equals `p2`; sheetname order matches.
- **Pass Condition**: 100 % cell-value match across sheets S01..S14.
- **Evidence**: `m2_verify.py` section AC-3: `sheets_x14_equal=True n_cells_equal=X n_cells_total=Y`.

### AC-4: JSON Adapter — stable schema, Decimal-as-string preserved, Enum-as-value
- **Type**: `rule`
- **Given**: SIMPLE_12M fixture with a field containing `Decimal("12.000")` and enum `PierType.WALL`.
- **When**: `json_str = to_json(fixture); parsed_back = from_json(json_str)`
- **Then**:
  (a) `"12.000"` is present in JSON string (not `12.0` / `12` float);
  (b) Enum value in JSON equals `PierType.WALL.value` (string not class-name);
  (c) `to_json(from_json(to_json(fixture))) == to_json(fixture)` (idempotent 3-way).
- **Pass Condition**: (a) ∧ (b) ∧ (c).
- **Evidence**: `m2_verify.py` AC-4 console pass + 3-way JSON text diff sha256 match.

### AC-5: CSV Adapter — 14 + 2 = 16 files, from_csv(to_csv(project)) matches
- **Type**: `rule`
- **Given**: SIMPLE_12M fixture.
- **When**: `paths = to_csv(fixture, tmpdir); bp_rt = from_csv(tmpdir)`.
- **Then**:
  (a) `len(paths) == 16` (14 sub-models + `bearing_schedule.csv` + `expansion_joint_schedule.csv`);
  (b) `to_json(bp_rt, exclude_auto_fields) == to_json(fixture, exclude_auto_fields)`.
- **Pass Condition**: (a) ∧ (b).
- **Evidence**: `m2_verify.py` AC-5.

### AC-6: Structured errors on invalid inputs — no raw leaks, public exception classes
- **Type**: `rubric`
- **Dimension**: Exception UX quality.
- **Scale**: 1–3
- **Anchors**:
  - 1 = 0 scenarios covered; raw `ValidationError` / `KeyError` propagate to caller.
  - 2 = 2/3 scenarios (bad workbook, bad JSON, bad CSV) → custom error types, still no actionable hints.
  - 3 = 3/3 scenarios covered, each error includes (file, sheet/field, suggestion), e.g. `"File bad.xlsx sheet PROJECT_MASTER missing project_code (hint: add cell B4 with unique code)"`.
- **Pass Threshold**: ≥ 2
- **Evidence**: `m2_verify.py` scenario table (3 rows × 2 cols: exc_type_str, hint_keyword_present).

### AC-7: Package public surface — 8 names + lazy import
- **Type**: `rule`
- **Given**: A fresh Python interpreter with `bridgecad_core` REMOVED from `sys.path`.
- **When**: `import bridgecad_io as io; names = {"read_excel","write_excel","generate_template","to_json","from_json","to_csv","from_csv","exceptions"}`.
- **Then**:
  (a) `names ⊆ set(dir(io))`;
  (b) `import bridgecad_io` with `bridgecad_core` uninstalled does not raise ImportError.
- **Pass Condition**: (a) ∧ (b).
- **Evidence**: `m2_verify.py` section AC-7 runs a subprocess `python -c "import bridgecad_io; ..."` with `PYTHONPATH` excluding bridgecad-core.

### AC-8: Performance — round-trip ≤ 0.5 s / project, 28-fixture batch ≤ 10 s
- **Type**: `rubric`
- **Dimension**: Speed of hot paths.
- **Scale**: 1–3
- **Anchors**:
  - 1 = RT ≥ 1.0 s per project; slow — blocks batch mode.
  - 2 = RT ≤ 0.5 s per project; batch 28 fixtures in ≤ 20 s.
  - 3 = RT ≤ 0.3 s per project; batch 28 fixtures ≤ 10 s.
- **Pass Threshold**: ≥ 2
- **Evidence**: `m2_verify.py` perf section — wall-clock via `time.perf_counter`.

## Open Questions
- [ ] **(legacy compat)** Do we need M2 to read the 4 legacy single-sheet `Parameters` workbooks today, or is 14-sheet V2 layout sufficient? (Plan-Assessment note 5 says we should later "bridge legacy → Suite" but leaves timing open; I've scoped it as Non-Goal 3 with `_SHEET_ALIASES` reserved for a future shim — needs your Y/N.)
- [ ] **(28-fixture payloads)** Does `bridgecad_core/tests/fixtures_projects.py` hold the 5 bridge-type payloads, or should we re-use `smoke_test_m3.py:SIMPLE_12M` + define CONTINUOUS/CULVERT/GIRDER/ARCH as dict-literal companions in `bridgecad_io/_fixtures.py`?
- [ ] **(Excel "styles" parity)** Do we care if `write_excel` skips styling tiers (FR-3) in the name of speed? NFR-2 says yes, but if the downstream use case is GUI round-trips, users want styling; I'll keep the 4-tier styling ON for both template and writer unless you say otherwise.
