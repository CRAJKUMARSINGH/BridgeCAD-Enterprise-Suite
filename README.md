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
  baseline is preserved verbatim under `references/lisp/` and audited in
  [docs/lisp-baseline.md](docs/lisp-baseline.md) — see
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
  — the starting point. The geometric basis was diluted during the suite
  enhancement; abutment cap, dirt wall and wearing-coat extents are now
  re-derived from the reference above rather than from the LISP.

---

## 🤝 Contributing · 📞 Support · 📜 Licence

See **[CONTRIBUTING.md](CONTRIBUTING.md)**.

Issues: https://github.com/CRAJKUMARSINGH/BridgeCAD-Enterprise-Suite/issues —
tag `support` for help, `rks-legal` for professional-services enquiries.

MIT — see [LICENSE](LICENSE).

---

**⭐ If this saves you a drawing set, star the repo — it is the fastest way to
help another bridge engineer find it.**
