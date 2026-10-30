# Compliance Traceability Matrix

Every clause-mapped check the compliance engine emits (`CC-001` … `CC-006`)
traced from the **code clause** it enforces, through the **test** that proves it,
to the **V&V benchmark** that independently re-derives the same identity.

The DoD for W06 is *no gap in this matrix*: a check id with no clause, no test,
or no benchmark fails `tests/compliance/test_compliance_engine.py`.

Tiers follow [TOLERANCE_POLICY.md](TOLERANCE_POLICY.md); the benchmark ids are
indexed in [BENCHMARKS.md](BENCHMARKS.md).

| Check | Title | Module | Clause | Test | Benchmark |
|-------|-------|--------|--------|------|-----------|
| CC-001 | Span / depth ratio | `bridgecad_qa.compliance_engine` | IRC:21-2000 Table 12 | tests/compliance/test_compliance_engine.py::test_cc001_span_depth_uses_the_registered_band | VV-CMP-001 |
| CC-002 | Minimum deck slab thickness | `bridgecad_qa.compliance_engine` | IRC:21-2000 Clause 304.7 | tests/compliance/test_compliance_engine.py::test_cc002_slab_thickness_is_required_over_provided | VV-CMP-002 |
| CC-003 | Impact factor | `bridgecad_qa.compliance_engine` | IRC:6-2017 Clause 3.5 | tests/compliance/test_compliance_engine.py::test_cc003_impact_factor_within_irc_ceiling | VV-CMP-003 |
| CC-004 | Expansion joint gap | `bridgecad_qa.compliance_engine` | IRC:6-2017 Clause 3.8 | tests/compliance/test_compliance_engine.py::test_cc004_expansion_joint_gap_rounds_to_five_mm | VV-CMP-004 |
| CC-005 | Freeboard above HFL | `bridgecad_qa.compliance_engine` | IRC:5-2015 Clause 22.1 | tests/compliance/test_compliance_engine.py::test_cc005_freeboard_uses_soffit_minus_hfl | VV-CMP-005 |
| CC-006 | Deck concrete grade | `bridgecad_qa.compliance_engine` | IRC:112-2020 Clause 6.1 | tests/compliance/test_compliance_engine.py::test_cc006_deck_grade_meets_irc112_minimum | VV-CMP-006 |

## Notes

* Each check is a `demand / capacity / utilisation` record; the clause names the
  code **and its edition** so a checker can reproduce the number.
* The `Test` column names a runnable node (`file::function`); the `Benchmark`
  column names a case in `tests/verification/cases.py` that re-derives the same
  identity from first principles.
* Load-combination sets (`IRC:6-2017`, EN 1990:2002) are catalogued in the
  calculation sheet rendered by `calc_sheet_markdown`.
