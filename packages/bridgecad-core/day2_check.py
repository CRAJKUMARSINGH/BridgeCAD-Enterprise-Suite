import sys
sys.path.insert(0, '.')
from bridgecad_core import types
count = len(types.ENUM_REGISTRY)
print(f'ENUM_REGISTRY count: {count}')
target_pass = count >= 160
print(f'Target >= 160: {"PASS" if target_pass else "FAIL"}')
total_members = sum(len(list(c)) for c in types.ENUM_REGISTRY.values())
print(f'Total members: {total_members}')
print()
print('New D2 enums added:')
d2 = ['RiverBankType','SoilClass','RegimeConstantKValue','ConcreteAggregateType','CementType','AdmixtureType','WeldType','BearingMaterial','JointSealantType','WearingCoatGrade','LayerGroup','LineWeightCode','HatchPatternCode','FontStyle','ArrowStyle','ScaleDenominatorSet','SeismicImportanceFactor','WindImportanceFactor','WindSpeedBasic_ms','LoadCombination','ImpactFactorCoeff','TemperatureLoadDeltaT']
for name in d2:
    if name in types.ENUM_REGISTRY:
        c = len(list(types.ENUM_REGISTRY[name]))
        print(f'  OK {name}: {c}')
    else:
        print(f'  MISSING {name}')
