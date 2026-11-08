# BridgeCAD Enterprise Suite — User Manual

**Version:** v0.1.0 · **License:** BRIDGECAD-OSS-1.0 · **Standard:** IRC / MoRTH

The current, task-oriented manual. For the retired `.exe` product see
[Bridge_GAD_User_Manual.md](Bridge_GAD_User_Manual.md) (legacy — do not use).

---

## 1. What this software does

BridgeCAD turns a **single Excel workbook** into a full bridge drawing and
documentation package:

- 9-sheet DXF drawing package (GAD, long section, cross-section, foundation,
  pier/abutment details, bearings/joints, BOQ, side elevations, reinforcement)
- Parametric abutment families — rectangular, cantilever/inverted-T, and
  **battered gravity abutments** with independent riverside/earthside batters
  (`abutment_face_batter_1n` / `abutment_back_batter_1n`, LISP `abt1()` 1:n)
- MoRTH-priced Bill of Quantities (Excel + CSV)
- IRC/MoRTH QA report (HTML)
- Bar bending schedule (CSV + Excel, IS 2502 column order)
- Export ZIP bundle + `manifest.json` audit trail

**The workbook is the only input contract.** Hand-building it is not supported —
generate it (see §5).

---

## 2. Install

Pick one path. Python **3.11–3.12** is recommended (3.14 may lack wheels).

### Path A — local virtualenv
```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[ui,refs]"
```

### Path B — Docker
```powershell
docker compose up --build
```

### Path C — zero-install preview
Download the built artifacts from the repository Releases page.

**Windows PATH trap.** Console scripts (`streamlit`, `mkdocs`) install to
`%APPDATA%\Python\PythonXXX\Scripts`, which is often not on PATH. If
`streamlit` is "not recognized", use the module form:
`python -m streamlit ...`. To fix permanently:
```powershell
[Environment]::SetEnvironmentVariable("Path",
[Environment]::GetEnvironmentVariable("Path","User") + ";$env:APPDATA\Python\Python314\Scripts","User")
```

---

## 3. The web console (Streamlit)

Start it:
```powershell
python -m streamlit run apps/streamlit-ui/app.py --server.port 8517
```

Wait for `Local URL: http://localhost:8517`, then open it.

The left sidebar lists **15 tabs**. Work them in this order:

| Order | Tab | Purpose |
|---|---|---|
| 1 | 🏠 Home | capability matrix; read-only |
| 2 | 📁 Load Project | **upload your `.xlsx`** (this is the upload box) |
| 3 | ✅ Validate | per-field `valid`/`warning`/`blocked`; fix all `blocked` |
| 4 | 📐 Drawing Gen | emit the 9-sheet DXF package |
| 5 | 📊 QA Report | IRC/MoRTH compliance score |
| 6 | 💰 BOQ Generator | priced bill (Excel + CSV) |
| 7 | 📦 Export Bundle | ZIP = DXFs + BOQ + QA + BBS + `manifest.json` |

Reference tabs: 🔌 Plugins · 📋 Templates · 🏗️ Geometry · 🌊 Hydraulics ·
📄 Standards · 🔁 History · ⚙️ Settings · ❓ Help.

> The upload widget accepts **`.xlsx` only** and lives under **📁 Load Project**.

The React console (`apps/web-console`) additionally exposes a
**Reinforcement** page that loads a workbook and patches abutment/bar fields
on blur, returning live checks + QA verdict per change.

---

## 4. Command-line interface

Command groups (run `bridgecad --help`):

| Group | Commands |
|---|---|
| *top-level* | `version` · `health` · `validate` · `calc-sheet` · `issue` · `diff` |
| `draw` | `gad` · `booklet` |
| `bill` | `gen` |
| `export` | `all` |
| `plugin` | `list` · `info` |
| `template` | `new` · `fill` |

Typical run:
```powershell
bridgecad validate bridge.xlsx
bridgecad draw booklet bridge.xlsx -o out/
bridgecad bill gen --input bridge.xlsx --format all
bridgecad export all bridge.xlsx -o out/
```

Output layout: `dxf/` (9 sheets) · `pdf/` · `boq.xlsx` · `qa.html` ·
`bbs.xlsx`/`bbs.csv` · `manifest.json` (keep this — it is the audit trail).

`bridgecad issue` / `bridgecad diff` manage the revision register and entity
fingerprints for drawing redlines.

---

## 5. The workbook

- **15 sheets (S01–S15)** — see [excel-contract.md](excel-contract.md) for
  every field.
- **Yellow cells are inputs**; calculated cells are locked.
- Generate a fresh, styled template with dropdowns + validation:
```powershell
python -c "import sys; sys.path.insert(0,'packages/bridgecad-io'); from bridgecad_io.excel_template import generate_template; generate_template('my_bridge.xlsx')"
```

### Sample workbooks
The intended demos live in [`public/samples/`](../public/samples) (served at
`/samples/`): `template_simple_12m.xlsx` (start here),
`template_continuous_3x12m.xlsx`, `template_girder_4x18m.xlsx`,
`template_box_culvert_8m.xlsx`, `template_arch_24m.xlsx`. A wider scenario set
is in [`templates/`](../templates) — `minor_bridges/`, `major_bridges/`,
`viaducts/`, `culverts/`, `robs_rubs_fobs/`.

---

## 6. The drawing viewer (GAD frontend)

The React sheet viewer renders sheets 01, 04 and 05 and is the place to inspect
abutment/pier geometry.

```powershell
cd frontend
npm install
npm run dev

# open http://localhost:5173
```

Controls: layer-visibility toggles, drawing-type presets, the IRC/MoRTH
compliance panel, and BOQ/geometry tabs.

---

## 7. Verifying an install

```powershell
python scripts/verify_docs.py          # docs: paths, integrity, selftest, links
python -m pytest tests/docs -q         # doc integrity tests
bridgecad health                       # API/engine health
```

Optional tools (`lychee`, `mkdocs`, `sphinx`) report as **skip**, never fail —
an absent binary is not a broken repo.

---

## 8. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `streamlit` not recognized | PATH — use `python -m streamlit run ...` (§2) |
| `ERR_CONNECTION_REFUSED :8517` | the server isn't running — start §3 first |
| Upload rejected | file must be `.xlsx`, not `.xls`/`.csv` |
| `validate` shows `blocked` | a required input is missing/inconsistent — read the message |
| Draw package "incomplete" | generation is all-or-nothing; one failed sheet fails the run |
| Robot gate looks green but nothing ran | if the walk crashed, the gate passes *vacuously* — confirm the server emitted its `Local URL` line first |

---

## 9. Where to go next

- [getting-started.md](getting-started.md) — first-bridge end-to-end
- [how-to-use-video.md](how-to-use-video.md) — walkthrough storyboard
- [excel-contract.md](excel-contract.md) — workbook schema
- [standards.md](standards.md) — IRC/MoRTH coverage
- [abutment-geometry.md](abutment-geometry.md) — datum stack
- Battered abutments: set `abutment_type = GRAVITY` (or `SEMI_GRAVITY`) on
  sheet S05 and give `abutment_face_batter_1n` / `abutment_back_batter_1n`
  (e.g. 10 river / 3 earth). Sheet 5 draws the LISP `abt1()` profile; larger
  `n` = gentler batter. Other abutment types keep the rectangular stack.
- [troubleshooting.md](troubleshooting.md) — deeper fault finding

---

## 10. Layers and drawing standards

Every sheet is drawn on ISO 13567-named layers. The standard set: `SUB-ABUT`,
`SUB-PIER`, `SUB-BEARING`, `ABUT-PROF`, `SUB-DIRT-WALL`, `SUPER-WEARING`,
`CIVIL-ROAD`, `STRUC-HATCHING`, `TEXT-HEADER`, `CL`, `FRAME`. Draw new
geometry only on these — see [drafting-standard.md](drafting-standard.md).

## 11. Transient output — never commit

These trees are **regenerable and must not be versioned** (this is the section
`.gitignore` cites):

`output/` · `outputs/detail/` · `reports/` · `artifacts/*.txt` ·
`artifacts/*.xlsx` · `wing_report.json` · `CODE-JUNCTION/` · `ATTACHED ASSETS/`

Tracked exemplars live under `outputs/<project>/` — keep those; ignore the
rest. The S1/S2 register `artifacts/TRIAGE_LOG.md` **is** tracked.
