# BridgeCAD Suite — Triage Log

**Owner:** _(QA lead)_ **Rotation:** weekly, Mon 09:00 IST
**Source of truth for S1/S2.** `scripts/robot/gate.py` reads this file. A PR cannot merge
with an open S1 or S2 in its area.

**Rules**
1. Nothing enters here without a **minimized trace** (`TRIAGE_AND_DEBUG.md` §2).
2. ID is assigned by `scripts/robot/triage.py` only — never by hand.
3. One entry = one defect class. Related findings get `REL:` links, not merged rows.
4. A row closes only when all six DoD boxes are ticked.
5. Severity can only be **raised** by the reporter. Lowering needs the QA lead's initials.

**Severity**
| Sev | Definition | Merge gate | Target |
|---|---|---|---|
| S1 | crash, 5xx, corrupt/empty export, **wrong engineering number** | blocks | same day |
| S2 | silent no-op, missing validation, mojibake, wrong label | blocks | 3 days |
| S3 | layout overflow, a11y warning, slow tab | advisory | sprint |
| S4 | cosmetic | none | backlog |

**Root-cause classes** — `VAL` validation · `STATE` session/rerun · `ENC` encoding ·
`RACE` concurrency · `UNIT` units/dimensioning · `EXPORT` file generation ·
`PERF` · `A11Y` · `UX`

**Patch classes** — cross-reference `PATCH_GUIDE.md` §1–§10.

---

## Open

_Seeded rows below are **predictions** from the persona plan, not findings. A real
robot run flips a row to `OPEN`; until then it stays `UNCONFIRMED` and does not
count toward the gate. Delete the ones a run fails to reproduce._

| ID | Sev | Persona | Symptom (one line) | Class | Patch § | Owner | Status |
|---|---|---|---|---|---|---|---|
| BCAD-0001 | S1 | P3_advanced | span=0 → ZeroDivisionError in depth calc | VAL | §1 | — | UNCONFIRMED |
| BCAD-0002 | S1 | P2_intermediate | concurrent export returns truncated DXF | RACE | §3 | — | UNCONFIRMED |
| BCAD-0003 | S1 | P2_intermediate | identical input yields different DXF bytes | EXPORT | §4 | — | UNCONFIRMED |
| BCAD-0004 | S1 | P2_intermediate | `पुल` renders as `????` in PDF + XLSX | ENC | §10 | — | UNCONFIRMED |
| BCAD-0005 | S2 | P3_advanced | negative skew accepted silently | VAL | §1 | — | UNCONFIRMED |
| BCAD-0006 | S2 | P1_basic | span value blanks after any other widget interaction | STATE | §2 | — | UNCONFIRMED |
| BCAD-0007 | S2 | P3_advanced | 50 MB PDF upload freezes worker, no cap | VAL | §6 | — | UNCONFIRMED |
| BCAD-0008 | S2 | P3_advanced | `.dxf` renamed `.pdf` accepted as valid | VAL | §6 | — | UNCONFIRMED |
| BCAD-0009 | S2 | P1_basic | traceback with internal paths shown to user | UX | §7 | — | UNCONFIRMED |
| BCAD-0010 | S2 | P2_intermediate | project name `a b/c:d` truncates the export filename | VAL | §9 | — | UNCONFIRMED |
| BCAD-0011 | S3 | P3_advanced | max span generation exceeds perf budget, UI freezes | PERF | §8 | — | UNCONFIRMED |
| BCAD-0012 | S3 | P1_basic | 1280×720 viewport scrolls horizontally | A11Y | — | — | UNCONFIRMED |

---

## In progress

| ID | Sev | Fix branch | Test written (red) | Patch SHA | Reviewer |
|---|---|---|---|---|---|
| | | | | | |

---

## Closed

| ID | Sev | Patch SHA | Regression test | Closed by | Closed on |
|---|---|---|---|---|---|
| | | | | | |

---

## Entry detail — template

Copy below the tables for every S1/S2. S3/S4 need only the first four fields.

```markdown
### BCAD-0000 — <symptom>

- **Sev / class:** S1 · VAL
- **Persona / seed:** P3_advanced · seed 3003
- **Opened:** 2026-01-01
- **First bad step:** step 47 — `fill stNumberInput(span) = "0"`
- **Minimized trace (≤6 steps):**
  1. open app
  2. fill span = 0
  3. click Generate
- **Expected:** validation message, no generation
- **Actual:** `ZeroDivisionError: float division by zero`
- **Screenshot / artifact:** `artifacts/robot/P3_advanced_step47.png`
- **First bad location:** `validation.py` (depth derivation)
- **Why not caught before:** no zero-span case in the fixture matrix
- **Class blast radius:** every public engine entry point that divides by span
- **Oracle that should have existed:** boundary parametrize on every public engine fn
- **REL:** BCAD-0005

**DoD**
- [ ] Reproduced from minimized trace by a second person
- [ ] Failing test committed and observed red
- [ ] Patch merged, one class only
- [ ] Blast radius grep done, siblings fixed or filed
- [ ] `make robot-full` green on the fix branch
- [ ] Entry moved to Closed with SHA + test path
```

---

## Weekly metrics

| Week | Opened | Closed | S1 open (end) | S2 open (end) | Median age (d) |
|---|---|---|---|---|---|
| | | | | | |

Trend target: S1 open = 0 at every week boundary.
