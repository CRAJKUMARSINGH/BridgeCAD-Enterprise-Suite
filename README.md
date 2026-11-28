# BridgeCAD Enterprise Suite

Bridge General Arrangement Drawing (GAD) generation, QA, BOQ and export suite.

## ⚠️ STANDING ORDER — repository layout

1. **All code files live in folders** (`packages/`, `apps/`, `scripts/`, `tests/`, ...).
   No new code files at the repository root.
2. **The only exception is `CODE-JUNCTION/`.**
3. **`CODE-JUNCTION/` holds ONLY new enhancement guides and patches**, waiting to be
   applied. Once a patch is applied, tested and merged into its proper folder,
   **its guide and patch are DELETED from `CODE-JUNCTION/`.**

<a id="-standing-instructions--continuity-log-creatmd"></a>

## Standing instructions — continuity log (CREAT.MD)

Use [CREAT.MD](CREAT.MD) to hand off recent work between tools and engineers.
Keep only the last 24 hours. Put the newest entry first, summarize the work and
its verification, and remove older entries whenever you add a new one.

Preserve `CODE-JUNCTION/`, `ATTACHED ASSETS/`, and reference asset directories,
including when they are empty. The [release verification report](docs/verification/RELEASE_REPORT.md#consolidated-bridgecad-launch-instructions)
records the applicable launch instructions and their verification status.

## Original LISP and dirt-wall references

- [YogiPWD: explanation of Shri P. M. Baviskar's solid-slab GAD AutoLISP](https://www.yogipwd.com/2023/05/explanation-of-lisp-code-for-solid-slab.html?m=1).
  The preserved files are in `ATTACHED ASSETS/`. Preservation and static inventory
  are distinct from an executable, validated port.
- [Prewallcivil: dirt wall in bridge abutment](https://prewallcivil.com/dirt-wall-in-bridge-abutment/).
  Use this as contextual reading about retained fill and drainage, not as an
  approved dimensional, reinforcement or construction-joint specification.
- [LISP preservation and accuracy work](docs/LISP_FIDELITY_AND_DIRT_WALL.md):
  implemented changes, compatibility API and the remaining acceptance tests.

## Production status

Use the live drafting demo for browser-only previews with sample bridge parameters,
geometry checks, and SVG or DXF review exports. The workbook workspace sends the
selected workbook to the configured drawing backend. Use approved inputs and
project codes when sharing review artifacts.

Install the Python `dev,api,draw` extras, `httpx`, and `playwright`, then run the
software launch checks from the repository root.

```bash
npm ci --include=dev --prefix frontend
python -m playwright install chromium
python scripts/check_software_launch.py
```

The software check runs frontend tests, TypeScript checking, the production build,
a static-browser download check, and drawing API and acceptance tests. Engineering acceptance
requires reference verification and explicit sign-off by the responsible engineer.
Treat browser exports and unsigned drawings as review drafts.

See [deployment and rollback](docs/DEPLOYMENT.md) for the hosting workflow.

## Quick start

```bash
pip install -e packages/bridgecad-core -e packages/bridgecad-draw -e packages/bridgecad-ai
streamlit run apps/streamlit-ui/app.py
python -m pytest -q tests/draw
```

## 🧹 Cleaning the workspace

`scripts/clean.py` removes only regenerable artifacts — build output, caches,
test dumps and stale git locks. It **never stops running processes**: browsers,
AI tools, editors and `git` keep running, and protected paths (`.git`,
`.env*`, `ATTACHED ASSETS/`, `CODE-JUNCTION/`, `.playwright-browsers/`) are
always refused.

Every category is selectable — untick what you want to keep:

```bash
make clean-select                  # interactive picker — enter numbers to exclude
make clean                         # everything, non-interactive
make clean SKIP=pytest,mypy        # everything except these categories
make clean ONLY=dist,pycache       # only these categories
python scripts/clean.py --dry-run  # preview without deleting
python scripts/clean.py --list     # show all categories
```

| Category | Cleans |
|---|---|
| `dist` | `build/`, `dist/`, `*.egg-info/` |
| `pycache` | all `__pycache__/` outside dependency trees |
| `pytest` `mypy` `ruff` `hypothesis` | tool caches |
| `coverage` | `.coverage`, `coverage.xml`, `htmlcov/` |
| `robot-artifacts` | `artifacts/robot/`, `artifacts/browser_check/`, `.screenshots/` |
| `draw-baselines` | `tests/draw/baselines/*.hash` |
| `node-modules` | `node_modules/` trees |
| `os-temp` | temp-dir files older than 7 days |
| `ide-caches` | cache dirs inside `%APPDATA%` of Antigravity IDE, Cursor, Kiro, Qoder, Replit, Trae, devin, Windsurf — settings/sign-ins never touched |
| `git-locks` | stale `.git/*.lock` files |

📊 **Run statistics:** each clean records pre/post free space, bytes freed,
paths removed and duration to `~/.bridgecad/clean_stats.json` on the local
machine. Every **50th run** prints a full statistics report automatically —
`python scripts/clean.py --stats` shows it anytime.

See [OBJECTIVES.md](OBJECTIVES.md) for the full objective book of every
cleaning script and target.

## Drawing review

```bash
python -m bridgecad_ai.drawing_review sheet.dxf requirements.json        # rule checks
LOVABLE_API_KEY=... python -m bridgecad_ai.drawing_review sheet.dxf requirements.json --ai
```
Or use the **🔎 Drawing Review** tab in the Streamlit app.
