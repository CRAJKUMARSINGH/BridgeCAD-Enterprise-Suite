# Robotic oracle test plan

The oracle lane proves the **engine, API and exports** behave the way the real
code says they do. It is the contract-level half of the robotic kit: the persona
walker in [ROBOTIC-TEST-GUIDE.MD](../ROBOTIC-TEST-GUIDE.MD) drives the UI like a
user; this lane asserts the numbers, routes, files and bytes underneath it.

Everything here is bound to symbols that exist in the tree — no illustrative
routes, no invented models. If a name in this plan is not importable, the test
that uses it fails, by design.

**See also:** [TRIAGE_AND_DEBUG.md](TRIAGE_AND_DEBUG.md) (what to do when one
fails) · [PATCH_GUIDE.md](PATCH_GUIDE.md) (fix patterns by class) ·
[GUIDE.md](../GUIDE.md) (authoritative operating guide).

---

## 1. What the lane covers

| Suite | File | Binds to |
|---|---|---|
| Engine oracles | `tests/robot/test_engine_oracles.py` | `bridgecad_core` geometry, quantities, validation, `irc6_combinations` |
| API contract | `tests/robot/test_api_contract.py` | the gateway ASGI `app`, its routers, RFC 7807 errors, upload limits |
| Export integrity | `tests/robot/test_exports.py` | `bridgecad_draw.booklet`, `bridgecad_export.orchestrator`, `bridgecad_io` |
| Console sweep | `tests/robot/test_ui_streamlit.py` | the Streamlit console via `AppTest` |

All of them carry the `robot` marker, which is registered in `pyproject.toml`.

## 2. Engine oracles — engineering truth, not smoke

These assert relationships a bridge engineer would defend, not just "it ran":

- The validation report is well formed: findings exist, severities are typed,
  the score is 0–100, and the status agrees with whether any CRITICAL check
  failed.
- Plan geometry matches the project: four deck corners, a total length and
  overall width that equal the inputs, and `len(span_lengths_m) == span_count`.
- Cross-section width equals the input width and the half-width offsets are
  sorted.
- Long-section levels are ordered: top of deck above soffit.
- Quantities are non-negative, and concrete volume grows with total length.
- IRC:6 combinations are complete: unique ids, `IRC` in the standard, a limit
  state in `{ULS, SLS, SEISMIC}`, non-empty terms, and at least one ULS.

## 3. API contract — the routes that actually exist

The gateway exposes an ASGI object named `app`. The lane pins:

- `/health` lists the loaded packages; `/version` reports the codename
  (`0.1.0-rc1`); the OpenAPI document builds.
- `/bridges/parse` returns a project summary; `/bridges/validate` returns a
  score and findings.
- `/draw/gad` returns a DXF ZIP; `/bills/generate` returns a priced BOQ with a
  positive grand total; `/qa/report` returns HTML.
- `/exports/bundle` contains `manifest.json` and `drawings/*.dxf`.
- `/plugins` lists plugins, serves a detail route, and 404s an unknown id.

Hardening is pinned too. Upload errors are RFC 7807 `problem+json` with all five
members (`type`, `title`, `status`, `detail`, `instance`): a wrong suffix is
`415`, a missing file is `422`. The size cap is enforced
(`MAX_UPLOAD_BYTES == 50 MiB`) against a real oversized upload.

Note: a bad `scale` raises a plain FastAPI `HTTPException(400)`, so it returns
`application/json` with a `detail` key — **not** problem+json. The test asserts
that actual shape rather than the aspirational one.

## 4. Export integrity — eight sheets, valid DXF, deterministic bytes

`generate_package` emits **eight** sheets for the fixture project. The lane
asserts:

- The package is exactly eight files.
- Every sheet is a valid DXF (`doc.audit()` reports no errors; `$INSUNITS` is
  metric).
- Every sheet carries real geometry (≥ 20 modelspace entities) — no empty title
  blocks shipping.
- Re-generating produces byte-identical output (`canonical_dxf_bytes`).
- The export bundle has a manifest and drawings.
- A workbook round-trip (`write_excel` → `read_excel`) preserves the geometry.

## 5. Console sweep — every page renders

Using Streamlit's `AppTest` the lane boots the console, iterates every page in
the `Navigate` radio, and fails on any traceback. It also sends non-ASCII free
text (`पुल–૭`) into the drawing page to catch mojibake.

## 6. Personas

The oracle lane is deterministic by construction; the persona walker layers
seeded user journeys on top of it.

| Persona | Who | Seed |
|---|---|---|
| `P1_basic` — "Ravi" | first-time user | 1001 |
| `P2_intermediate` — "Sneha" | tweaks inputs | 2002 |
| `P3_advanced` — "Col. Iyer" | power user | 3003 |

```sh
python scripts/robot/run_robot.py --url http://localhost:8517 --out artifacts/robot
```

## 7. How to run

```sh
python -m pytest tests/robot -v --tb=short
```

Just one suite:

```sh
python -m pytest tests/robot/test_api_contract.py -q
```

## 8. CI wiring

`tests/robot` is a dedicated lane, not a marker inside the default unit job: the
oracles need `httpx` (TestClient), `ezdxf` (drawing integrity) and `streamlit`
(`AppTest`), which the unit job does not install.

- `.github/workflows/suite-ci.yml` — the unit job ignores `tests/robot`.
- `.github/workflows/robot.yml` — the `oracles` job installs
  `dev,api,ui,draw` plus `httpx openpyxl` and runs `pytest tests/robot`.

## 9. Exit gates

Same severity scale as the persona walker, applied to oracle failures:

| Sev | Example in this lane | Gate |
|---|---|---|
| S1 | wrong engineering number, corrupt/empty export, 5xx | blocks merge |
| S2 | wrong error shape, missing validation, mojibake | blocks merge |
| S3 | slow page, layout overflow | next sprint |
| S4 | cosmetic | backlog |

```sh
python scripts/robot/gate.py
python scripts/robot/triage.py --metrics
```

Merge only when the oracle lane is green and `open S1=0`.
