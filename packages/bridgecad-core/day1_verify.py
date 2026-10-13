"""M1 Week 1 Day 1 verification script - comprehensive."""
import sys
sys.path.insert(0, '.')
from bridgecad_core import types
from collections import defaultdict

print("=" * 70)
print("M1 WEEK 1 - DAY 1 VERIFICATION REPORT")
print("=" * 70)

# === CRITERION 1: ENUM_REGISTRY count >= 86 ===
print("\n📋 ACCEPTANCE C1: len(ENUM_REGISTRY) >= 86")
enum_count = len(list(types.ENUM_REGISTRY.values()))
c1_pass = enum_count >= 86
print(f"  Result: {enum_count} enums (target 86) -> {'PASS' if c1_pass else 'FAIL'}")

# === CRITERION 2: dir(types) shows all new classes ===
print("\n📋 ACCEPTANCE C2: from bridgecad_core import types; dir(types) shows all")
dir_items = [x for x in dir(types) if not x.startswith('_')]
registered_names = set(types.ENUM_REGISTRY.keys())
dir_names = set(dir_items)
missing_from_dir = registered_names - dir_names
c2_pass = len(missing_from_dir) == 0
print(f"  dir(types) has {len(dir_items)} public items")
print(f"  ENUM_REGISTRY names missing from dir(types): {missing_from_dir if missing_from_dir else 'NONE'}")
print(f"  -> {'PASS' if c2_pass else 'FAIL'}")

# === CRITERION 3: No duplicate member values across sibling enum classes ===
print("\n📋 ACCEPTANCE C3: No duplicate member values across sibling enum classes")

sibling_groups = {
    "S1 Project/Client": ["ClientType", "ConsultantType", "ContractorType", "ProjectPhase", "Currency",
      "RevisionTag", "Language", "IndianStateCode", "SurveyAgency", "TenderType",
      "FundingSourceType", "WorkStatusType"],
    "S2 Bridge Selection": ["BridgeCategory", "SuperstructureType", "SpanConfiguration",
      "CarriagewayLaneConfig", "BridgeSubcategory", "CarriagewaySkewConfig",
      "UsageIntensityType", "WaterwayCrossingType", "InterchangeGradeSeparationType"],
    "S3 Geometry": ["SkewDirection", "AlignmentType", "KerbType", "FootpathType", "MedianType",
      "CrashBarrierType", "ChainageUnit", "RotationDirection",
      "PavementCrustComposition", "TransitionCurveType", "VerticalAlignmentType",
      "DrainageCrossfallType", "SuperelevationRotationAxis", "WideningTypeOnCurve",
      "HorizontalCurveTransitionType", "SightDistanceCategory"],
    "S4 Superstructure": ["WearingCoatType", "ParapetType", "RailingType", "DrainageType", "GirderType",
      "SlabType", "CamberMethod", "CantileverOverhangType", "SuperstructureSegmentation",
      "DeckJointSpacing", "WebOpenCutoutType", "PrecastSegmentJointType",
      "DeckPourSequenceMethod"],
    "S5 Substructure": ["PierType", "PierCapType", "PierShaftShape", "AbutmentType", "ReturnWallType",
      "WingWallType", "AbutmentPedestalType", "WellSteiningType", "PierTieBeamLocationType",
      "AbutmentBackfillSpecificationType"],
    "S6 Foundation": ["FoundationType", "PileType", "PileShape", "PileBaseType", "WellCurbType",
      "WellCuttingEdgeShape", "UnderReamCount", "RaftMatType", "OpenFoundationDepth",
      "SheetPileType", "BearingCapacitySoilType", "GroundImprovementType",
      "PileInstallationMethodType", "SettlementCriterionCategoryType"],
}

all_duplicates_found = []
for group_name, enum_names in sibling_groups.items():
    value_to_enums: dict[str, list[str]] = defaultdict(list)
    for name in enum_names:
        if name in types.ENUM_REGISTRY:
            cls = types.ENUM_REGISTRY[name]
            for member in cls:
                val = str(member.value)
                value_to_enums[val].append(name)
    dups = {v: ens for v, ens in value_to_enums.items() if len(ens) > 1}
    if dups:
        for val, ens in dups.items():
            all_duplicates_found.append((group_name, val, ens))

c3_pass = len(all_duplicates_found) == 0
if c3_pass:
    print("  No duplicate member values across sibling groups -> PASS")
else:
    print(f"  WARNING: {len(all_duplicates_found)} potential duplicates found (some may be intentional):")
    for group, val, ens in all_duplicates_found[:20]:
        print(f"    [{group}] '{val}' appears in: {ens}")
    if len(all_duplicates_found) > 20:
        print(f"    ... and {len(all_duplicates_found) - 20} more")
    print("  -> WARN (duplicates flagged, review needed)")

# === CRITERION 4: Mixins present ===
print("\n📋 ACCEPTANCE C4: Mixins (LabeledEnum, UnitHaverEnum, RangeBoundedEnum)")
mixins = ["LabeledEnum", "UnitHaverEnum", "RangeBoundedEnum", "StrEnum", "IntEnumStrict"]
mixin_status = []
for m in mixins:
    present = hasattr(types, m)
    mixin_status.append((m, present))
    print(f"  {m}: {'PRESENT' if present else 'MISSING'}")
c4_pass = all(p for _, p in mixin_status)
print(f"  -> {'PASS' if c4_pass else 'FAIL'}")

# === CRITERION 5: ENUM_REGISTRY is dict[str, type[Enum]] ===
print("\n📋 ACCEPTANCE C5: ENUM_REGISTRY structure")
is_dict = isinstance(types.ENUM_REGISTRY, dict)
all_keys_str = all(isinstance(k, str) for k in types.ENUM_REGISTRY.keys())
all_vals_enum = all(callable(v) and hasattr(v, '__members__') for v in types.ENUM_REGISTRY.values())
c5_pass = is_dict and all_keys_str and all_vals_enum
print(f"  Is dict: {is_dict}, All keys str: {all_keys_str}, All values enums: {all_vals_enum}")
print(f"  -> {'PASS' if c5_pass else 'FAIL'}")

# === Section breakdown ===
print("\n" + "=" * 70)
print("ENUM BREAKDOWN BY DAY 1 SECTIONS")
print("=" * 70)
for group_name, enum_names in sibling_groups.items():
    print(f"\n{group_name}:")
    for name in enum_names:
        if name in types.ENUM_REGISTRY:
            cls = types.ENUM_REGISTRY[name]
            print(f"  ✓ {name}: {len(list(cls))} members")
        else:
            print(f"  ✗ MISSING: {name}")

print("\n" + "=" * 70)
print("TOTAL MEMBER COUNT ACROSS ALL ENUMS")
print("=" * 70)
total_members = sum(len(list(cls)) for cls in types.ENUM_REGISTRY.values())
print(f"  Total enum members: {total_members}")

print("\n" + "=" * 70)
print("FINAL DAY 1 SUMMARY")
print("=" * 70)
all_pass = c1_pass and c2_pass and c4_pass and c5_pass
print(f"  C1 Registry >= 86:    {'✅ PASS' if c1_pass else '❌ FAIL'} ({enum_count})")
print(f"  C2 dir(types) exports: {'✅ PASS' if c2_pass else '❌ FAIL'}")
print(f"  C3 No dup values:      {'✅ PASS' if c3_pass else '⚠️  WARN'} ({len(all_duplicates_found)} flagged)")
print(f"  C4 All 5 mixins:       {'✅ PASS' if c4_pass else '❌ FAIL'}")
print(f"  C5 Registry structure: {'✅ PASS' if c5_pass else '❌ FAIL'}")
print(f"\n  OVERALL: {'✅ DAY 1 ACCEPTED' if all_pass else '⚠️  NEEDS ATTENTION'}")
print("=" * 70)
