# 🌉 BridgeCAD Enterprise Suite

**BRIDGECAD-OSS-1.0-RC1** — AI-powered parametric bridge General Arrangement Drawing (GAD) generation platform.

[![Suite CI](https://github.com/CRAJKUMARSINGH/Bridge_GAD_Yogendra_Borse/actions/workflows/suite-ci.yml/badge.svg)](https://github.com/CRAJKUMARSINGH/Bridge_GAD_Yogendra_Borse/actions/workflows/suite-ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![IRC:112-2020](https://img.shields.io/badge/standard-IRC%3A112--2020-green.svg)](#)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

---

## What it does

BridgeCAD takes a **14-sheet Excel workbook** as input and produces:

| Output | Detail |
|--------|--------|
| **7-sheet DXF GAD package** | Plan view · Long section · Cross section · Foundation · Pier/Abutment · Bearings · BOQ |
| **Priced Bill of Quantities** | Excel + CSV, 90-item MORTH 2024-25 rates, state PWD override |
| **QA Compliance Report** | 30 IRC/MORTH checks, score 0–100, grade A+→F, HTML report |
| **ZIP Bundle** | All of the above + manifest.json in one download |

All outputs comply with **IRC:SP:55-2019** drawing standards, **IRC:112-2020** structural code, **IRC:5-2015** hydraulics, and **MORTH 5th Revision** contract specifications.

---

## Supported Bridge Types

| Category | Variants | Span Range |
|----------|----------|------------|
| Minor Bridges | RCC T-Beam simply supported | 6–30 m |
| Major Bridges | PSC I-Girder / PSC Box Girder | 20–60 m |
| Viaducts | PSC I-Girder / Box / Steel Composite | Multi-span urban |
| Culverts | RCC Box (1–4 cell) / Pipe / Arch | 2–10 m |
| ROB / RUB / FOB | Railway crossings / Foot over bridge | Any span |

---

## Quick Start

### Option A — CLI (recommended)

```bash
# Clone
git clone https://github.com/bridgecad/enterprise-suite
cd "BridgeCAD Enterprise Suite"

# Install all packages
pip install -e packages/*

# Generate from a template
python scripts/generate_templates.py   # create 25 blank xlsx templates
bridgecad template new simple_12m -o my_bridge.xlsx
bridgecad draw gad my_bridge.xlsx -o ./output/drawings
bridgecad validate my_bridge.xlsx --report QA.html
bridgecad bill gen my_bridge.xlsx -o ./output/bill
bridgecad export all my_bridge.xlsx -o ./output
```

### Option B — Streamlit UI

```bash
cd apps/streamlit-ui
streamlit run app.py
# Open http://localhost:8501
```

### Option C — Docker (production)

```bash
cp .env.example .env          # fill DATABASE_URL, POSTGRES_PASSWORD, etc.
docker compose -f docker-compose.prod.yml up -d
# API:       http://localhost:8000
# Streamlit: http://localhost:8501
# React UI:  http://localhost:80
```

### Option D — FastAPI

```bash
cd apps/api-gateway
uvicorn bridgecad_api.main:app --reload --port 8000
# Docs: http://localhost:8000/docs
```

---

## Architecture

```
BridgeCAD Enterprise Suite/
├── packages/
│   ├── bridgecad-core/       # 200+ enums · 427-field Pydantic models ·
│   │                         # 4 geometry modules · 30 validation checks ·
│   │                         # IRC/MORTH standards (irc_05, irc_21, irc_sp55, morth_specs)
│   ├── bridgecad-io/         # Excel ↔ BridgeProject (14-sheet parser + template generator)
│   ├── bridgecad-draw/       # 7 DXF sheet modules · IRC SP:55 layer registry
│   ├── bridgecad-bill/       # MORTH BOQ · 90-item rates DB · Excel/CSV formatters
│   ├── bridgecad-qa/         # Compliance scorer · HTML report generator
│   ├── bridgecad-export/     # ZIP orchestrator · manifest
│   ├── bridgecad-plugins/    # 3 built-in plugins: rcc_tbeam · psc_igirder · box_culvert
│   ├── bridgecad-ai/         # scipy optimizer · parametric estimator · comparator
│   └── bridgecad-infra/      # SQLAlchemy DB · LRU cache · API-key auth · structlog
├── apps/
│   ├── api-gateway/          # FastAPI 7 routers — file-upload → DXF/BOQ/QA/ZIP
│   ├── cli-console/          # Typer CLI — draw/validate/bill/export/plugin/template
│   ├── streamlit-ui/         # 15-tab Streamlit app
│   └── web-console/          # React/Vite/Tailwind SPA — 6 pages wired to FastAPI
├── templates/                # 25 pre-filled xlsx templates (5 categories × 5 variants)
├── tests/
│   ├── e2e/fixtures/         # 28 JSON fixtures from real Scribd GAD drawings
│   └── integration/          # Full pipeline smoke test (12/12)
└── standards/                # YAML: IRC:5 · IRC:21 · IRC SP:55 · MORTH rates
```

---

## Package Versions

All packages are at **v0.1.0-rc1**.

| Package | Contents |
|---------|---------|
| `bridgecad-core` | Types, models, geometry, validation, standards |
| `bridgecad-io` | Excel reader + template generator |
| `bridgecad-draw` | 7 DXF sheet modules + booklet |
| `bridgecad-bill` | BOQ engine + MORTH rates DB |
| `bridgecad-qa` | Compliance checker + HTML report |
| `bridgecad-export` | Export orchestrator + ZIP bundler |
| `bridgecad-plugins` | Plugin system + 3 bridge-type plugins |
| `bridgecad-ai` | scipy optimizer + estimator + comparator |
| `bridgecad-infra` | DB + cache + auth + logging |

---

## E2E Test Coverage — 28 Scribd Reference GADs

The test suite includes fixtures from 28 real-world Indian bridge GAD drawings:

```
simple_12m          continuous_3x12m    girder_4x18m        box_culvert_8m
arch_24m            shiwalay_3x30m      chambakkara_5x25m   newaj_3x45m
rob_viaduct         binder_skew5        gad_2x15m           gad_361_935
mnb_8_485           nh353c_4x24m        gad_7_233           well_0_600
mjb_pkg7_viaduct    box_2cell_8m        viaduct_br187       gad_24_750m
bridge_ch_2_100     sh35_mjb_psc_box    basantar_well       pp05_30m_psc
srctip_4x20m        launching_apron     mr5_lc29_4x30m      skew15_3x18m
```

Run: `python tests/e2e/run_e2e.py` → **28/28 ★ ACCEPTED ★**

---

## IRC/MORTH Compliance

### Validation Rules (30 implemented, 150 specified)

| Category | Count | Examples |
|----------|-------|---------|
| Critical (C01–C25) | 25 | Project phase set · bridge category assigned · span/depth coherent · scour > 0 |
| Warning (W01–W05) | 5 | Deck width > 15m · pier height > 20m · span > 50m · skew > 30° |

### Standards Implemented

| Standard | Module | Coverage |
|---------|--------|---------|
| IRC:5-2015 | `standards/irc_05.py` | Lacey regime · scour depth · afflux · freeboard |
| IRC:21/IRC:112 | `standards/irc_21.py` | Span/depth ratios · cover · impact factor · deflection |
| IRC SP:55-2019 | `standards/irc_sp55.py` | 53 layers · scales · text heights · lineweights · hatching |
| MORTH 5th Rev | `standards/morth_specs.py` | Concrete/rebar specs · test frequencies · contract clauses |

---

## Release Verification

```bash
python rc1_smoke.py
# Checks: version strings (9 packages) · CLI · FastAPI · AI optimizer ·
#         DB tables · 28 E2E fixtures · bridgecad --version
# Result: 34/34  ★ ACCEPTED ★  exit 0
```

---

## License

MIT © BridgeCAD Team 2026. See [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

See [SECURITY.md](SECURITY.md) for responsible disclosure policy.
