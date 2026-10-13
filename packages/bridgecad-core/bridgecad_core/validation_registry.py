from __future__ import annotations

from dataclasses import dataclass

from bridgecad_core.types import ValidationSeverity, ENUM_REGISTRY


@dataclass(frozen=True)
class RuleSpec:
    rule_id: str
    severity: ValidationSeverity
    applies_to: frozenset[str]
    description: str
    reference_clause: str


_ALL_ENUM_NAMES: frozenset[str] = frozenset(ENUM_REGISTRY.keys())


def _a(names: list[str]) -> frozenset[str]:
    return frozenset(n for n in names if n in _ALL_ENUM_NAMES)


# ---------------------------------------------------------------------------
# C01-C25 — CRITICAL plan-level rules (IRC/MORTH mandatory clauses)
# ---------------------------------------------------------------------------
_CRITICAL_RULES: list[RuleSpec] = [
    RuleSpec("C01", ValidationSeverity.CRITICAL, _a(["ProjectStage"]), "Project stage must be defined and non-empty for every GAD deliverable", "IRC SP-55 Clause 1.2"),
    RuleSpec("C02", ValidationSeverity.CRITICAL, _a(["ClientType", "ProjectOwnerType"]), "Client and project owner identity must be populated before design freeze", "MORTH 5th Rev Clause 101.2"),
    RuleSpec("C03", ValidationSeverity.CRITICAL, _a(["BridgeCategory", "BridgeSelectionCriterion"]), "Bridge category shall be assigned per functional class and selection criteria verified", "IRC:112-2020 Clause 3.1"),
    RuleSpec("C04", ValidationSeverity.CRITICAL, _a(["BridgeLengthCode", "SpanArrangementClass"]), "Total length and span arrangement must be structurally coherent", "IRC SP-55 Clause 3.2"),
    RuleSpec("C05", ValidationSeverity.CRITICAL, _a(["CarriagewayWidthClass", "FootpathWidthClass"]), "Carriageway + footpath widths must not exceed overall deck width", "IRC:86-2018 Clause 4.3"),
    RuleSpec("C06", ValidationSeverity.CRITICAL, _a(["HorizontalAlignmentType"]), "Horizontal alignment on bridge shall be tangent unless curve radius > 300 m", "IRC:112 Clause 5.4"),
    RuleSpec("C07", ValidationSeverity.CRITICAL, _a(["VerticalAlignmentType", "CrownType"]), "Vertical gradient on deck must not exceed 1 in 30 for urban ROB", "IRC:86 Clause 4.2"),
    RuleSpec("C08", ValidationSeverity.CRITICAL, _a(["SuperstructureType", "DeckSlabType"]), "Superstructure-deck combination must be a standard IRC pairing", "IRC:112 Clause 6.1"),
    RuleSpec("C09", ValidationSeverity.CRITICAL, _a(["SubstructureType", "PierType", "AbutmentType"]), "Pier / abutment family must be consistent with declared substructure type", "IRC:78-2014 Clause 9"),
    RuleSpec("C10", ValidationSeverity.CRITICAL, _a(["FoundationType", "BearingType"]), "Bearing type must be valid for chosen foundation and superstructure system", "IRC:83 Part I Clause 7"),
    RuleSpec("C11", ValidationSeverity.CRITICAL, _a(["ExpansionJointClass"]), "Expansion joint class must be compatible with span length range", "IRC SP-55 Clause 7.3"),
    RuleSpec("C12", ValidationSeverity.CRITICAL, _a(["HydraulicDesignMethod", "DesignReturnPeriod"]), "Hydrological return period must match selected hydraulic design method", "IRC:5-2015 Clause 2.1"),
    RuleSpec("C13", ValidationSeverity.CRITICAL, _a(["DesignFloodFrequency", "ScourDepthMethod"]), "Scour depth must be computed at design flood frequency or higher", "IRC:78 Clause 7.2"),
    RuleSpec("C14", ValidationSeverity.CRITICAL, _a(["SoilClass", "BearingCapacityType"]), "Bearing capacity classification must be consistent with declared soil class", "IS:6403 Clause 4"),
    RuleSpec("C15", ValidationSeverity.CRITICAL, _a(["ConcreteGrade", "ExposureZoneClass"]), "Minimum concrete grade for exposure zone must satisfy IS:456 Table 5", "IS:456-2000 Table 5"),
    RuleSpec("C16", ValidationSeverity.CRITICAL, _a(["SeismicZoneType", "SeismicImportanceFactor"]), "Seismic importance factor shall be applied per zone classification", "IS:1893 Part 1 Clause 6.4.2"),
    RuleSpec("C17", ValidationSeverity.CRITICAL, _a(["WindSpeedBasic_ms", "WindImportanceFactor"]), "Design wind speed Vz uses importance factor Iw per terrain risk class", "IS:875 Part 3 Clause 5.3"),
    RuleSpec("C18", ValidationSeverity.CRITICAL, _a(["LoadCombination"]), "All analysis load cases must reference a declared load combination set", "IRC:6-2017 Table 1"),
    RuleSpec("C19", ValidationSeverity.CRITICAL, _a(["ChainageReferenceSystem", "SurveyGridZone"]), "Chainage origin must match the declared survey grid reference", "IRC SP-55 Clause 2.1"),
    RuleSpec("C20", ValidationSeverity.CRITICAL, _a(["StructuralAnalysisSoftware", "FEAModelSolverClass"]), "FEA solver must be within approved software list for IRC design", "MORTH Clause 507.2"),
    RuleSpec("C21", ValidationSeverity.CRITICAL, _a(["ContractPackageType"]), "Deliverables set must correspond to declared contract package phase", "MORTH Clause 102"),
    RuleSpec("C22", ValidationSeverity.CRITICAL, _a(["SafetyComplianceClass"]), "Road safety audit compliance flag must be YES for GAD submission", "IRC SP-55 Clause 12"),
    RuleSpec("C23", ValidationSeverity.CRITICAL, _a(["ConstructionQualityClass"]), "Quality class must meet minimum AVERAGE for public bridge works", "MORTH Clause 1007"),
    RuleSpec("C24", ValidationSeverity.CRITICAL, _a(["RegimeConstantKValue", "RiverBankType"]), "Lacey's regime K value must be consistent with river bank soil type", "IRC:78 Clause 7.3"),
    RuleSpec("C25", ValidationSeverity.CRITICAL, _a(["ApproachRoadAlignmentClass", "VerticalCurveKValueClass"]), "Vertical curve K-values must satisfy sight distance requirements", "IRC:73-1980 Clause 4.5"),
]
assert len(_CRITICAL_RULES) == 25, f"C-group expected 25, got {len(_CRITICAL_RULES)}"


# ---------------------------------------------------------------------------
# W01-W75 — WARNING value-range / compatibility rules
# ---------------------------------------------------------------------------
_WARNING_RULES: list[RuleSpec] = [
    RuleSpec("W01", ValidationSeverity.WARNING, _a(["DeckWidthOverallClass"]), "Overall deck width exceeds 15 m — consider cross-drainage detailing review", "IRC:86 Table 2"),
    RuleSpec("W02", ValidationSeverity.WARNING, _a(["PierHeightClass"]), "Pier height over 20 m triggers second-order P-Delta moment check", "IRC:78 Clause 9.4"),
    RuleSpec("W03", ValidationSeverity.WARNING, _a(["SpanLengthCode"]), "Span over 50 m requires erection scheme plan in GAD notes", "IRC SP-55 Clause 6.4"),
    RuleSpec("W04", ValidationSeverity.WARNING, _a(["SuperstructureMaterial"]), "Steel superstructure needs fatigue detail classification in drawings", "IS:800 Clause 10.7"),
    RuleSpec("W05", ValidationSeverity.WARNING, _a(["ConcreteGrade"]), "Grade above M60 requires HPC mix design approval document", "IS:456 Clause 5.1"),
    RuleSpec("W06", ValidationSeverity.WARNING, _a(["ReinforcementGradeType"]), "FE500D or higher requires additional ductility detailing", "IS:1786 Clause 4.1"),
    RuleSpec("W07", ValidationSeverity.WARNING, _a(["BearingPadMaterial"]), "Elastomeric pad over 700 kN load needs check for creep compression set", "IRC:83 Part II Clause 4"),
    RuleSpec("W08", ValidationSeverity.WARNING, _a(["ExpansionJointGapSize"]), "Joint gap over 100 mm requires modular multi-gap joint specification", "IRC SP-55 Clause 7.3"),
    RuleSpec("W09", ValidationSeverity.WARNING, _a(["CementType"]), "Slag or flyash blended cement needs extended curing period schedule", "IS:1489 Clause 8"),
    RuleSpec("W10", ValidationSeverity.WARNING, _a(["AggregateNominalSize"]), "Nominal aggregate > 20 mm requires pumpability review for deck pours", "IS:383 Clause 6"),
    RuleSpec("W11", ValidationSeverity.WARNING, _a(["WaterQualityAggressiveType"]), "Aggressive water classification needs extra cover + protective coating", "IS:456 Table 5"),
    RuleSpec("W12", ValidationSeverity.WARNING, _a(["ConcreteCoverNominalClass"]), "Nominal cover > 75 mm requires anti-crack surface reinforcement mesh", "IS:456 Clause 26.4"),
    RuleSpec("W13", ValidationSeverity.WARNING, _a(["ConcreteSlumpClass"]), "Slump above S4 requires superplasticizer admixture declaration", "IS:456 Clause 12.1"),
    RuleSpec("W14", ValidationSeverity.WARNING, _a(["ConcreteCuringMethodType"]), "Membrane curing needs compatible release-agent / painting surface prep", "IRC SP-55 Clause 10.3"),
    RuleSpec("W15", ValidationSeverity.WARNING, _a(["CurvatureClass"]), "Sharp curvature class triggers superelevation transition review", "IRC:73 Clause 5.2"),
    RuleSpec("W16", ValidationSeverity.WARNING, _a(["SkewAngleClass"]), "Skew > 30 deg requires torsional stiffness analysis note", "IRC:112 Annex C"),
    RuleSpec("W17", ValidationSeverity.WARNING, _a(["PierType"]), "Well / open caisson pier needs detailed sinking sequence plan", "IRC:78 Clause 10"),
    RuleSpec("W18", ValidationSeverity.WARNING, _a(["FoundationType"]), "Pile foundation requires lateral load + group efficiency analysis", "IS:2911 Part 1"),
    RuleSpec("W19", ValidationSeverity.WARNING, _a(["AbutmentType"]), "Counterfort / T-type abutment needs passive earth pressure verification", "IRC:78 Clause 8.3"),
    RuleSpec("W20", ValidationSeverity.WARNING, _a(["WearingCoatGrade"]), "Wearing coat grade SMA needs mandatory polymer modified binder", "MORTH Clause 510"),
    RuleSpec("W21", ValidationSeverity.WARNING, _a(["WearingCoatThicknessClass"]), "Wearing coat > 50 mm requires levelling course specification", "IRC:58-2005 Clause 5"),
    RuleSpec("W22", ValidationSeverity.WARNING, _a(["WaterproofingMembraneType"]), "Buried deck waterproofing must be compatible with wearing coat tack coat", "IRC SP-55 Clause 7.5"),
    RuleSpec("W23", ValidationSeverity.WARNING, _a(["ParapetTypeClass"]), "Rigid parapet class requires vehicle impact load case (HL-93 sidebar)", "IRC:6 Clause 3.11"),
    RuleSpec("W24", ValidationSeverity.WARNING, _a(["KerbTypeCode"]), "High mount kerb needs dedicated drainage scupper spacing plan", "IRC:86 Clause 4.6"),
    RuleSpec("W25", ValidationSeverity.WARNING, _a(["StreetLightingLuxClass"]), "Lux class above M3 triggers dual-luminaire mounting on abutment walls", "IRC:86 Annex D"),
    RuleSpec("W26", ValidationSeverity.WARNING, _a(["ScourProtectionSubtype"]), "Launching apron protection needs stone weight against design flow velocity", "IRC:78 Clause 7.6"),
    RuleSpec("W27", ValidationSeverity.WARNING, _a(["RiverGeomorphologyType"]), "Braided / meandering river reach requires 2D hydraulic model note", "IRC:5 Clause 6.2"),
    RuleSpec("W28", ValidationSeverity.WARNING, _a(["WaterSurfaceProfileType"]), "Backwater-affected profile must include afflux bund heights", "IRC:5 Clause 7"),
    RuleSpec("W29", ValidationSeverity.WARNING, _a(["DesignReturnPeriod"]), "Return period > 100 yr requires PMF / probable maximum flood overlay", "IRC:5 Clause 2.2"),
    RuleSpec("W30", ValidationSeverity.WARNING, _a(["RainfallIntensityStormType"]), "Short-duration 10-min flash storm needs culvert peak discharge review", "IRC:5 Annex B"),
    RuleSpec("W31", ValidationSeverity.WARNING, _a(["FloodZoneElevationClass"]), "HFL within 0.5 m of soffit requires deck-level raising study", "IRC:78 Clause 7.1"),
    RuleSpec("W32", ValidationSeverity.WARNING, _a(["SedimentYieldClassification"]), "High sediment yield river needs annual desilting provisions note", "IRC:5 Clause 8.3"),
    RuleSpec("W33", ValidationSeverity.WARNING, _a(["RiverCrossingClass"]), "Major river crossing must have independent peer review hydrology", "MORTH Appendix B"),
    RuleSpec("W34", ValidationSeverity.WARNING, _a(["WindSpeedBasic_ms"]), "Vb > 50 m/s triggers along-wind + across-wind response spectrum", "IS:875 Part 3 Clause 6"),
    RuleSpec("W35", ValidationSeverity.WARNING, _a(["SeismicZoneType"]), "Zone V demands ductility class DCL special moment frame detailing", "IS:1893 Part 1 Clause 7.9"),
    RuleSpec("W36", ValidationSeverity.WARNING, _a(["ResponseSpectrumCategory"]), "Site class C/D soil requires site-specific response spectrum development", "IS:1893 Part 1 Fig. 2"),
    RuleSpec("W37", ValidationSeverity.WARNING, _a(["DuctilityClassLink"]), "DCL link to deck joint demands fuse-bearing capacity verification", "IRC:112 Annex E"),
    RuleSpec("W38", ValidationSeverity.WARNING, _a(["FatigueDetailCategorySteel"]), "Category C or lower detail must use reduced stress range curve", "IS:800 Table 18"),
    RuleSpec("W39", ValidationSeverity.WARNING, _a(["PrestressLossTypeEnum"]), "Long-term creep + shrinkage loss over 25% requires revised jacking stress", "IRC:112 Clause 6.8"),
    RuleSpec("W40", ValidationSeverity.WARNING, _a(["CreepShrinkageFactorClass"]), "Humidity < 40% geographic region demands extra creep factor 1.3x", "IS:1343 Clause 5.3"),
    RuleSpec("W41", ValidationSeverity.WARNING, _a(["TemperatureLoadDeltaT"]), "Temperature differential > 20 C requires non-linear through-depth gradient", "IRC:6 Clause 3.8"),
    RuleSpec("W42", ValidationSeverity.WARNING, _a(["ImpactFactorCoeff"]), "Impact factor above 0.33 needs dynamic amplification factor (DAF) check", "IRC:6 Clause 3.5"),
    RuleSpec("W43", ValidationSeverity.WARNING, _a(["LoadCombination"]), "Ultimate EQ combination without overstrength factor flagged for review", "IRC:6 Table 1"),
    RuleSpec("W44", ValidationSeverity.WARNING, _a(["FrictionCoeffBearingPadType"]), "Coefficient < 0.08 on PTFE requires stainless steel mating surface note", "IRC:83 Part II"),
    RuleSpec("W45", ValidationSeverity.WARNING, _a(["DampingRatioTypeEnum"]), "Damping ratio < 2% for steel requires tuned mass damper feasibility note", "IS:1893 Clause 6.4.3"),
    RuleSpec("W46", ValidationSeverity.WARNING, _a(["RetainingWallModeType"]), "Gravity retaining wall > 6 m height may need counterfort redesign note", "IS:14458 Part 2"),
    RuleSpec("W47", ValidationSeverity.WARNING, _a(["LayerGroup"]), "Layer group OUT_OF_SERVICE used on primary deliverable — confirm suppress-plot", "IRC SP-55 Annex F"),
    RuleSpec("W48", ValidationSeverity.WARNING, _a(["LineWeightCode"]), "Line weight > 1.0 mm used in section hatching boundary — review print bleed", "IRC SP-55 Clause 11.2"),
    RuleSpec("W49", ValidationSeverity.WARNING, _a(["HatchPatternCode"]), "User-defined hatch pattern present — verify plotter pen-table includes it", "IRC SP-55 Annex F"),
    RuleSpec("W50", ValidationSeverity.WARNING, _a(["FontStyle"]), "Non-ISO font family detected — confirm PDF embedding enabled", "IRC SP-55 Annex G"),
    RuleSpec("W51", ValidationSeverity.WARNING, _a(["ScaleDenominatorSet"]), "Scale 1:100 or larger needs dimension round-off tolerance 5 mm class", "IRC SP-55 Clause 11.3"),
    RuleSpec("W52", ValidationSeverity.WARNING, _a(["ViewTypeClassification"]), "3D isometric view on GAD sheet triggers dimension true-length check", "IRC SP-55 Clause 11.4"),
    RuleSpec("W53", ValidationSeverity.WARNING, _a(["DimensionStyleClass"]), "Chained dimension style needs ± cumulative tolerance statement", "IRC SP-55 Clause 11.3"),
    RuleSpec("W54", ValidationSeverity.WARNING, _a(["TitleBlockRevisionClass"]), "Revision class C (issued-for-tender) without QA sign-off flagged", "MORTH Clause 1007.1"),
    RuleSpec("W55", ValidationSeverity.WARNING, _a(["PlotterPaperClass"]), "A0+ jumbo paper class — confirm plotter media inventory before print run", "IRC SP-55 Annex G"),
    RuleSpec("W56", ValidationSeverity.WARNING, _a(["CrossSectionViewTypeCode"]), "Half-symmetric cross-section — verify that section cut-plane is noted", "IRC SP-55 Clause 11.4"),
    RuleSpec("W57", ValidationSeverity.WARNING, _a(["LineStyleCode"]), "Centerline dash used for outline border — verify drafting convention", "IRC SP-55 Annex F"),
    RuleSpec("W58", ValidationSeverity.WARNING, _a(["ArrowStyle"]), "Arrow dot style on dimension leader for small features — switch to slash?", "IRC SP-55 Annex F"),
    RuleSpec("W59", ValidationSeverity.WARNING, _a(["ConcreteAggregateType"]), "Lightweight aggregate needs specific unit weight value in design report", "IS:383 Part 2"),
    RuleSpec("W60", ValidationSeverity.WARNING, _a(["AdmixtureType"]), "Accelerator + retarder admixture mix — verify compatibility document", "IS:9103 Clause 5"),
    RuleSpec("W61", ValidationSeverity.WARNING, _a(["WeldType"]), "Full-penetration groove weld class needs NDT UT/RT plan", "IS:800 Clause 10.5"),
    RuleSpec("W62", ValidationSeverity.WARNING, _a(["BearingMaterial"]), "PTFE + stainless steel pair — specify sliding surface roughness Ra", "IRC:83 Part II Clause 4"),
    RuleSpec("W63", ValidationSeverity.WARNING, _a(["JointSealantType"]), "Polysulfide sealant class — 10 yr re-seal maintenance note", "IRC SP-55 Clause 7.4"),
    RuleSpec("W64", ValidationSeverity.WARNING, _a(["ReinforcementBarType"]), "Epoxy-coated bar class — specify coating thickness class T3", "IS:13620 Clause 5"),
    RuleSpec("W65", ValidationSeverity.WARNING, _a(["RebarCouplerType"]), "Parallel-thread coupler type — require mill test Type II performance", "IS:1786 Annex H"),
    RuleSpec("W66", ValidationSeverity.WARNING, _a(["ConcreteSurfaceFinishClass"]), "Fair-faced F4 finish — specify approved formwork liner material", "IRC SP-55 Clause 10.4"),
    RuleSpec("W67", ValidationSeverity.WARNING, _a(["FormworkPanelType"]), "Plywood panel > 3 pours — check panel surface degradation reuse criteria", "IS:3640 Clause 6"),
    RuleSpec("W68", ValidationSeverity.WARNING, _a(["FormworkReleaseAgentType"]), "Reactive release agent — confirm no bond-degradation on next lift face", "IRC SP-55 Clause 10.2"),
    RuleSpec("W69", ValidationSeverity.WARNING, _a(["AntiCorrosionProtectionType"]), "Hot-dip galvanizing class — post-galvanize distortion correction plan", "IS:4759 Part 1"),
    RuleSpec("W70", ValidationSeverity.WARNING, _a(["PaintCoatSystemType"]), "Paint system with zinc-rich primer — surface blast class Sa 2.5 required", "IS:1477 Part 5"),
    RuleSpec("W71", ValidationSeverity.WARNING, _a(["DeckOverlayType"]), "Polymer concrete overlay class — minimum 40 day age before overlay", "IRC SP-55 Clause 7.2"),
    RuleSpec("W72", ValidationSeverity.WARNING, _a(["CableStayingSystemClass"]), "Cable-stay system class — specify dehumidification monitoring note", "IRC SP-55 Clause 6.6"),
    RuleSpec("W73", ValidationSeverity.WARNING, _a(["ArchShapeType"]), "Tied-arch with hanger rods — fatigue class per IS:800 Table 18 required", "IS:800 Clause 10.7"),
    RuleSpec("W74", ValidationSeverity.WARNING, _a(["TrussConfigurationClass"]), "Warren truss class without verticals — check secondary bending in chords", "IS:800 Annex D"),
    RuleSpec("W75", ValidationSeverity.WARNING, _a(["PierCapType"]), "Drop-cap type pier cap — check negative reinforcement congestion at soffit", "IRC:78 Clause 9.3"),
]
assert len(_WARNING_RULES) == 75, f"W-group expected 75, got {len(_WARNING_RULES)}"


# ---------------------------------------------------------------------------
# I01-I50 — INFO best-practice / metadata / drawing / documentation rules
# ---------------------------------------------------------------------------
_INFO_RULES: list[RuleSpec] = [
    RuleSpec("I01", ValidationSeverity.INFO, _a(["ProjectStage"]), "Consider updating stage to DESIGN_DEVELOPED after 60% model review", "Best practice: IRSP-55 workflow"),
    RuleSpec("I02", ValidationSeverity.INFO, _a(["ProjectName"]), "Recommended: project name include station names e.g. 'X to Y ROB'", "MORTH Appendix A naming"),
    RuleSpec("I03", ValidationSeverity.INFO, _a(["ClientType"]), "MORTH / NHAI clients mandate additional clause 101.1 documents set", "MORTH Clause 101.1"),
    RuleSpec("I04", ValidationSeverity.INFO, _a(["ContractPackageType"]), "Item-rate DBO packages require BOQ cross-reference in drawing notes", "MORTH Clause 102.2"),
    RuleSpec("I05", ValidationSeverity.INFO, _a(["DesignFirmCategoryClass"]), "Class-A firm must provide licensed engineer seal per state bye-law", "COE India bye-laws"),
    RuleSpec("I06", ValidationSeverity.INFO, _a(["SiteVisitStatus"]), "Pre-design site visit photos should be linked to project issue register", "IRC SP-55 Clause 1.4"),
    RuleSpec("I07", ValidationSeverity.INFO, _a(["BridgeCategory"]), "Category MAJOR bridge — schedule 3rd peer review checkpoint", "MORTH Appendix B"),
    RuleSpec("I08", ValidationSeverity.INFO, _a(["SpanArrangementClass"]), "Even-span arrangement recommended for balanced construction sequence", "IRC SP-55 Clause 3.3"),
    RuleSpec("I09", ValidationSeverity.INFO, _a(["SpanLengthCode"]), "Modular span multiples (e.g. 25 m) reduce formwork set count", "Best practice"),
    RuleSpec("I10", ValidationSeverity.INFO, _a(["PierSpacingPatternClass"]), "Equal pier spacing gives aesthetic uniformity across viaduct", "IRC SP-55 3.3"),
    RuleSpec("I11", ValidationSeverity.INFO, _a(["CarriagewayWidthClass"]), "7.5 m single-lane + 2.5 m shoulder width common for 2-lane ROB", "IRC:86 Table 1"),
    RuleSpec("I12", ValidationSeverity.INFO, _a(["MedianWidthClass"]), "Central median ≥ 1.5 m allows future barrier upgrade", "IRC:86 4.4"),
    RuleSpec("I13", ValidationSeverity.INFO, _a(["FootpathWidthClass"]), "1.5 m footpath minimum recommended for urban ROB", "IRC:86 4.5"),
    RuleSpec("I14", ValidationSeverity.INFO, _a(["SkewAngleClass"]), "Skew 0 preferred — simplifies reinforcement detailing", "IRC:112 Annex C"),
    RuleSpec("I15", ValidationSeverity.INFO, _a(["HorizontalAlignmentType"]), "Tangent alignment simplifies bearing layout & expansion joints", "IRC:112 5.4"),
    RuleSpec("I16", ValidationSeverity.INFO, _a(["VerticalAlignmentType"]), "Sag vertical curve under deck — add deck drainage extra slope", "IRC:73 4.4"),
    RuleSpec("I17", ValidationSeverity.INFO, _a(["CrownType"]), "2% parabolic crown standard for bituminous wearing surface", "IRC:86 4.2"),
    RuleSpec("I18", ValidationSeverity.INFO, _a(["SuperelevationClass"]), "Max 7% superelevation for urban plain terrain ROBs", "IRC:73 Table 7"),
    RuleSpec("I19", ValidationSeverity.INFO, _a(["CamberType"]), "Pre-camber equal to sum of dead load deflection + 0.5 live load", "IRC:112 Clause 6.5"),
    RuleSpec("I20", ValidationSeverity.INFO, _a(["SuperstructureType"]), "Post-tensioned box girder best for 30-60 m continuous spans", "IRC SP-55 6.2"),
    RuleSpec("I21", ValidationSeverity.INFO, _a(["DeckSlabType"]), "Cast-in-situ RC slab standard for simply supported I-girder decks", "IRC:112 6.3"),
    RuleSpec("I22", ValidationSeverity.INFO, _a(["SubstructureType"]), "In-situ RCC substructure common for piers under 25 m height", "IRC:78 Clause 9"),
    RuleSpec("I23", ValidationSeverity.INFO, _a(["PierType"]), "Single-pier column type aesthetic for viaduct with hammerhead cap", "IRC SP-55 8.1"),
    RuleSpec("I24", ValidationSeverity.INFO, _a(["AbutmentType"]), "Cantilever abutment preferred for bank height 4-10 m range", "IRC:78 8.2"),
    RuleSpec("I25", ValidationSeverity.INFO, _a(["FoundationType"]), "Spread footing preferred when N > 30 SPT blow count at depth", "IS:6403 Clause 7"),
    RuleSpec("I26", ValidationSeverity.INFO, _a(["BearingType"]), "Pot bearing for heavy loads > 2000 kN with rotational demand", "IRC:83 Part I"),
    RuleSpec("I27", ValidationSeverity.INFO, _a(["ExpansionJointClass"]), "Strip seal joint class economical for ±25 mm movement range", "IRC SP-55 7.3"),
    RuleSpec("I28", ValidationSeverity.INFO, _a(["WearingCoatGrade"]), "BC + SDBC 40 mm overlay common MORTH specification for ROB", "MORTH 510"),
    RuleSpec("I29", ValidationSeverity.INFO, _a(["ParapetTypeClass"]), "Metal beam crash barrier class WB2 for urban arterial ROB", "IRC SP-55 7.6"),
    RuleSpec("I30", ValidationSeverity.INFO, _a(["KerbTypeCode"]), "Mountable kerb V shape allows emergency vehicle access", "IRC:86 4.6"),
    RuleSpec("I31", ValidationSeverity.INFO, _a(["StreetLightingLuxClass"]), "Class M2 average maintained lux for urban interchanges", "IRC:86 Annex D"),
    RuleSpec("I32", ValidationSeverity.INFO, _a(["SurveyGridZone"]), "WGS-84 / UTM zone required for MORTH highway geo-referencing", "MORTH Clause 502"),
    RuleSpec("I33", ValidationSeverity.INFO, _a(["ChainageReferenceSystem"]), "Cumulative chainage across project — avoid reset at structures", "Best practice"),
    RuleSpec("I34", ValidationSeverity.INFO, _a(["TopographicSurveyScaleClass"]), "1:500 scale recommended for detailed structure site plan", "IRC SP-55 2.1"),
    RuleSpec("I35", ValidationSeverity.INFO, _a(["GeotechnicalInvestigationClass"]), "1 bore per pier + 2 per abutment minimum for GAD level", "IRC SP-55 2.2"),
    RuleSpec("I36", ValidationSeverity.INFO, _a(["StructuralAnalysisSoftware"]), "CSI SAP2000 / MIDAS Civil most commonly accepted under MORTH", "MORTH 507.2"),
    RuleSpec("I37", ValidationSeverity.INFO, _a(["FEAModelSolverClass"]), "Sparse direct solver recommended for large frame models", "Best practice"),
    RuleSpec("I38", ValidationSeverity.INFO, _a(["ConcreteCoverNominalClass"]), "Cover 40 mm deck / 50 mm substructure / 60 mm piles — standard", "IS:456 26.4"),
    RuleSpec("I39", ValidationSeverity.INFO, _a(["ConcreteGrade"]), "M40 deck / M35 substructure / M30 foundation typical", "IRC SP-55 10.1"),
    RuleSpec("I40", ValidationSeverity.INFO, _a(["ReinforcementGradeType"]), "Fe500D recommended for ductility in seismic zones", "IS:1786"),
    RuleSpec("I41", ValidationSeverity.INFO, _a(["DrawingSheetNumberingClass"]), "Use sheet number PREFIX/SERIES/SUB-SHEET per ISO 7200", "ISO 7200"),
    RuleSpec("I42", ValidationSeverity.INFO, _a(["TitleBlockRevisionClass"]), "Revision history must show at least PRELIM/A/ISSUE/B stages", "IRC SP-55 Annex G"),
    RuleSpec("I43", ValidationSeverity.INFO, _a(["LayerGroup"]), "Layer naming convention should be BS 1192 / ISO 19650 compliant", "BS 1192"),
    RuleSpec("I44", ValidationSeverity.INFO, _a(["DimensionStyleClass"]), "Dual dimension unit (mm + m) recommended for large layout plans", "Best practice"),
    RuleSpec("I45", ValidationSeverity.INFO, _a(["ScaleDenominatorSet"]), "Sheet layout scales: GA 1:200 / CS 1:50 / Detail 1:10 standard", "IRC SP-55 Annex G"),
    RuleSpec("I46", ValidationSeverity.INFO, _a(["ViewTypeClassification"]), "GA plan + elevation + 3 typical cross-sections minimum GAD set", "IRC SP-55 Clause 11"),
    RuleSpec("I47", ValidationSeverity.INFO, _a(["BarBendingScheduleClass"]), "BBS bar marks must correspond 1:1 with reinforcement drawing marks", "MORTH Appendix F"),
    RuleSpec("I48", ValidationSeverity.INFO, _a(["QualityAssurancePlanClass"]), "QAP must be approved before start of concrete works", "MORTH 1007.1"),
    RuleSpec("I49", ValidationSeverity.INFO, _a(["EnvironmentalBaselineClass"]), "CRZ clearance needed if structure within 500 m of high-tide line", "CRZ Notification 2019"),
    RuleSpec("I50", ValidationSeverity.INFO, _a(["ProjectDeliveryMethod"]), "EPC delivery method integrates GAD + detailed design in one phase", "IRC SP-55 1.1"),
]
assert len(_INFO_RULES) == 50, f"I-group expected 50, got {len(_INFO_RULES)}"


ALL_RULES: list[RuleSpec] = _CRITICAL_RULES + _WARNING_RULES + _INFO_RULES
assert len(ALL_RULES) == 150, f"ALL_RULES expected 150, got {len(ALL_RULES)}"

__all__ = ["RuleSpec", "ALL_RULES"]
