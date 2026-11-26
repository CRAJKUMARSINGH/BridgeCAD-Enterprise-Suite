# BridgeCAD launch hardening report

25 November 2026 IST

## Changes

- The live drafting studio validates the current inputs at each save or export.
  An invalid edit leaves the last valid preview visible and blocks SVG and DXF
  downloads. Generated files carry a review-draft label.
- The static demo uses sample bridge parameters and browser-local storage.
  Workbook download responses use `Cache-Control: no-store`. The workbook
  proxies return generic server-error messages when the upstream service fails.
- A single command, `python scripts/check_software_launch.py`, runs the frontend
  tests, typecheck, build, browser-only demo check, and focused Python drawing
  and acceptance tests. The suite workflow runs the same command for pull
  requests and the configured branches.
- The existing engineering gate continues to require evidence for each gate,
  including reference fidelity and approval by the responsible engineer.

## Verification

- [Baseline](BASELINE.md) records the original checkout and checks.
- All 27 frontend tests passed, including 11 invalid-input probes, recovery
  after correcting inputs, and the workbook proxy test. Typecheck and the
  production build passed.
- Headless Chromium exercised the static demo with API requests blocked.
  Invalid inputs blocked export. Corrected inputs produced review-stamped SVG
  and DXF files.
- All 16 quality-manifest tests passed, including the seven cases with one
  omitted piece of evidence.
- The software launch command passed all 31 focused Python tests. The Netlify
  readiness check passed all 25 checks.
- The original asset directories and the launch guide were preserved.

## Release status

The engineering release gate reports a missing defect ledger and sign-off
file. Engineering reference verification, recorded sign-off, and deployed
staging verification remain open. Browser and workbook exports are for review.
See [deployment and rollback](docs/DEPLOYMENT.md) for the staging checks.
