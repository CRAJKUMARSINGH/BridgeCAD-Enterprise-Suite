# BridgeCAD launch baseline

The initial checkout was on `980f7ea` with 37 tracked files modified and existing
untracked drafting sources and browser evidence. GitHub `main` was one commit
ahead. The checkout was fast-forwarded to `4998d7d`, and three conflicts were
resolved while reapplying the local edits.

Before the launch changes, all 14 frontend tests passed, along with the frontend
typecheck and production build. Backend test collection in the system Python
failed on a Pydantic version mismatch and a Windows font scan in ezdxf.

The critical review paths are the browser drafting validator and SVG/DXF export
handlers, the workbook upload and drawing endpoints, and the quality manifest's
engineering acceptance decision. `ATTACHED ASSETS/` and `CODE-JUNCTION/` were
present at the start of this work.
