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

**Workbook workflow:** generate the workbook as described in §5. The separate PWD booklet CLI also accepts validated catalogue overrides and sweeps; it is not a replacement Excel schema. See the supplement below.

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

---

## 12. Format and layout choice

BridgeCAD supports **three output formats** and two layout modes for every project.

### Output format

| Format | Command | Notes |
|---|---|---|
| **DXF** (default) | `bridgecad draw booklet bridge.xlsx -o out/` | Full 9-sheet package. Open in AutoCAD, BricsCAD, LibreCAD or the [A360 viewer](https://viewer.autodesk.com). |
| **PNG preview** | `python scripts/render_asset_pack.py out/ --out out/png` | 150–200 dpi raster; for checking geometry without a CAD viewer. |
| **PDF** | `bridgecad export all bridge.xlsx -o out/` | Included in the ZIP bundle alongside DXF + BOQ + QA report. |

In the **Streamlit console** (§3) the "📐 Drawing Gen" tab offers a **scale selector** (Auto / 1:50 / 1:100 / 1:200 / 1:500) and a **format toggle** (DXF-only or DXF + PNG preview). The ZIP download always contains both.

In the **deployed workspace** the same two choices live in the **Format & variants** dock: format chips (DXF / PDF / PNG) are passed to the engine as `?output_format=`, and the plot-scale chips are passed as `?scale=` (omitted when set to Auto so the ladder decides).

### Layout / scale selection

The drawing engine picks the **largest standard IRC SP:55 scale rung** (50 / 75 / 100 / 150 / 200 / 250 / 300 / 400 / 500) that keeps text ≥ 2.5 mm and annotation gaps ≥ 8 mm per pier. For very long bridges (e.g. 270 m 9-span) it falls to 1:500 and splits Sheet 2 into two horizontal bands with match-lines.

Override the scale on the CLI:
```powershell
bridgecad draw booklet bridge.xlsx -o out/ --scale 200
```
Or in the Streamlit console: select the "Plot scale" dropdown before clicking **Generate**.

### Which drawing set for which purpose

| Purpose | Recommended set | Notes |
|---|---|---|
| Tender submission | Full 9-sheet DXF + PDF | Generated by `bridgecad export all` |
| Site reference | Sheet 1 (plan) + Sheet 2 (long section) + Sheet 5 (pier/abutment) | Extract from the ZIP |
| Design check | Sheet 3 (cross-section) + Sheet 5 + Sheet 8 (end elevations) | Contains all structural dimensions |
| BOQ pricing | Sheet 7 (BOQ) + `boq.xlsx` | The DXF BOQ and the Excel file are equivalent |
| QA review | `qa.html` + Sheet 7 | The HTML report cites every IRC clause |

---

## 13. Varying parameters for a standard bridge type (PWD Generator)

The **PWD Generator** tab in the Streamlit console (§3) lets you pick any of the
15 Maharashtra PWD standard bridge types and vary its parameters interactively.
No Excel workbook needed — the catalogue provides the base values.

The deployed workspace exposes the same variable surface: the **Drawing
workspace** dock holds the FREE dials (project identity, `Spans`,
`Span length (m)`, `Deck width (m)`, `Datum (m)`, plus the twelve foundation and
wing-wall detail fields) and the **Format & variants** dock carries the class
reference plus the format/scale controls. The booklet identity
(`foundation_type`, `superstructure_type`, `bearing_type`) stays LOCKED, and the
catalogue's DERIVED values are recalculated on every edit.

### How it works

```
Type card (booklet-faithful baseline)
    +  Engineer overrides (FREE dials)
    ↓
Resolver → auto-derives total_length, soffit, bearing_type, pier_count
    ↓
Constraint check (freeboard, SBC, span/depth)
    ↓
9-sheet DXF package → download
```

### Variable classes

| Class | Meaning | Examples |
|---|---|---|
| **FREE** | Engineer's dials — full range with IRC clause bounds | `span_length_m`, `pier_height_m`, `skew_deg`, `carriageway_width` |
| **LOCKED** | Booklet identity — fixed for the standard type, editable only with `--force` | `foundation_type`, `superstructure_type`, `bearing_type` |
| **DERIVED** | Auto-calculated — never type by hand | `total_length_m`, `soffit_level`, `pier_count`, `bearing_type` |

### Sweeping a variable (CLI)

```powershell
# Vary pier height from 6 to 12 m in 3 m steps for type 001
python scripts/generate_all_pwd_gads.py \
    --type BR-I-2022-001 \
    --sweep pier_height_m=6:12:3

# Change span length and carriageway together
python scripts/generate_all_pwd_gads.py \
    --type BR-I-2022-007 \
    --set span_length_m=18 \
    --set carriageway_width=11.0

# Dry run — resolve and print without generating DXF
python scripts/generate_all_pwd_gads.py \
    --type BR-I-2022-010 \
    --sweep pier_height_m=10:16:2 \
    --dry-run
```

### FREE variable reference

| Variable | Unit | Range | IRC clause |
|---|---|---|---|
| `span_length_m` | m | 6 – 50 (step 0.5) | IRC 112 Table 12.1 |
| `span_count` | — | 1 – 12 | IRC 5 cl.101 |
| `carriageway_width` | m | 3.5 / 7.5 / 11.0 | IRC 73 |
| `footpath_width` | m | 0 – 2.0 (step 0.25) | IRC 103 |
| `skew_deg` | ° | 0 – 30 (step 5) | IRC 5 cl.101.3 |
| `pier_height_m` | m | 3 – 25 | site datum |
| `pier_shaft_width_m` | m | 0.8 – 3.0 (step 0.1) | IRC 112 cl.16 |
| `deck_thickness_mm` | mm | 200 – 900 (step 25) | IRC 112 |
| `girder_depth_mm` | mm | 600 – 3000 (step 50) | IRC 112 |
| `hfl_m` | m RL | 0 – 1000 | PSD |
| `freeboard_m` | m | 0.6 – 4.0 (step 0.05) | IRC 5 cl.104 |
| `scour_depth_m` | m | 0.5 – 8.0 | IRC 78 cl.703 |
| `pile_diameter_mm` | mm | 1000 / 1200 / 1500 | IRC 78 cl.709 |
| `pile_length_m` | m | 6 – 45 (step 0.5) | IRC 78 cl.709 |
| `sbc_t_per_m2` | t/m² | 10 – 200 | IRC 78 cl.701 |

---


## PWD drawing selection, variables, layout and verification

For the 15 reference configurations, page mapping, supported CLI keys, units,
code-declared ranges and layout-selection steps, use
[BRIDGECAD_SUPPLEMENTARY_PATCH.md](BRIDGECAD_SUPPLEMENTARY_PATCH.md).
The root [master guide](../GUIDE.md) remains authoritative.

Choose foundation and superstructure identity before changing free variables.
Keep derived levels and lengths read-only. Preserve approximation warnings for
004/014/015. Example, from the repository root:

```powershell
python scripts/generate_all_pwd_gads.py --type BR-I-2022-009 --sweep carriageway_width=3.5,7.5,11 --dry-run
python scripts/generate_all_pwd_gads.py --type BR-I-2022-006 --sweep pier_height_m=6:12:3
```

Choice fields use comma lists; continuous ranges use `lo:hi:step`.
Overrides write `out/pwd_sweep`, not the baseline `EXAMPLES_PWD` corpus.
Rejected variants make the batch unsuccessful even if some jobs resolve.
Requested PNG renders must be nonblank; a render error or all-white result
fails the package. `SKIP_PNG=1` is a DXF-only check and is recorded as skipped
in `render-status.json`. It must not be used to claim raster/PDF fidelity.

Paper format is a presentation choice, not a geometry override. Match the
reference page, reserve notes/tables/title-block space and fit each viewport
independently. Check print text height and clipping. The companion workspace
prepares scenarios and CLI commands; it cannot run local Python or deliver
browser CAD generation until connected to the existing backend.

See [V_INSTRUCTIONS_APPLIED.md](V_INSTRUCTIONS_APPLIED.md) for which uploaded
instructions were applied, already present, or left open with reasons.
