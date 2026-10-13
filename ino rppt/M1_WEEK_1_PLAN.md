# M1 Core Domain — WEEK 1 (of 3) Plan
> **Codename:** BRIDGECAD-OSS-1.0-M1W1
> **Start Date:** 2026-09-30
> **End Date:** 2026-10-06 (5 working days)
> **M1 Objective:** 200+ enums, Pydantic V2 14-sheet models, 150 QA rules, 4 geometry modules
> **Week 1 Objective:** Types + Model Schema Layer + Validation Wiring + Unit Test Framework
> **Exit Criteria:** 200 enum target met, 14 Pydantic sub-models fully field-populated with constraints, 25 critical QA checks (V001–V025) passing, 100+ pytest cases, types + models coverage ≥ 85%

---

## Gap Audit (before Week 1)

| Target | M0 today | Gap |
|--------|----------|-----|
| Enums | 21 enums (≈30 members) | ⚠️ 179+ enums/members to add |
| 14 sheet models | Skeleton (1-5 fields each) | ⚠️ ~380 fields missing (avg 27 fields/sheet) |
| Geometry modules | Empty placeholders | Week 2/3 — skip this week |
| Validation | Empty RulesEngine + 1 stub V001 | 149 check functions to add |
| Unit tests | 0 files | 100+ test cases needed |

---

## 5-Day Breakdown

---

### 📅 DAY 1 — 200+ Enums: Sections 1–6 (types.py)
**File changed:** [packages/bridgecad-core/bridgecad_core/types.py](file:///E:/Rajkumar/Bridge_GAD_Yogendra_Borse/BridgeCAD%20Enterprise%20Suite/packages/bridgecad-core/bridgecad_core/types.py)
**Lines of code target:** +1450 lines
**Est. enum classes added:** 65 classes (Sections 1–6)

| # | Section | Enum Classes to Add | Members Count |
|---|---------|---------------------|---------------|
| 1 | Project / Client | `ClientType`, `ConsultantType`, `ContractorType`, `ProjectPhase`, `Currency`, `RevisionTag` | 30 |
| 2 | Bridge Selection | `SpanConfiguration` (Simply/Continuous/Cantilever/CableStayed/Suspension), `CarriagewayLaneConfig` (1L/2L/3L/4L/6L/Multi), `BridgeSubcategory` (Minor 12m/Minor 15m/Major 3×12m/Viaduct 10×30m/ROB/RUB/FOB single/FOB multi/BoxCulvert8m/PipeCulvert1500/…) | 25 |
| 3 | Geometry | `AlignmentType` (Straight/Circular/Spiral/Compound), `KerbType` (Mountain/Vertical/Sloped), `FootpathType` (None/Footpath/CycleTrack), `MedianType` (None/Rigid/Flexible), `CrashBarrierType` (MetalBeam/RCC/SemiRigid), `ChainageUnit` (m/Km), `RotationDirection` (CW/CCW) | 20 |
| 4 | Superstructure | `WearingCoatType` (BC/SMA/MS/DBST/AsphalticConcrete), `ParapetType` (RCC/MetalCrash/SS304Pipe), `RailingType`, `DrainageType` (Scupper/InletPipe/EdgeChannel), `GirderType` (I/Box/T/Delta/Plate/Truss), `SlabType`, `CamberMethod` (Parabolic/Linear/Pre-camber), `CantileverSlabOverhangType` | 40 |
| 5 | Substructure | `ReturnWallType` (Cantilever/Buttress/None), `WingWallType` (Parallel/Perpendicular/Splayed/Tapered), `PierCapType` (Drop/NonDrop/Flared), `PierShaftShape` (Rectangular/Circular/Hex/Dumbbell), `AbutmentPedestalType`, `WellSteiningType` | 30 |
| 6 | Foundation | `PileType` (BoredCastInSitu/Driven/UnderReamed/Micro/Compaction), `PileShape` (Circular/Square/Octagonal), `PileBaseType` (Flat/Bulb/UnderReamed), `WellCurbType` (RCC/Steel), `WellCuttingEdgeShape` (StraightChamfered/Conical), `UnderReamCount` (0/1/2/3), `RaftMatType`, `OpenFoundationDepth` (Shallow/Deep/Stepped), `SheetPileType` | 45 |

#### Sub-tasks D1
- [ ] Re-order types.py into 10 explicit section headers with comment dividers
- [ ] Add all 65 new enum classes above with members
- [ ] Add helper mixins: `LabeledEnum` (label), `UnitHaverEnum` (unit), `RangeBoundedEnum` (min/max)
- [ ] Add `ENUM_REGISTRY` dict at bottom (enum_name → class) for Excel template generator
- [ ] Append new enums to `__all__` list (keep alphabetical within sections)

#### Acceptance D1
- `len(list(ENUM_REGISTRY.values())) >= 86` (21 existing + 65 new)
- `from bridgecad_core import types; dir(types)` shows all new classes
- No duplicate member values across sibling enum classes
- mypy — types.py clean (no errors)

---

### 📅 DAY 2 — 200+ Enums: Sections 7–10 + Validation Rules Registry
**File changed:** `packages/bridgecad-core/bridgecad_core/types.py`
**Files created:**
  - `packages/bridgecad-core/bridgecad_core/validation_registry.py`
  - `packages/bridgecad-core/tests/test_types.py`
**Lines target:** +900 (types) / +220 (validation_registry) / +600 (tests)

| # | Section | Enum Classes to Add | Members Count |
|---|---------|---------------------|---------------|
| 7 | Hydraulic | `WaterSourceType` (River/Nala/Culvert/Drain/Rainfall/Tidal), `ScourRegime` (Lacey/Regime/USGS/Pelton), `HydrographType`, `BankType`, `SoilClass` (Clay/Silt/Sand/Gravel/Rock), `AffluxFormulaType` (KindsvaterCarter/Yarnell), `RegimeConstantKValue` | 30 |
| 8 | Materials | `ConcreteAggregateType`, `CementType` (OPC/PPC/PSC), `AdmixtureType`, `WeldType`, `BearingMaterial` (NRB/Nitrile/Urethane/SteelBack), `JointSealantType`, `WearingCoatGrade` | 30 |
| 9 | Drawing | `LayerGroup` (Centrelines/DeckStructure/Substructure/Foundation/Dimensions/Hatching/Annotations/Hydraulics/Tables/TitleBlock — matches IRC:SP:55), `LineWeightCode` (0.13/0.18/0.25/0.35/0.50/0.70 mm), `HatchPatternCode` (SOLID/ANSI31/ANSI32/DOTS/EARTH/CONCRETE), `FontStyle` (ISOCPEUR/ROMANS/SIMPLEX/STANDARD), `ArrowStyle` (Closed/Open/Dot/ArchitecturalTick), `ScaleDenominatorSet` | 40 |
| 10 | Load / Seismic / Wind | `SeismicImportanceFactor`, `WindImportanceFactor`, `WindSpeedBasic_ms` (33/39/44/47/50/55), `LoadCombination` (DL+LL/DL+LL+EQ/DL+WIND/…), `ImpactFactorCoeff`, `TemperatureLoadDeltaT` | 20 |

#### Also D2: Validation Registry Skeleton
File: `validation_registry.py`
- Define dataclass `RuleSpec(rule_id, title, sheet_ref, field_refs, severity, owner_module, run_after=[])`
- Define hardcoded list `ALL_RULES: list[RuleSpec] = [...]` with all 150 rule IDs (15 Critical C01–C25, 75 Warning W01–W75, 50 Info I01–I50)
- Week 1: Implement bodies for **C01–C25 Critical rules only** in `validation.py` (others added Weeks 2–3)

#### Also D2: Test suite for enums
File: `tests/test_types.py`
- Parameterised test: every enum has unique member names/values
- Parameterised test: every enum member is a valid `StrEnum` (has `.value`)
- Coverage for top-20 enums (superstructure, pier, foundation, concrete grades) with realistic usage

#### Acceptance D2
- `len(ENUM_REGISTRY.values()) >= 160` (total 200-target buffer)
- `ALL_RULES` list length == 150 IDs (skeleton bodies will follow D3–D5)
- `pytest tests/test_types.py -q` → 50+ cases PASS

---

### 📅 DAY 3 — 14 Sheet Pydantic Models (Fields 100% Complete)
**File changed:** [packages/bridgecad-core/bridgecad_core/models.py](file:///E:/Rajkumar/Bridge_GAD_Yogendra_Borse/BridgeCAD%20Enterprise%20Suite/packages/bridgecad-core/bridgecad_core/models.py)
**Line target:** +2000 lines (replace skeleton)

| Sheet (class) | Est. fields | Key fields to add from Excel template generator spec |
|---------------|-------------|-----------------------------------------------------|
| `ProjectMaster` | 25 | project_title (len 100), project_code (pattern `[A-Z]+-\d{4}-\d{3}`), bridge_name, chainage_km, package_no, client (enum), consultant, contractor, drawing_no, drawing_title, revision, date, designed_by, checked_by, approved_by, road_level_rl, ground_level_rl, survey_date, state_code, district_code, language, lattitude, longitude, total_estimated_cost, tender_no, contract_no |
| `BridgeSelection` | 16 | bridge_category, bridge_type, span_configuration, span_count, carriageway_config, design_code, loading_class, seismic_zone, wind_zone_ms, foundation_type, subcategory_tag, custom_superstructure_note, custom_substructure_note, climate_zone, terrain_category, corridor_type |
| `GeometryInput` | 45 | alignment/sections: road_width, design_speed, horizontal_curve_R_m, gradient_pct, **+ 10 more span_m list with validation**, carriageway_width, footpath_left/right, crash_barrier_width, kerb_width, median_width, skew_angle/direction, curved_bridge, curve_radius_m, camber_mm, vertical_curve_passing_R_m, superelevation_pct, median_barrier_width, left/right_ditch_width, service_road_left/right_m, pavement_thickness_total_mm, crust_layer_count, chainage_start_km, chainage_end_km, bearing_pad_spacing_m, minimum_curve_speed_check_required |
| `Superstructure` | 40 | type, deck_material, deck_thickness_mm, wearing_coat_type/thickness/slope_pct, camber_mm, girder_type/depth_mm/spacing_m, parapet_type/height, drainage_type/spacing_m, slab_effective_flange_width_check, bearing_shelf_width_m, kerb_elevation_m, footpath_elevation_m, crash_barrier_reinforcement_required, girders_per_deck_count, transverse_diaphragm_spacing_m, continuity_slab_thickness_mm, haunch_height_mm, cable_duct_required, stay_sag_ratio_for_cable |
| `Substructure` | 45 | pier_type/material, pier_height_typical_m, pier_cap (width/length/depth), pier_shaft (width/length/shape), pier_pedestal_height_m, abutment_type/material, abutment (width/length/height), abutment_pedestal_height_m, return_wall_type/size, wing_wall_type/angle/splay, backfill_type, approach_slab (length/thickness), pier_diaphragm_required, pier_hammerhead_overhang_m, well_cap_width_m, pile_cap_thickness_m, bearings_per_pier, bearings_per_abutment |
| `FoundationDetails` | 35 | type, pile type/diameter_mm/length_m/piles_per_pier/pile_group_config/spacing, pile_cap (thickness, cutoff_level_m), well (diameter_m, steining_tmm, depth_below_bed_m, curb_height_m, sump_depth_m), open (width_m, depth_m, stepped), raft (thickness_mm, reinforcement_dia), combined footing (l/w), under_ream_count, factor_of_safety_on_bearing, bearing_capacity_kpa |
| `Approaches` | 20 | left/right_approach_length_m, retaining_wall_type/height, type_of_embankment, soil_embankment_unit_weight, approach_slope_width_m, shoulder_width_left/right, guide_rail_required, sign_gantry_required, speed_limit_on_approach, transition_curve_length, vertical_alignment |
| `HydraulicData` | 30 | design_discharge_cumecs, hfl/lwl/normal_wl_m, **scour_level_m**, design_scour_depth_m, freeboard_m, **actual_soffit_level_m**, waterway_required/provided_m², regime_waterway_coeff, lacey_silt_factor, regime_perimeter_m, regime_depth_m, regime_velocity_mps, afflux_m, max_afflux_allowable_m, water_source_type, soil_class, river_bed_slope, catchment_area_sqkm, return_period_yr, any_regime_equation_not_applied_flag, highest_recorded_flood_year |
| `Materials` | 25 | concrete_super/sub/foundation, rebar, prestress, bearing, expansion_joint, wearing_coat_material_type, aggregate_type, cement_type, admixture_required, joint_sealant_type, weld_type_for_steel, brick_type_for_return_walls, mortar_type, backfill_material, metal_parapet_finish |
| `BearingsJoints` | 22 | bearing_schedule_rows (N rows with type/size_x/size_y/load_kn/fixed_or_guide_or_free/location/quantity/ELASTOMERIC_layers/steel_back_bool/POT_pressure/SPHERICAL_rotation_rad), expansion_joint_schedule (rows: type/width_mm/movement_range_mm/gap_mm/sealant_type/anchor_spacing/mm/location/quantity) |
| `ComponentsLib` | 18 | standard_pier_tag, standard_abutment_tag, standard_foundation_tag, typical_girder_library_key, standard_parapet_id, standard_railing_id, standard_retaining_wall_id, standard_kerb_id, standard_crash_barrier_id, standard_bearing_typical_pair_id, standard_expansion_joint_id, standard_drainage_outlet_id, standard_pile_group_template_id, standard_wing_wall_id, standard_return_wall_id, standard_approach_slab_id |
| `DrawingControl` | 30 | output_formats list, autocad_version, sheet_size, drawing_scale, generate (plan/long_section/cross_section/foundation/reinforcement/pier_details/abutment_details/bearings_joints/boq/cover_sheet/legends_sheet/hydraulics_sheet), drawing_rotation_deg, layer_standard, title_block_style, dimension_precision_mm, text_height_scale_factor, lineweight_scale_factor, north_arrow_size, scale_bar_length, plot_style_used, drawing_border_inside_mm, revision_block_count, legend_sheet_required |
| `Calculations` | 22 | total_length_m, span_count, span_depth_ratio, deck_area_sqm, overall_width_check_ok, concrete_volume_superstructure/substructure/foundation_total_cum, rebar_weight_tonnes_approx, prestress_tonnes_approx, bearing_count, expansion_joint_count, total_estimated_quantity_cost_inr, design_scour_vs_foundation_cover_ok, waterway_check_pass, afflux_ok, freeboard_actual_m, minimum_vertical_clearance_m, horizontal_clearance_m, impact_factor_applied, seismic_coeff_applied, deflection_check_ratio_live_load |
| `ValidationModel` | 12 | overall_status (PASS/WARN/FAIL), critical_fail_count, warning_count, info_count, score_0_to_100, score_irc05, score_irc21, score_ircsp55, score_structural, score_hydraulic, score_drawing_standards, report_html_or_pdf_generated_flag, last_validated_at_iso_datetime, check_version_tag |

#### Sub-tasks D3
- [ ] For every class, add `model_config = ConfigDict(validate_assignment=True, extra="forbid")`
- [ ] Use typed `Decimal` for lengths/volumes/costs; `int` for mm/counts; `bool` for flags
- [ ] Add `Field(ge=, le=, max_digits=, decimal_places=, pattern=, description=)` everywhere. Keep descriptions aligned to Excel sheet "Description" column
- [ ] Add `@computed_field` where appropriate: e.g., `total_length_m = sum(span_lengths_m)`, `overall_width_m = carriageway + kerbs*2 + barriers*2 + footpaths + median`, `freeboard_actual = actual_soffit_level_m - hfl_m`

#### Acceptance D3
- `BridgeProject.model_json_schema()` generates a schema ≥ 40 KB
- Construct a `BridgeProject(**SAMPLE_PROJECT_MINOR_BRIDGE_12M)` → validates OK
- Construct with 10 obvious bad values → raises clear pydantic ValidationError per field
- `mypy models.py` → 0 errors

---

### 📅 DAY 4 — 25 Critical QA Checks Implement + Validation Integration
**Files changed/created:**
  - [packages/bridgecad-core/bridgecad_core/validation.py](file:///E:/Rajkumar/Bridge_GAD_Yogendra_Borse/BridgeCAD%20Enterprise%20Suite/packages/bridgecad-core/bridgecad_core/validation.py)
  - `packages/bridgecad-core/tests/test_validation.py`
  - `packages/bridgecad-core/tests/fixtures_projects.py`
**Lines target:** +1800 (validation.py) / +1200 (tests)

#### 25 Critical Checks to Deliver (Week 1 = C-tier only)
| ID | Title | Sheet(s) | Pass Condition |
|----|-------|----------|----------------|
| C01 | project_code_format | PM | `re.match(r"^[A-Z]+-\d{4}-\d{3}$", pm.project_code)` |
| C02 | bridge_name_set | PM | `pm.bridge_name` not empty |
| C03 | span_count_consistency | BS + GI | `bs.span_count == len(gi.span_lengths_m) >= 1` |
| C04 | hfl_greater_than_lwl | HD | `hd.hfl_m > hd.lwl_m` (if both set) |
| C05 | soffit_gt_hfl_plus_freeboard | HD | `hd.actual_soffit_level_m >= hd.hfl_m + hd.freeboard_m` (with 5mm tolerance) |
| C06 | foundation_cover_below_scour | FD + HD | `fd.cutoff_level_m or well_depth or pile_bottom` is `< (hd.scour_level_m - design_scour_depth × safety_margin_2)` |
| C07 | overall_width_gt_carriageway | GI | `gi.overall_width_m > gi.carriageway_width_m + 2*0.15` (min kerb safety) |
| C08 | materials_concrete_not_empty | Mat | `concrete_super/sub/foundation` all set (not None) |
| C09 | materials_steel_not_empty | Mat | `reinforcement_steel` != None |
| C10 | bearings_per_pier_consistent | Sub + BearJn | `sub.bearings_per_pier matches sum(pier bearings_schedule rows at pier locs)` |
| C11 | carriageway_lane_configuration_width_check | GI + BS | `BS.2-lane ⇒ 7.0 ≤ carriageway ≤ 7.5m`, 4-lane 14.0–15.0m, etc. |
| C12 | span_lengths_positive | GI | `all(L > 0 for L in span_lengths_m)` and `all(L < 150m for …)` (max box girder span limit) |
| C13 | span_length_count_match_span_count | GI + BS | `len(span_lengths_m) == span_count` |
| C14 | concrete_grade_superstructure_minimum | Mat + BS | `M30 minimum for Major; M25 for Culvert; M20 for minor (enums by BS.category)` |
| C15 | skew_angle_bounds | GI | `0 ≤ skew_angle_deg ≤ 60` (IRC limit) |
| C16 | pile_diameter_in_valid_range | FD | `if foundation=PILE → 400 ≤ pile_diameter_mm ≤ 2000` |
| C17 | pile_length_bounds | FD | `if PILE → 5m ≤ pile_length_m ≤ 60m` |
| C18 | pier_height_bounds | Sub | `2m ≤ pier_height ≤ 50m` (typical IRC range) |
| C19 | abutment_dimensions_non_zero | Sub | `abutment width/length/height all > 0` |
| C20 | bearings_joints_schedule_not_empty | BearJn | `len(bearing_schedule) ≥ 2 and len(expansion_joint_schedule) ≥ 1` |
| C21 | hydraulic_source_matches_bridge_category | HD + BS | Culvert: source=DRAIN/NALA/RIVER allowed; ROB: source=NA allowed; |
| C22 | approach_slope_thickness_non_negative | Appr | `≥0` for all approach lengths/thicknesses |
| C23 | design_discharge_and_catchment_mutually_consistent | HD | If catchment > 1000 sqkm ⇒ discharge ≥ 100 cumecs (sanity) |
| C24 | drawing_control_has_output_format | DC | `len(output_formats) ≥ 1` |
| C25 | girder_depth_matches_superstructure_type | Supr + GI | If `PSC BOX → depth ≥ span/30` as first-pass span-depth check; T-beam span/20 lower bound etc. |

#### Tests Created (test_validation.py)
- One parametrized test per critical rule (25 tests)
- 2 fixture projects in `fixtures_projects.py`:
  - `SAMPLE_MINOR_12M_VALID` → passes every C-rule
  - `SAMPLE_MINOR_12M_WITH_12_BUGS` → triggers specific known failures
- Edge cases: None-allowed fields with `Optional` → rules that only fire when non-None use `.get() or None` safe

#### Acceptance D4
- `RulesEngine().run(SAMPLE_MINOR_12M_VALID).overall_status == "PASS"`  (score 100)
- Engine run on buggy fixture → finds ≥ 12 distinct C-rule failures
- pytest `tests/test_validation.py -q` → 75+ cases PASS

---

### 📅 DAY 5 — Pydantic model round-trip tests + standards helpers + CI wiring + Week 1 Sign-Off
**Files created / changed:**
  - `packages/bridgecad-core/tests/test_models_roundtrip.py`
  - `packages/bridgecad-core/tests/test_quantities_smoke.py`
  - `packages/bridgecad-core/bridgecad_core/standards/__init__.py` + 4 standards modules wiring (skeleton stubs → actual constants)
  - `pyproject.toml` root → add pytest coverage threshold
  - `Makefile` → add `make types-coverage`, `make week1-signoff`
  - `tests/conftest.py` → expose `SAMPLE_MINOR_12M_VALID` as pytest fixture

#### Sub-tasks D5
1. **Round-trip tests:** Construct `BridgeProject`, serialise to `.model_dump_json()`, re-parse → equal. Test for 3 scenarios (12m minor / 3×12m major / 8m box culvert)
2. **Standards wiring stubs:** Add at least 2 real constants per module:
   - `irc_sp55.py`: `SPANS_PER_SCALE_MIN_MAX`, `TEXT_HEIGHT_TABLE_MM`
   - `irc_05.py`: `LACEY_MIN_SCOUR_MULTIPLIER = 2.0`, `MAX_AFFLUX_M_DEFAULT = 0.3`
   - `irc_21.py`: `SPAN_DEPTH_RATIO_TABLE[SuperstructureType × SpanConfig] = (min,max,best)`
   - `morth_specs.py`: `MORTH_ITEM_CODE_LIMITS`, `UNIT_RATE_TOLERANCE_PCT = 15`
3. **Coverage thresholds:** `pytest --cov-fail-under=85` for M1 week1 target
4. **Add `make week1-signoff`** target → runs: `lint + typecheck + pytest --cov-fail-under=85 + roundtrip + smoke-quantities`
5. **Bug triage:** Fix any failures discovered during signoff run

#### Acceptance D5 (Week 1 Exit Criteria)
- ✅ `make week1-signoff` target exits 0
- ✅ Enum registry count ≥ 180
- ✅ 14 Pydantic models have ≥ 380 total fields
- ✅ 25 C-rule QA checks all have passing + failing tests
- ✅ pytest total ≥ 100 passing cases
- ✅ coverage report: core package ≥ 85%
- ✅ `BridgeProject.model_json_schema()` → valid JSON Schema ≥ 40 KB

---

## Week 1 Deliverables Summary

| Deliverable | File Path | Expected Size |
|-------------|-----------|---------------|
| 200+ Enums (Sections 1–10) | [types.py](file:///E:/Rajkumar/Bridge_GAD_Yogendra_Borse/BridgeCAD%20Enterprise%20Suite/packages/bridgecad-core/bridgecad_core/types.py) | 2350 lines, ~180 classes |
| 150-rule Registry (IDs + specs; bodies C01–25 only) | `validation_registry.py` | 220 lines |
| 14 Sheet Pydantic Models, 100% fields | [models.py](file:///E:/Rajkumar/Bridge_GAD_Yogendra_Borse/BridgeCAD%20Enterprise%20Suite/packages/bridgecad-core/bridgecad_core/models.py) | 2000 lines, 380+ fields |
| 25 Critical Check Implementations | [validation.py](file:///E:/Rajkumar/Bridge_GAD_Yogendra_Borse/BridgeCAD%20Enterprise%20Suite/packages/bridgecad-core/bridgecad_core/validation.py) | 1800 lines |
| Test: Types enum coverage | `tests/test_types.py` | 600 lines, 50 cases |
| Test: Validation C01–C25 | `tests/test_validation.py` | 1200 lines, 75 cases |
| Test: Model round-trip JSON | `tests/test_models_roundtrip.py` | 400 lines, 6 cases |
| Test: Fixture projects | `tests/fixtures_projects.py` | 300 lines, 3 fixtures |
| Standards: IRC + MORTH constants | `standards/{irc_sp55,irc_05,irc_21,morth_specs}.py` | 300 lines total |
| CI: Makefile sign-off target + pyproject coverage thresholds | `Makefile` + root `pyproject.toml` | +60 lines / +20 lines |

---

## Risk Register (Week 1)

| Risk | Impact | Mitigation |
|------|--------|------------|
| Enum explosion → duplicates | Medium | `ENUM_REGISTRY` validation test catches collisions |
| Pydantic field count underestimated | Low | Keep 1:1 match to Excel ADITIONAL_ITEMS sheet rows; add `extra = "allow"` fallback only temporarily, revert before D3 end |
| 25 Critical checks need cross-sheet lookups | Medium | D4 afternoon: review every rule, document all field refs in docstring per check |
| Coverage 85% missed | Low | D5 morning: write edge-case parametrized tests for enums/models to pad |

---

## Roll-Up into M1 Remaining (Week 2–3 preview)

| Week | Topic |
|------|-------|
| W1 (this plan) | Types + Models + Validation C-tier |
| **W2** | 75 Warning QA checks + 50 Info QA checks; geometry.plan + geometry.long_section pure math |
| **W3** | geometry.cross_section + geometry.foundation; quantities + costs extract; total coverage 90%; regression fixtures 3/28 running |

---

_Plan v1.0 frozen 2026-09-30. Next step: execute Day 1._
