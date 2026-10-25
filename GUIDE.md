# 🌉 BridgeCAD Enterprise Suite — Master Guide

> **If this file contradicts any other doc, this file wins.**

**Version:** v0.1.0-rc1 · **Codename:** `BRIDGECAD-OSS-1.0` · **Licence:** MIT
**Repo:** https://github.com/CRAJKUMARSINGH/BridgeCAD-Enterprise-Suite

> This is the single authoritative guide. If any other document in this repo
> contradicts it, this file wins. Last verified against `main` on 2026-10-22.

---

## 0. Repo orientation — read before you `cd` anywhere

This repository is a **single-tree monorepo**. The repo root *is* the product
root. There is no subfolder to descend into.

| Generation | Location | Status | Entry point |
|---|---|---|---|
| **BridgeCAD Enterprise Suite** | repo root | ✅ **ACTIVE** · v0.1.0-rc1 | `python -m bridgecad` |
| Ultimate Bridge GAD Generator | `streamlit_app_ultimate.py` + `src/bridge_gad/` | 🏛️ LEGACY | `streamlit run streamlit_app_ultimate.py` |
| Lean Bridge GAD Generator | `app_lean.py` | 🧪 SIDE TOOL | `streamlit run app_lean.py` |

> ⚠️ **Older docs are wrong.** `README.md`, `SKELETON.md` and
> `GAPS_OPPORTUNITIES_FIXES.md` all tell you to `cd` into a legacy
> `BridgeCAD Enterprise Suite` directory.
> That directory no longer exists on `main`. All Suite code — `packages/`,
> `apps/`, `standards/`, `templates/`, `tests/` — lives at the repo root.

**Start with the Suite.** The two Streamlit apps are preserved for reference and
are still smoke-tested, but no new engineering features land in them.

---

## 1. What this is

BridgeCAD Enterprise Suite turns a parametric Excel workbook into a
standards-compliant bridge **General Arrangement Drawing (GAD)** package, a
priced Bill of Quantities, and a QA compliance report — then bundles the lot.

**Input:** one 14-sheet `.xlsx` workbook.
**Output:** 7-sheet DXF drawing set, priced BOQ, QA report (0–100 grade),
`manifest.json`, ZIP bundle.

It is built for Indian highway and rail bridge practice: IRC 5, 6, 21, 83,
SP:55, SP:114 and MORTH 2024-25 schedule of rates are wired into the domain
model, not bolted on.

### Capability matrix

| Capability | Status | Where |
|---|---|---|
| Excel → `BridgeProject` model | ✅ implemented | `packages/bridgecad-io` |
| 7-sheet DXF drawing engine | ✅ implemented | `packages/bridgecad-draw` |
| 53 IRC SP:55 layer definitions | ✅ implemented | `bridgecad_draw/layers.py` |
| Priced BOQ (8 sections, MORTH rates) | ✅ implemented | `packages/bridgecad-bill` |
| QA rules + 0–100 compliance grade | ✅ implemented | `packages/bridgecad-qa` |
| ZIP bundle + manifest | ✅ implemented | `packages/bridgecad-export` |
| Bridge-type plugin registry | ✅ 3 built-in | `packages/bridgecad-plugins` |
| Optimiser / estimator / comparator | ✅ implemented | `packages/bridgecad-ai` |
| CLI · FastAPI · Streamlit · React | ✅ all four | `apps/` |
| 28 E2E fixtures | ✅ 28/28 passing | `tests/e2e/fixtures/` |
| SVG / PNG / 3D engines | 🚧 partial | `bridgecad_draw/engines/` |
| Sheet 2–7 full engineering geometry | 🚧 scaffolds | see §11 |

---

## 2. Quick start

### Path A — zero install (fastest, verifies the repo works)

```bash
git clone https://github.com/CRAJKUMARSINGH/BridgeCAD-Enterprise-Suite.git
cd BridgeCAD-Enterprise-Suite

python -m bridgecad                 # banner + usage
python -m bridgecad info            # interpreter, repo root, workspace paths
python -m bridgecad verify          # runs day3_verify.py + day4_verify.py
python -m bridgecad generate 11span # generates the 11-span RCC solid slab GAD
```

`python -m bridgecad` works without `pip install` because `sitecustomize.py`
at the repo root bootstraps `sys.path` onto `packages/*` and `apps/*`. Run it
from the repo root.

### Path B — development install

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
make lint && make test
```

### Path C — full stack in Docker

```bash
cp .env.example .env
docker compose up api          # FastAPI on :8000, health at /health
docker compose up              # api + postgres + redis + minio + jaeger
```

### Path D — interfaces

```bash
pip install -e apps/cli-console && bridgecad-cli --help   # 10 command groups
streamlit run apps/streamlit-ui/app.py                    # 15-tab UI
cd apps/web-console && npm ci && npm run dev               # React console
```

---

## 3. Architecture

```
Excel workbook
   │
   ▼
bridgecad_io ──► BridgeProject (Pydantic v2, single in-memory truth)
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
  bridgecad_draw  bridgecad_bill  bridgecad_qa
   7 DXF sheets    priced BOQ      150 rules → grade
        └─────────────┼─────────────┘
                      ▼
              bridgecad_export ──► ZIP + manifest.json
```

**Design invariants — do not break these:**

1. `BridgeProject` is the only in-memory truth. Every consumer reads it.
2. The Excel workbook is the only external contract. 14 sheets, 1:1 with models.
3. `bridgecad-core` has zero dependencies on other Suite packages.
4. Drawing, billing and QA never call each other. Only `bridgecad_export` fans out.
5. Plugins override drawing behaviour; they never mutate the model.

### Package map

| Package | Responsibility |
|---|---|
| `bridgecad-core` | enums, Pydantic models, geometry maths, validation, quantities |
| `bridgecad-io` | Excel template / reader / writer, CSV + JSON adapters |
| `bridgecad-draw` | layers, primitives, title blocks, 7 sheets, 5 engines, booklet |
| `bridgecad-bill` | MORTH rates DB, hierarchical processor, 4 formatters |
| `bridgecad-qa` | rules engine, compliance scoring, HTML reports, recommendations |
| `bridgecad-export` | orchestrator, ZIP bundler, versioner |
| `bridgecad-plugins` | manifest schema, registry, runner, installer |
| `bridgecad-ai` | scipy optimiser, estimator, comparator, param suggester |
| `bridgecad-infra` | SQLAlchemy db, repositories, LRU cache, storage, auth, logging |

### Apps

| App | Stack | Surface |
|---|---|---|
| `apps/cli-console` | Typer | 10 command groups |
| `apps/api-gateway` | FastAPI | `/bridges` `/draw` `/bills` `/qa` `/exports` `/plugins` `/health` |
| `apps/streamlit-ui` | Streamlit | 15 tabs |
| `apps/web-console` | React + Vite + TS | 6 pages |

---

## 4. The Excel contract

One workbook, 14 sheets, 427 mapped fields. Input cells are yellow, calculated
cells grey and locked. Generate a fresh template rather than hand-building one:

```bash
bridgecad-cli template new --type simple_12m -o bridge.xlsx
```

**Sheet set:** ProjectMaster · BridgeSelection · GeometryInput ·
Superstructure · Substructure · FoundationDetails · Approaches · HydraulicData ·
Materials · BearingsJoints · ComponentsLib · DrawingControl · Calculations ·
ValidationModel.

**Minimum viable input:** `GeometryInput` (span count, span lengths, skew,
carriageway width, deck levels), `HydraulicData` (HFL, LWL, scour),
`FoundationDetails` (foundation type + dimensions), `Materials` (concrete grade,
steel grade). Everything else has IRC-derived defaults.

**Validation runs at parse time** and returns `{valid, warning, blocked,
unsupported}` per field before any heavy work starts.

### Round-trip rule

`Excel → model → Excel` must drift by ≤5%, cosmetic only. If a change makes a
workbook fail to round-trip, the change is wrong.

---

## 5. Standard workflows

### 5.1 Generate a GAD drawing

```bash
bridgecad-cli draw gad bridge.xlsx -o out/gad.dxf
curl -F file=@bridge.xlsx localhost:8000/draw/gad -o gad.dxf
```

### 5.2 Generate the 7-sheet package

```bash
bridgecad-cli draw booklet bridge.xlsx -o out/
```

Sheets: `sheet1_plan` · `sheet2_long_section` · `sheet3_cross_section` ·
`sheet4_foundation` · `sheet5_pier_abutment_details` · `sheet6_bearings_joints` ·
`sheet7_bill_of_quantities`.

> **Naming note:** the legacy app README calls these IDX/GAD/TYP/ABT/PIER/BRG/DRN.
> That is the legacy 4-sheet naming. The Suite names above are canonical.

### 5.3 Price a BOQ

```bash
bridgecad-cli bill gen --input bridge.xlsx --format all
```

Four formatters: styled Excel, A4 PDF, HTML, master CSV. Rates come from
`standards/morth_rates_2024.yaml` (90 seeded items across chapters 300, 401,
500, 600, 800, 1600, 1700, 1800, 2400, 2500–2900) with a State PWD override
chain.

### 5.4 Score compliance

```bash
bridgecad-cli qa report bridge.xlsx -o out/qa.html
python -m bridgecad qa project.json
```

150 rule specs — 25 critical, 75 warning, 50 info. Weighted grade A+ → F with
sub-scores for IRC:5, IRC:112 and IRC SP:55. 30 of the 150 are fully
implemented; the rest are registered with metadata and stubbed.

### 5.5 Export everything

```bash
bridgecad-cli export all bridge.xlsx -o out/
```

Produces a ZIP containing DXF sheets, BOQ, QA report and `manifest.json`
(package versions, standards version, rate schedule version, input hash,
QA findings).

### 5.6 Batch

```bash
python -m bridge_gad.generate_all_drawings out_dir --n 10 --base-template continuous_3x12m
python tests/e2e/run_e2e.py
```

---

## 6. Standards coverage

| Standard | Scope | Wired into |
|---|---|---|
| IRC:5 | Road bridges — general features | geometry, validation, QA |
| IRC:6 | Loads and load combinations | validation, QA |
| IRC:21 | Concrete bridge design | validation, span/depth limits |
| IRC:83 | Bearings | bearing schedule, QA |
| IRC:SP:55 | Drawing practice and layers | 53 layer definitions |
| IRC:SP:114 | Seismic design | zone presets, QA |
| MORTH 2024-25 | Schedule of rates | BOQ pricing |

Span/depth is constrained to $$10 \le L/d \le 20$$ in the optimiser and the
validator. Owner presets exist for NHAI, PWD, MORTH and RAILWAY.

---

## 7. Authoring a plugin

```
packages/bridgecad-plugins/bridgecad_plugins/plugins/<name>/
├── manifest.json      # name, span range, standards, sheet overrides
├── defaults.yaml      # typical values
└── draw_overrides.py  # per-sheet geometry overrides
```

Register via `PluginRegistry.discover_builtin()`. Built-in types: `rcc_tbeam`
(6–30 m), `psc_igirder` (20–45 m), `box_culvert` (2–8 m). Planned to ten.

```bash
bridgecad-cli plugin list
bridgecad-cli plugin info rcc_tbeam
python scripts/scaffold_plugin.py <name>
```

---

## 8. Configuration

`config.yaml` for app config; `.env` (from `.env.example`, 60+ documented vars)
for secrets and service endpoints. Never commit `.env`.

Key groups: database DSN, redis URL, S3/MinIO credentials, API key +
role ladder, OTel/Jaeger endpoint, upload limits, rate-schedule version pin.

**API hardening already in place:** scale validated to 10–2500, prefix
sanitised against path traversal and unsafe characters, atomic temp-file
staging with `BackgroundTasks` cleanup on both `/draw/gad` and `/export/bundle`.

**Still open:** upload size cap, `.xlsx`-only MIME allowlist (reject `.xls` /
`.xlsm` with 415), RFC 7807 `application/problem+json` error bodies.

---

## 9. Testing and verification

```bash
python -m bridgecad verify      # day3 (7/7) + day4 (8/8) acceptance verifiers
python rc1_smoke.py             # 11-check release gate
python tests/e2e/run_e2e.py     # 28 fixtures, 7 checks each
pytest tests/integration        # 12/12 full-pipeline
make test
```

28 E2E fixtures cover the reference GAD corpus: `simple_12m`,
`continuous_3x12m`, `girder_4x18m`, `box_culvert_8m`, `arch_24m`, Shiwalay
3×30 m PSC box, Chambakkara 5×25 m, Newaj River 3×45 m, ROB viaduct CH 37+730,
Binder skew 5°, 2R-03 2×15 m, 361+935 3×18 m, MNB 8+485, NH-353C 4×24 m,
GAD-7+233, 0+600 well foundation, MJB PKG-7 6×30 m viaduct, 2-cell box culvert,
Viaduct BR-187 8×25 m, GAD 24.75 m, CH 2+100, 14583-E PSC box 4×25 m, Basantar
well layout, PP-05 30 m PSC, SRCTIP DOR 4×20 m, launching apron 10.1 m,
MR-5-LC-29 4×30 m, GAD 3×18 m skew 15°.

**Benchmark gates** (`bench.yml`, weekly, 20% regression tolerance): QA < 200 ms,
BOQ < 500 ms, single sheet < 3 s, 7 sheets < 15 s.

**CI:** `.github/workflows/suite-ci.yml` (6 jobs: lint, typecheck, unit, e2e,
rc1-smoke, react-build) and `.github/workflows/ci.yml` (legacy app). Both run in
parallel. The PII scan uses `git grep` with an `egg-info` exclusion so generated
metadata can never fail the build.

---

## 10. Deployment

```bash
docker compose -f docker-compose.prod.yml up -d
```

Stack: api + streamlit + web + postgres + redis + minio + nginx reverse proxy
with SSL termination, WebSocket upgrade for Streamlit, 50 MB upload limit.
Multi-arch images (linux/amd64 + linux/arm64), 2-stage builds, non-root users,
healthchecks on api and streamlit.

`release.yml` builds and pushes to ghcr.io and cuts a GitHub Release with wheels.

---

## 11. Release rule — what you may and may not claim

Do **not** call this repo "perfect" and do **not** ship a drawing or BOQ as
construction-ready until all four hold:

1. **CI green** on both workflows.
2. **All 28 fixtures** emit explicit pass/fail JSON with 5 golden-case model
   summaries pinned.
3. **All 7 DXF sheets** for those 5 golden cases pass structural checks *and* an
   engineer has visually reviewed representative output per bridge family.
4. **Every non-zero BOQ line** has traceable inputs and an engineer-approved
   tolerance.

Until then, every export manifest must carry **"Generated — not reviewed for
construction"** and the UI must show it at download time.

### Known limitations (be honest about these)

- **Sheets 2–7 are scaffolds.** Per `2 OCT PROGRAM.MD`, only sheet 1 carries
  complete engineering geometry. Until fixed, the export manifest should list
  which sheets are scaffolds.
- **BOQ multipliers are heuristic.** `bridgecad_bill/processor.py` uses
  multipliers, not derived quantities. Every line needs a formula/source-field
  list and a `calculated` / `estimated` / `not_calculated` status. Missing input
  must return `not_calculated` with a reason, never a plausible default.
- **120 of 150 QA rules are registered but stubbed.**
- **Sheet origins are not yet on one shared coordinate contract.**
- **SVG, PNG and 3D engines are partial.**

---

## 12. Roadmap

M0–M10 complete through RC1. Open workstreams, in priority order:

1. **Phase 1** — deterministic fixtures, golden-case model summaries, non-fuzzy
   enum deserialisation.
2. **Phase 2** — real geometry for sheets 2–7, shared coordinate contract,
   structural DXF checks, visual regression. *(1–2 weeks)*
3. **Phase 3** — traceable BOQ with per-line provenance. *(4–8 eng-days)*
4. **Phase 4** — single versioned workbook schema across every consumer, upload
   hardening, structured error responses.
5. **Phase 5** — release readiness, plugin matrix decision, artifact gitignore,
   provenance-stamped fixtures.

---

## 13. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `cd: BridgeCAD Enterprise Suite: No such file` | stale docs | you are already in the product root |
| `ModuleNotFoundError: bridgecad_core` | not at repo root | `cd` to repo root; `sitecustomize.py` handles the rest |
| `pip install -r requirements_lean.txt` fails | file does not exist | use `requirements.txt` |
| PDF renders blank | matplotlib backend | confirm DXF has entities, not text only |
| Text-rendering warnings | font fallback | expected and harmless |
| Batch run OOM above 50 items | memory | batch in chunks, use `--seed` for reproducibility |
| API returns 400 on `scale` | out of range | valid range is 10–2500 |
| API returns 400 on `prefix` | path separators / unsafe chars | keep it under 32 chars, alphanumeric |

---

## 14. Documentation map

| File | Purpose |
|---|---|
| `GUIDE.md` | **this file** — authoritative |
| `README.md` | front door |
| `CHANGELOG.md` | versioned change log |
| `CONTRIBUTING.md` | how to contribute |
| `CODE_OF_CONDUCT.md` | conduct |
| `SECURITY.md` | vulnerability reporting |
| `SKELETON.md` | M0 scaffold tree |
| `01_ACTION_PLAN_M0_to_M10.md` | milestone plan |
| `00_REPORT_Trust_Assessment_and_Synthesis.md` | source synthesis |
| `GAPS_OPPORTUNITIES_FIXES.md` | audit + patch report |
| `docs/` | user manual builder |
| `app-robustness-testing.md` | robustness test notes |
| `OUTPUT_GENERATION_GUIDE.md` | legacy output driver |
| `PDF_OUTPUT_FEATURES.md` | PDF feature notes |

---

## 15. Contributing, support, licence

See `CONTRIBUTING.md`. Open an issue at
https://github.com/CRAJKUMARSINGH/BridgeCAD-Enterprise-Suite/issues and tag it
`support` for help or `rks-legal` for professional-services enquiries.

MIT — see `LICENSE`.

---

## Changelog for this guide

| Date | Verified against commit | What changed |
|---|---|---|
| 2026-10-22 | `main` | Initial authoritative guide; consolidated the scattered, drifted docs into one master document. |
