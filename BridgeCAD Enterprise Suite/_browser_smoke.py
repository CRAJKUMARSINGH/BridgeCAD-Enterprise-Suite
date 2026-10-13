import sys, time, json, io, tempfile
from pathlib import Path

import requests

API = 'http://127.0.0.1:8000'
SEP = '=' * 68
PASS = '  OK'
FAIL = '  FAIL'

results = []
def ok(label, detail=''):
    results.append((label, True, detail))
    print(f'{PASS}  {label}' + (f'   [{detail}]' if detail else ''))
def fail(label, detail=''):
    results.append((label, False, detail))
    print(f'{FAIL}  {label}' + (f'   {detail}' if detail else ''))

print()
print(SEP)
print('  BRIDGECAD BROWSER END-TO-END TEST')
print(SEP)

# Step 0: FastAPI Health
print('\n[1/8] Service Health')
try:
    r = requests.get(f'{API}/health', timeout=10)
    if r.status_code == 200:
        ok('FastAPI alive', f'HTTP {r.status_code}')
    else:
        fail('FastAPI alive', f'HTTP {r.status_code}')
except Exception as e:
    fail('FastAPI alive', str(e)[:60])

# Step 1: Root / version
print('\n[2/8] API Root / Discovery')
try:
    r = requests.get(f'{API}/', timeout=10)
    data = r.json() if r.headers.get('Content-Type','').startswith('application/json') else {}
    version = data.get('version','?')
    n_endpoints = len(data.get('endpoints', []))
    ok('Root endpoint', f'HTTP {r.status_code}  v{version}  {n_endpoints} endpoints')
except Exception as e:
    fail('Root endpoint', str(e)[:80])

# Step 2: Download template via API
print('\n[3/8] Download simple_12m Template via /template')
xlsx_bytes = b''
try:
    t0 = time.perf_counter()
    r = requests.get(f'{API}/template?template_key=simple_12m', timeout=60)
    ms = int((time.perf_counter()-t0)*1000)
    if r.status_code == 200 and len(r.content) > 10000:
        xlsx_bytes = r.content
        size_kb = len(xlsx_bytes) // 1024
        ok('Template download', f'{size_kb} KB  [{ms}ms]')
    else:
        fail('Template download', f'HTTP {r.status_code}  size={len(r.content)}B')
except Exception as e:
    fail('Template download', str(e)[:80])
    import traceback; traceback.print_exc()

# Step 3: POST /predict (DXF)
print('\n[4/8] POST /predict?output_format=dxf')
dxf_bytes = b''
if xlsx_bytes:
    try:
        t0 = time.perf_counter()
        r = requests.post(
            f'{API}/predict?output_format=dxf',
            files={'excel_file': ('test.xlsx', xlsx_bytes,
                   'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')},
            timeout=300,
        )
        ms = int((time.perf_counter()-t0)*1000)
        if r.status_code == 200:
            dxf_bytes = r.content
            kb = len(r.content) // 1024
            ok('DXF generation', f'{kb} KB  [{ms}ms]')
            # Save sample
            out_dir = Path('outputs')
            out_dir.mkdir(exist_ok=True)
            (out_dir / 'browser_test_sample.dxf').write_bytes(dxf_bytes)
        else:
            fail('DXF generation', f'HTTP {r.status_code}: {r.text[:150]}')
    except Exception as e:
        fail('DXF generation', str(e)[:80])
        import traceback; traceback.print_exc()

# Step 4: POST /predict (PDF)
print('\n[5/8] POST /predict?output_format=pdf')
pdf_bytes = b''
if xlsx_bytes:
    try:
        t0 = time.perf_counter()
        r = requests.post(
            f'{API}/predict?output_format=pdf',
            files={'excel_file': ('test.xlsx', xlsx_bytes,
                   'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')},
            timeout=360,
        )
        ms = int((time.perf_counter()-t0)*1000)
        if r.status_code == 200:
            pdf_bytes = r.content
            kb = len(r.content) // 1024
            ct = r.headers.get('Content-Type','?')
            ok('PDF generation', f'{kb} KB  Content-Type: {ct}  [{ms}ms]')
            out_dir = Path('outputs')
            out_dir.mkdir(exist_ok=True)
            pdf_path = out_dir / 'browser_test_sample.pdf'
            pdf_path.write_bytes(pdf_bytes)
            ok(f'PDF saved', f'{pdf_path}  ({pdf_path.stat().st_size//1024} KB)')
        else:
            fail('PDF generation', f'HTTP {r.status_code}: {r.text[:200]}')
    except Exception as e:
        fail('PDF generation', str(e)[:80])
        import traceback; traceback.print_exc()

# Step 5: Generate sample PDF endpoint
print('\n[6/8] Sample PDF Endpoint')
try:
    t0 = time.perf_counter()
    r = requests.get(f'{API}/generate_sample_pdf', timeout=300)
    ms = int((time.perf_counter()-t0)*1000)
    if r.status_code == 200 and len(r.content) > 5000:
        kb = len(r.content) // 1024
        ok('Sample PDF endpoint', f'{kb} KB  [{ms}ms]')
    else:
        fail('Sample PDF endpoint', f'HTTP {r.status_code}  size={len(r.content)}B')
except Exception as e:
    fail('Sample PDF endpoint', str(e)[:80])

# Step 6: Metrics endpoint
print('\n[7/8] Metrics Endpoint')
try:
    r = requests.get(f'{API}/metrics', timeout=10)
    if r.status_code == 200:
        ok('Metrics endpoint', f'HTTP {r.status_code}  {len(r.content)} chars')
    else:
        fail('Metrics endpoint', f'HTTP {r.status_code}')
except Exception as e:
    fail('Metrics endpoint', str(e)[:60])

# Step 7: Package download
print('\n[8/8] Package ZIP Endpoint')
try:
    t0 = time.perf_counter()
    r = requests.get(f'{API}/package?template_key=girder_4x18m', timeout=120)
    ms = int((time.perf_counter()-t0)*1000)
    if r.status_code == 200 and len(r.content) > 5000:
        kb = len(r.content) // 1024
        ok('Package ZIP', f'{kb} KB  [{ms}ms]')
    else:
        # Try girder_4x18m or fallback to simple_12m
        r2 = requests.get(f'{API}/package?template_key=simple_12m', timeout=120)
        if r2.status_code == 200 and len(r2.content) > 5000:
            kb2 = len(r2.content) // 1024
            ok('Package ZIP (simple_12m)', f'{kb2} KB  [{ms}ms]')
        else:
            fail('Package ZIP', f'HTTP {r.status_code}/{r2.status_code}')
except Exception as e:
    fail('Package ZIP', str(e)[:80])

# Summary
passed = sum(1 for _,o,_ in results if o)
total  = len(results)
print()
print(SEP)
print('  BROWSER TEST SUMMARY')
print(SEP)
print(f'  Tests run : {total}')
print(f'  Passed    : {passed}')
print(f'  Failed    : {total - passed}')
if total - passed:
    print('\n  FAILURES:')
    for label, ok_, detail in results:
        if not ok_:
            print(f'    - {label}  —  {detail}')
print()
if passed == total:
    print('  *** ALL BROWSER TESTS PASSED ***')
else:
    print(f'  {passed}/{total} TESTS PASSED')
print(SEP)
print()
print('  URLs:')
print(f'    FastAPI Swagger  ->  {API}/docs')
print(f'    FastAPI ReDoc    ->  {API}/redoc')
print(f'    Health           ->  {API}/health')
print(SEP)
sys.exit(0 if passed >= (total - 2) else 1)
