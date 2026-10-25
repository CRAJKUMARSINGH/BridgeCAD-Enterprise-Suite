# Troubleshooting

## Install and run

| Symptom | Cause | Fix |
|---|---|---|
| `cd: BridgeCAD Enterprise Suite: No such file` | stale doc | you are already in the product root |
| `ModuleNotFoundError: bridgecad_core` | not at repo root | `cd` to the repo root; `sitecustomize.py` does the rest |
| `pip install -r requirements_lean.txt` → no such file | stale doc | use `requirements.txt` |
| `python -m bridgecad` prints usage and exits | expected with no args | pass `verify`, `info`, `generate` or `qa` |
| `bridgecad-cli: command not found` | CLI not installed | `pip install -e apps/cli-console` |
| `make dev` prints version then exits | expected — it is a smoke check | it verifies the workspace resolves |

## Generation

| Symptom | Cause | Fix |
|---|---|---|
| Blank PDF | matplotlib backend, or text-only DXF | confirm the DXF has entities, not just text |
| Text-rendering warnings | font fallback | expected and harmless |
| Only sheet 1 has real geometry | sheets 2–7 are scaffolds | see `GUIDE.md` §11 |
| DXF opens but extents look wrong | sheet coordinate contract not unified | known limitation |
| `blocked` fields on a hand-built workbook | missing required input | use `bridgecad-cli template new` instead |
| Workbook rejected as `.xls` | allowlist not yet landed | save as `.xlsx` |
| Batch run OOM above 50 items | memory | chunk the batch, use `--seed` |
| BOQ numbers look plausible but unsourced | heuristic multipliers | `GUIDE.md` §11 — traceability is Phase 3 |

## API

| Symptom | Cause | Fix |
|---|---|---|
| 400 on `scale` | out of range | valid range is 10–2500 |
| 400 on `prefix` | path separators or unsafe chars | under 32 chars, alphanumeric |
| 500 with a wrapped validation message | bare `except` re-wrapping | already fixed — re-pull |
| Temp files accumulate in `/tmp` | old `mktemp` path | already fixed — re-pull |
| `415` on upload | wrong content type | send `.xlsx` as `multipart/form-data` |

## CI

| Symptom | Cause | Fix |
|---|---|---|
| PII scan fails | a contact detail is in tracked source | route via issues; tag `support` |
| PII scan fails on `egg-info` | generated metadata matched | already fixed — `git grep` with exclusion |
| `suite-ci` finds no workflow | nested `.github` | workflows must sit at the repo root |
| mypy job green but wrong | legacy `\|\| true` | legacy only; `suite-ci` enforces |
| react-build fails on `npm ci` | wrong working directory | job overrides `working-directory` per step |

## Diagnostics

```bash
python -m bridgecad info        # interpreter, repo root, resolved paths
python -m bridgecad verify      # acceptance verifiers, 15 checks
python rc1_smoke.py             # 11-check release gate
python tests/e2e/run_e2e.py     # 28 fixtures
bridgecad-cli health
pytest tests/integration -v
```

Run `info` first for anything import-related — it prints the resolved workspace
paths, which tells you immediately whether `sitecustomize.py` fired.

## Filing a good bug

Include: `python -m bridgecad info` output · the exact command · the full
traceback · the workbook or a minimal reproduction · expected vs actual.

Tag `support`. If it involves a drawing, attach the DXF *and* the manifest.

## Not a bug

- Text-rendering warnings.
- Sheets 2–7 being scaffolds.
- BOQ lines being `estimated` rather than `verified`.
- QA score below 100 on a template — templates are typical, not optimal.
