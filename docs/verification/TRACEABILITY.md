# Verification & Validation — Traceability Matrix

This matrix is the **Definition-of-Done gate** for the compliance engine
(`bridgecad_qa.compliance_engine`). Every registered check id (`CC-00N`) must
name, on one row:

1. its governing **standard** and **clause**,
2. an **existing test node** (`path::function`) that exercises the identity, and
3. an **existing V&V benchmark** registered in
   [`tests/verification/cases.py`](../../tests/verification/cases.py).

CI enforces "no gap": `tests/compliance/test_compliance_engine.py` fails if any
`CHECK_IDS` entry is absent, under-specified, names a missing test, or points at
an unknown benchmark id.

| Check | Title | Standard | Clause | Test node | V&V benchmark |
|---|---|---|---|---|---|
| CC-001 | Span / depth ratio | IRC:21-2000 | Table 12 | `tests/compliance/test_compliance_engine.py::test_cc001_span_depth_uses_the_registered_band` | VV-CMP-001 |
| CC-002 | Minimum deck slab thickness | IRC:21-2000 | Clause 304.7 | `tests/compliance/test_compliance_engine.py::test_cc002_slab_thickness_is_required_over_provided` | VV-CMP-002 |
| CC-003 | Impact factor | IRC:6-2017 | Clause 3.5 | `tests/compliance/test_compliance_engine.py::test_cc003_impact_factor_within_irc_ceiling` | VV-CMP-003 |
| CC-004 | Expansion joint gap | IRC:6-2017 | Clause 3.8 | `tests/compliance/test_compliance_engine.py::test_cc004_expansion_joint_gap_rounds_to_five_mm` | VV-CMP-004 |
| CC-005 | Freeboard above HFL | IRC:5-2015 | Clause 22.1 | `tests/compliance/test_compliance_engine.py::test_cc005_freeboard_uses_soffit_minus_hfl` | VV-CMP-005 |
| CC-006 | Deck concrete grade | IRC:112-2020 | Clause 6.1 | `tests/compliance/test_compliance_engine.py::test_cc006_deck_grade_meets_irc112_minimum` | VV-CMP-006 |

## Maintaining this file

* The **Standard**/*Clause* columns must mirror the `ClauseRef` passed when the
  check is built in `packages/bridgecad-qa/bridgecad_qa/compliance_engine.py`.
* The **Test node** must resolve to a real `def test_...(` on disk — a rename
  without a matrix update breaks `test_traceability_tests_exist_on_disk`.
* The **V&V benchmark** must be present in the `REGISTRY` in
  `tests/verification/cases.py`; a new `CC-007` therefore needs a matching
  `VV-CMP-007` case **and** a row here before the suite goes green.
