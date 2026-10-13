# BridgeCAD Enterprise Suite — Action Plan: M0 → M10

**Codename:** BRIDGECAD-OSS-1.0
**Start Date:** 2026-09-30 (M0)
**Target RC1 Date:** 2027-03-24 (≈25 weeks)

---

## M0 — SCAFFOLD (Week 1)

### Objective
Create the monorepo directory structure, 9 Python package workspaces, 4 app entry points, infrastructure stubs, and build tooling.

### Exit Criteria
- `make lint`, `make test`, `make dev` all run (exit 0 even if no tests yet)
- `docker-compose up api` starts a FastAPI "healthy" stub
- All 9 packages have a `pyproject.toml` and `__init__.py`
- Directory tree matches `SKELETON.md` exactly

### Deliverables
1. Root `pyproject.toml` with `workspace = ["packages/*", "apps/*"]`
2. Root `Makefile` with targets: `install`, `lint`, `test`, `format`, `dev`, `build`, `clean`
3. `docker-compose.yml` with services: `api`, `cli`, `db`, `cache`, `storage` (minio)
4. `.env.example` with 20+ environment variables
5. `.gitignore` (Python + Node + IDE + secrets)
6. 4 app stubs:
   - `apps/streamlit-ui/app.py` (placeholder "coming soon")
   - `apps/web-console/` (vite + TS skeleton `package.json`)
   - `apps/cli-console/main.py` (typer single `version` command)
   - `apps/api-gateway/main.py` (fastapi `/health` endpoint)
7. 9 package stubs with `pyproject.toml` + `__init__.py` + `tests/__init__.py`:
   - `bridgecad-core` (types, models, geometry, standards, validation, quantities, costs)
   - `bridgecad-io` (excel, csv, json adapters)
   - `bridgecad-draw` (5 engines × 7 sheets)
   - `bridgecad-plugins` (registry + 10 plugin dir stubs)
   - `bridgecad-bill` (models, rates_db, processor, formatters)
   - `bridgecad-qa` (rules_engine, compliance, reports, recommendations)
   - `bridgecad-export` (orchestrator, bundler, booklet, versioner)
   - `bridgecad-ai` (optimizer, estimator, comparator, suggester)
   - `bridgecad-infra` (db, cache, queue, storage, logging, metrics, auth)
8. Directory scaffold:
   - `templates/` (5 empty category dirs)
   - `standards/` (5 empty YAML placeholders + state_pwd_overrides/)
   - `tests/` (conftest.py, e2e/, integration/, benchmarks/)
   - `scripts/` (3 placeholder scripts)
   - `migrations/` (alembic.ini empty placeholder)
   - `docs/` (sphinx conf.py placeholder)
9. `SKELETON.md` tree listing

---

## M1 — CORE DOMAIN (Weeks 2–4)

### Objective
Implement 200+ enums, Pydantic V2 models for all 14 Excel sheets, 150 QA rule functions, and 4 pure-function geometry modules.

### Deliverables
1. `bridgecad_core/types.py` → all enums (categorize with `# ---` section headers)
2. `bridgecad_core/models.py` → 12 sub-models + top-level `BridgeProject` aggregate
3. `bridgecad_core/geometry/{plan,long_section,cross_section,foundation}.py`
4. `bridgecad_core/standards/{irc_sp55,irc_05,irc_21,morth_specs}.py`
5. `bridgecad_core/validation.py` → 150 `check_xxx()` functions with severity tags
6. `bridgecad_core/quantities.py` + `costs.py` → aggregation helpers
7. Unit tests ≥ 80% coverage on core
8. Mermaid data-flow diagram committed to `docs/`

---

## M2 — IO LAYER (Weeks 5–6)

### Objective
Excel ⇄ Model serialization. The 14-sheet workbook must:
- Load into a fully-valid `BridgeProject` Pydantic model
- Round-trip with ≤5% cosmetic drift

### Deliverables
1. `bridgecad_io/excel_template.py` → 14 sheets with styling/validation/protection
2. `bridgecad_io/excel_reader.py` → 14 per-sheet parsers
3. `bridgecad_io/excel_writer.py` → model → styled sheets with locked calculated cells
4. `bridgecad_io/{csv,json}_adapter.py`
5. Integration tests: round-trip on all 25 templates
6. CLI subcommand: `bridgecad template --type simple_12m -o out.xlsx`

---

## M3 — DRAWING ENGINE (Weeks 7–10)

### Objective
5 engines × 7 sheets = 35 drawing paths. Layers, title blocks, hatching, dimensions.

### Deliverables
1. `bridgecad_draw/layers.py` → IRC standard layer registry
2. `bridgecad_draw/primitives.py` → line, polyline, arc, circle, hatch, dim, text
3. `bridgecad_draw/titleblocks.py` → Standard / Compact / Detailed
4. 5 engines: `dxf_engine.py`, `svg_engine.py`, `pdf_engine.py`, `png_engine.py`, `three_engine.py`
5. 7 sheets: `sheet1_plan.py`, `sheet2_long_section.py`, `sheet3_cross_section.py`, `sheet4_foundation.py`, `sheet5_pier_abutment_details.py`, `sheet6_bearings_joints.py`, `sheet7_bill_of_quantities.py`
6. `bridgecad_draw/booklet.py` → 7-sheet PDF with cover + TOC
7. Benchmark target: simple_12m 7-sheet package < 10s wall

---

## M4 — PLUGINS (Weeks 11–14)

### Objective
10 bridge-type plugins. Each plugin = drawing override sheet(s) + typical values YAML + installer registration.

### Deliverables
1. `bridgecad_plugins/{registry,runner,installer,manifest_schema}.py`
2. 10 plugins in `plugins/` (each with its own `manifest.json` + `draw_overrides.py` + `defaults.yaml`):
   - rcc_tbeam / psc_igirder / psc_boxgirder / solid_slab / voided_slab
   - arch_bridge / steel_composite / box_culvert / pipe_culvert / cable_stayed
3. 25 Excel templates in `templates/` (5 categories × 5 variants each)
4. `bridgecad plugin list / install / uninstall` CLI commands
5. Plugin smoke test: all 10 types produce valid DXF

---

## M5 — BILL ENGINE (Weeks 15–17)

### Objective
MORTH schedule-rate database + hierarchical bill generation with 4 formatters.

### Deliverables
1. `standards/morth_rates_2024.yaml` → 5000+ items placeholder (100 seed items real)
2. `bridgecad_bill/models.py` → ItemGroup / BillItem / Deviation / Statement
3. `bridgecad_bill/rates_db.py` → YAML-backed lookup with State-PWD override chain
4. `bridgecad_bill/processor.py` → tender premium, deviations, draft versioning
5. 4 formatters: Excel (styled, exact widths) / PDF (A4) / HTML (professional) / CSV (Master)
6. RA-bill + Running-account + Final-bill statements
7. CLI: `bridgecad bill generate --input bridge.xlsx --format all`

---

## M6 — EXPORT + QA REPORTS (Weeks 18–19)

### Objective
Unified export orchestrator + QA compliance reports 0–100 scoring.

### Deliverables
1. `bridgecad_export/orchestrator.py` → fan-out job → all formats
2. `bridgecad_export/bundler.py` → ZIP with manifest JSON (DXF+PDF+XLSX+JSON)
3. `bridgecad_export/versioner.py` → Git-tag stamp in drawing title block + PDF metadata
4. `bridgecad_qa/rules_engine.py` → runs 150 checks; returns `ValidationReport`
5. `bridgecad_qa/compliance.py` → weighted 0–100 compliance score (IRC:05, IRC:21, IRC:SP:55)
6. `bridgecad_qa/reports.py` → PDF/HTML QA report with severity matrix
7. `bridgecad_qa/recommendations.py` → per-failure auto-fix suggestions

---

## M7 — INTERFACES (Weeks 20–22)

### Objective
4 interface layers are first-class citizens of the product.

### Deliverables
1. **CLI (20+ commands):** `bridgecad {template, validate, draw, bill, qa, export, plugin, project, history, compare, ...}`
2. **FastAPI 5 routers:** `/bridges`, `/bills`, `/exports`, `/qa`, `/auth` (async jobs via arq)
3. **Streamlit 15 tabs:** Drawing Gen, Bill Gen, Templates, Quality, 3D Preview, Compare, AI Optimizer, Export Manager, History, Help, Projects, Standards, Reports, Settings, About
4. **React Console MVP:** Projects list, detail view, 3D canvas (three.js), QA dashboard, export panel
5. OpenAPI spec + Postman collection

---

## M8 — AI + INFRA (Weeks 23–24)

### Objective
ML optimization layer + enterprise infrastructure adapters.

### Deliverables
1. `bridgecad_ai/optimizer.py` → scipy SLSQP: minimize cost vs span/depth/width constraints
2. `bridgecad_ai/estimator.py` → no-API cost/quantity predictor (heuristic + regressor)
3. `bridgecad_ai/comparator.py` → side-by-side % diff + radar chart (matplotlib)
4. `bridgecad_ai/param_suggester.py` → defaults from 28 Scribd reference corpus
5. `bridgecad_infra/db.py` → SQLAlchemy (SQLite dev / Postgres prod)
6. `bridgecad_infra/repositories.py` → ProjectRepo, BridgeRepo, HistoryRepo
7. `bridgecad_infra/cache.py` → Redis + in-memory LRU fallback
8. `bridgecad_infra/queue.py` → arq async job runner
9. `bridgecad_infra/storage.py` → local disk + S3 (boto3) adapter
10. `bridgecad_infra/{logging,metrics,auth}.py` → structlog, prometheus, OAuth2+API keys
11. Alembic migrations 0001_init through 0003_histories
12. OTel collector + Jaeger docker-compose profile

---

## M9 — REGRESSION & BENCH (Weeks 25–26)

### Objective
28 E2E fixtures (one per Scribd ref). Benchmark targets hit. CI green.

### Deliverables
1. `tests/fixtures/` → 28 `{slug}.xlsx` + `{slug}.expected.json` minimal pairs
2. `tests/e2e/test_roundtrip_*.py` → all 28 fixtures pass
3. `tests/benchmarks/test_*.py` with pytest-benchmark:
   - simple_12m single GAD DXF: < 2s
   - simple_12m 7-sheet PDF booklet: < 10s
   - QA check suite: < 0.5s
   - Bill generation: < 1s
4. `.github/workflows/ci.yml`: lint + typecheck + unit + integration + e2e (sample 5/28)
5. `.github/workflows/bench.yml`: weekly benchmark check (fail if >20% regression)
6. `.github/workflows/release.yml`: build docker images + publish to PyPI (placeholder)

---

## M10 — RELEASE RC1 (Week 27)

### Objective
Production-ready release candidate: all 25 templates smoke-tested, docs complete, deployable.

### Deliverables
1. `bridgecad --version` prints `BRIDGECAD-OSS-1.0-RC1`
2. Smoke test: every template → all 7 sheets → all 5 formats → ZIP bundle
3. Sphinx + MkDocs hybrid docs: Getting Started, API Reference, Plugin Authoring, Standards, Deployment, FAQ
4. Docker images: `bridgecad/{api,cli,streamlit,web}:1.0-rc1` (multi-arch)
5. Helm chart: `charts/bridgecad/` for K8s deploy
6. `CHANGELOG.md` 1.0 RC1 entry
7. `CONTRIBUTING.md` + `CODE_OF_CONDUCT.md` + `SECURITY.md`
8. Tag `v1.0.0-rc1`

---

## Dependencies Between Milestones

```
M0 ──► M1 ──► M2 ──┬──► M3 ──► M6 ──► M7 ──► M9 ──► M10
                   │              ▲
                   └──► M4 ──────┘
                          │
                          └──► M5 ──┘
M8 runs parallel after M1 (uses stable core types)
```

---

_Action Plan frozen as of 2026-09-30. Execute M0 immediately._
