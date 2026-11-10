# 🌉 BridgeCAD Enterprise Suite

[![version](https://img.shields.io/badge/version-0.1.0--rc1-blue.svg)](CHANGELOG.md)
[![python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![license](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![suite-ci](https://github.com/CRAJKUMARSINGH/BridgeCAD-Enterprise-Suite/actions/workflows/suite-ci.yml/badge.svg)](https://github.com/CRAJKUMARSINGH/BridgeCAD-Enterprise-Suite/actions/workflows/suite-ci.yml)

**One parametric Excel workbook in. An 8-sheet standards-compliant bridge GAD
package, priced Bill of Quantities, and QA compliance report out.**

Built on IRC 5 / 6 / 21 / 83 / SP:55 / SP:114 and the MORTH 2024-25 schedule of
rates. Runs as a CLI, an HTTP API, a Streamlit console, and a React web app.

**Why it's different**

- 🧾 **The workbook is the only contract.** One Excel template is the whole input
  surface — no bespoke config, no per-project scripts. → [docs/excel-contract.md](docs/excel-contract.md)
- 📐 **Traceable, not generated-and-forgotten.** Every BOQ line carries its
  inputs and every export manifest states plainly that output is
  *"Generated — not reviewed for construction."*
- 🔍 **Gated by proof, not by promise.** Golden models are pinned byte-for-byte,
  architecture invariants are enforced by import-linter, and each documentation
  guard is itself proven able to fail.

> **Read [GUIDE.md](GUIDE.md) next.** It is the authoritative document. If
> anything here contradicts it, the guide wins.

---

## ⚠️ Repo orientation — read before you `cd` anywhere

**The Suite lives at the repository root.** There is no subfolder to descend
into. Older docs telling you to `cd` into a legacy `BridgeCAD Enterprise Suite`
subfolder are stale.

| Generation | Location | Status | Entry point |
|---|---|---|---|
| **BridgeCAD Enterprise Suite** | repo root | ✅ **ACTIVE** · v0.1.0-rc1 | `python -m bridgecad` |
| Ultimate Bridge GAD Generator | `streamlit_app_ultimate.py` + `src/bridge_gad/` | 🏛️ LEGACY | `streamlit run streamlit_app_ultimate.py` |
| Lean Bridge GAD Generator | `app_lean.py` | 🧪 SIDE TOOL | `streamlit run app_lean.py` |

---

## ⚡ Quick start

```bash
git clone https://github.com/CRAJKUMARSINGH/BridgeCAD-Enterprise-Suite.git
cd BridgeCAD-Enterprise-Suite

# No install needed — sitecustomize.py bootstraps the workspace
python -m bridgecad verify      # run the acceptance verifiers
python -m bridgecad info        # interpreter, repo root, resolved paths
```

Then, to produce something real:

```bash
pip install -e ".[dev]"
bridgecad-cli template new --type simple_12m -o bridge.xlsx
bridgecad-cli draw booklet bridge.xlsx -o out/
```

Full paths (dev install, Docker, API, React console) → **[docs/getting-started.md](docs/getting-started.md)**

---

## 🚦 Status — read this before quoting output

This is a **release candidate**. Per the project's release rule, generated
drawings and BOQs are **not construction-ready** until CI is green, all 28 E2E
fixtures emit pinned pass/fail JSON, all 8 sheets pass structural checks with
engineer visual review, and every BOQ line carries traceable inputs.

Until then, every export manifest carries
**"Generated — not reviewed for construction."**

| Area | State |
|---|---|
| Excel → model | ✅ complete |
| Sheet 1 (plan) | ✅ complete geometry |
| Sheets 2–7 | 🚧 scaffolds |
| BOQ pricing | 🚧 heuristic multipliers |
| QA rules | 🚧 30 of 150 implemented |
| CLI · API · Streamlit · React | ✅ all four |
| 28 E2E fixtures | ✅ 28/28 |

Full list → **[GUIDE.md §11](GUIDE.md)**

---

## 🏗 What's in the box

**9 packages** — `core` (models, geometry, validation) · `io` (Excel/CSV/JSON) ·
`draw` (8 sheets, 53 IRC layers) · `bill` (MORTH rates, 4 formatters) ·
`qa` (150 rules, 0–100 grade) · `export` (orchestrator, ZIP, manifest) ·
`plugins` (bridge-type registry) · `ai` (optimiser, estimator, comparator) ·
`infra` (db, cache, auth, logging)

**4 interfaces** — Typer CLI (10 command groups) · FastAPI (7 routers) ·
Streamlit (15 tabs) · React console (6 pages)

**Standards** — IRC 5 · 6 · 21 · 83 · SP:55 · SP:114 · MORTH 2024-25 rates

Architecture and invariants → **[ARCHITECTURE.md](ARCHITECTURE.md)** · in depth → **[GUIDE.md §3](GUIDE.md)**

---

## 🧪 Verify it works

```bash
python -m bridgecad verify      # day3 (7/7) + day4 (8/8)
python rc1_smoke.py             # 11-check release gate
python tests/e2e/run_e2e.py     # 28 fixtures × 7 checks
pytest tests/integration        # 12/12 full pipeline
make lint && make test
```

---

## 📚 Documentation

| Start here | Then |
|---|---|
| **[GUIDE.md](GUIDE.md)** — master guide | [DOCS_INDEX.md](DOCS_INDEX.md) — every doc, indexed |
| [docs/getting-started.md](docs/getting-started.md) | [docs/excel-contract.md](docs/excel-contract.md) |
| [docs/standards.md](docs/standards.md) | [docs/plugin-authoring.md](docs/plugin-authoring.md) |
| [docs/deployment.md](docs/deployment.md) | [docs/troubleshooting.md](docs/troubleshooting.md) |
| [MASTER_ROADMAP.md](MASTER_ROADMAP.md) — plan-level status | [CHANGELOG.md](CHANGELOG.md) — released history |
| [CREAT.md](CREAT.md) — rolling 24h hand-off log | [README_RAJKUMAR.md](README_RAJKUMAR.md) — operator handbook |

---

## 📐 Engineering references

Abutment/dirt-wall detailing and drainage practice is cross-checked against:

- **Dirt Wall in Bridge Abutment** — purpose, weep-hole / geotextile-filter
  drainage, layered granular backfill and MSE reinforcement, and the
  pile → cap → abutment → abutment-cap → dirt-wall construction sequence:
  <https://prewallcivil.com/dirt-wall-in-bridge-abutment/>

- **Abutment Cap in Bridge Construction** — cap depth, bearing-shelf
  projection, pedestal and the cap → dirt-wall interface:
  <https://prewallcivil.com/abutment-cap-in-bridge-construction/>

- **Original LISP baseline** — [Explanation of LISP code for Solid Slab GAD](https://www.yogipwd.com/2023/05/explanation-of-lisp-code-for-solid-slab.html):
  the AutoLISP source this project started from. The LISP solid-slab baseline
  was diluted during enhancement; abutment/dirt-wall/wearing-coat geometry is
  now re-derived from the reference above rather than from the LISP. The
  whole AutoLISP listing is preserved **in toto** in
  [`ATTACHED ASSETS/LISP_Solid_Slab_GAD_In_Toto.lsp`](ATTACHED%20ASSETS/LISP_Solid_Slab_GAD_In_Toto.lsp),
  the raw blog text in `ATTACHED ASSETS/yogipwd_lisp_solid_slab_gad_original.txt`,
  and a verbatim baseline under `references/lisp/`. The architectural drift is
  audited in [docs/lisp-baseline.md](docs/lisp-baseline.md) — see
  `python scripts/refs_lisp.py references/lisp/*.lsp` for the inventory.

- **Peer implementation — nxstructural** — a design-to-drawing workflow worth
  studying for clause-anchored checks printed on the sheet, bidirectional
  rebar editing, live preview and BBS (IS 456 / IS 800 / IRC 112 / IRC 58 /
  IRC 37): <https://www.nxstructural.com/>

---

## 🚀 Deploy

```bash
cp .env.example .env
docker compose up api                  # API on :8000, health at /health
docker compose -f docker-compose.prod.yml up -d   # full prod stack
```

→ **[docs/deployment.md](docs/deployment.md)**

---

## 🧭 Continuity

Working-session hand-off lives in **[CREAT.md](CREAT.md)** and keeps only the
last 24 hours — append the new entry, delete the stale portion.

> **Standing order — chat-log cadence.** The session chat log in
> [CREAT.md](CREAT.md) is refreshed **every 12 minutes** for the duration of an
> active session, so the hand-off never trails the work by more than one cadence.
> The order is stated here **and** at the top of [CREAT.md](CREAT.md) so neither
> copy is the single point of loss.

`Attached_Folder/`, `Test_Files/`, and any "how to use" guide are exempt from
duplicate-file removal. Durable history belongs in [CHANGELOG.md](CHANGELOG.md).

---

## 🙏 Shout-outs

Standing on: **Pydantic** and **FastAPI** (contracts and gateway) · **ezdxf**
(DXF authoring) · **Typer** and **Rich** (CLI) · **Streamlit**, **React**,
**Vite** and **Tailwind** (the two consoles) · **pytest** and **mypy** (the
gates) · **import-linter** (the architecture invariants).

### Geometry references

- **Dirt wall / abutment cap**: [Dirt Wall in Bridge Abutment — PreWall Civil](https://prewallcivil.com/dirt-wall-in-bridge-abutment/)
  — source for the dirt-wall-as-back-wall definition, its position at the rear
  of the cap, and the drainage (weep hole + filter) requirement.
- **Original LISP baseline**: [Explanation of LISP code for Solid Slab GAD](https://www.yogipwd.com/2023/05/explanation-of-lisp-code-for-solid-slab.html)
  — the AutoLISP routine by **Shri. P.M. Baviskar, Executive Engineer, Design Division
  Nashik (Bridge)** that is the direct ancestor of BridgeCAD Enterprise Suite. The
  complete AutoLISP listing — saved **in toto** from the article, with the basic
  guiding principles carried in its header — is in
  [`ATTACHED ASSETS/LISP_Solid_Slab_GAD_In_Toto.lsp`](ATTACHED%20ASSETS/LISP_Solid_Slab_GAD_In_Toto.lsp),
  with the function-by-function analysis and the 14 guiding principles in
  [`ATTACHED ASSETS/LISP_Solid_Slab_GAD_Complete_Archive.md`](ATTACHED%20ASSETS/LISP_Solid_Slab_GAD_Complete_Archive.md).

---

## 📐 LISP Baseline — Guiding Principles

BridgeCAD is a **direct evolution** of Shri. Baviskar's `gad.lsp`, rewritten in
Python + ezdxf but honouring every geometric principle the LISP pioneered.
The full archive is in `ATTACHED ASSETS/`. The 14 principles:

| # | Principle | LISP origin | BridgeCAD module |
|---|---|---|---|
| P1 | Single input file → all geometry | `opn()` reads `gad.txt` | 14-sheet Excel → `bridgecad_io` |
| P2 | Datum at bottom, all RLs from one reference | `datum` in `reed()` | `resolve_abutment_stack()` |
| P3 | Metres in, millimetres out (`×1000`) | `vvs = 1000/vs` | `sc_h`, `sc_v` in every sheet |
| P4 | Skew propagates to every plan dimension (`÷cos θ`) | `capwsq = capw/c` | `bridgecad_core.skew.support_line()` |
| P5 | Wearing coat end-to-end, never breaks at joints | WC runs left approach → deck → right approach | `sheet2`: continuous WC over both approach slabs |
| P6 | Abutment = 14-vertex battered polygon, not rectangle | `abt1()` LISP function | `battered_side_outline()`, `ABUT-PROF` layer |
| P7 | Independent batters: river face gentle, earth face steep | `face_batter_1n` / `back_batter_1n` | `abutment_profiles.py` |
| P8 | Dirt wall is a separate element (back wall) | `DWTH` / backwall thickness | `SUB-DIRT-WALL` layer, `dirt_wall_thickness_mm` |
| P9 | Cap projects both faces: bearing shelf front, dirt-wall seat rear | `capw` projections | `abutment_cap_projection_front/rear_mm` |
| P10 | Dimension style set once, globally | `st()` → `pmb100` style | `LAYER_REGISTRY`, `dim_linear_h/v` |
| P11 | Span loop: all spans in `while <= nspan` | `(while (<= a nspan) ...)` | `for i, slen in enumerate(span_lens)` |
| P12 | Footing rectangle: founding RL + depth + width | `futrl`, `futd`, `futw`, `futl` | `FoundationDetails.pile_cutoff_level_m` |
| P13 | Every element is dimensioned | `DIMLINEAR` after every shape | `dim_along()` with `ViewAxis` enforcement |
| P14 | Section view at different scale | `v2pos()`/`h2pos()` with `sc` ratio | `sheet3_cross_section.py` scale_denom=50 |

> The LISP solid-slab geometric basis was diluted during early enhancement.
> All 14 principles are now **fully restored** in BridgeCAD v0.1.0-rc1.
> See [`ATTACHED ASSETS/LISP_Solid_Slab_GAD_Complete_Archive.md`](ATTACHED%20ASSETS/LISP_Solid_Slab_GAD_Complete_Archive.md)
> for the complete function-by-function analysis.

---

## 📜 LISP Baseline — Article Principles (function-by-function)

The 14 principles above are the **engineering laws**. This table is the
**basic guiding principles as written in the source article** — one row per
AutoLISP function of `gad.lsp` by **Shri. P.M. Baviskar** — with the BridgeCAD
drawing code that carries each segment. Source:
[Explanation of LISP Code for Solid Slab GAD Drawing](https://www.yogipwd.com/2023/05/explanation-of-lisp-code-for-solid-slab.html).

| LISP routine | What the article draws | Basic guiding principle | Drawing segment in BridgeCAD |
|---|---|---|---|
| `opn()` | Opens `gad.txt` read-only. | One flat input file drives the whole drawing. | Excel workbook contract → `bridgecad_io` |
| `reed()` | Reads `scale1`, `scale2`, `skew`, `datum`, `toprl`, `left`, `right`, `xincr`, `yincr`, `noch`; `hs=vs=1`; `vvs=hhs=1000/vs`; `skew1 = skew × 0.0174532`; `s`, `c`, `tn = s/c`; `sc = scale1/scale2`. | Read every parameter once; metres → mm and degrees → radians. | `bridgecad_core` geometry + `sc_h`/`sc_v` |
| `vpos(a)` | `a = (a − datum)·vvs + datum` | All levels share **one datum**. | `resolve_abutment_stack()` |
| `hpos(a)` | `a = (a − left)·hhs + left` | All chainages share **one start chainage**. | `ViewAxis` chainage map |
| `v2pos()` / `h2pos()` | `vpos`/`hpos` then `× sc` | A section view is drawn at a **different scale** via one ratio. | `sheet3` `scale_denom=50` |
| `st()` | Arial; `DIMASZ 150`, `DIMDEC 0`, `DIMEXE 400`, `DIMEXO 400`, `DIMLFAC 1`, `DIMTXSTY Arial`, `DIMTXT 400`, `DIMTAD 0`, `DIMTIH 1`; saved as `pmb100`. | Dimension style is set **once, globally**. | `LAYER_REGISTRY` + `dim_linear_h/v` |
| `layout()` | OSNAP off; X/Y axes + two lines parallel to X; labels `BED LEVEL`, `CHAINAGE`; Y ticks arrayed over `toprl − datum`; RL text every `yincr`; chainage text + ticks every `xincr`. | The **elevation plotting grid** — axes, levels, chainage — is drawn first and separately. | `sheet2_long_section.py` |
| `cs()` | Per point: print RL always, chainage at increments; small ticks; line from axis to datum; connect `(hpos x, vpos y)` into the profile. | The **river cross-section** is a polyline through the surveyed chainage/RL points. | long-section bed profile |
| `pier()` | Reads `nspan`, `lbridge`, `abtl`, `RTL`, `rtl2 = RTL − 30·sc`, `Sofl`, `kerbw`, `kerbd`, `ccbr`, `slbthc/slbthe/slbtht`, `capt/capb/capw`, `piertw`, `battr`, `pierst`, `piern`. | The **pier** is drawn in elevation, plan **and** side view from one parameter block. | `sheet4_foundation.py`, `sheet5_pier_abutment_details.py` |
| abutment (§6) | Point calculation → `line` commands → summary. | The **abutment** is built from computed points (battered outline), not a fixed shape. | `battered_side_outline()`, `abutment_profiles.py` |

> The **complete AutoLISP listing** behind this table is saved **in toto** at
> [`ATTACHED ASSETS/LISP_Solid_Slab_GAD_In_Toto.lsp`](ATTACHED%20ASSETS/LISP_Solid_Slab_GAD_In_Toto.lsp)
> — every routine (`opn`, `reed`, `vpos/hpos`, `v2pos/h2pos`, `st`, `layout`,
> `cs`, `pier`, `pt/p2t`, `abt1`) in article order, with the 14 **basic guiding
> principles** carried as a header comment block so the drawing code and its
> ancestor travel together.

> **Derived module map (unverified).** A separate 8-row module map
> (`c:GAD_INIT … c:GEN_TEXT`) that was pasted in from an outside/generated source
> is kept at
> [`ATTACHED ASSETS/GAD_Module_Mapping_Derived_Unverified.md`](ATTACHED%20ASSETS/GAD_Module_Mapping_Derived_Unverified.md).
> It does **not** describe the archived `gad.lsp` — none of its function names
> exist in the preserved source — so it is stored as a *derived/aspirational* map
> only, and must not be read as the source record.

---

## 🤝 Contributing · 📞 Support · 📜 Licence

See **[CONTRIBUTING.md](CONTRIBUTING.md)**.

Issues: https://github.com/CRAJKUMARSINGH/BridgeCAD-Enterprise-Suite/issues —
tag `support` for help, `rks-legal` for professional-services enquiries.

MIT — see [LICENSE](LICENSE).

---

**⭐ If this saves you a drawing set, star the repo — it is the fastest way to
help another bridge engineer find it.**
