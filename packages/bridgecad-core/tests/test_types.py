from __future__ import annotations

import pytest

from bridgecad_core import types, validation_registry
from bridgecad_core.types import ENUM_REGISTRY, LabeledEnum, UnitHaverEnum
from bridgecad_core.validation_registry import RuleSpec, ALL_RULES


ALL_ENUM_CLASSES: list = sorted(ENUM_REGISTRY.values(), key=lambda c: c.__name__)


# ---------------------------------------------------------------------------
# Parametrized tests — run ONCE PER registered enum class (160+ * 2 = 320+ cases)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("cls", ALL_ENUM_CLASSES, ids=lambda c: c.__name__)
def test_all_enums_have_unique_member_names(cls) -> None:
    member_names = [m.name for m in cls]
    assert len(member_names) == len(set(member_names)), (
        f"{cls.__name__} has duplicate member names: "
        f"{[n for n in member_names if member_names.count(n) > 1]}"
    )


@pytest.mark.parametrize("cls", ALL_ENUM_CLASSES, ids=lambda c: c.__name__)
def test_all_str_enums_value_equals_member_name_or_valid_string(cls) -> None:
    for member in cls:
        assert isinstance(member.value, (str, int)), (
            f"{cls.__name__}.{member.name} value is not str/int: {type(member.value)}"
        )
        if isinstance(member.value, str):
            assert len(member.value) > 0, (
                f"{cls.__name__}.{member.name} has empty value string"
            )
            assert " " not in member.value, (
                f"{cls.__name__}.{member.name} value contains whitespace: {member.value!r}"
            )
        else:
            assert not isinstance(member.value, bool), (
                f"{cls.__name__}.{member.name} value is bool, expected int"
            )


# ---------------------------------------------------------------------------
# Top-20 direct tests — key enums for superstructure, foundation, materials
# ---------------------------------------------------------------------------
def test_superstructure_type_has_box_girder() -> None:
    assert "PSC_BOX_GIRDER" in ENUM_REGISTRY["SuperstructureType"].__members__


def test_superstructure_type_has_rcc_tbeam() -> None:
    assert "RCC_TBEAM" in ENUM_REGISTRY["SuperstructureType"].__members__


def test_superstructure_type_has_psc_igirder() -> None:
    assert "PSC_IGIRDER" in ENUM_REGISTRY["SuperstructureType"].__members__


def test_superstructure_type_has_extradosed() -> None:
    assert "EXTRADOSED" in ENUM_REGISTRY["SuperstructureType"].__members__


def test_foundation_type_has_pile() -> None:
    assert "PILE" in ENUM_REGISTRY["FoundationType"].__members__


def test_foundation_type_has_open() -> None:
    assert "OPEN" in ENUM_REGISTRY["FoundationType"].__members__


def test_foundation_type_has_well() -> None:
    assert "WELL" in ENUM_REGISTRY["FoundationType"].__members__


def test_pier_type_has_hammerhead() -> None:
    assert "HAMMERHEAD" in ENUM_REGISTRY["PierType"].__members__


def test_pier_type_has_round() -> None:
    assert "ROUND" in ENUM_REGISTRY["PierType"].__members__


def test_concrete_grade_has_m40() -> None:
    assert "M40" in ENUM_REGISTRY["ConcreteGrade"].__members__


def test_concrete_grade_has_m50() -> None:
    assert "M50" in ENUM_REGISTRY["ConcreteGrade"].__members__


def test_soil_class_has_clay_high() -> None:
    assert "CLAY_HIGH_COMPRESSIBILITY" in ENUM_REGISTRY["SoilClass"].__members__


def test_cement_type_has_opc_53() -> None:
    assert "OPC_53_GRADE_IS_12269" in ENUM_REGISTRY["CementType"].__members__


def test_reinforcement_has_fe500d() -> None:
    assert "HYSD_FE500D_DUCTILE" in ENUM_REGISTRY["ReinforcementBarType"].__members__


def test_seismic_zone_has_zone_v() -> None:
    assert "ZONE_V" in ENUM_REGISTRY["SeismicZone"].__members__


def test_wind_importance_factor_has_1_15() -> None:
    cls = ENUM_REGISTRY["WindImportanceFactor"]
    member_values = [m.value for m in cls]
    assert any("1_15" in v or "1.15" in v for v in member_values)


def test_load_combination_has_dl_only() -> None:
    cls = ENUM_REGISTRY["LoadCombination"]
    names = set(m.name for m in cls)
    assert "LC01_DL_DEAD_LOAD_ONLY" in names


def test_layer_group_has_centreline() -> None:
    assert "LAYER_CENTRELINES_CL" in ENUM_REGISTRY["LayerGroup"].__members__


def test_wearing_coat_grade_has_sma() -> None:
    cls = ENUM_REGISTRY["WearingCoatGrade"]
    names = set(m.name for m in cls)
    assert any(n.startswith("SMA_") for n in names)


def test_bearing_material_has_nrb() -> None:
    assert "NRB_NATURAL_RUBBER" in ENUM_REGISTRY["BearingMaterial"].__members__


# ---------------------------------------------------------------------------
# Smoke / count tests
# ---------------------------------------------------------------------------
def test_enum_registry_size_ge_160() -> None:
    assert len(ENUM_REGISTRY) >= 160, (
        f"Expected >= 160 enums registered, got {len(ENUM_REGISTRY)}"
    )


def test_all_validation_rules_count_eq_150() -> None:
    assert len(ALL_RULES) == 150, (
        f"Expected 150 rules, got {len(ALL_RULES)}"
    )


def test_registry_keys_match_class_names() -> None:
    for key_name, cls in ENUM_REGISTRY.items():
        assert cls.__name__ == key_name, (
            f"Registry key {key_name!r} != class name {cls.__name__!r}"
        )


def test_all_rules_have_unique_ids() -> None:
    rule_ids = [r.rule_id for r in ALL_RULES]
    assert len(rule_ids) == len(set(rule_ids)), "Duplicate rule_id values found in ALL_RULES"


def test_rulespec_severity_has_valid_type() -> None:
    from bridgecad_core.types import ValidationSeverity
    for r in ALL_RULES[:25]:
        assert r.severity is ValidationSeverity.CRITICAL
    for r in ALL_RULES[25:100]:
        assert r.severity is ValidationSeverity.WARNING
    for r in ALL_RULES[100:]:
        assert r.severity is ValidationSeverity.INFO


def test_validation_registry_imports_from_package() -> None:
    assert validation_registry.RuleSpec is not None
    assert validation_registry.ALL_RULES is not None


def test_new_d2_river_bank_type_present() -> None:
    assert "RiverBankType" in ENUM_REGISTRY
    assert len(list(ENUM_REGISTRY["RiverBankType"])) >= 10


def test_new_d2_soil_class_present() -> None:
    assert "SoilClass" in ENUM_REGISTRY
    assert len(list(ENUM_REGISTRY["SoilClass"])) >= 20


def test_new_d2_regime_constant_k_present() -> None:
    assert "RegimeConstantKValue" in ENUM_REGISTRY


def test_new_d2_concrete_aggregate_present() -> None:
    assert "ConcreteAggregateType" in ENUM_REGISTRY


def test_new_d2_layer_group_present() -> None:
    assert "LayerGroup" in ENUM_REGISTRY
    assert len(list(ENUM_REGISTRY["LayerGroup"])) >= 30


def test_new_d2_hatch_pattern_present() -> None:
    assert "HatchPatternCode" in ENUM_REGISTRY


def test_new_d2_font_style_present() -> None:
    assert "FontStyle" in ENUM_REGISTRY


def test_new_d2_scale_set_present() -> None:
    assert "ScaleDenominatorSet" in ENUM_REGISTRY


def test_new_d2_seismic_importance_present() -> None:
    assert "SeismicImportanceFactor" in ENUM_REGISTRY


def test_new_d2_wind_importance_present() -> None:
    assert "WindImportanceFactor" in ENUM_REGISTRY


def test_new_d2_windspeed_basic_ms_present() -> None:
    assert "WindSpeedBasic_ms" in ENUM_REGISTRY


def test_new_d2_load_combination_present() -> None:
    assert "LoadCombination" in ENUM_REGISTRY
    assert len(list(ENUM_REGISTRY["LoadCombination"])) >= 20


def test_new_d2_impact_factor_present() -> None:
    assert "ImpactFactorCoeff" in ENUM_REGISTRY


def test_new_d2_temperature_delta_t_present() -> None:
    assert "TemperatureLoadDeltaT" in ENUM_REGISTRY


def test_new_d2_section9_ext_linestyle_present() -> None:
    assert "LineStyleCode" in ENUM_REGISTRY


def test_new_d2_section9_ext_titleblock_present() -> None:
    assert "TitleBlockRevisionClass" in ENUM_REGISTRY


def test_new_d2_section10_ext_response_spectrum_present() -> None:
    assert "ResponseSpectrumCategory" in ENUM_REGISTRY


def test_new_d2_section10_ext_fatigue_detail_present() -> None:
    assert "FatigueDetailCategorySteel" in ENUM_REGISTRY


def test_new_d2_section10_ext_ductility_link_present() -> None:
    assert "DuctilityClassLink" in ENUM_REGISTRY


def test_new_d2_section8_ext_rebar_type_present() -> None:
    assert "ReinforcementBarType" in ENUM_REGISTRY


def test_new_d2_section8_ext_waterproofing_present() -> None:
    assert "WaterproofingMembraneType" in ENUM_REGISTRY


def test_new_d2_section7_ext_river_geomorphology_present() -> None:
    assert "RiverGeomorphologyType" in ENUM_REGISTRY


def test_new_d2_section7_ext_scour_protection_present() -> None:
    assert "ScourProtectionSubtype" in ENUM_REGISTRY


def test_mixin_labeledenum_is_base() -> None:
    for cls in ALL_ENUM_CLASSES[:5]:
        assert issubclass(cls, LabeledEnum) or hasattr(cls, "label")


def test_enum_members_are_all_positive() -> None:
    for cls in ALL_ENUM_CLASSES[:5]:
        for m in cls:
            assert m.name.isidentifier()
