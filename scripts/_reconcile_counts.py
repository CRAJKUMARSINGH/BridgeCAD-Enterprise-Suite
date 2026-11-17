"""Reconcile content-report counts and explain the gap mapping."""
import json, pathlib
REPO = pathlib.Path(__file__).parents[1]
j = json.loads((REPO / 'artifacts/gad-acceptance/content-report.json').read_text())

total = len(j['requirements'])
appl  = j['applicable']
na    = j['not_applicable']
fails = j['failures']
ok    = appl - fails

print(f'Total requirements in manifest : {total}')
print(f'  applicable (when matched)    : {appl}')
print(f'  not applicable               : {na}')
print(f'  satisfied (applicable & ok)  : {ok}')
print(f'  failures (applicable & !ok)  : {fails}')
print()
print('Failure ledger:')
print(f'  {"ID":<20}  {"Declared":12}  {"Measured":8}  Reason')
for r in j['requirements']:
    if r['applicable'] and not r['ok']:
        reason = 'declared PARTIAL/MISSING' if r['declared_status'] != 'IMPLEMENTED' else 'measured absent'
        print(f'  {r["id"]:<20}  {r["declared_status"]:12}  {r["measured"]:<8}  {reason}')
        print(f'              {r["detail"][:90]}')
print()
print('Not-applicable (excluded from pass set):')
for r in j['requirements']:
    if not r['applicable']:
        print(f'  {r["id"]:<20}  {r["detail"][:80]}')
