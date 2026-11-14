"""Black-box saved-scenario corruption and round-trip checks using emitted JS."""
from pathlib import Path
import shutil
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[2]

@pytest.mark.skipif(shutil.which('node') is None, reason='Node is not installed')
def test_scenario_recovery_contract(tmp_path):
    tsc = ROOT/'frontend/node_modules/typescript/bin/tsc'
    if not tsc.exists(): pytest.skip('Run frontend npm ci for TypeScript checks')
    subprocess.run(['node',str(tsc),str(ROOT/'frontend/src/workflowScenarios.ts'),'--target','ES2020','--module','commonjs','--skipLibCheck','--outDir',str(tmp_path)],check=True,capture_output=True)
    emitted=tmp_path/'workflowScenarios.js';emitted.rename(tmp_path/'workflowScenarios.cjs')
    script=tmp_path/'check.cjs'
    script.write_text('''const assert=require('node:assert/strict');
const {readScenarios}=require('./workflowScenarios.cjs');
const item={schemaVersion:2,id:'study-1',name:'Nine span',type:'BR-I-2022-002',overrides:{span_count:'9'},paper:'A1',orientation:'Landscape',scale:'300',savedAt:'2026-11-14T00:00:00Z'};
const parse=items=>readScenarios(JSON.stringify(items),[item.type],(_,o)=>Object.keys(o).every(k=>k==='span_count'));
assert.deepEqual(parse([item]),[item]);
for(const patch of [{savedAt:'broken'},{id:''},{name:' '},{scale:'NaN'},{scale:'0'},{type:'unknown'},{overrides:{bogus:'2'}},{overrides:{span_count:'Infinity'}}]) assert.equal(parse([{...item,...patch}]).length,0);
assert.equal(parse([item,item]).length,1);
assert.deepEqual(readScenarios('{bad',[item.type]),[]);
assert.deepEqual(readScenarios('{}',[item.type]),[]);
''')
    subprocess.run(['node',str(script)],check=True,capture_output=True)
