"""Day 2 audit - check Sections 7-10 enums."""
import sys
sys.path.insert(0, '.')
from bridgecad_core import types

d2_required = {
    "S7 Hydraulic (plan)": [
        "WaterSourceType", "ScourRegimeType", "HydrographShapeType",
        "BankType", "SoilClass", "AffluxEstimationFormulaType",
        "RegimeConstantKValue"
    ],
    "S8 Materials (plan)": [
        "ConcreteAggregateType", "CementType", "AdmixtureType",
        "WeldType", "BearingMaterial", "JointSealantType",
        "WearingCoatGrade"
    ],
    "S9 Drawing (plan)": [
        "LayerGroup", "LineWeightCode", "HatchPatternCode",
        "FontStyle", "ArrowStyle", "ScaleDenominatorSet"
    ],
    "S10 Load/Seismic/Wind (plan)": [
        "SeismicImportanceFactor", "WindImportanceFactor",
        "WindSpeedBasic_ms", "LoadCombination",
        "ImpactFactorCoeff", "TemperatureLoadDeltaT"
    ],
}

registered = set(types.ENUM_REGISTRY.keys())
print("=" * 70)
print("DAY 2 AUDIT: Sections 7-10 Enums Presence Check")
print("=" * 70)
missing_all = []
for section, names in d2_required.items():
    print(f"\n{section}:")
    for name in names:
        present = name in registered
        if present:
            cls = types.ENUM_REGISTRY[name]
            print(f"  ✓ {name} exists ({len(list(cls))} members)")
        else:
            print(f"  ✗ MISSING: {name}")
            missing_all.append((section, name))

print(f"\nTOTAL MISSING from D2 plan: {len(missing_all)}")
for s, n in missing_all:
    print(f"  - [{s}] {n}")

print(f"\nCurrent ENUM_REGISTRY count: {len(registered)}")
print(f"D2 target: >= 160")
print(f"Need at least: {max(0, 160 - len(registered))} new enums")
