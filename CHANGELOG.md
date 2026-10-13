# CHANGELOG

All notable changes to BridgeCAD Enterprise Suite are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [0.1.0-rc1] — 2026-10-01 — BRIDGECAD-OSS-1.0 Release Candidate 1

### Summary
First public release candidate of BridgeCAD Enterprise Suite — an end-to-end
parametric bridge GAD (General Arrangement Drawing) generation platform built
on IRC/MORTH engineering standards. Covers the full workflow from Excel input
to 7-sheet DXF drawings, priced BOQ, QA compliance reports, and ZIP bundle
delivery through CLI, FastAPI, Streamlit, and React interfaces.

### Added — M0 (Scaffold)
- 9-package Python monorepo: `bridgecad-core`, `bridgecad-io`, `bridgecad-draw`,
  `bridgecad-bill`, `bridgecad-qa`, `bridgecad-export`, `bridgecad-plugins`,
  `bridgecad-ai`, `bridgecad-infra`
- Root `Makefile` with 20+ targets (install, lint, test, docker-up, etc.)
- `docker-compose.yml` (dev: API + PostgreSQL + Redis + MinIO + Jaeger)
- `.env.example` with 60+ documented configuration variables
- `.gitignore` covering Python/Node/IDE/secrets/outputs

### Added — M1 (Core Domain)
- `bridgecad_core/types.py` — 200+ enums across 10 IRC/MORTH sections
  (ClientType, BridgeCategory, SuperstructureType, FoundationType, ConcreteGrade,
  SeismicZone, WindSpeedBasic_ms, LoadCombination, LayerGroup, ...)
- `bridgecad_core/models.py` — 14 Pydantic V2 sheet models, 427 total fields
  (ProjectMaster, BridgeSelection, GeometryInput, Superstructure, Substructure,
  FoundationDetails, Approaches, HydraulicData, Materials, BearingsJoints,
  ComponentsLib, DrawingControl, Calculations, ValidationModel + BridgeProject aggregate)
- `bridgecad_core/geometry/` — 4 real-math geometry modules:
  - `plan.py` — skew-aware deck corners, pier centrelines, bearing positions
  - `long_section.py` — HFL/LWL/scour/soffit levels, 21-point ground profile
  - `cross_section.py` — parabolic camber (IRC:112 Clause 6.5), zone offsets
  - `foundation.py` — N×M pile grid, pile cap corners, well/open footing
- `bridgecad_core/validation.py` — 30 check functions (25 Critical + 5 Warning)
  wired to `RulesEngine`; `run_all()` returns `ValidationReport` with 0–100 score
- `bridgecad_core/validation_registry.py` — 150 `RuleSpec` entries (25C + 75W + 50I)
- Day verifiers: `day3_verify.py` (7/7 ★), `day4_verify.py` (8/8 ★)

### Added — M2 (IO Layer)
- `bridgecad_io/excel_reader.py` — 14-sheet xlsx → BridgeProject parser with
  enum name/value lookup, type coercion, bearing/joint tabular block parsing,
  span_length_N fallback pattern
- `bridgecad_io/excel_template.py` — styled 14-sheet xlsx generator with
  dropdowns, numeric validation, colour-coded cells (input=yellow, calc=grey)

### Added — M3 (Drawing Engine)
- `bridgecad_draw/layers.py` — 53 IRC SP:55-2019 layer definitions
- `bridgecad_draw/primitives.py` — 15 DXF drawing helpers (line/poly/rect/circle/
  arc/text/hatch/dim_linear_h/dim_linear_v/level_tag/chainage_tag/north_arrow/
  section_mark/scale_bar)
- `bridgecad_draw/dxf_engine.py` — ezdxf document factory + `CoordMapper`
  (hpos/vpos/pt/h_len/v_len)
- `bridgecad_draw/titleblocks.py` — IRC 5-row title block, revision strip, A1 border
- **7 real DXF sheet modules:**
  - `sheet1_plan.py` — skew-aware plan view, deck + piers + abutments + bearings + dims
  - `sheet2_long_section.py` — long section with HFL/LWL/scour/soffit, ground profile,
    pier shafts, pile tips, freeboard annotation
  - `sheet3_cross_section.py` — mid-span cross section with I/T girders, kerbs,
    parapets, parabolic camber curve
  - `sheet4_foundation.py` — pile cap plan + elevation, pile schedule table
  - `sheet5_pier_abutment_details.py` — pier + abutment elevations, wing walls,
    approach slab, construction notes
  - `sheet6_bearings_joints.py` — bearing schedule table, pad sketches,
    expansion joint schedule, IRC:83 / IRC SP:55 notes
  - `sheet7_bill_of_quantities.py` — abstract BOQ table (15 MORTH items)
- `bridgecad_draw/booklet.py` — 7-sheet coordinator via `importlib`
- Smoke test (`smoke_test_m3.py`): 7/7 sheets, 378 KB, ★ ACCEPTED ★

### Added — M4 (Plugin System)
- `bridgecad_plugins/manifest_schema.py` — `PluginManifest` dataclass + `load_manifest()`
- `bridgecad_plugins/registry.py` — `PluginRegistry` with `discover_builtin()`,
  `find_for_type()`, `find_for_span()`, module-level singleton `get_registry()`
- `bridgecad_plugins/runner.py` — `PluginRunner` with `apply_defaults()`,
  `get_typical_values()`, `describe()`, `load_defaults_yaml()`
- **3 built-in bridge-type plugins:**
  - `rcc_tbeam` — spans 6–30m, IRC:21-2000 / IRC:112-2020
  - `psc_igirder` — spans 20–45m, prestress defaults (G1860, POT-PTFE)
  - `box_culvert` — spans 2–8m, IRC SP:13 / IRC:112-2020

### Added — M5 (Bill Engine)
- `bridgecad_bill/models.py` — `BillItem`, `BillSection`, `BillOfQuantities`,
  `Deviation` dataclasses
- `bridgecad_bill/rates_db.py` — 90-item MORTH 2024-25 schedule-of-rates DB
  covering chapters 300 (earthwork), 401 (GSB), 500 (bituminous), 600 (river training),
  800 (safety), 1600 (reinforcement), 1700 (concrete), 1800 (piling), 2400 (steel),
  2500–2900 (bridge items); state PWD rate override chain
- `bridgecad_bill/processor.py` — `extract_and_price()` — 8-section BOQ from
  BridgeProject with pile-code selection by diameter, concrete-code by grade
- `bridgecad_bill/formatters/excel_formatter.py` — styled xlsx with ₹ totals
- `bridgecad_bill/formatters/csv_formatter.py` — flat CSV

### Added — M6 (Export + QA)
- `bridgecad_export/orchestrator.py` — `export_all()` runs DXF + BOQ + QA in
  sequence, returns ZIP bundle path
- `bridgecad_export/bundler.py` — `create_bundle()` + `manifest.json`
- `bridgecad_qa/rules_engine.py` — thin adapter to `bridgecad_core.validation.run_all`
- `bridgecad_qa/compliance.py` — `ComplianceScore` with sub-scores (IRC:5 / IRC:112 /
  IRC SP:55) and grades A+ → F
- `bridgecad_qa/reports.py` — `generate_html_report()` — responsive HTML with
  score gauge, severity matrix, findings table

### Added — M7 (Interfaces)
- **CLI** (`apps/cli-console/bridgecad_cli/main.py`) — Typer app with 10 command
  groups: `draw gad`, `validate`, `bill gen`, `export all`, `plugin list/info`,
  `template new/fill`, `health`, `version`
- **FastAPI** (`apps/api-gateway/bridgecad_api/main.py`) — 7 routers:
  `/bridges` (parse/validate), `/draw` (gad), `/bills` (generate),
  `/qa` (report), `/exports` (bundle), `/plugins` (list/detail), `/health`
  — all accept file uploads, return typed JSON or Blob downloads
- **Streamlit** (`apps/streamlit-ui/app.py`) — 15-tab app: Home, Load, Validate,
  Drawing Gen, QA Report, BOQ, Export, Plugins, Templates, Geometry, Hydraulics,
  Standards, History, Settings, Help
- **React** (`apps/web-console/`) — 6 pages wired to FastAPI:
  Dashboard, Projects, Drawing Gen, QA, BOQ, Export; typed API client (axios),
  Zustand store, React-Query hooks, Tailwind CSS + Vite build

### Added — M8 (AI + Infra)
- `bridgecad_ai/optimizer.py` — `BridgeOptimizer` using scipy SLSQP; minimises
  concrete volume cost subject to IRC:112 span/depth constraints (10 ≤ L/d ≤ 20);
  heuristic fallback when scipy unavailable
- `bridgecad_ai/estimator.py` — parametric `estimate_quantities()` + `estimate_cost()`
  with state PWD adjustment factors
- `bridgecad_ai/comparator.py` — 6-dimension side-by-side comparison with
  `radar_data()` for matplotlib/Plotly
- `bridgecad_ai/param_suggester.py` — `suggest()` from 6-type corpus of 28 Scribd
  reference GADs + IRC standard proportioning rules
- `bridgecad_infra/db.py` — SQLAlchemy 2.0 with 3 ORM tables
  (ProjectRecord, BridgeRecord, GenerationHistory); SQLite dev / Postgres prod
- `bridgecad_infra/repositories.py` — `ProjectRepo`, `BridgeRepo`, `HistoryRepo`
- `bridgecad_infra/cache.py` — `LRUCache` (OrderedDict + TTL), singleton caches
  for QA / BOQ / drawings
- `bridgecad_infra/auth.py` — constant-time API-key verification, role ladder
  (admin > engineer > viewer), `generate_api_key()`
- `bridgecad_infra/logging_setup.py` — structlog JSON (prod) / stdlib (dev) fallback

### Added — M9 (E2E Fixtures)
- `tests/e2e/run_e2e.py` — fixture runner (7 checks per fixture: total_length,
  span_count, width range, QA score, 7 DXF sheets, BOQ total, ZIP contents)
- **28 E2E fixtures** covering all 28 Scribd reference GAD drawings:
  - 5 primary fixtures (simple_12m, continuous_3x12m, girder_4x18m,
    box_culvert_8m, arch_24m)
  - 23 additional: Shiwalay 3×30m PSC box, Chambakkara 5×25m,
    Newaj River 3×45m, ROB viaduct CH 37+730, Binder Bridge skew 5°,
    2R-03 GAD 2×15m, 361+935 GAD 3×18m, MNB 8+485 minor, NH-353C 4×24m,
    GAD-7+233 20m, 0+600 well foundation, MJB PKG-7 6×30m viaduct,
    2-cell box culvert 8m, Viaduct BR-187 8×25m, GAD 24.75m, CH 2+100,
    14583-E PSC box 4×25m, Basantar Bridge well layout, PP-05 30m PSC,
    SRCTIP DOR 4×20m, Launching apron 10.1m, MR-5-LC-29 4×30m continuous,
    GAD 3×18m skew 15°
- Integration smoke: `tests/integration/test_full_pipeline.py` — 12/12 ★

### Added — M10 (RC1 Hardening)
- `rc1_smoke.py` — 11-check release gate (versions + AI + DB + E2E + CLI)
- `scripts/bump_version_rc1.py` — bumped all 11 package files to `0.1.0-rc1`
- **Docker multi-arch** (linux/amd64 + linux/arm64):
  - `apps/api-gateway/Dockerfile` — 2-stage, non-root, healthcheck
  - `apps/streamlit-ui/Dockerfile` — 2-stage, non-root, healthcheck
  - `apps/cli-console/Dockerfile` — 2-stage, volume mount `/work`
  - `apps/web-console/Dockerfile` — Node build + nginx runtime, SPA routing
- `docker-compose.prod.yml` — production stack: api + streamlit + web + db +
  cache + storage + nginx reverse proxy
- `nginx/prod.conf` — SSL termination, WebSocket for Streamlit, 50 MB upload limit
- **GitHub Actions:**
  - `.github/workflows/ci.yml` — 6 parallel jobs: lint, typecheck, unit,
    e2e, rc1-smoke, react-build
  - `.github/workflows/bench.yml` — weekly benchmarks with 20% regression gate
    (QA < 200ms, BOQ < 500ms, 1 sheet < 3s, 7 sheets < 15s)
  - `.github/workflows/release.yml` — multi-arch Docker buildx push to ghcr.io
    + GitHub Release with Python wheels
- `.pre-commit-config.yaml` — ruff lint+format, mypy, bandit, gitleaks,
  trailing-whitespace, commitizen
- `pyproject.toml` — pinned optional-dependency groups, full ruff/mypy/pytest/
  coverage/benchmark configuration
- `.env.example` — 60+ documented variables covering all services

### Fixed
- `BearingScheduleRow.location` — changed from `DS()` (default=None → optional)
  to `Field(max_length=40)` (required); unblocked C3 bad-value validation check
- `ChainageUnit.METRE` alias replaced with `METER` throughout E2E fixtures
- `DrawingScale` IntEnum lookup in `_enum()` — added int-value fallback
- `ExpansionJointScheduleRow.width_mm` — minimum 10 mm enforced in all fixtures
- Sheet 6 `circle()` — removed unsupported `lw` kwarg
- `excel_template.py` — removed placeholder `"B__"` cell references causing
  openpyxl `InvalidCoordinate` error
- `smoke_test_m3.py` — removed `chainage_start_km` from `ProjectMaster`
  (field belongs to `GeometryInput`)

### Tested
- Day 3 verifier: 7/7 ★ ACCEPTED ★
- Day 4 verifier: 8/8 ★ ACCEPTED ★
- M3 smoke test: 7/7 sheets, 378 KB ★ ACCEPTED ★
- Integration smoke: 12/12 ★ ACCEPTED ★
- RC1 smoke: 11/11 ★ ACCEPTED ★
- E2E fixture suite: **28/28 ★ ACCEPTED ★** (full Scribd GAD corpus)

---

## [0.0.1] — 2026-09-27 — M0 Scaffold

### Added
- Initial monorepo scaffold (9 packages, 4 apps)
- CI/CD pipeline stubs
- Legacy `src/bridge_gad/` DXF engine preserved (working PMGSY GAD pipeline)
- PMGSY §18 DXF→PDF blank-page hotfix: two-layer defense in `bridge_generator.py`
  + `dxf_to_pdf.py`; pytest 5/5 GREEN

---

[0.1.0-rc1]: https://github.com/bridgecad/enterprise-suite/releases/tag/v0.1.0-rc1
[0.0.1]: https://github.com/bridgecad/enterprise-suite/releases/tag/v0.0.1
