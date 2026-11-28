# Group workspace entry points by purpose

## Status

Accepted for the local Phase 0 changes.

## Context

Root Python files included application entry points, diagnostic scripts, an
interpreter startup hook, and manually invoked tests. Several are still called by
the command-line facade or CI.

## Decision

Move the applications to `apps/streamlit-ui/legacy/`, diagnostics and explicitly
invoked legacy tests to `scripts/legacy/`, and the RC smoke runner to `scripts/`.
Move the Python startup hook to `scripts/` and point source launchers there.
Update callers with the new paths. Preserve the original command-line facade
commands and the individual application implementations.

## Alternatives considered

- Keep all root entry points. This leaves the documented repository layout
  unenforced.
- Delete legacy entry points. This would remove working workflows ahead of the
  feature parity review.

## Consequences

The moves preserve the drawing algorithms, reference files and output locations.
Legacy tests remain opt-in. The primary package continues to bootstrap source
checkout imports when explicitly imported.

## Migration

Run `python scripts/rc1_smoke.py` for the RC verifier and
`python -m pytest scripts/legacy/test_ultimate_app.py` for the legacy app tests.
Use `apps/streamlit-ui/legacy/` for the old Streamlit launch paths.
