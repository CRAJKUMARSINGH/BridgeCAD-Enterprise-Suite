# Getting Started with BridgeCAD Enterprise Suite

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | ≥ 3.11 | 3.12 also supported |
| pip | ≥ 23.0 | `pip install --upgrade pip` |
| Node.js | ≥ 20 | For React web console only |
| Docker | ≥ 24 | For production deployment only |
| ezdxf | ≥ 1.4.0 | Installed automatically |
| openpyxl | ≥ 3.1 | Installed automatically |
| scipy | ≥ 1.12 | Installed automatically |

---

## Installation

### Step 1 — Clone the repository

```bash
git clone https://github.com/bridgecad/enterprise-suite
cd "BridgeCAD Enterprise Suite"
```

### Step 2 — Install Python packages

```bash
pip install --upgrade pip
for pkg in packages/*/pyproject.toml; do
    pip install -e "${pkg%/pyproject.toml}"
done
```

On Windows (PowerShell):

```powershell
foreach ($pkg in Get-ChildItem packages\*\pyproject.toml) {
    pip install -e $pkg.DirectoryName
}
```

### Step 3 — Verify installation

```bash
python rc1_smoke.py
# Expected: 34/34  ★ ACCEPTED ★  exit 0
```

---

## Your First GAD Drawing

### Step 1 — Get a blank template

```bash
bridgecad template new simple_12m -o my_bridge.xlsx
```

This generates a 14-sheet Excel workbook pre-filled with sensible defaults for a 12m RCC T-Beam bridge.

### Step 2 — Fill in your project data

Open `my_bridge.xlsx` in Microsoft Excel or LibreOffice Calc. The 14 sheets are:

| Sheet | What to fill |
|-------|-------------|
| `PROJECT_MASTER` | Project title, code, chainage, client, consultant, revision |
| `BRIDGE_SELECTION` | Bridge category, type, span count, loading class, seismic zone |
| `GEOMETRY_INPUT` | Span lengths, carriageway width, footpath, skew, camber |
| `SUPERSTRUCTURE` | Deck grade, thickness, girder type/depth/spacing |
| `SUBSTRUCTURE` | Pier type, abutment type, wing walls, approach slab |
| `FOUNDATION_DETAILS` | Foundation type, pile dia/length, pile count |
| `APPROACHES` | Approach lengths, embankment, speed limit |
| `HYDRAULIC_DATA` | HFL, LWL, scour level, design discharge, return period |
| `MATERIALS` | Concrete grades, rebar, prestress, bearing type |
| `BEARINGS_JOINTS` | Bearing schedule (tabular), expansion joint schedule |
| `COMPONENTS_LIB` | Standard component tags |
| `DRAWING_CONTROL` | Output formats, scale, sheet size |
| `CALCULATIONS` | Auto-computed (read-only) |
| `VALIDATION` | Auto-computed (read-only) |

**Yellow cells** = input (you edit these).  
**Grey cells** = calculated (auto-populated, do not edit).

### Step 3 — Validate

```bash
bridgecad validate my_bridge.xlsx --report QA.html
```

This runs 30 IRC/MORTH compliance checks and writes an HTML report. Fix any **Critical** failures before drawing.

### Step 4 — Generate 7-sheet DXF package

```bash
bridgecad draw gad my_bridge.xlsx -o ./output/drawings
```

Opens `./output/drawings/` with 7 DXF files:

```
my_bridge_Sheet1_Plan.dxf
my_bridge_Sheet2_LongSection.dxf
my_bridge_Sheet3_CrossSection.dxf
my_bridge_Sheet4_Foundation.dxf
my_bridge_Sheet5_PierAbutment.dxf
my_bridge_Sheet6_BearingsJoints.dxf
my_bridge_Sheet7_BOQ.dxf
```

Open in AutoCAD, BricsCAD, ZWCAD, or any ezdxf-compatible viewer.

### Step 5 — Generate priced BOQ

```bash
bridgecad bill gen my_bridge.xlsx -o ./output/bill --state MH
```

Produces `my_bridge_BOQ.xlsx` and `my_bridge_BOQ.csv` with quantities and Maharashtra PWD rates.

### Step 6 — Full export bundle

```bash
bridgecad export all my_bridge.xlsx -o ./output
```

One ZIP containing DXF drawings + BOQ + QA HTML report + manifest.json.

---

## Using the Streamlit UI

```bash
cd apps/streamlit-ui
streamlit run app.py
```

Then open `http://localhost:8501`. The **15 tabs** cover:

| Tab | Action |
|-----|--------|
| 🏠 Home | Status dashboard |
| 📁 Load Project | Upload xlsx → view metadata |
| ✅ Validate | Run 30 QA checks + download HTML report |
| 📐 Drawing Gen | Generate 7-sheet DXF → download ZIP |
| 📊 QA Report | Interactive compliance report |
| 💰 BOQ | Generate + view priced BOQ with charts |
| 📦 Export Bundle | Full pipeline → ZIP download |
| 🔌 Plugins | Browse available bridge-type plugins |
| 📋 Templates | Download blank templates |
| 🏗️ Geometry | Visualise plan/long-section/cross-section values |
| 🌊 Hydraulics | View IRC:5 hydraulic parameters |
| 📄 Standards | IRC/MORTH quick reference |
| 🔁 History | Generation history (M8+) |
| ⚙️ Settings | Configure API URL, output paths |
| ❓ Help | Full documentation |

---

## Using the FastAPI

```bash
cd apps/api-gateway
uvicorn bridgecad_api.main:app --reload --port 8000
```

Interactive docs at `http://localhost:8000/docs`.

Key endpoints:

```
POST /bridges/parse     → upload xlsx → project metadata JSON
POST /bridges/validate  → upload xlsx → 30-check QA JSON
POST /draw/gad          → upload xlsx → DXF ZIP download
POST /bills/generate    → upload xlsx → BOQ JSON
POST /qa/report         → upload xlsx → HTML report download
POST /exports/bundle    → upload xlsx → full ZIP download
GET  /plugins/          → list all plugins
GET  /plugins/{id}      → plugin detail + typical values
```

---

## Bridge-Type Plugins

Plugins provide default values and descriptions for standard bridge types:

```bash
bridgecad plugin list
# ID                   Name                  Spans
# rcc_tbeam            RCC T-Beam Bridge     6–30m
# psc_igirder          PSC I-Girder Bridge   20–45m
# box_culvert          RCC Box Culvert       2–8m

bridgecad plugin info psc_igirder
```

---

## Production Deployment (Docker)

```bash
cp .env.example .env
# Edit .env — change POSTGRES_PASSWORD, REDIS_PASSWORD, BRIDGECAD_API_KEYS

docker compose -f docker-compose.prod.yml up -d

# Services:
# API Gateway:  http://localhost:8000
# Streamlit UI: http://localhost:8501
# React Console:http://localhost:80
# PostgreSQL:   localhost:5432
# Redis:        localhost:6379
# MinIO:        http://localhost:9001 (console)
```

---

## IRC Standards Used

| Standard | Version | Coverage |
|----------|---------|---------|
| IRC:5 | 2015 | Hydraulic design, Lacey scour, waterway |
| IRC:6 | 2017 | Loads and stresses, impact factor, seismic |
| IRC:21 | 2000 | Span/depth ratios, concrete cover |
| IRC:78 | 2014 | Foundations, scour depth multipliers |
| IRC:83 | 2018 | Bearings (elastomeric / POT-PTFE) |
| IRC:112 | 2020 | Concrete road bridges — comprehensive |
| IRC SP:13 | 2004 | Culverts and small bridges |
| IRC SP:55 | 2019 | Drawing quality systems, layer naming |
| MORTH 5th Rev | 2013+ | Contract specifications, QA framework |
| IS:456 | 2000 | Plain and reinforced concrete |
| IS:1786 | 2008 | High-strength deformed bars |
| IS:2911 | 2010 | Pile foundations |

---

## FAQ

**Q: Can I use this for actual bridge design submissions?**  
A: BridgeCAD produces GAD-level drawings (concept / tender stage). Structural calculations for detailed design must be done by a licensed engineer using approved analysis software (SAP2000, MIDAS Civil, etc.).

**Q: Which DXF version is output?**  
A: R2018 by default (configurable to R2000–R2024 via `DRAWING_CONTROL.autocad_version`).

**Q: Can I add a custom bridge type?**  
A: Yes — see [CONTRIBUTING.md](../CONTRIBUTING.md#adding-a-new-bridge-type-plugin).

**Q: Does it generate reinforcement drawings?**  
A: The BOQ includes rebar quantities. Reinforcement drawing generation (bar marks, BBS) is planned for M11+.

**Q: Is there a web demo?**  
A: The Streamlit UI can be deployed publicly. See `docker-compose.prod.yml` for the full stack.
