# Interoperability

BridgeCAD reads and writes a small, deliberately boring set of formats. This
document is the contract: what each format carries, which direction it flows,
and — critically — how much information it is allowed to lose.

The suite is built on a single in-memory model, `BridgeProject` (427 Pydantic
fields across 14 logical sheets). Every adapter below either reconstructs that
model exactly or is documented as an export-only view.

## Round-trip formats

These three formats are **bidirectional** and must reconstruct the model — the
canonical project written out and read back must diff to nothing.

| Format | Extension | Adapter | Direction |
|---|---|---|---|
| JSON | `.bridgecad.json` | `bridgecad_io.json_adapter` | read + write |
| CSV | `csv/` roster (17 files) | `bridgecad_io` CSV roster | read + write |
| Excel | `.xlsx` (14 sheets) | `bridgecad_io.excel_reader` / `excel_template` | read + write |

## Export-only formats

These are produced for downstream consumers (reviewers, other CAD packages) and
are **not** read back by BridgeCAD. Their readers live in other vendors' tools,
so the suite cannot assert a byte-for-byte round-trip.

| Format | Extension | Direction |
|---|---|---|
| IFC | `.ifc` | write only |
| DWG | `.dwg` | write only |

## Loss budget

The loss budget is the tolerated information loss per format. It is a claim CI
can hold us to: the round-trip comparison in
`tests/interop/test_roundtrip.py` is **numeric, not textual**, so
`Decimal("350")`, `350.0` and `"350"` are the same quantity written three ways.

| Format | Loss budget | Rationale |
|---|---|---|
| JSON | **Zero** | The transport format — a dump/load cycle must return the identical `BridgeProject` dump. |
| CSV | **Zero** | The 15 sub-model CSVs + 2 schedules are a second lossless view; every dumped leaf survives the roster split/merge. |
| Excel | **Zero** | `write_excel` and `read_excel` both derive their column set from the Pydantic model, so the round-trip is lossless by construction rather than by a hand-maintained column list that can drift. |
| IFC | **Structural** | Export-only. Geometry, storey and element semantics are preserved for external BIM tools; BridgeCAD-specific QA metadata is not carried back (no in-suite reader). |
| DWG | **Visual** | Export-only. The DXF/DWG drawing is a rendering of the model for drafting review; it is not a data channel (no in-suite reader). |

**Invariant:** every format this suite *writes* must appear in the table above.
A new adapter without a budget row fails
`test_loss_budget_is_published_for_every_format`.
