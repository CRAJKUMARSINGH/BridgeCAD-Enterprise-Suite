# LISP fidelity and dirt-wall accuracy

Reviewed public main: `aed97f8c4f1b576b3ebb42f7555fc501de736ea6`, 21 November 2026.
Status: **generated draft — acceptance pending**. No full-port or perfect-match claim.

## Findings

The repository preserves thirteen named routines: opn, reed, vpos, hpos,
v2pos, h2pos, st, layout, cs, pier, pt, p2t and abt1. The inventory tests
check source structure and some geometry invariants; they do not execute AutoLISP.
The archive includes explanatory comments and rearranged fragments. Treat it as
a preservation copy, not an independently certified executable original.

`src/bridge_gad/lisp_mirror.py` is a simplified deck-face generator, not the full
routine sequence. Its `span * .025` longitudinal rise must not be advertised as
source crossfall/camber parity. Other legacy generators and the production
`bridgecad_draw` package have separate implementations; changes in one do not
prove the others are corrected.

The blanket claim that every dimension must be divided by cos(skew) is wrong.
The archived `pier` uses that correction for cap width. Several `abt1` widths
and offsets explicitly divide by 1. Preserve each view's geometry convention;
record deliberate engineering departures rather than calling them literal ports.

## Implemented here

1. `bridgecad_refs.gad_text`: strict reader/writer for active archive read order.
   No silent defaults, non-finite values, integer truncation, incomplete records
   or trailing extensions. Invalid data is rejected before a write touches its
   destination. Numeric values round-trip; whitespace does not.
2. Production Sheet 5 transverse weep-hole circles now use the configured
   diameter, matching the longitudinal view. Previously only 100 mm matched.
   Exported DXFs are measured at 50, 100 and 150 mm, using a dimensioned cap line
   to recover drawing scale independently of the radius calculation.
3. README restored with both requested source links and an honest status.

The codec is intentionally not wired to the production generator. An adapter
must resolve the source's final-span convention and absolute-RL semantics first.
Do not silently use a legacy record as a modern pier/foundation specification.

## Using gad.txt without losing values

With `packages/bridgecad-refs` installed or on PYTHONPATH:

```python
from bridgecad_refs.gad_text import read, write
legacy = read("gad.txt")
write("gad-copy.txt", legacy)
```

The exact blocks are:

| Block | Fields in consumption order |
|---|---|
| reed | scale1, scale2, skew, datum, toprl, left, right, xincr, yincr, noch |
| cs, repeated noch times | chainage, RL |
| pier header | nspan, lbridge, abtl, rtl, sofl, kerbw, kerbd, ccbr, slbthc, slbthe, slbtht, capt, capb, capw, piertw, battr, pierst, piern |
| pier records, repeated nspan times | span1, futrl, futd, futw, futl |
| abt1 | dwth, alcw, alcd, alfb, alfbl, altb, altbl, alfo, alfd, albb, albbl |

The active archive reads datum/toprl with atoi. Fractional values are rejected
rather than silently truncated. Engineering RLs need not be integers: keep the
canonical model's precision; do not force it through a lossy legacy export.
The source draws a residual span after its loop. Do not assume nspan has the
same meaning as a modern span-count field without checking an original input.
No abtlen line is consumed: its read is commented out. Store new properties in
a separate JSON sidecar; do not invent extra positional fields.

## Required enrichment before accepting drawing parity

| Area | Current evidence or gap | Required acceptance evidence |
|---|---|---|
| Input mapping | Compatibility codec exists; production adapter absent | Every original field mapped once with units, RL interpretation and conflict policy; no ignored overrides |
| Grid/survey | Preserved layout/cs routines | Measured BED LEVEL / CHAINAGE strips, ticks, survey vertices and labels, including nonzero chainage/datum |
| Pier skew | Partial invariant tests | At 0, ±15, ±30 degrees, measure cap/footing projection, rounded nose arcs and rotation about the declared centre |
| Section Y-Y | Multiple implementations | Measured kerbs, carriageway and centre/edge/tip slab geometry; distinguish transverse crossfall from longitudinal camber |
| Battered abutment | 14-point helper exists | Exported polygon agrees with independently calculated vertices, including front/back break RLs, toe batter and footing depth |
| Production abutment inputs | Sheet 5 still supplies fixed toe 1.5 m and footing depth 1.0 m to the helper | Replace with resolved design inputs; reject contradictions, print unresolved inputs, measure both mirrored ends |
| Cantilever | Separate modern family, not an abt1 equivalent | Dimensioned longitudinal stem/base/toe/heel from actual design inputs; correct transverse projection |
| Style/units | pmb100 preserved in source | Verify modelspace mm versus paper mm and dimension values after scaling; never copy modelspace text heights into paper layout unchanged |
| Dirt wall | Geometry and notes already exist | Verify cap/approach/wearing-course levels, thickness, joints, drainage path, filter region and clearances across views |
| Output fidelity | Tests are not a reference overlay | Approved PDF hash, page/region/scale registration, residual measurements and engineering sign-off |

Use the same inputs for legacy and modern outputs. Compare coordinates and
entity roles, not only layer names or entity counts. Test asymmetric batters,
unequal spans and skew of both signs so accidental symmetry cannot hide errors.
A nine-span drawing without a matching reference page needs independent design
review; do not claim direct PDF parity.

## Dirt-wall source limits and remaining defects

Prewallcivil provides contextual discussion of retaining fill and drainage. It
is not evidence for the pasted claim of 1:20 weep slope, bracket dimensions,
waterbar dimensions or reinforcement. The article was retrievable through search;
the earlier statement that the domain had expired is not established here.

Sheet 5 still contains illustrative two-row weep-hole symbols and a spacing
note; this patch fixes diameter consistency, not a fully spaced drainage layout.
Its catalogue builder currently supplies 100 mm rather than exposing a user
diameter dial. The E2E fixture loader also did not propagate a diameter override;
the new renderer test explicitly sets and checks the canonical model field.

Before promoting details, review existing Sheet 5 notes about 100 mm GSB,
150 mm PVC waterbar and monolithic construction versus a construction joint.
Those prescriptions are not established by the supplied article. Replace them
with approved project details or visibly mark them unresolved. Require actual
input for weep slope/outlet, spacing/edge distances, filter thickness, approach
slab support, joint type and reinforcement. Do not synthesize structural bar
arrangements from a quantity schedule.

## Patch application and verification

No commit/push. On a changed Windows tree, preserve all local work first. Use
`git apply --check lisp-fidelity.patch`. If it fails, merge only reviewed hunks;
do not replace newer files with whole snapshots. README was absent on this base;
merge its references into an existing local README instead of overwriting it.

Run the focused suite listed in TEST-RESULTS.txt, then regenerate representative
nominal, skewed, battered and cantilever cases using the actual production entry
point. Inspect rendered sheets and measure DXFs. Retain failed runs in FAILED-RUN;
requested blank PNGs still fail. None of this work closes existing content,
reference-fidelity, overlap-classification or engineering-review gates by itself.
