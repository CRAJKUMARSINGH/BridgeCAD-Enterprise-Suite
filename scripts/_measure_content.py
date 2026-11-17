"""Measure required content against the resolved fixture and write the ledger.

The measurement is taken with the **same inputs the REQUIRED_CONTENT gate
uses** — the same resolver output and the same built project the renderers read
(``abutment_shape_family`` comes from the built project's ``AbutmentType``, via
``_gen_nine_span._content_report``).  A ledger that fed a hand-kept parameter
map instead would report applicability the gate never saw: the card declares an
elastomeric bearing and a cantilever-shaped abutment, so a map saying
``bearing_type: NONE`` marks five real bearing requirements "not applicable"
(suppressing them) while declaring the battered-abutment area applicable to a
cantilever drawing (a false failure).  Both are measurement errors, not
findings, so the ledger reads its inputs from the resolved package.
"""
import sys, json, pathlib

REPO = pathlib.Path(__file__).parents[1]
for _rel in ("packages/bridgecad-qa", "packages/bridgecad-core",
             "packages/bridgecad-catalogue", "packages/bridgecad-draw",
             "artifacts/gad-acceptance"):
    _p = REPO / _rel
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import _gen_nine_span as G  # noqa: E402
from bridgecad_catalogue import registry, resolve as R  # noqa: E402

pkg_dirs = sorted(x for x in (REPO / 'artifacts/gad-acceptance/nine_span_slab_resolved').iterdir()
                  if x.is_dir())
pkg_dir = pkg_dirs[0]

card = registry.by_id(G.CARD_ID)
p = R.resolve(card, {**G.BASE, **dict(G.SUPPLIED_STACK)})
p['id'] = card['id']
gen = G._load_generator()
project = gen._build_project(p)

report = G._content_report(pkg_dir, p, project)
j = report.to_json()
print(f'applicable: {j["applicable"]}  failures: {j["failures"]}  passed: {j["passed"]}')
print()
for r in j['requirements']:
    if r['applicable'] and not r['ok']:
        print(f'FAIL {r["id"]:20s}  declared={r["declared_status"]:12s}  measured={r["measured"]}')
        print(f'     {r["detail"]}')
print()
print('--- not applicable ---')
for r in j['requirements']:
    if not r['applicable']:
        print(f'N/A  {r["id"]:20s}  {r["detail"][:80]}')

out = REPO / 'artifacts/gad-acceptance/content-report.json'
out.write_text(json.dumps(j, indent=2), encoding='utf-8')
print(f'\nwrote {out}')
