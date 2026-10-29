#!/usr/bin/env bash
# Week-1+ metric collector. Regenerates the golden packages, dumps facts, and
# prints the MASTER-PLAN §5 table. Never estimates a cell.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/build/metrics"
GOLDEN="$ROOT/tests/draw/golden"

rm -rf "$OUT"; mkdir -p "$OUT/pkg" "$OUT/facts"

python "$ROOT/scripts/_gen_golden_packages.py" --out "$OUT/pkg"

mapfile -t DXFS < <(find "$OUT/pkg" -name '*.dxf' | sort)
python "$ROOT/scripts/dump_dxf_facts.py" "${DXFS[@]}" --out "$OUT/facts" >/dev/null

python - "$OUT/facts" <<'PY'
import json, sys
from pathlib import Path

facts = [json.loads(p.read_text()) for p in sorted(Path(sys.argv[1]).glob("*.json"))]
n = len(facts) or 1

def col(f, key, pred=lambda v: v):
    return sum(1 for f in facts if pred(f.get(key)))

print()
print("  metric                                    value")
print("  " + "-" * 52)
print(f"  sheets analysed                           {len(facts)}")
print(f"  sheets declaring a true scale              {col(facts, 'scale_declared')}/{n}")
print(f"  native DIMENSION entities                  {sum(f['dimension_count'] for f in facts)}")
print(f"  dims without dimlfac=1000                  {sum(f['dimensions_without_lfac_1000'] for f in facts)}")
print(f"  distinct text heights (max per sheet)      {max((f['text_height_distinct'] for f in facts), default=0)}")
print(f"  layers used (union)                        {len(set().union(*[set(f['layers_used']) for f in facts]) if facts else set())}")
print(f"  duplicated lines                           {sum(f['duplicate_line_count'] for f in facts)}")
print(f"  zero-length lines                          {sum(len(f['zero_length_lines']) for f in facts)}")
print(f"  layouts                                    {max((f['layout_count'] for f in facts), default=0)}")
print()
PY

echo "  facts: $OUT/facts"
