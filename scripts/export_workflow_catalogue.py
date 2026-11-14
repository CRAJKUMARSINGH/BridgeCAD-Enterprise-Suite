"""Export frontend guidance from the canonical Python catalogue (no generation)."""
from __future__ import annotations
import json
import sys
from decimal import Decimal
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'packages/bridgecad-catalogue'))
from bridgecad_catalogue import registry
from bridgecad_catalogue.resolve import resolve
from bridgecad_catalogue.schema import VARIABLES

REFERENCE_PAGES = {f"BR-I-2022-{i:03d}": pages for i, pages in enumerate([[5], [6], [7], [8], [9,10], [11], [12,13], [14,15], [16,17], [18,19], [20,21], [22,23], [24,25], [26], [27]], 1)}

def numeric(value):
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral() else float(value)
    raise TypeError(type(value).__name__)

def build():
    cards = []
    common = ['span_count','span_length_m','carriageway_width','footpath_width','skew_deg','deck_thickness_mm','hfl_m','freeboard_m','scour_depth_m','sbc_t_per_m2']
    for card in registry.load():
        resolved = resolve(card, {})
        fields = common + (['pier_height_m','pier_shaft_width_m'] if resolved['pier_count'] else [])
        if card['superstructure_type'] in ('RCC_T_BEAM','PSC_I_GIRDER','PSC_BOX'):
            fields += ['girder_depth_mm','girder_spacing_m','girders_per_deck']
        if card['foundation_type'] == 'PILE': fields += ['pile_diameter_mm','pile_length_m','piles_per_pier']
        if card['foundation_type'] == 'WELL': fields += ['well_diameter_m']
        cards.append({**card, 'referencePdfPages': REFERENCE_PAGES[card["id"]], 'resolved': dict(resolved), 'warnings': resolved.warnings, 'fields': fields})
    return {'schemaVersion':1, 'cards':cards, 'variables':{key:{'unit':spec.unit,'kind':spec.kind.value,'min':spec.lo,'max':spec.hi,'step':spec.step,'choices':list(spec.choices),'note':spec.note} for key,spec in VARIABLES.items()}}

if __name__ == '__main__':
    path=ROOT/'frontend/src/generated/workflow.json'
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(build(),indent=2,default=numeric)+'\n',encoding='utf-8')
    print(path.relative_to(ROOT))
