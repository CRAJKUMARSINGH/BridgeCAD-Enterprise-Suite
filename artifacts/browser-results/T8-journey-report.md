# T8 — Production browser/API journey report

Runner: `scripts/browser_test.py` (Steps 0–13, real data over live services).
Raw console: `artifacts/browser-results/report.txt`.

## Services

| Service | URL | Health |
|---|---|---|
| FastAPI gateway | http://127.0.0.1:8000 | `/health` 200 |
| Streamlit UI | http://127.0.0.1:8501 | `/_stcore/health` → `ok` |
| React/Vite console | http://127.0.0.1:5173 | `/` 200 |

API version `0.1.0-rc1` (`BRIDGECAD-OSS-1.0`); 18 OpenAPI paths; plugin registry lists 10 ids.

## Result

**16 / 16 steps pass** (exit 0). Timings: parse 2.4 s, validate 2.4 s, `/draw/gad` 4.7 s,
BOQ 2.2 s, QA HTML 2.5 s, `/exports/bundle` 5.8 s.

Exported artefacts retained in this directory:

- `gad-draw.zip` — 9 DXF sheets (`JOURNEY_Sheet1_Plan … Sheet9_Reinforcement`)
- `export-bundle.zip` — 16 files: 9 DXF + BOQ xlsx/csv/pdf + QA html + BBS csv/xlsx + `manifest.json`
- `qa-report.html`, `bills.json`, `simple_12m.xlsx`
- `api-server.log`, `streamlit-server.log`, `vite-server.log`

> Note: the runner's docstring says "8-sheet"; the product now emits **9** sheets
> (Sheet9 Reinforcement). Docstring staleness only — no functional impact.

## Defect found and fixed (first run: 10/16)

First run was 10/16. Every mutating endpoint rejected the freshly generated template:

```
HTTP 422 {"detail":"1 validation error for BridgeProject\nsuperstructure
  Value error, superstructure.type=RCC_TBEAM requires girder_depth_mm >= 200 (got None)"}
```

Raw response: `defect-blank-template-parse.json`.

### Root cause

The blank 14-sheet template writes empty SUPERSTRUCTURE cells
(`_build_generic_sheet` emits `""` when `obj is None`). The canonical reader then
defaulted `superstructure.type = RCC_TBEAM` — a girder-bearing family the model
validator ([models.py](../packages/bridgecad-core/bridgecad_core/models.py#L1136-L1152))
requires to carry `girder_depth_mm`, `girder_spacing_m` and `girders_per_deck_count`.

The legacy reader path already injects those three prefills
([excel_reader.py](../packages/bridgecad-io/bridgecad_io/excel_reader.py#L606-L614)),
but the canonical 14-sheet path did not — so the canonical workbook could not
round-trip through the API at all.

Coverage gap: `tests/integration/test_io_wiring.py::test_generate_template_public_wrapper`
only asserts the file **exists**, never reads it back; `tests/api/test_project_patch.py`
calls `generate_template(..., project=project)` (prefilled), so it never exercised the
blank path. The defect was therefore untested.

### Fix

[excel_reader.py](../packages/bridgecad-io/bridgecad_io/excel_reader.py#L777-L792): when the
workbook supplies **no** superstructure type (the blank case), mirror the legacy/template
prefills (`girder_depth_mm=1200`, `girder_spacing_m=2.5`, `girders_per_deck_count=4`).
When the workbook **explicitly** chooses a type, its own girder cells must stand on their
own — an explicit girder type with blank dimensions still raises.

## Verification

- Local round-trip: `read_excel(blank template)` → `type=RCC_TBEAM depth=1200 spacing=2.5 girders=4`.
- `pytest tests/integration tests/api packages/bridgecad-io/tests` → **13 passed**, no regressions.
- Journey re-run → **16 / 16** (this report).

## Combined-suite stall (already diagnosed — not environmental)

See `artifacts/continue/T8-full-suite.txt`: 1461 passed / 9 skipped / 5 xfailed in 962 s,
bounded and repeatable. faulthandler traceback points at
`tests/docs/test_detection_proof.py:21` → `subprocess.run` → `_communicate` → `join`, with the
child `scripts/prove_detection.py` (PID 19492/24376). Root cause: per-mutation full-tree copy
volume in the child. Proven, not environmental.
