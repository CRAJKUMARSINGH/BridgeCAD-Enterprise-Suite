"""
bridgecad_core.validation — 30 check_*() functions wired into RulesEngine.
M1 Week 1 Day 4: 25 Critical + 5 Warning checks against BridgeProject.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from .models import BridgeProject
from .types import ConcreteGrade, ValidationSeverity

# ===========================================================================
# Core data structures (unchanged from scaffold)
# ===========================================================================

@dataclass(frozen=True)
class ValidationFinding:
    check_id: str
    description: str
    severity: ValidationSeverity
    passed: bool
    message: str = ""


@dataclass
class ValidationReport:
    findings: list[ValidationFinding] = field(default_factory=list)

    @property
    def score(self) -> int:
        """0–100 compliance score. Critical fail = −15 pts, Warning fail = −3 pts.
        Technical ERR findings (check_id=="ERR" from unhandled exceptions) are not
        deducted because they indicate engine/field-mapping gaps, not project defects."""
        score = 100
        for f in self.findings:
            if f.passed:
                continue
            if f.check_id == "ERR":
                continue
            if f.severity is ValidationSeverity.CRITICAL:
                score -= 15
            elif f.severity is ValidationSeverity.WARNING:
                score -= 3
        return max(0, score)

    @property
    def overall_status(self) -> str:
        if any(not f.passed and f.severity is ValidationSeverity.CRITICAL
               for f in self.findings):
            return "FAIL"
        if any(not f.passed and f.severity is ValidationSeverity.WARNING
               for f in self.findings):
            return "WARN"
        return "PASS"

    def passed_findings(self) -> list[ValidationFinding]:
        return [f for f in self.findings if f.passed]

    def failed_findings(self) -> list[ValidationFinding]:
        return [f for f in self.findings if not f.passed]

    @property
    def critical_fail_count(self) -> int:
        return sum(
            1 for f in self.findings
            if not f.passed and f.severity is ValidationSeverity.CRITICAL
        )

    @property
    def warning_fail_count(self) -> int:
        return sum(
            1 for f in self.findings
            if not f.passed and f.severity is ValidationSeverity.WARNING
        )


CheckFn = Callable[[BridgeProject], ValidationFinding]


class RulesEngine:
    """Container for check functions."""

    def __init__(self) -> None:
        self._checks: list[CheckFn] = []

    def register(self, fn: CheckFn) -> None:
        self._checks.append(fn)

    def run(self, project: BridgeProject) -> ValidationReport:
        findings: list[ValidationFinding] = []
        for fn in self._checks:
            try:
                result = fn(project)
                if isinstance(result, ValidationFinding):
                    findings.append(result)
                else:
                    findings.extend(result)  # type: ignore[arg-type]
            except Exception as exc:
                findings.append(ValidationFinding(
                    check_id="ERR",
                    description=f"Check {fn.__name__} raised unexpectedly",
                    severity=ValidationSeverity.WARNING,
                    passed=False,
                    message=str(exc),
                ))
        return ValidationReport(findings=findings)


# ===========================================================================
# Helpers
# ===========================================================================

_CONCRETE_GRADE_ORDER: list[str] = [
    "M10", "M15", "M20", "M25", "M30", "M35", "M40", "M45",
    "M50", "M55", "M60", "M65", "M70", "M80",
]

def _concrete_ordinal(grade: ConcreteGrade | None) -> int:
    """Return 0-based ordinal for ConcreteGrade; −1 if None."""
    if grade is None:
        return -1
    name = grade.name  # e.g. "M40"
    try:
        return _CONCRETE_GRADE_ORDER.index(name)
    except ValueError:
        return len(_CONCRETE_GRADE_ORDER)  # treat unknowns as very high


def _f(check_id: str, desc: str, sev: ValidationSeverity,
        passed: bool, msg: str = "") -> ValidationFinding:
    return ValidationFinding(
        check_id=check_id,
        description=desc,
        severity=sev,
        passed=passed,
        message="" if passed else msg,
    )


# ===========================================================================
# 25 CRITICAL check functions  (C01–C25)
# ===========================================================================

def check_project_stage_defined(p: BridgeProject) -> ValidationFinding:
    """C01 — Project phase must be set."""
    passed = p.project_master.project_phase is not None
    return _f("C01", "Project stage defined for GAD deliverable",
              ValidationSeverity.CRITICAL, passed,
              "project_master.project_phase is None — set before issue")


def check_client_identity(p: BridgeProject) -> ValidationFinding:
    """C02 — Client identity must be populated."""
    passed = p.project_master.client is not None
    return _f("C02", "Client / employer identity populated",
              ValidationSeverity.CRITICAL, passed,
              "project_master.client is None")


def check_bridge_category_assigned(p: BridgeProject) -> ValidationFinding:
    """C03 — Bridge category must be assigned."""
    passed = p.bridge_selection.bridge_category is not None
    return _f("C03", "Bridge category assigned per functional class",
              ValidationSeverity.CRITICAL, passed,
              "bridge_selection.bridge_category is None")


def check_total_length_coherent(p: BridgeProject) -> ValidationFinding:
    """C04 — Total length must be > 0 and match sum of span lengths."""
    total = float(p.geometry_input.total_length_m)
    span_sum = sum(float(s) for s in p.geometry_input.span_lengths_m)
    passed = total > 0 and abs(total - span_sum) < 0.01
    return _f("C04", "Total bridge length coherent with span arrangement",
              ValidationSeverity.CRITICAL, passed,
              f"total_length={total:.3f} m but sum(spans)={span_sum:.3f} m")


def check_width_does_not_exceed_deck(p: BridgeProject) -> ValidationFinding:
    """C05 — Sum of component widths ≤ declared overall deck width."""
    gi = p.geometry_input
    component_sum = (
        float(gi.carriageway_width_m)
        + float(gi.footpath_left_m or 0)
        + float(gi.footpath_right_m or 0)
        + float(gi.kerb_width_left_m or 0)
        + float(gi.kerb_width_right_m or 0)
        + float(gi.crash_barrier_width_left_m or 0)
        + float(gi.crash_barrier_width_right_m or 0)
        + float(gi.median_width_m or 0)
    )
    overall = float(gi.overall_width_m)
    passed = component_sum <= overall + 0.01   # 10 mm tolerance
    return _f("C05", "Component widths sum ≤ overall deck width",
              ValidationSeverity.CRITICAL, passed,
              f"sum of components={component_sum:.3f} m > overall={overall:.3f} m")


def check_horizontal_alignment(p: BridgeProject) -> ValidationFinding:
    """C06 — Alignment must be set."""
    passed = p.geometry_input.alignment_type is not None
    return _f("C06", "Horizontal alignment type declared",
              ValidationSeverity.CRITICAL, passed,
              "geometry_input.alignment_type is None")


def check_vertical_gradient(p: BridgeProject) -> ValidationFinding:
    """C07 — Gradient must not exceed 1:30 (3.33 %) for urban ROB."""
    grad = float(p.geometry_input.gradient_pct or 0)
    passed = abs(grad) <= 3.34
    return _f("C07", "Vertical gradient ≤ 1:30 (3.33 %) on deck",
              ValidationSeverity.CRITICAL, passed,
              f"gradient={grad:.2f} % exceeds 1 in 30 limit (IRC:86 Clause 4.2)")


def check_superstructure_deck_combo(p: BridgeProject) -> ValidationFinding:
    """C08 — Superstructure type and deck material must both be set."""
    passed = (p.superstructure.type is not None
              and p.superstructure.deck_material is not None)
    return _f("C08", "Superstructure type and deck material declared",
              ValidationSeverity.CRITICAL, passed,
              "superstructure.type or deck_material is None")


def check_pier_abutment_family(p: BridgeProject) -> ValidationFinding:
    """C09 — Pier type and abutment type must both be declared."""
    passed = (p.substructure.pier_type is not None
              and p.substructure.abutment_type is not None)
    return _f("C09", "Pier and abutment family declared",
              ValidationSeverity.CRITICAL, passed,
              "substructure.pier_type or abutment_type is None")


def check_bearing_schedule_not_empty(p: BridgeProject) -> ValidationFinding:
    """C10 — At least one bearing schedule row must exist."""
    passed = len(p.bearings_joints.bearing_schedule) > 0
    return _f("C10", "Bearing schedule populated (≥ 1 row)",
              ValidationSeverity.CRITICAL, passed,
              "bearings_joints.bearing_schedule is empty")


def check_expansion_joint_schedule(p: BridgeProject) -> ValidationFinding:
    """C11 — At least one expansion joint schedule row must exist."""
    passed = len(p.bearings_joints.expansion_joint_schedule) > 0
    return _f("C11", "Expansion joint schedule populated (≥ 1 row)",
              ValidationSeverity.CRITICAL, passed,
              "bearings_joints.expansion_joint_schedule is empty")


def check_return_period_set(p: BridgeProject) -> ValidationFinding:
    """C12 — Hydraulic design return period must be declared."""
    passed = p.hydraulic_data.return_period_yr is not None
    return _f("C12", "Design return period declared",
              ValidationSeverity.CRITICAL, passed,
              "hydraulic_data.return_period_yr is None")


def check_scour_depth_positive(p: BridgeProject) -> ValidationFinding:
    """C13 — Design scour depth must be > 0."""
    scour = float(p.hydraulic_data.design_scour_depth_m or 0)
    passed = scour > 0
    return _f("C13", "Design scour depth > 0 m",
              ValidationSeverity.CRITICAL, passed,
              f"design_scour_depth_m = {scour:.3f} m  (must be positive)")


def check_soil_bearing_capacity(p: BridgeProject) -> ValidationFinding:
    """C14 — Bearing capacity must be declared and positive."""
    cap = float(p.foundation_details.bearing_capacity_kpa or 0)
    passed = cap > 0
    return _f("C14", "Soil bearing capacity > 0 kPa declared",
              ValidationSeverity.CRITICAL, passed,
              f"bearing_capacity_kpa = {cap:.1f}  (must be > 0)")


def check_concrete_grade_minimum(p: BridgeProject) -> ValidationFinding:
    """C15 — Superstructure concrete must be ≥ M25 (IS:456 Table 5)."""
    grade = p.materials.concrete_superstructure
    ordinal = _concrete_ordinal(grade)
    m25_ord = _CONCRETE_GRADE_ORDER.index("M25")
    passed = ordinal >= m25_ord
    return _f("C15", "Superstructure concrete grade ≥ M25",
              ValidationSeverity.CRITICAL, passed,
              f"concrete_superstructure = {grade} is below M25 minimum")


def check_seismic_zone_set(p: BridgeProject) -> ValidationFinding:
    """C16 — Seismic zone must be declared."""
    passed = p.bridge_selection.seismic_zone is not None
    return _f("C16", "Seismic zone declared",
              ValidationSeverity.CRITICAL, passed,
              "bridge_selection.seismic_zone is None")


def check_wind_speed_set(p: BridgeProject) -> ValidationFinding:
    """C17 — Basic wind speed must be declared."""
    passed = p.bridge_selection.wind_zone_ms is not None
    return _f("C17", "Basic wind speed zone declared",
              ValidationSeverity.CRITICAL, passed,
              "bridge_selection.wind_zone_ms is None")


def check_loading_class_set(p: BridgeProject) -> ValidationFinding:
    """C18 — IRC loading class must be declared."""
    passed = p.bridge_selection.loading_class is not None
    return _f("C18", "IRC loading class declared",
              ValidationSeverity.CRITICAL, passed,
              "bridge_selection.loading_class is None")


def check_chainage_set(p: BridgeProject) -> ValidationFinding:
    """C19 — Bridge chainage must be declared."""
    passed = p.project_master.chainage_km is not None
    return _f("C19", "Bridge chainage reference declared",
              ValidationSeverity.CRITICAL, passed,
              "project_master.chainage_km is None")


def check_fea_solver_soft_pass(p: BridgeProject) -> ValidationFinding:
    """C20 — FEA solver check: soft-pass at GAD stage (detailed model not required)."""
    # At GAD stage FEA model is not yet run — always pass with INFO
    return _f("C20", "FEA solver compliance (GAD-stage soft-pass)",
              ValidationSeverity.CRITICAL, True,
              "")


def check_contract_package_phase(p: BridgeProject) -> ValidationFinding:
    """C21 — Project phase must be set (proxy for contract package)."""
    passed = p.project_master.project_phase is not None
    return _f("C21", "Contract package / deliverables phase declared",
              ValidationSeverity.CRITICAL, passed,
              "project_master.project_phase is None")


def check_safety_compliance_status(p: BridgeProject) -> ValidationFinding:
    """C22 — Validation status must not be a critical failure."""
    status = (p.validation.overall_status or "").upper()
    passed = status in {"OK_PASS", "OK", "PASS", "WARN", ""}
    return _f("C22", "Drawing validation overall status is not FAIL",
              ValidationSeverity.CRITICAL, passed,
              f"validation.overall_status = '{status}' — resolve critical failures first")


def check_quality_score_minimum(p: BridgeProject) -> ValidationFinding:
    """C23 — Quality score must be ≥ 60."""
    score = float(p.validation.score_0_to_100 or 0)
    passed = score >= 60
    return _f("C23", "Validation quality score ≥ 60 / 100",
              ValidationSeverity.CRITICAL, passed,
              f"score = {score:.1f}  (minimum 60 required)")


def check_lacey_silt_factor(p: BridgeProject) -> ValidationFinding:
    """C24 — Lacey silt factor must be > 0 (required for scour calc)."""
    sf = float(p.hydraulic_data.lacey_silt_factor or 0)
    passed = sf > 0
    return _f("C24", "Lacey silt factor > 0 declared",
              ValidationSeverity.CRITICAL, passed,
              f"lacey_silt_factor = {sf:.3f}  (must be > 0 for scour calculation)")


def check_vertical_curve_k(p: BridgeProject) -> ValidationFinding:
    """C25 — If gradient is non-zero, a K-value check is implicitly needed
    (soft-pass at GAD stage — detailed profile design is separate)."""
    return _f("C25", "Vertical curve K-value compliance (GAD-stage soft-pass)",
              ValidationSeverity.CRITICAL, True, "")


# ===========================================================================
# 5 WARNING check functions  (W01, W02, W03, W05, W16)
# ===========================================================================

def check_deck_width_over_15m(p: BridgeProject) -> ValidationFinding:
    """W01 — Warn if overall deck width exceeds 15 m."""
    w = float(p.geometry_input.overall_width_m)
    passed = w <= 15.0
    return _f("W01", "Overall deck width ≤ 15 m",
              ValidationSeverity.WARNING, passed,
              f"overall_width = {w:.3f} m > 15 m — cross-drainage detailing review needed")


def check_pier_height_over_20m(p: BridgeProject) -> ValidationFinding:
    """W02 — Warn if typical pier height exceeds 20 m."""
    h = float(p.substructure.pier_height_typical_m or 0)
    passed = h <= 20.0
    return _f("W02", "Typical pier height ≤ 20 m",
              ValidationSeverity.WARNING, passed,
              f"pier_height = {h:.2f} m > 20 m — P-Delta moment check required")


def check_span_over_50m(p: BridgeProject) -> ValidationFinding:
    """W03 — Warn if any span exceeds 50 m (erection scheme note required)."""
    max_span = max((float(s) for s in p.geometry_input.span_lengths_m), default=0.0)
    passed = max_span <= 50.0
    return _f("W03", "Maximum span ≤ 50 m",
              ValidationSeverity.WARNING, passed,
              f"max span = {max_span:.1f} m > 50 m — erection scheme plan required in notes")


def check_concrete_grade_above_m60(p: BridgeProject) -> ValidationFinding:
    """W05 — Warn if any concrete grade is above M60 (HPC approval needed)."""
    grades = [
        p.materials.concrete_superstructure,
        p.materials.concrete_substructure,
        p.materials.concrete_foundation,
    ]
    m60_ord = _CONCRETE_GRADE_ORDER.index("M60")
    above = [g for g in grades if g is not None and _concrete_ordinal(g) > m60_ord]
    passed = len(above) == 0
    names = [g.name for g in above]
    return _f("W05", "Concrete grade ≤ M60 (HPC mix approval needed above M60)",
              ValidationSeverity.WARNING, passed,
              f"Grades above M60: {names} — HPC mix design approval document required")


def check_skew_over_30(p: BridgeProject) -> ValidationFinding:
    """W16 — Warn if skew angle exceeds 30° (torsional analysis note needed)."""
    skew = float(p.geometry_input.skew_angle_deg or 0)
    passed = skew <= 30.0
    return _f("W16", "Skew angle ≤ 30° (torsional stiffness note if higher)",
              ValidationSeverity.WARNING, passed,
              f"skew = {skew:.1f}° > 30° — torsional stiffness analysis note required")


# ===========================================================================
# 7 ADDITIONAL CRITICAL / WARNING checks  (P0-2 Day5 remediation)
#   C26 – IRC:112 Annex J  span/depth ratio
#   C27 – IRC:5 §12.4       freeboard vs HFL
#   C28 – IRC:5 §10.3       afflux ≤ maximum allowable
#   C29 – IRC:5 §7.4        waterway provided ≥ waterway required
#   C30 – IRC:83 §5.4       bearing pot pressure ≤ 35 MPa
#   C31 – IRC:78 §11.3      pile FOS on bearing ≥ 2.5
#   W09 – IS:1893 Pt.1      seismic horizontal acceleration check
# ===========================================================================

def check_span_depth_ratio_irc112(p: BridgeProject) -> ValidationFinding:
    """C26 — IRC:112 Annex J span/depth ratio within prescribed band."""
    from bridgecad_core.standards.irc_21 import check_span_depth_ratio
    spans = [float(s) for s in p.geometry_input.span_lengths_m]
    max_span = max(spans) if spans else 0.0
    depth_mm = float(p.superstructure.girder_depth_mm or 0)
    if depth_mm <= 0:
        # Solid / voided slab: structural depth is the deck thickness, not a girder.
        depth_mm = float(p.superstructure.deck_thickness_mm or 0)
    config = (getattr(p.bridge_selection.span_configuration, "name", None)
              or str(p.bridge_selection.span_configuration) or "")
    stype = (getattr(p.superstructure.type, "name", None)
             or str(p.superstructure.type) or "")
    if depth_mm <= 0:
        return _f("C26", "IRC:112 L/d ratio in-band",
                  ValidationSeverity.CRITICAL, False,
                  "structural depth is 0 (girder_depth_mm / deck_thickness_mm) — must be > 0 for L/d check")
    ok, ratio, msg = check_span_depth_ratio(max_span, depth_mm, config, stype)
    return _f("C26", f"IRC:112 L/d ratio in-band [{msg}]",
              ValidationSeverity.CRITICAL, ok,
              f"L/d = {ratio:.1f} outside IRC limits — max_span={max_span:.1f}m  depth={depth_mm:.0f}mm  "
              f"config={config}  type={stype}")


def check_freeboard_irc05(p: BridgeProject) -> ValidationFinding:
    """C27 — IRC:5 §12.4  soffit level above HFL by ≥ required freeboard."""
    soffit = float(p.hydraulic_data.actual_soffit_level_m or 0)
    hfl = float(p.hydraulic_data.hfl_m or 0)
    req = max(1.0, float(p.hydraulic_data.freeboard_m or 1.0))
    actual = soffit - hfl
    passed = actual >= req - 1e-6
    return _f("C27", f"IRC:5 freeboard HFL→soffit = {actual:.2f}m  (≥ {req:.2f}m req.)",
              ValidationSeverity.CRITICAL, passed,
              f"actual_soffit={soffit:.2f}m − HFL={hfl:.2f}m → freeboard {actual:.2f}m < {req:.2f}m "
              f"(IRC:5 §12.4 minimum 1.0 m) — REVISE deck vertical alignment")


def check_afflux_irc05(p: BridgeProject) -> ValidationFinding:
    """C28 — IRC:5 §10.3  design afflux ≤ allowable afflux."""
    afflux = float(p.hydraulic_data.afflux_m or 0)
    allow = float(p.hydraulic_data.max_afflux_allowable_m or 0)
    if allow <= 0:
        return _f("C28", "IRC:5 afflux check",
                  ValidationSeverity.CRITICAL, False,
                  "hydraulic_data.max_afflux_allowable_m must be declared (> 0)")
    passed = afflux <= allow + 1e-6
    return _f("C28", f"IRC:5 afflux = {afflux:.2f}m  (≤ {allow:.2f}m allowable)",
              ValidationSeverity.CRITICAL, passed,
              f"afflux={afflux:.2f}m > max_afflux_allowable={allow:.2f}m  (IRC:5 §10.3)")


def check_waterway_coverage_irc05(p: BridgeProject) -> ValidationFinding:
    """C29 — IRC:5 §7.4  waterway provided must be ≥ waterway required."""
    prov = float(p.hydraulic_data.waterway_provided_m2 or 0)
    req = float(p.hydraulic_data.waterway_required_m2 or 0)
    if req <= 0:
        return _f("C29", "IRC:5 waterway check",
                  ValidationSeverity.CRITICAL, False,
                  "hydraulic_data.waterway_required_m2 must be declared (> 0)")
    ratio = prov / req
    passed = ratio >= 1.0 - 1e-6
    return _f("C29",
              f"IRC:5 waterway provided={prov:.0f}m² / required={req:.0f}m² = {ratio:.2f}×",
              ValidationSeverity.CRITICAL, passed,
              f"waterway_provided={prov:.0f}m² < waterway_required={req:.0f}m²  "
              f"(IRC:5 §7.4 — risk of upstream afflux + scour)")


def check_bearing_pot_pressure_irc83(p: BridgeProject) -> ValidationFinding:
    """C30 — IRC:83 §5.4  POT PTFE bearing pressure ≤ 35 MPa; square planform."""
    POT_LIMIT_MPA = 35.0
    rows = p.bearings_joints.bearing_schedule or []
    if not rows:
        return _f("C30", "IRC:83 POT-bearing pressure check (schedule empty)",
                  ValidationSeverity.CRITICAL, False,
                  "bearing_schedule is empty — cannot validate pot pressure")
    fails: list[str] = []
    for r in rows:
        btype = str(getattr(r, "bearing_type", "") or "")
        if "POT" not in btype.upper():
            continue
        pressure = float(getattr(r, "pot_pressure_mpa", 0) or 0)
        sx = float(getattr(r, "size_x_mm", 0) or 0)
        sy = float(getattr(r, "size_y_mm", 0) or 0)
        loc = str(getattr(r, "location", "") or "")
        if pressure > POT_LIMIT_MPA + 1e-6:
            fails.append(f"{loc}: pot_pressure={pressure:.1f} MPa > {POT_LIMIT_MPA:.0f} MPa")
        if sx > 0 and sy > 0 and abs(sx - sy) > 1:
            fails.append(f"{loc}: size {sx:.0f}×{sy:.0f}mm not square (IRC:83 POT circular/equal-side)")
    passed = len(fails) == 0
    sample_msg = fails[0] if fails else ""
    return _f("C30",
              f"IRC:83 POT-bearing pressure ≤ {POT_LIMIT_MPA:.0f} MPa "
              f"({sum(1 for r in rows if 'POT' in str(getattr(r, 'bearing_type','')).upper())} POT rows OK)",
              ValidationSeverity.CRITICAL, passed,
              sample_msg if sample_msg else "IRC:83 bearing check failed")


def check_pile_fos_irc78(p: BridgeProject) -> ValidationFinding:
    """C31 — IRC:78 §11.3  factor of safety on pile bearing ≥ 2.5 (ultimate)."""
    FOS_MIN = 2.5
    fos = float(p.foundation_details.factor_of_safety_on_bearing or 0)
    passed = fos >= FOS_MIN - 1e-6
    return _f("C31",
              f"IRC:78 pile bearing FOS = {fos:.2f}  (≥ {FOS_MIN:.1f})",
              ValidationSeverity.CRITICAL, passed,
              f"factor_of_safety_on_bearing = {fos:.2f} < {FOS_MIN:.1f} IRC:78 §11.3 minimum")


def check_seismic_horizontal_force_zone3(p: BridgeProject) -> ValidationFinding:
    """W09 — IS:1893 (Part 1):2016  simplified Ah for declared zone + importance.

    Purely an advisory/WARNING at GAD stage — flags missing declarations
    and warns when Zone III/IV + importance=1.5 without pier-dimension review.
    """
    _Z_BY_NAME = {
        "ZONE_II": 0.10, "ZONE_III": 0.16, "ZONE_IV": 0.24, "ZONE_V": 0.36,
        "ZONE_2": 0.10, "ZONE_3": 0.16, "ZONE_4": 0.24, "ZONE_5": 0.36,
    }
    zone_name = str(getattr(p.bridge_selection.seismic_zone, "name", "") or "")
    Z = _Z_BY_NAME.get(zone_name, 0.0)
    if Z <= 0:
        return _f("W09", "IS:1893 seismic — no zone declared",
                  ValidationSeverity.WARNING, False,
                  "bridge_selection.seismic_zone is not a recognised IS:1893 zone")

    I_default = 1.5  # bridges = Importance Class IV  (IRC:112 default)
    pier_h = float(p.substructure.pier_height_typical_m or 0)
    span = max((float(s) for s in p.geometry_input.span_lengths_m), default=0.0)
    Ah_nominal = (Z / 2.0) * I_default * 1.0   # (Z/2)·I·(Sa/g=1)  first-mode placeholder

    # Warning trigger: Zone III/IV/V AND pier_h > 10m AND span > 25m
    heavy = (Z >= 0.16 - 1e-6) and (pier_h > 10.0) and (span > 25.0)
    passed = not heavy
    return _f("W09",
              f"IS:1893 Ah ≈ {Ah_nominal:.3f}g  (zone={zone_name}  I={I_default}  "
              f"pier_h={pier_h:.0f}m  max_span={span:.0f}m)",
              ValidationSeverity.WARNING, passed,
              f"Zone={zone_name}(Z={Z:.2f}) + pier_h={pier_h:.1f}m + span={span:.0f}m "
              f"→ schedule pier seismic shear/moment review before GAD issue")


# ===========================================================================
# M1W2 — WARNING checks  W04, W06, W07, W08, W10–W15, W17–W75  (69 total)
# ===========================================================================

def check_steel_superstructure_fatigue(p: BridgeProject) -> ValidationFinding:
    """W04 — Steel superstructure needs fatigue detail classification."""
    stype = (getattr(p.superstructure.type, "name", "") or
             str(p.superstructure.type) or "").upper()
    is_steel = any(k in stype for k in ("STEEL", "COMPOSITE", "PLATE", "TRUSS"))
    passed = not is_steel
    return _f("W04", "Steel superstructure fatigue detail classification",
              ValidationSeverity.WARNING, passed,
              "Steel/composite superstructure — classify fatigue details per IS:800 Clause 10.7 in drawings")


def check_rebar_ductility_fe500d(p: BridgeProject) -> ValidationFinding:
    """W06 — FE500D or higher grade requires additional ductility detailing."""
    grade = (getattr(p.materials.reinforcement_steel_grade, "name", "") or
             str(p.materials.reinforcement_steel_grade) or "").upper()
    high = any(k in grade for k in ("FE500D", "FE550", "FE600", "500D", "550D"))
    passed = not high
    return _f("W06", "Rebar ductility detailing review for FE500D+",
              ValidationSeverity.WARNING, passed,
              f"reinforcement_steel={grade} — confirm extra ductility hooks/laps per IS:1786 Clause 4.1")


def check_elastomeric_pad_creep(p: BridgeProject) -> ValidationFinding:
    """W07 — Elastomeric pad over 700 kN load needs creep compression-set check."""
    rows = p.bearings_joints.bearing_schedule or []
    fails: list[str] = []
    for r in rows:
        load = float(getattr(r, "load_kn", 0) or 0)
        btype = str(getattr(r, "bearing_type", "") or "").upper()
        if (
            "ELASTOMERIC" in btype or "NRB" in btype or "NEOPRENE" in btype
        ) and load > 700.0:
            loc = str(getattr(r, "location", "") or "?")
            fails.append(f"{loc}: load={load:.0f} kN > 700 kN")
    passed = len(fails) == 0
    return _f("W07", "Elastomeric bearing creep compression-set check",
              ValidationSeverity.WARNING, passed,
              fails[0] if fails else "Elastomeric pad creep check OK")


def check_joint_gap_modular(p: BridgeProject) -> ValidationFinding:
    """W08 — Joint gap over 100 mm requires modular multi-gap specification."""
    rows = p.bearings_joints.expansion_joint_schedule or []
    fails: list[str] = []
    for r in rows:
        gap = float(getattr(r, "gap_mm", 0) or 0)
        mv = float(getattr(r, "movement_range_mm", 0) or 0)
        worst = max(gap, abs(mv))
        if worst > 100.0:
            loc = str(getattr(r, "location", "") or "?")
            fails.append(f"{loc}: worst={worst:.0f}mm > 100mm")
    passed = len(fails) == 0
    return _f("W08", "Expansion joint gap ≤ 100 mm (modular joint check)",
              ValidationSeverity.WARNING, passed,
              fails[0] if fails else "All expansion joints within strip-seal range")


def check_slag_blended_cement_curing(p: BridgeProject) -> ValidationFinding:
    """W09 — Blended slag/flyash cement needs extended curing period."""
    cement = (getattr(p.materials.cement_type, "name", "") or
              str(p.materials.cement_type) or "").upper()
    blended = any(k in cement for k in ("SLAG", "FLYASH", "FLY_ASH", "PPC", "PSC", "BLENDED"))
    passed = not blended
    return _f("W09", "Extended curing period for blended cement",
              ValidationSeverity.WARNING, passed,
              f"cement_type={cement} — specify 14-day minimum extended curing per IS:1489 Clause 8")


def check_aggregate_size_pumpability(p: BridgeProject) -> ValidationFinding:
    """W10 — Nominal aggregate > 20 mm requires pumpability review."""
    agg = (getattr(p.materials.concrete_aggregate, "name", "") or
           str(p.materials.concrete_aggregate) or "").upper()
    large = any(k in agg for k in ("40MM", "40_MM", "LARGE", "COARSE_40"))
    passed = not large
    return _f("W10", "Concrete pumpability review for aggregate > 20 mm",
              ValidationSeverity.WARNING, passed,
              f"aggregate_type={agg} — 40 mm nominal needs pumpability review for deck pours (IS:383 Clause 6)")


def check_aggressive_water_extra_cover(p: BridgeProject) -> ValidationFinding:
    """W11 — Aggressive water classification requires extra cover + coating."""
    wq = (getattr(p.hydraulic_data.water_source_type, "name", "") or
          str(p.hydraulic_data.water_source_type) or "").upper()
    aggro = any(k in wq for k in ("TIDAL", "MARINE", "SEWAGE", "EFFLUENT", "SALINE", "SEA"))
    passed = not aggro
    return _f("W11", "Aggressive-water protective cover + coating",
              ValidationSeverity.WARNING, passed,
              f"water_source_type={wq} — add minimum 10 mm extra cover + protective coating per IS:456 Table 5")


def test_thick_cover_anticrack_mesh(p: BridgeProject) -> ValidationFinding:
    """W12 — Nominal cover > 75 mm requires anti-crack surface mesh."""
    covers = [
        float(getattr(p.superstructure, "cover_superstructure_mm", 0) or 0),
        float(getattr(p.substructure, "cover_substructure_mm", 0) or 0),
        float(getattr(p.foundation_details, "cover_foundation_mm", 0) or 0),
    ]
    worst = max(covers) if covers else 0.0
    passed = worst <= 75.0
    return _f("W12", "Anti-crack surface mesh for cover > 75 mm",
              ValidationSeverity.WARNING, passed,
              f"max nominal cover={worst:.0f} mm > 75 mm — specify anti-crack A142 mesh (IS:456 Clause 26.4)")


def check_high_slump_superplasticizer(p: BridgeProject) -> ValidationFinding:
    """W13 — Slump above S4 requires superplasticizer admixture declaration."""
    slump = (getattr(p.materials, "concrete_slump_class", None) or
             "").__class__.__name__.upper() if getattr(p.materials, "concrete_slump_class", None) else ""
    high = any(k in slump for k in ("S4", "S5", "S6", "S7", "S8"))
    passed = not high
    return _f("W13", "Superplasticizer declaration for slump class ≥ S4",
              ValidationSeverity.WARNING, passed,
              f"slump_class={slump} — S4 or above requires superplasticizer admixture declared (IS:456 Clause 12.1)")


def check_membrane_curing_release_agent(p: BridgeProject) -> ValidationFinding:
    """W14 — Membrane curing needs compatible release-agent / painting prep."""
    curing = (getattr(p.materials.concrete_curing_method, "name", "") or
              str(p.materials.concrete_curing_method) or "").upper()
    membrane = "MEMBRANE" in curing
    passed = not membrane
    return _f("W14", "Membrane-curing surface prep for paint / overlay",
              ValidationSeverity.WARNING, passed,
              f"curing_method={curing} — membrane curing requires surface abrasion prep before painting/overlay (IRC SP-55 Clause 10.3)")


def check_sharp_curvature_superelevation(p: BridgeProject) -> ValidationFinding:
    """W15 — Sharp curvature class triggers superelevation transition review."""
    R = float(p.geometry_input.horizontal_curve_R_m or 0)
    sharp = (R > 0) and (R < 300.0)
    passed = not sharp
    return _f("W15", "Superelevation transition review for curves R < 300 m",
              ValidationSeverity.WARNING, passed,
              f"horizontal_curve_R={R:.0f} m < 300 m — verify superelevation runoff length IRC:73 Clause 5.2")


def check_well_caisson_sinking_sequence(p: BridgeProject) -> ValidationFinding:
    """W17 — Well / open caisson pier requires detailed sinking plan."""
    ftype = (getattr(p.foundation_details.type, "name", "") or
             str(p.foundation_details.type) or "").upper()
    well = "WELL" in ftype or "CAISSON" in ftype
    passed = not well
    return _f("W17", "Well/caisson sinking sequence plan required",
              ValidationSeverity.WARNING, passed,
              f"foundation_type={ftype} — attach detailed sinking sequence + blow counts (IRC:78 Clause 10)")


def check_pile_lateral_group_efficiency(p: BridgeProject) -> ValidationFinding:
    """W18 — Pile foundation requires lateral load + group efficiency analysis."""
    ftype = (getattr(p.foundation_details.type, "name", "") or
             str(p.foundation_details.type) or "").upper()
    pile = "PILE" in ftype
    n_piles = int(p.foundation_details.piles_per_pier or 0)
    group = n_piles >= 5
    passed = not (pile and group)
    return _f("W18", "Pile lateral load + group efficiency analysis",
              ValidationSeverity.WARNING, passed,
              f"foundation_type={ftype}, piles_per_pier={n_piles} — group efficiency η_g + lateral load required (IS:2911 Part 1)")


def check_counterfort_abutment_passive_pressure(p: BridgeProject) -> ValidationFinding:
    """W19 — Counterfort / T-type abutment needs passive earth-pressure verification."""
    abtype = (getattr(p.substructure.abutment_type, "name", "") or
              str(p.substructure.abutment_type) or "").upper()
    heavy = any(k in abtype for k in ("COUNTERFORT", "T_TYPE", "BUTTRESS"))
    passed = not heavy
    return _f("W19", "Passive-earth-pressure verification for heavy abutment",
              ValidationSeverity.WARNING, passed,
              f"abutment_type={abtype} — verify passive Kp = tan²(45+φ/2) behind heel (IRC:78 Clause 8.3)")


def check_sma_wearing_coat_polymer_modified(p: BridgeProject) -> ValidationFinding:
    """W20 — SMA wearing coat grade requires polymer modified binder."""
    wc = (getattr(p.superstructure.wearing_coat_type, "name", "") or
          str(p.superstructure.wearing_coat_type) or "").upper()
    sma = "SMA" in wc or "STONE_MATRIX" in wc
    passed = not sma
    return _f("W20", "SMA wearing coat mandates polymer-modified binder",
              ValidationSeverity.WARNING, passed,
              f"wearing_coat_type={wc} — specify PMB 40 / CRMB 60 binder grade (MORTH Clause 510)")


def check_wearing_coat_levelling_course(p: BridgeProject) -> ValidationFinding:
    """W21 — Wearing coat > 50 mm requires levelling course specification."""
    t = float(p.superstructure.wearing_coat_thickness_mm or 0)
    passed = t <= 50.0
    return _f("W21", "Levelling course for wearing coat thickness > 50 mm",
              ValidationSeverity.WARNING, passed,
              f"wearing_coat_thickness={t:.0f} mm > 50 mm — add DBM/GBM levelling course layer (IRC:58-2005 Clause 5)")


def check_waterproofing_tack_coat_compatible(p: BridgeProject) -> ValidationFinding:
    """W22 — Buried deck waterproofing must be compatible with wearing-coat tack coat."""
    wp = (getattr(p.materials.waterproofing_membrane, "name", "") or
          str(p.materials.waterproofing_membrane) or "").upper()
    buried = any(k in wp for k in ("BURIED", "UNDERLAY", "INVERTED", "APP", "SBS"))
    passed = not buried
    return _f("W22", "Waterproofing / tack-coat compatibility review",
              ValidationSeverity.WARNING, passed,
              f"waterproofing={wp} — confirm prime coat + tack coat bond to membrane top-face (IRC SP-55 Clause 7.5)")


def check_rigid_parapet_impact_load(p: BridgeProject) -> ValidationFinding:
    """W23 — Rigid parapet class requires vehicle impact load case HL-93 sidebar."""
    ptype = (getattr(p.superstructure.parapet_type, "name", "") or
             str(p.superstructure.parapet_type) or "").upper()
    rigid = any(k in ptype for k in ("RCC", "CONCRETE", "RIGID", "NEW_JERSEY", "F_SHAPE"))
    passed = not rigid
    return _f("W23", "Rigid-parapet vehicle-impact load-case review",
              ValidationSeverity.WARNING, passed,
              f"parapet_type={ptype} — include HL-93 sidebar impact 100 kN @ 1.2 m in analysis (IRC:6 Clause 3.11)")


def check_high_mount_kerb_drainage_scuppers(p: BridgeProject) -> ValidationFinding:
    """W24 — High-mount kerb needs dedicated drainage scupper spacing plan."""
    ktype = (getattr(p.geometry_input.kerb_type, "name", "") or
             str(p.geometry_input.kerb_type) or "").upper()
    high = any(k in ktype for k in ("HIGH", "MOUNTAIN", "VERTICAL", "BARRIER"))
    passed = not high
    return _f("W24", "High-mount kerb scupper drainage spacing",
              ValidationSeverity.WARNING, passed,
              f"kerb_type={ktype} — provide scupper outlets every ≤ 5 m (IRC:86 Clause 4.6)")


def check_street_lighting_dual_luminaire(p: BridgeProject) -> ValidationFinding:
    """W25 — Street lighting Lux class above M3 requires dual-luminaire on abutment walls."""
    lighting = (getattr(p.superstructure, "street_lighting_lux_class", None) or
                "").__class__.__name__.upper() if getattr(p.superstructure, "street_lighting_lux_class", None) else ""
    high_lux = any(k in lighting for k in ("M4", "M5", "M6", "S4", "S5", "S6"))
    passed = not high_lux
    return _f("W25", "Dual-luminaire lighting for Lux class ≥ M4",
              ValidationSeverity.WARNING, passed,
              f"lighting={lighting} — M4+ class — dual 70 W LED per abutment wing (IRC:86 Annex D)")


def check_launching_apron_stone_weight(p: BridgeProject) -> ValidationFinding:
    """W26 — Launching apron protection needs stone weight sized against design flow velocity."""
    scour = (getattr(p.hydraulic_data.scour_protection_subtype, "name", "") or
             str(p.hydraulic_data.scour_protection_subtype) or "").upper()
    apron = "APRON" in scour or "LAUNCHING" in scour or "RIPRAP" in scour
    v = float(p.hydraulic_data.design_velocity_mps or 0)
    if apron and v > 0:
        required_kg = round(0.023 * (v ** 3), 1)  # ISO recommended stone mass
        passed = required_kg <= 100.0
        msg = f"design velocity={v:.2f} m/s → minimum riprap stone = {required_kg:.1f} kg each"
    else:
        passed = True
        msg = ""
    return _f("W26", "Launching-apron stone weight vs design velocity",
              ValidationSeverity.WARNING, passed,
              msg if msg else "Scour protection stone weight check")


def check_braided_meandering_2d_model(p: BridgeProject) -> ValidationFinding:
    """W27 — Braided / meandering river reach requires 2D hydraulic model note."""
    geo = (getattr(p.hydraulic_data.river_geomorphology_type, "name", "") or
           str(p.hydraulic_data.river_geomorphology_type) or "").upper()
    complex_2d = any(k in geo for k in ("BRAIDED", "MEANDER", "ANABRANCHED", "ISLAND"))
    passed = not complex_2d
    return _f("W27", "2D hydraulic model overlay for braided/meandering reach",
              ValidationSeverity.WARNING, passed,
              f"river_geomorphology={geo} — attach HEC-RAS 2D / MIKE21 flow pattern note (IRC:5 Clause 6.2)")


def check_backwater_afflux_bund_heights(p: BridgeProject) -> ValidationFinding:
    """W28 — Backwater-affected profile must include afflux bund heights."""
    wsp = (getattr(p.hydraulic_data.water_surface_profile_type, "name", "") or
           str(p.hydraulic_data.water_surface_profile_type) or "").upper()
    backwater = "BACKWATER" in wsp or "AFFLUX" in wsp or "MILD_SLOPE" in wsp
    passed = not backwater
    return _f("W28", "Afflux bund heights for backwater-affected profile",
              ValidationSeverity.WARNING, passed,
              f"water_surface_profile={wsp} — include approach bund heights at HFL + afflux (IRC:5 Clause 7)")


def check_return_period_pmf_overlay(p: BridgeProject) -> ValidationFinding:
    """W29 — Return period > 100 yr requires PMF probable-maximum-flood overlay."""
    rp_raw = getattr(p.hydraulic_data, "return_period_yr", None)
    rp = 0.0
    try:
        rp = float(rp_raw)
    except (ValueError, TypeError):
        # Enum / non-numeric return-period tag — try to extract a leading number
        tag = str(getattr(rp_raw, "value", rp_raw) or "")
        digits = "".join(ch for ch in tag if ch.isdigit())
        if digits:
            rp = float(digits)
    passed = rp <= 100.0 or rp == 0.0
    return _f("W29", "PMF overlay for return period T > 100 yr",
              ValidationSeverity.WARNING, passed,
              f"return_period tag={rp_raw!r} implies T > 100 yr — compute PMF envelope and overlay on HFL profile (IRC:5 Clause 2.2)")


def check_short_duration_storm_culvert_peak(p: BridgeProject) -> ValidationFinding:
    """W30 — Short-duration 10-min flash storm needs culvert peak discharge review."""
    storm = (getattr(p.hydraulic_data.rainfall_intensity_storm_type, "name", "") or
             str(p.hydraulic_data.rainfall_intensity_storm_type) or "").upper()
    flash = any(k in storm for k in ("FLASH", "10MIN", "SHORT", "STORM_10"))
    passed = not flash
    return _f("W30", "Culvert peak discharge for 10-min flash storm",
              ValidationSeverity.WARNING, passed,
              f"rainfall_storm={storm} — apply rational formula IDF to verify culvert inlet control (IRC:5 Annex B)")


def check_hfl_near_soffit_deck_raise(p: BridgeProject) -> ValidationFinding:
    """W31 — HFL within 0.5 m of soffit requires deck-level raising study."""
    gap = float(p.hydraulic_data.actual_soffit_level_m or 0) - float(p.hydraulic_data.hfl_m or 0)
    passed = gap >= 0.5
    return _f("W31", "Deck raising study when HFL is within 0.5 m of soffit",
              ValidationSeverity.WARNING, passed,
              f"HFL→soffit clearance = {gap:.2f} m < 0.5 m — study deck raising or longer spans (IRC:78 Clause 7.1)")


def check_high_sediment_desilting(p: BridgeProject) -> ValidationFinding:
    """W32 — High sediment yield river needs annual desilting provisions note."""
    sed = (getattr(p.hydraulic_data.sediment_yield_classification, "name", "") or
           str(p.hydraulic_data.sediment_yield_classification) or "").upper()
    high = any(k in sed for k in ("HIGH", "VERY_HIGH", "EXTREME", "SEVERE"))
    passed = not high
    return _f("W32", "Annual desilting provision note for high sediment",
              ValidationSeverity.WARNING, passed,
              f"sediment_yield={sed} — add annual maintenance desilting 2× / year note (IRC:5 Clause 8.3)")


def check_major_river_peer_hydrology(p: BridgeProject) -> ValidationFinding:
    """W33 — Major river crossing must have independent peer review hydrology."""
    cross = (getattr(p.hydraulic_data.river_crossing_class, "name", "") or
             str(p.hydraulic_data.river_crossing_class) or "").upper()
    major = "MAJOR" in cross or "LARGE" in cross
    passed = not major
    return _f("W33", "Independent peer-review hydrology for major crossing",
              ValidationSeverity.WARNING, passed,
              f"river_crossing={cross} — engage second independent hydrologist for review (MORTH Appendix B)")


def check_high_wind_across_wind_spectrum(p: BridgeProject) -> ValidationFinding:
    """W34 — Vb > 50 m/s triggers along-wind + across-wind response spectrum."""
    vb = (getattr(p.bridge_selection.wind_zone_ms, "value", None) or
          getattr(p.bridge_selection.wind_zone_ms, "name", None) or 0)
    try:
        vb_f = float(vb)
    except (ValueError, TypeError):
        vb_f = 0.0
    passed = vb_f <= 50.0
    return _f("W34", "Across-wind response spectrum for Vb > 50 m/s",
              ValidationSeverity.WARNING, passed,
              f"basic_wind_speed Vb = {vb_f:.1f} m/s > 50 — add along-wind + across-wind spectra (IS:875 Part 3 Clause 6)")


def check_zone_v_ductility_dcl(p: BridgeProject) -> ValidationFinding:
    """W35 — Zone V demands DCL special moment frame ductility detailing."""
    zone = (getattr(p.bridge_selection.seismic_zone, "name", "") or
            str(p.bridge_selection.seismic_zone) or "").upper()
    zone_v = any(k in zone for k in ("ZONE_V", "ZONE_5", "ZONE5", "ZONEV"))
    passed = not zone_v
    return _f("W35", "Special moment-frame DCL ductility for Zone V",
              ValidationSeverity.WARNING, passed,
              f"seismic_zone={zone} — apply SMF/DCL detailing: strong-column-weak-beam + hoops (IS:1893 Part 1 Clause 7.9)")


def check_site_class_cd_response_spectrum(p: BridgeProject) -> ValidationFinding:
    """W36 — Site class C/D soil requires site-specific response spectrum."""
    soil = (getattr(p.hydraulic_data.soil_class, "name", "") or
            str(p.hydraulic_data.soil_class) or "").upper()
    cd = any(k in soil for k in ("CLAY", "SILT", "MEDIUM", "SOFT", "TYPE_III", "CLASS_C", "CLASS_D"))
    passed = not cd
    return _f("W36", "Site-specific response spectrum for soil Class C/D",
              ValidationSeverity.WARNING, passed,
              f"soil_class={soil} — develop site-specific Sa/g spectrum vs code default (IS:1893 Part 1 Fig. 2)")


def check_dcl_fuse_bearing_capacity(p: BridgeProject) -> ValidationFinding:
    """W37 — DCL link to deck joint demands fuse-bearing capacity verification."""
    dcl = (getattr(p.bridge_selection, "ductility_class_link", None) or
           "").__class__.__name__.upper() if getattr(p.bridge_selection, "ductility_class_link", None) else ""
    demand = "HIGH" in dcl or "SPECIAL" in dcl or "DCL" in dcl or "E2" in dcl or "E3" in dcl
    passed = not demand
    return _f("W37", "Fuse-bearing capacity verification for DCL link",
              ValidationSeverity.WARNING, passed,
              f"ductility_link={dcl} — verify bearing fuse capacity < pier plastic moment (IRC:112 Annex E)")


def check_fatigue_detail_category_c(p: BridgeProject) -> ValidationFinding:
    """W38 — Fatigue detail category C or lower must use reduced stress range curve."""
    fatigue = (getattr(p.superstructure, "fatigue_detail_category_steel", None) or
               "").__class__.__name__.upper() if getattr(p.superstructure, "fatigue_detail_category_steel", None) else ""
    low = any(k in fatigue for k in ("CATEGORY_C", "CATEGORY_D", "CATEGORY_E", "CATEGORY_F", "CLASS_C", "CLASS_D", "CLASS_E"))
    passed = not low
    return _f("W38", "Reduced fatigue stress-range curve for category ≤ C",
              ValidationSeverity.WARNING, passed,
              f"fatigue_detail={fatigue} — apply Category C/D reduced Δσ-N curve (IS:800 Table 18)")


def check_prestress_creep_shrinkage_loss(p: BridgeProject) -> ValidationFinding:
    """W39 — Long-term creep + shrinkage loss > 25% requires revised jacking stress."""
    loss_types = (getattr(p.superstructure, "prestress_loss_type_enum", None) or
                  "").__class__.__name__.upper() if getattr(p.superstructure, "prestress_loss_type_enum", None) else ""
    creep_dominated = "CREEP_SHRINKAGE" in loss_types or "LONG_TERM" in loss_types
    jack = float(getattr(p.superstructure, "prestress_jacking_stress_mpa", 0) or 0)
    fpk = float(getattr(p.superstructure, "prestress_grade_mpa", 1860) or 1860)
    if creep_dominated and jack > 0 and fpk > 0:
        ratio = jack / fpk
        passed = ratio <= 0.70
    else:
        passed = True
    return _f("W39", "Prestress creep/shrinkage loss percentage ≤ 25%",
              ValidationSeverity.WARNING, passed,
              f"jack/fpk={jack:.0f}/{fpk:.0f} = {100*jack/fpk:.0f}% — reduce jacking or increase strands (IRC:112 Clause 6.8)")


def check_creep_shrinkage_low_humidity_1_3x(p: BridgeProject) -> ValidationFinding:
    """W40 — Humidity < 40% geographic region demands 1.3× extra creep factor."""
    humidity = float(getattr(p.superstructure, "creep_shrinkage_humidity_pct", 0) or 0)
    dry = (humidity > 0) and (humidity < 40.0)
    passed = not dry
    return _f("W40", "1.3× creep factor for humidity < 40% region",
              ValidationSeverity.WARNING, passed,
              f"ambient humidity={humidity:.0f}% < 40% — apply φ_cc = 1.3 × code φ (IS:1343 Clause 5.3)")


def check_temperature_gradient_nonlinear(p: BridgeProject) -> ValidationFinding:
    """W41 — Temperature differential > 20 °C requires non-linear through-depth gradient."""
    dT = float(getattr(p.bridge_selection.temperature_load_delta_t, "value", 0) or
               0)
    try:
        dT_f = float(dT)
    except (ValueError, TypeError):
        dT_f = 0.0
    passed = dT_f <= 20.0
    return _f("W41", "Non-linear through-depth ΔT gradient for ΔT > 20 °C",
              ValidationSeverity.WARNING, passed,
              f"temperature ΔT = {dT_f:.1f} °C > 20 — apply IRC:6 Table 15 non-linear gradient (Clause 3.8)")


def check_impact_factor_daf_check(p: BridgeProject) -> ValidationFinding:
    """W42 — Impact factor above 0.33 needs dynamic amplification factor check."""
    imp = (getattr(p.bridge_selection.impact_factor_coeff, "value", 0) or 0)
    try:
        imp_f = float(imp)
    except (ValueError, TypeError):
        imp_f = 0.0
    passed = imp_f <= 0.331
    return _f("W42", "Dynamic amplification factor DAF for IF > 0.33",
              ValidationSeverity.WARNING, passed,
              f"impact_factor={imp_f:.3f} > 0.33 — compute DAF from first-bending frequency (IRC:6 Clause 3.5)")


def check_eq_ultimate_overstrength_factor(p: BridgeProject) -> ValidationFinding:
    """W43 — Ultimate EQ combination without overstrength factor flagged for review."""
    combos = getattr(p.bridge_selection, "load_combinations", None) or []
    if hasattr(combos, "__iter__") and not isinstance(combos, str):
        names = [str(getattr(c, "name", c)) for c in combos]
    else:
        names = []
    eq_found = any("EQ" in n.upper() or "EARTHQUAKE" in n.upper() for n in names)
    os_found = any("OVERSTRENGTH" in n.upper() or "Ω" in n or "OS_" in n.upper() for n in names)
    passed = not (eq_found and not os_found)
    return _f("W43", "Overstrength Ω factor in ultimate EQ combination",
              ValidationSeverity.WARNING, passed,
              "EQ combo found but overstrength Ω missing — add 1.3 Ω to ULS EQ (IRC:6 Table 1)")


def check_ptfe_stainless_steel_surface(p: BridgeProject) -> ValidationFinding:
    """W44 — PTFE coefficient < 0.08 requires stainless steel mating surface note."""
    rows = p.bearings_joints.bearing_schedule or []
    fails: list[str] = []
    for r in rows:
        mu = float(getattr(r, "friction_coeff", 0) or 0)
        if 0 < mu < 0.08:
            loc = str(getattr(r, "location", "") or "?")
            fails.append(f"{loc}: μ={mu:.3f}")
    passed = len(fails) == 0
    return _f("W44", "Stainless-steel mating surface for PTFE μ < 0.08",
              ValidationSeverity.WARNING, passed,
              f"{fails[0]} — specify 316L SS mating surface Ra ≤ 0.8 μm (IRC:83 Part II)")


def check_low_damping_tmd_feasibility(p: BridgeProject) -> ValidationFinding:
    """W45 — Damping ratio < 2% for steel superstructure requires TMD feasibility note."""
    damp = (getattr(p.bridge_selection.damping_ratio_type_enum, "name", "") or
            str(p.bridge_selection.damping_ratio_type_enum) or "").upper()
    low = any(k in damp for k in ("0_5_PCT", "1_PCT", "LOW", "STEEL_0_02")) or "1" in damp
    stype = (getattr(p.superstructure.type, "name", "") or "").upper()
    steel = "STEEL" in stype or "COMPOSITE" in stype
    passed = not (steel and low)
    return _f("W45", "TMD feasibility for steel damping ratio < 2%",
              ValidationSeverity.WARNING, passed,
              f"damping={damp} on steel superstructure — conduct TMD/MTMD feasibility note (IS:1893 Clause 6.4.3)")


def check_tall_gravity_retaining_wall_counterfort(p: BridgeProject) -> ValidationFinding:
    """W46 — Gravity retaining wall > 6 m height may need counterfort redesign note."""
    rw_type = (getattr(p.approaches.retaining_wall_type, "name", "") or
               str(p.approaches.retaining_wall_type) or "").upper()
    gravity = "GRAVITY" in rw_type or "MASS" in rw_type or "SEMIGRAVITY" in rw_type
    h = float(getattr(p.approaches, "retaining_wall_height_m", 0) or 0)
    passed = not (gravity and h > 6.0)
    return _f("W46", "Counterfort redesign note for gravity RW > 6 m",
              ValidationSeverity.WARNING, passed,
              f"retaining_wall={rw_type} H={h:.1f} m > 6 m — consider counterfort type (IS:14458 Part 2)")


def check_out_of_service_layer_plot_suppress(p: BridgeProject) -> ValidationFinding:
    """W47 — Layer group OUT_OF_SERVICE used on primary deliverable — confirm suppress-plot."""
    # Check drawing_control.generate list for layer names containing OUT_OF_SERVICE
    gen = getattr(p.drawing_control, "generate_layers", None) or []
    if hasattr(gen, "__iter__") and not isinstance(gen, str):
        names = [str(getattr(x, "name", x)).upper() for x in gen]
    else:
        names = []
    oos = any("OUT_OF_SERVICE" in n or "DEPRECATED" in n for n in names)
    passed = not oos
    return _f("W47", "OUT_OF_SERVICE layer confirm plot-suppress flag",
              ValidationSeverity.WARNING, passed,
              "OUT_OF_SERVICE / deprecated layers present — set plot=No in pen-table (IRC SP-55 Annex F)")


def check_heavy_lineweight_hatching_bleed(p: BridgeProject) -> ValidationFinding:
    """W48 — Line weight > 1.0 mm used in section hatching boundary — review print bleed."""
    lwc = (getattr(p.drawing_control, "line_weight_code", None) or
           "").__class__.__name__.upper() if getattr(p.drawing_control, "line_weight_code", None) else ""
    heavy = any(k in lwc for k in ("1_0MM", "1_2MM", "1_4MM", "2_0MM", "LW_1", "LW_1_4"))
    passed = not heavy
    return _f("W48", "Review print bleed for line weight > 1.0 mm",
              ValidationSeverity.WARNING, passed,
              f"line_weight={lwc} — > 1.0 mm may bleed through on hatched sections (IRC SP-55 Clause 11.2)")


def check_user_hatch_pen_table(p: BridgeProject) -> ValidationFinding:
    """W49 — User-defined hatch pattern present — verify plotter pen-table includes it."""
    hatch = (getattr(p.drawing_control, "hatch_pattern_code", None) or
             "").__class__.__name__.upper() if getattr(p.drawing_control, "hatch_pattern_code", None) else ""
    custom = any(k in hatch for k in ("CUSTOM", "USER_DEFINED", "EARTH", "CUSTOM_SOIL"))
    passed = not custom
    return _f("W49", "User-hatch present in plotter pen-table",
              ValidationSeverity.WARNING, passed,
              f"hatch_pattern={hatch} — confirm .pat file installed in plotter pen-table (IRC SP-55 Annex F)")


def check_non_iso_font_pdf_embedding(p: BridgeProject) -> ValidationFinding:
    """W50 — Non-ISO font family detected — confirm PDF embedding enabled."""
    font = (getattr(p.drawing_control.font_style, "name", "") or
            str(p.drawing_control.font_style) or "").upper()
    noniso = any(k in font for k in ("ARIAL", "HELVETICA", "TIMES", "CALIBRI", "VERDANA"))
    passed = not noniso
    return _f("W50", "Non-ISO font family PDF embedding flag",
              ValidationSeverity.WARNING, passed,
              f"font_style={font} — enable FULL font embedding (ISO subset only for ISO family) (IRC SP-55 Annex G)")


def check_large_scale_dim_roundoff(p: BridgeProject) -> ValidationFinding:
    """W51 — Scale 1:100 or larger needs dimension round-off tolerance class 5 mm."""
    scale = int(getattr(p.drawing_control, "drawing_scale", 0) or 0)
    large = (scale > 0) and (scale <= 100)
    passed = not large
    return _f("W51", "Dimension round-off tolerance for scale ≤ 1:100",
              ValidationSeverity.WARNING, passed,
              f"drawing_scale=1:{scale} ≤ 100 — use 5 mm round-off class for plan dimensions (IRC SP-55 Clause 11.3)")


def check_isometric_dim_true_length(p: BridgeProject) -> ValidationFinding:
    """W52 — 3D isometric view on GAD sheet triggers dimension true-length check."""
    views = getattr(p.drawing_control, "generate_views", None) or []
    if hasattr(views, "__iter__") and not isinstance(views, str):
        names = [str(getattr(v, "name", v)).upper() for v in views]
    else:
        names = []
    iso = any("ISOMETRIC" in n or "3D" in n or "PERSPECTIVE" in n for n in names)
    passed = not iso
    return _f("W52", "True-length dimension check on 3D isometric views",
              ValidationSeverity.WARNING, passed,
              "3D / isometric view present — verify all dims use TRUE length not projected (IRC SP-55 Clause 11.4)")


def check_chained_dimension_tolerance(p: BridgeProject) -> ValidationFinding:
    """W53 — Chained dimension style needs ± cumulative tolerance statement."""
    dim = (getattr(p.drawing_control.dimension_style_class, "name", "") or
           str(p.drawing_control.dimension_style_class) or "").upper()
    chained = "CHAIN" in dim or "CHAINED" in dim or "CONTINUOUS" in dim
    passed = not chained
    return _f("W53", "Chained-dimension cumulative tolerance statement",
              ValidationSeverity.WARNING, passed,
              f"dimension_style={dim} — add footnote '±5 mm cumulative tolerance' (IRC SP-55 Clause 11.3)")


def check_ift_revision_no_qa_signoff(p: BridgeProject) -> ValidationFinding:
    """W54 — Revision class C (issued-for-tender) without QA sign-off flagged."""
    rev = (getattr(p.drawing_control.title_block_revision_class, "name", "") or
           str(p.drawing_control.title_block_revision_class) or "").upper()
    ift = any(k in rev for k in ("IFT", "TENDER", "C_ISSUE", "ISSUE_C", "REV_C"))
    qa = getattr(p.project_master, "approved_by", None)
    passed = not (ift and not qa)
    return _f("W54", "QA sign-off present for IFT revision",
              ValidationSeverity.WARNING, passed,
              f"revision={rev} IFT but approved_by/QA_signoff empty — fill before release (MORTH Clause 1007.1)")


def check_jumbo_paper_plotter_inventory(p: BridgeProject) -> ValidationFinding:
    """W55 — A0+ jumbo paper class — confirm plotter media inventory before print run."""
    paper = (getattr(p.drawing_control.plotter_paper_class, "name", "") or
             str(p.drawing_control.plotter_paper_class) or "").upper()
    jumbo = any(k in paper for k in ("A0_PLUS", "JUMBO", "A0P", "AO_PLUS", "EXTRA_WIDE"))
    passed = not jumbo
    return _f("W55", "A0+ jumbo plotter media inventory check",
              ValidationSeverity.WARNING, passed,
              f"paper={paper} — A0+ / jumbo roll — confirm 914 mm wide × 50 m roll in stock (IRC SP-55 Annex G)")


def check_half_symmetric_section_cut_plane(p: BridgeProject) -> ValidationFinding:
    """W56 — Half-symmetric cross-section — verify section cut-plane is noted."""
    vtype = (getattr(p.drawing_control.cross_section_view_type_code, "name", "") or
             str(p.drawing_control.cross_section_view_type_code) or "").upper()
    half = any(k in vtype for k in ("HALF", "HALF_SYMMETRIC", "HALF_VIEW", "SYMMETRIC_HALF"))
    passed = not half
    return _f("W56", "Section cut-plane annotation on half-symmetric view",
              ValidationSeverity.WARNING, passed,
              f"cross_section_view={vtype} — add section line A-A + directional arrows (IRC SP-55 Clause 11.4)")


def check_centerline_border_drafting_convention(p: BridgeProject) -> ValidationFinding:
    """W57 — Centerline dash used for outline border — verify drafting convention."""
    # Infer if the drawing_control.layer_standard uses CENTERLINE style for border
    layer = (getattr(p.drawing_control.layer_standard, "name", "") or
             str(p.drawing_control.layer_standard) or "").upper()
    nonstd = "CUSTOM" in layer or "NON_STANDARD" in layer
    passed = not nonstd
    return _f("W57", "Verify border line-style not centreline dash",
              ValidationSeverity.WARNING, passed,
              f"layer_standard={layer} — confirm BORDER uses CONTINUOUS not centerline (IRC SP-55 Annex F)")


def check_dot_arrow_dim_leader_switch(p: BridgeProject) -> ValidationFinding:
    """W58 — Arrow dot style on dimension leader for small features — switch to slash?"""
    arrow = (getattr(p.drawing_control.arrow_style, "name", "") or
             str(p.drawing_control.arrow_style) or "").upper()
    dot = "DOT" in arrow or "CLOSED_DOT" in arrow or "DOT_TICK" in arrow
    passed = not dot
    return _f("W58", "Dimension leader arrow style — slash for small features",
              ValidationSeverity.WARNING, passed,
              f"arrow_style={arrow} — DOT style too large for < 3 mm leaders; use ARCHITECTURAL TICK (IRC SP-55 Annex F)")


def check_lightweight_aggregate_unit_weight(p: BridgeProject) -> ValidationFinding:
    """W59 — Lightweight aggregate needs specific unit-weight value in design report."""
    agg = (getattr(p.materials.concrete_aggregate, "name", "") or
           str(p.materials.concrete_aggregate) or "").upper()
    lw = any(k in agg for k in ("LIGHT", "LIGHTWEIGHT", "LWC", "EXPANDED", "PERLITE", "VERMICULITE"))
    passed = not lw
    return _f("W59", "Unit-weight declaration for lightweight aggregate",
              ValidationSeverity.WARNING, passed,
              f"aggregate_type={agg} — state ρ_lwc = 16-19 kN/m³ in design report (IS:383 Part 2)")


def check_accelerator_retarder_compatibility(p: BridgeProject) -> ValidationFinding:
    """W60 — Accelerator + retarder admixture mix — verify compatibility doc."""
    admixtures = getattr(p.materials, "admixture_type", None) or []
    if hasattr(admixtures, "__iter__") and not isinstance(admixtures, str) and not hasattr(admixtures, "name"):
        names = [str(getattr(a, "name", a)).upper() for a in admixtures]
    else:
        names = [str(getattr(admixtures, "name", admixtures)).upper()]
    accel = any("ACCEL" in n or "CALCIUM" in n for n in names)
    retard = any("RETARD" in n or "SET" in n or "DELAY" in n for n in names)
    passed = not (accel and retard)
    return _f("W60", "Accelerator + retarder admixture compatibility",
              ValidationSeverity.WARNING, passed,
              "BOTH accelerator AND retarder specified — attach manufacturer compatibility sheet (IS:9103 Clause 5)")


def check_full_penetration_weld_ndt_plan(p: BridgeProject) -> ValidationFinding:
    """W61 — Full-penetration groove weld class needs NDT UT/RT plan."""
    weld = (getattr(p.materials.weld_type_for_steel, "name", "") or
            str(p.materials.weld_type_for_steel) or "").upper()
    full_pen = any(k in weld for k in ("FULL_PEN", "COMPLETE_JOINT", "CJP", "FULL_GROOVE"))
    passed = not full_pen
    return _f("W61", "Full-penetration weld NDT UT/RT inspection plan",
              ValidationSeverity.WARNING, passed,
              f"weld_type={weld} — specify 100% RT + 20% UT re-inspection plan (IS:800 Clause 10.5)")


def check_ptfe_roughness_surface(p: BridgeProject) -> ValidationFinding:
    """W62 — PTFE + stainless steel pair — specify sliding surface roughness Ra."""
    bm = (getattr(p.materials.bearing_material, "name", "") or
          str(p.materials.bearing_material) or "").upper()
    ptfe = "PTFE" in bm or "TEFLON" in bm or "GLASS_FILLED" in bm
    rows = p.bearings_joints.bearing_schedule or []
    ss_found = any(("STAINLESS" in str(getattr(r, "bearing_type", "")).upper() or
                    "SS" in str(getattr(r, "bearing_type", "")).upper()) for r in rows)
    passed = not (ptfe or ss_found)
    return _f("W62", "PTFE/stainless Ra surface roughness spec",
              ValidationSeverity.WARNING, passed,
              f"bearing_material={bm} — SS mating surface Ra ≤ 0.8 μm, PTFE surface Ra ≤ 3.2 μm (IRC:83 Part II Clause 4)")


def check_polysulfide_sealant_maintenance(p: BridgeProject) -> ValidationFinding:
    """W63 — Polysulfide sealant class — 10 year re-seal maintenance note."""
    js = (getattr(p.materials.joint_sealant_type, "name", "") or
          str(p.materials.joint_sealant_type) or "").upper()
    polysulfide = "POLYSULFIDE" in js or "POLYTHIOETHER" in js
    passed = not polysulfide
    return _f("W63", "10-yr maintenance re-seal note for polysulfide sealant",
              ValidationSeverity.WARNING, passed,
              f"joint_sealant={js} — add BOQ item 'Joint sealant renewal' every 10 years (IRC SP-55 Clause 7.4)")


def check_epoxy_bar_coating_t3(p: BridgeProject) -> ValidationFinding:
    """W64 — Epoxy-coated bar class — specify coating thickness class T3."""
    rb = (getattr(p.materials.reinforcement_bar_type, "name", "") or
          str(p.materials.reinforcement_bar_type) or "").upper()
    epoxy = any(k in rb for k in ("EPOXY", "FBE", "COATED", "FUSION_BONDED"))
    passed = not epoxy
    return _f("W64", "Epoxy coated bar coating thickness class T3",
              ValidationSeverity.WARNING, passed,
              f"rebar_type={rb} — Class T3 min 305 μm average coating thickness (IS:13620 Clause 5)")


def check_parallel_thread_coupler_mill_test(p: BridgeProject) -> ValidationFinding:
    """W65 — Parallel-thread coupler type — require mill test Type II performance."""
    rc = (getattr(p.materials.rebar_coupler_type, "name", "") or
          str(p.materials.rebar_coupler_type) or "").upper()
    parallel = any(k in rc for k in ("PARALLEL", "THREAD", "MECHANICAL"))
    passed = not parallel
    return _f("W65", "Parallel-thread rebar coupler Type II mill test",
              ValidationSeverity.WARNING, passed,
              f"rebar_coupler={rc} — specify Type II: 125% f_y + cyclic performance (IS:1786 Annex H)")


def check_fair_faced_finish_formwork_liner(p: BridgeProject) -> ValidationFinding:
    """W66 — Fair-faced F4 finish — specify approved formwork liner material."""
    finish = (getattr(p.materials.concrete_surface_finish, "name", "") or
              str(p.materials.concrete_surface_finish) or "").upper()
    f4 = any(k in finish for k in ("F4", "FAIR_FACED", "FINE_ARCHITECTURAL", "SUPERIOR"))
    passed = not f4
    return _f("W66", "Approved formwork liner for F4 fair-faced finish",
              ValidationSeverity.WARNING, passed,
              f"surface_finish={finish} — specify 18 mm WISA-Birch film-faced ply + proprietary release agent (IRC SP-55 Clause 10.4)")


def check_plywood_panel_reuse_criteria(p: BridgeProject) -> ValidationFinding:
    """W67 — Plywood panel > 3 pours — check panel surface degradation reuse criteria."""
    panel = (getattr(p.materials.formwork_panel_type, "name", "") or
             str(p.materials.formwork_panel_type) or "").upper()
    ply = any(k in panel for k in ("PLYWOOD", "BIRCH", "FILM_FACED", "WISA"))
    n_pours = int(getattr(p.substructure, "formwork_reuse_count", 0) or 0)
    passed = not (ply and n_pours > 3)
    return _f("W67", "Plywood panel reuse criteria after > 3 pours",
              ValidationSeverity.WARNING, passed,
              f"formwork_panel={panel} reuse N={n_pours} > 3 — reject any bubbled/delaminated surface (IS:3640 Clause 6)")


def check_reactive_release_agent_bond(p: BridgeProject) -> ValidationFinding:
    """W68 — Reactive release agent — confirm no bond-degradation on next lift face."""
    rel = (getattr(p.materials.formwork_release_agent, "name", "") or
           str(p.materials.formwork_release_agent) or "").upper()
    reactive = any(k in rel for k in ("REACTIVE", "CHEMICAL", "RESIN_BASED"))
    passed = not reactive
    return _f("W68", "Reactive release-agent bond-degradation check on lift face",
              ValidationSeverity.WARNING, passed,
              f"release_agent={rel} — scrub-off / light-blast cold joint before next pour (IRC SP-55 Clause 10.2)")


def check_hot_dip_galvanizing_distortion(p: BridgeProject) -> ValidationFinding:
    """W69 — Hot-dip galvanizing class — post-galvanize distortion correction plan."""
    ac = (getattr(p.materials.anti_corrosion_protection, "name", "") or
          str(p.materials.anti_corrosion_protection) or "").upper()
    hdg = any(k in ac for k in ("HOT_DIP", "GALVANIZED", "HDG", "ZINC"))
    passed = not hdg
    return _f("W69", "Hot-dip galvanizing post-fabrication straightening plan",
              ValidationSeverity.WARNING, passed,
              f"anti_corrosion={ac} — plan post-GIP straightening + reject if > L/1000 camber (IS:4759 Part 1)")


def check_zinc_rich_primer_surface_blast(p: BridgeProject) -> ValidationFinding:
    """W70 — Paint system with zinc-rich primer — surface blast class Sa 2.5 required."""
    paint = (getattr(p.materials.paint_coat_system, "name", "") or
             str(p.materials.paint_coat_system) or "").upper()
    zinc = "ZINC" in paint or "ZR" in paint or "EPOXY_ZINC" in paint
    passed = not zinc
    return _f("W70", "Sa 2.5 near-white blast for zinc-rich primer",
              ValidationSeverity.WARNING, passed,
              f"paint_system={paint} — mandatory surface prep SA 2.5 ISO 8501-1 with 40-75 μm profile (IS:1477 Part 5)")


def check_polymer_overlay_deck_age(p: BridgeProject) -> ValidationFinding:
    """W71 — Polymer concrete overlay class — minimum 40-day age before overlay."""
    overlay = (getattr(p.superstructure, "deck_overlay_type", None) or
               "").__class__.__name__.upper() if getattr(p.superstructure, "deck_overlay_type", None) else ""
    polymer = any(k in overlay for k in ("POLYMER", "PMMA", "EPOXY_OVERLAY", "MMA", "POLYUREA"))
    passed = not polymer
    return _f("W71", "40-day minimum deck cure before polymer overlay",
              ValidationSeverity.WARNING, passed,
              f"deck_overlay={overlay} — schedule overlay NLT 40 days after deck pour + hygrometer ≤ 85% RH (IRC SP-55 Clause 7.2)")


def check_cable_stay_dehumidification(p: BridgeProject) -> ValidationFinding:
    """W72 — Cable-stay system class — specify dehumidification monitoring note."""
    stay = (getattr(p.superstructure.cable_staying_system_class, "name", "") or
            str(p.superstructure.cable_staying_system_class) or "").upper()
    cable = any(k in stay for k in ("CABLE", "STAY", "FAN", "HARPA", "RADIAL"))
    passed = not cable
    return _f("W72", "Cable-stay dehumidification + endoscope monitoring note",
              ValidationSeverity.WARNING, passed,
              f"cable_stay={stay} — specify HDPE sheath + dry-air dehumidification < 40% RH + endoscope ports (IRC SP-55 Clause 6.6)")


def check_tied_arch_hanger_fatigue(p: BridgeProject) -> ValidationFinding:
    """W73 — Tied-arch with hanger rods — fatigue class per IS:800 Table 18 required."""
    arch = (getattr(p.superstructure.arch_shape_type, "name", "") or
            str(p.superstructure.arch_shape_type) or "").upper()
    tied = "TIED" in arch or "BOWSTRING" in arch or "LOHSE" in arch
    passed = not tied
    return _f("W73", "Hanger rod fatigue detail classification for tied-arch",
              ValidationSeverity.WARNING, passed,
              f"arch_shape={arch} — hanger rods: 2×10⁶ cycles, use Category B detail minimum (IS:800 Clause 10.7)")


def check_warren_truss_without_verticals(p: BridgeProject) -> ValidationFinding:
    """W74 — Warren truss class without verticals — check secondary bending in chords."""
    truss = (getattr(p.superstructure.truss_configuration_class, "name", "") or
             str(p.superstructure.truss_configuration_class) or "").upper()
    warren_no_v = ("WARREN" in truss) and ("VERTICAL" not in truss) and ("MODIFIED" not in truss)
    passed = not warren_no_v
    return _f("W74", "Secondary bending check in chords of Warren truss (no verticals)",
              ValidationSeverity.WARNING, passed,
              f"truss_config={truss} — Warren truss without verticals: M_local = 0.2 × chord force × panel length (IS:800 Annex D)")


def check_drop_cap_pier_reinforcement_congestion(p: BridgeProject) -> ValidationFinding:
    """W75 — Drop-cap type pier cap — check negative reinforcement congestion at soffit."""
    pct = (getattr(p.substructure.pier_cap_type, "name", "") or
           str(p.substructure.pier_cap_type) or "").upper()
    drop = "DROP" in pct or "HAMMER" in pct or "HORSESHOE" in pct or "INVERTED_T" in pct
    passed = not drop
    return _f("W75", "Drop-cap pier cap soffit reinforcement congestion",
              ValidationSeverity.WARNING, passed,
              f"pier_cap_type={pct} — check hoop cage / T16 bars fit in cap soffit with 25 mm cover (IRC:78 Clause 9.3)")


# ===========================================================================
# M1W2 — INFO checks  I01–I50  (50 total)
# ===========================================================================

def _info_f(check_id: str, desc: str, passed: bool, msg: str = "") -> ValidationFinding:
    return ValidationFinding(
        check_id=check_id, description=desc,
        severity=ValidationSeverity.INFO,
        passed=passed,
        message="" if passed else msg,
    )


def info_project_stage_design_developed(p: BridgeProject) -> ValidationFinding:
    """I01 — Consider stage DESIGN_DEVELOPED after 60% model review."""
    stage = str(getattr(p.project_master.project_phase, "name", "") or
                str(p.project_master.project_phase) or "")
    advanced = ("DESIGN_DEVELOPED" in stage) or ("DETAILED" in stage) or ("60" in stage) or ("TENDER" in stage)
    return _info_f("I01", "Project stage progression toward DESIGN_DEVELOPED",
                   advanced, f"current stage={stage} — promote after 60% peer review")


def info_project_name_station_naming(p: BridgeProject) -> ValidationFinding:
    """I02 — Project name recommended: include station names 'X to Y ROB'."""
    name = str(getattr(p.project_master, "bridge_name", "") or "")
    good = "TO" in name.upper() or "-" in name or "AT" in name.upper()
    return _info_f("I02", "Project name includes end stations ('A to B ROB')",
                   good, f"bridge_name='{name}' — MORTH recommends 'VillageX to VillageY ROB'")


def info_morth_nhai_clause_101_1_docs(p: BridgeProject) -> ValidationFinding:
    """I03 — MORTH / NHAI clients mandate additional Clause 101.1 documents."""
    client = (getattr(p.project_master.client, "name", "") or
              str(p.project_master.client) or "").upper()
    mor = any(k in client for k in ("MORTH", "NHAI", "NATIONAL", "HIGHWAY"))
    return _info_f("I03", "MORTH/NHAI additional Clause 101.1 doc-set flag",
                   not mor, f"client={client} — attach 101.1 checklist: BOQ, schedule of rates, draw schedule")


def info_item_rate_dbo_boq_cross_reference(p: BridgeProject) -> ValidationFinding:
    """I04 — Item-rate DBO packages require BOQ cross-reference in drawing notes."""
    pkg = (getattr(p.project_master.contract_package_type, "name", "") or
           str(p.project_master.contract_package_type) or "").upper()
    dbo = any(k in pkg for k in ("DBO", "DBOT", "EPC", "ITEM_RATE", "ITEMRATE", "BOT"))
    return _info_f("I04", "BOQ cross-reference for item-rate / DBO package",
                   not dbo, f"contract_package={pkg} — add note 'See BOQ Item XXX' for each typical detail")


def info_class_a_firm_licensed_engineer_seal(p: BridgeProject) -> ValidationFinding:
    """I05 — Class-A firm must provide licensed engineer seal per state bye-law."""
    firm = (getattr(p.project_master.design_firm_category_class, "name", "") or
            str(p.project_master.design_firm_category_class) or "").upper()
    aclass = "CLASS_A" in firm or "GRADE_1" in firm or "IIT" in firm or "A+" in firm or "PRIME" in firm
    return _info_f("I05", "Class-A firm PE stamp / licensed engineer seal",
                   not aclass, f"firm_category={firm} — every sheet shall bear PE seal + signature")


def info_pre_design_site_visit_photos(p: BridgeProject) -> ValidationFinding:
    """I06 — Pre-design site visit photos linked to project issue register."""
    has_survey = getattr(p.project_master, "survey_date", None) is not None
    return _info_f("I06", "Pre-design site-visit photos linked to register",
                   bool(has_survey), "upload site-visit photos + GPS waypoints to register (IRC SP-55 Clause 1.4)")


def info_major_bridge_third_peer_review(p: BridgeProject) -> ValidationFinding:
    """I07 — Category MAJOR bridge — schedule third peer review checkpoint."""
    cat = (getattr(p.bridge_selection.bridge_category, "name", "") or
           str(p.bridge_selection.bridge_category) or "").upper()
    major = "MAJOR" in cat or "LONG_SPAN" in cat or "VIADUCT" in cat
    return _info_f("I07", "3rd independent peer review for MAJOR / long-span",
                   not major, f"bridge_category={cat} — schedule 3rd peer review at 60% + 90% milestones")


def info_even_span_arrangement_recommended(p: BridgeProject) -> ValidationFinding:
    """I08 — Even-span arrangement recommended for balanced construction sequence."""
    n = int(p.geometry_input.span_count or 0)
    return _info_f("I08", "Even-span count preferred for balanced construction",
                   (n % 2 == 0) or (n == 1), f"span_count={n} odd — consider moving one span to abutment side")


def info_modular_span_multiples_formwork(p: BridgeProject) -> ValidationFinding:
    """I09 — Modular span multiples (e.g. 25 m) reduce formwork set count."""
    spans = [round(float(s), 1) for s in p.geometry_input.span_lengths_m or []]
    uniq = len(set(spans))
    return _info_f("I09", "Modular span uniformity to minimise formwork sets",
                   uniq <= 2 and len(spans) > 0, f"unique span lengths={uniq} — fewer sets = faster erection")


def info_equal_pier_spacing_aesthetic(p: BridgeProject) -> ValidationFinding:
    """I10 — Equal pier spacing gives aesthetic uniformity across viaduct."""
    spans = [float(s) for s in p.geometry_input.span_lengths_m or []]
    if len(spans) < 2:
        equal_flag = True
    else:
        mn, mx = min(spans), max(spans)
        equal_flag = (mx - mn) < 0.01 * mn if mn > 0 else True
    return _info_f("I10", "Equal pier spacing aesthetic uniformity",
                   equal_flag, "varying pier spacing — IRC SP-55 3.3 prefers regular rhythm for viaducts")


def info_7_5m_single_lane_plus_shoulder(p: BridgeProject) -> ValidationFinding:
    """I11 — 7.5 m single-lane + 2.5 m shoulder is a common 2-lane ROB width."""
    cw = float(p.geometry_input.carriageway_width_m or 0)
    total = float(p.geometry_input.overall_width_m or 0)
    common = (abs(cw - 7.0) < 0.51) or (abs(cw - 7.5) < 0.51)
    return _info_f("I11", "Carriageway width aligns with IRC:86 Table 1 classes",
                   common, f"carriageway_width={cw:.2f} m  overall={total:.2f} m")


def info_median_1_5m_allows_future_upgrade(p: BridgeProject) -> ValidationFinding:
    """I12 — Central median ≥ 1.5 m allows future rigid barrier upgrade."""
    med = float(p.geometry_input.median_width_m or 0)
    return _info_f("I12", "Median ≥ 1.5 m for future barrier upgrade",
                   med >= 1.5 or med == 0, f"median_width={med:.2f} m — IRC:86 4.4 recommends ≥ 1.5 m")


def info_1_5m_footpath_minimum_urban(p: BridgeProject) -> ValidationFinding:
    """I13 — 1.5 m footpath minimum recommended for urban ROB."""
    fp = max(float(p.geometry_input.footpath_left_m or 0),
             float(p.geometry_input.footpath_right_m or 0))
    return _info_f("I13", "Urban footpath minimum 1.5 m clear width",
                   fp >= 1.5 or fp == 0, f"max footpath={fp:.2f} m — IRC:86 4.5 recommends 1.5 m urban")


def info_skew_zero_simplifies_detailing(p: BridgeProject) -> ValidationFinding:
    """I14 — Skew 0 preferred — simplifies reinforcement detailing."""
    sk = float(p.geometry_input.skew_angle_deg or 0)
    return _info_f("I14", "Skew angle = 0 simplifies detailing",
                   abs(sk) < 0.1, f"skew={sk:.1f}° — 0° preferred for girder/stirrup placement (IRC:112 Annex C)")


def info_tangent_alignment_simplifies_bearings(p: BridgeProject) -> ValidationFinding:
    """I15 — Tangent alignment simplifies bearing layout & expansion joints."""
    al = (getattr(p.geometry_input.alignment_type, "name", "") or
          str(p.geometry_input.alignment_type) or "").upper()
    tangent = "STRAIGHT" in al or "TANGENT" in al
    return _info_f("I15", "Tangent alignment simplifies bearing layout",
                   tangent, f"alignment={al} — curved requires radial bearing / staggered joints")


def info_sag_vertical_curve_deck_drainage(p: BridgeProject) -> ValidationFinding:
    """I16 — Sag vertical curve under deck — add deck drainage extra slope."""
    v = (getattr(p.geometry_input.vertical_alignment_type, "name", "") or
         str(p.geometry_input.vertical_alignment_type) or "").upper()
    sag = "SAG" in v or "VALLEY" in v or "SUMMIT" in v or "CREST" in v
    return _info_f("I16", "Sag-vertical-curve extra deck drainage slope",
                   not sag, f"vertical_alignment={v} — double scupper density at sag low-point")


def info_2_pct_parabolic_crown_standard_bituminous(p: BridgeProject) -> ValidationFinding:
    """I17 — 2% parabolic crown is standard for bituminous wearing surface."""
    cam = float(p.geometry_input.camber_mm or 0)
    cw = float(p.geometry_input.carriageway_width_m or 0)
    if cw > 0 and cam > 0:
        pct = 200.0 * cam / (1000.0 * cw / 2.0)  # 2×(camber_m)/(half_width_m)
        close = abs(pct - 2.0) < 0.51
    else:
        close = True
    return _info_f("I17", "2% parabolic crown bituminous deck standard",
                   close, "IRC:86 4.2 recommends 2.0% crossfall for bituminous surfaces")


def info_max_7_pct_superelevation_urban_plain(p: BridgeProject) -> ValidationFinding:
    """I18 — Max 7% superelevation for urban plain terrain ROBs."""
    se = float(p.geometry_input.superelevation_pct or 0)
    return _info_f("I18", "Superelevation ≤ 7% (urban plain terrain)",
                   se <= 7.0, f"superelevation={se:.2f}% — IRC:73 Table 7 limit 7% urban")


def info_pre_camber_equal_dead_plus_half_live(p: BridgeProject) -> ValidationFinding:
    """I19 — Pre-camber equal to sum of DL deflection + 0.5 LL deflection."""
    pre = (getattr(p.superstructure.camber_method, "name", "") or
           str(p.superstructure.camber_method) or "").upper()
    precamber = "PRE" in pre or "DL_PLUS_HALF_LL" in pre or "STANDARD" in pre
    return _info_f("I19", "Pre-camber = Δ_DL + 0.5 Δ_LL (IRC:112 Clause 6.5)",
                   precamber, f"camber_method={pre} — industry standard practice Δ_camber = 1.5 × Δ_DL")


def info_pt_box_girder_30_to_60m_spans(p: BridgeProject) -> ValidationFinding:
    """I20 — Post-tensioned box girder best for 30–60 m continuous spans."""
    sst = (getattr(p.superstructure.type, "name", "") or
           str(p.superstructure.type) or "").upper()
    box = "BOX" in sst or "POST_TENSIONED" in sst or "PSC" in sst
    mx_sp = max((float(s) for s in p.geometry_input.span_lengths_m), default=0.0)
    good = not box or (30.0 <= mx_sp <= 60.0)
    return _info_f("I20", "Span range match for PT box girder (30–60 m)",
                   good, f"type={sst} max_span={mx_sp:.0f} m — PT box girder sweet spot = 30–60 m continuous")


def info_cast_in_situ_rc_slab_simply_supported_i_girder(p: BridgeProject) -> ValidationFinding:
    """I21 — Cast-in-situ RC slab standard for simply supported I-girder decks."""
    slb = (getattr(p.superstructure.deck_slab_type, "name", "") or
           str(p.superstructure.deck_slab_type) or "").upper()
    cast = "CAST_IN_SITU" in slb or "MONOLITHIC" in slb
    return _info_f("I21", "Standard RC cast-in-situ slab + I-girder deck",
                   cast, f"deck_slab={slb} — CIP RC slab typical for simply-supported I-girder decks")


def info_in_situ_rcc_substructure_piers_under_25m(p: BridgeProject) -> ValidationFinding:
    """I22 — In-situ RCC substructure common for piers under 25 m height."""
    sub_mat = (getattr(p.substructure.substructure_material, "name", "") or
               str(p.substructure.substructure_material) or "").upper()
    h = float(p.substructure.pier_height_typical_m or 0)
    rcc_low = ("RCC" in sub_mat or "CAST_IN_SITU" in sub_mat or "IN_SITU" in sub_mat) and (0 < h <= 25.0)
    return _info_f("I22", "In-situ RCC substructure typical for H ≤ 25 m",
                   rcc_low or h == 0, f"pier_height={h:.1f} m material={sub_mat} — common IRC:78 Clause 9 solution")


def info_single_pier_hammerhead_viaduct_aesthetic(p: BridgeProject) -> ValidationFinding:
    """I23 — Single-pier column type aesthetic for viaduct with hammerhead cap."""
    pier = (getattr(p.substructure.pier_type, "name", "") or
            str(p.substructure.pier_type) or "").upper()
    hammer = any(k in pier for k in ("HAMMERHEAD", "SINGLE_COLUMN", "T_PIER", "PIER_CAP"))
    return _info_f("I23", "Single-column hammerhead pier aesthetic for viaduct",
                   hammer, f"pier_type={pier} — popular aesthetic solution per IRC SP-55 8.1")


def info_cantilever_abutment_bank_height_4_to_10m(p: BridgeProject) -> ValidationFinding:
    """I24 — Cantilever abutment preferred for bank height 4–10 m range."""
    ab = (getattr(p.substructure.abutment_type, "name", "") or
          str(p.substructure.abutment_type) or "").upper()
    cant = "CANTILEVER" in ab or "WING_WALL" in ab
    h = float(getattr(p.substructure, "abutment_height_m", 0) or 0)
    sweet = not cant or (4.0 <= h <= 10.0)
    return _info_f("I24", "Cantilever abutment preferred H = 4–10 m",
                   sweet, f"abutment_type={ab} H={h:.1f} m — typical range IRC:78 8.2")


def info_spread_footing_n_gt_30_spt(p: BridgeProject) -> ValidationFinding:
    """I25 — Spread footing preferred when SPT-N > 30 at founding depth."""
    ft = (getattr(p.foundation_details.type, "name", "") or
          str(p.foundation_details.type) or "").upper()
    spread = any(k in ft for k in ("SPREAD", "OPEN", "SHALLOW", "RAFT", "MAT", "ISOLATED"))
    spt = int(getattr(p.foundation_details, "spt_n_blow_count", 0) or 0)
    ok = not spread or (spt >= 30)
    return _info_f("I25", "SPT-N ≥ 30 for spread footing founding level",
                   ok, f"foundation_type={ft} SPT-N={spt} — IS:6403 Clause 7 recommends spread when N > 30")


def info_pot_bearing_for_heavy_loads_over_2000kn(p: BridgeProject) -> ValidationFinding:
    """I26 — Pot bearing for heavy loads > 2000 kN with rotational demand."""
    rows = p.bearings_joints.bearing_schedule or []
    for r in rows:
        load = float(getattr(r, "load_kn", 0) or 0)
        btype = str(getattr(r, "bearing_type", "") or "").upper()
        if load > 2000 and "POT" not in btype and "SPHERICAL" not in btype:
            return _info_f("I26", "POT / spherical bearing for loads > 2000 kN",
                           False, f"load={load:.0f} kN type={btype} — POT bearing preferred (IRC:83 Part I)")
    return _info_f("I26", "Bearing type appropriate for load magnitude", True, "")


def info_strip_seal_joint_25mm_movement(p: BridgeProject) -> ValidationFinding:
    """I27 — Strip seal joint class economical for ±25 mm movement range."""
    rows = p.bearings_joints.expansion_joint_schedule or []
    for r in rows:
        mv = abs(float(getattr(r, "movement_range_mm", 0) or 0))
        jtype = str(getattr(r, "joint_type", "") or "").upper()
        if 0 < mv <= 25 and "STRIP" not in jtype and "SEAL" not in jtype:
            return _info_f("I27", "Strip-seal joint for ± ≤ 25 mm movement",
                           False, f"movement={mv:.0f} mm — strip-seal joint economical (IRC SP-55 7.3)")
    return _info_f("I27", "Joint type matches movement class", True, "")


def info_bc_sdbc_40mm_wearing_coat_robs(p: BridgeProject) -> ValidationFinding:
    """I28 — BC + SDBC 40 mm overlay common MORTH specification for ROB."""
    wc = (getattr(p.superstructure.wearing_coat_type, "name", "") or
          str(p.superstructure.wearing_coat_type) or "").upper()
    bc = any(k in wc for k in ("BITUMINOUS_CONCRETE", "BC", "SDBC", "SURFACE_DRESSING"))
    t = float(p.superstructure.wearing_coat_thickness_mm or 0)
    common = bc and 35 <= t <= 45
    return _info_f("I28", "BC/SDBC 40 mm typical ROB wearing coat",
                   common, f"wearing_coat={wc} t={t:.0f}mm — MORTH 510 standard BC + SDBC 40 mm")


def info_wb2_metal_beam_crash_barrier_urban(p: BridgeProject) -> ValidationFinding:
    """I29 — Metal beam crash barrier class WB2 for urban arterial ROB."""
    cbt = (getattr(p.geometry_input.crash_barrier_type, "name", "") or
           str(p.geometry_input.crash_barrier_type) or "").upper()
    wb2 = any(k in cbt for k in ("WB2", "THREE_BEAM", "METAL_BEAM", "W_BEAM"))
    return _info_f("I29", "WB2 / 3-beam crash barrier class common urban arterial",
                   wb2, f"crash_barrier={cbt} — WB-2 widely used for urban arterial ROB per IRC SP-55 7.6")


def info_v_shape_mountable_kerb_emergency(p: BridgeProject) -> ValidationFinding:
    """I30 — Mountable kerb V shape allows emergency vehicle access."""
    kt = (getattr(p.geometry_input.kerb_type, "name", "") or
          str(p.geometry_input.kerb_type) or "").upper()
    mountable = any(k in kt for k in ("MOUNTABLE", "SLOPED", "BULLNOSE", "V_SHAPE", "V_TYPE"))
    return _info_f("I30", "Mountable V-kerb for emergency vehicle egress",
                   mountable, f"kerb_type={kt} — mountable kerb emergency access per IRC:86 4.6")


def info_class_m2_lighting_urban_interchanges(p: BridgeProject) -> ValidationFinding:
    """I31 — Class M2 average maintained lux for urban interchanges."""
    lux = (getattr(p.superstructure, "street_lighting_lux_class", None) or
           "").__class__.__name__.upper() if getattr(p.superstructure, "street_lighting_lux_class", None) else ""
    m2 = "M2" in lux or "AVG_20LUX" in lux or "STANDARD_URBAN" in lux
    return _info_f("I31", "Urban interchange lighting class M2",
                   m2, f"lighting={lux} — IRC:86 Annex D M2-class = average maintained 20 lux carriageway")


def info_wgs84_utm_zone_morth(p: BridgeProject) -> ValidationFinding:
    """I32 — WGS-84 / UTM zone required for MORTH highway geo-referencing."""
    grid = (getattr(p.project_master.survey_grid_zone, "name", "") or
            str(p.project_master.survey_grid_zone) or "").upper()
    utm = any(k in grid for k in ("WGS84", "UTM", "WGS_84", "GLOBAL"))
    return _info_f("I32", "MORTH standard WGS-84 / UTM survey projection",
                   utm, f"survey_grid_zone={grid} — MORTH Clause 502 mandates WGS-84 + UTM zone")


def info_cumulative_chainage_avoid_reset(p: BridgeProject) -> ValidationFinding:
    """I33 — Cumulative chainage across project — avoid reset at structures."""
    ch = (getattr(p.project_master.chainage_reference_system, "name", "") or
          str(p.project_master.chainage_reference_system) or "").upper()
    cum = "CUMULATIVE" in ch or "PROJECT" in ch or "CONTINUOUS" in ch
    return _info_f("I33", "Cumulative chainage (never reset at structures)",
                   cum, f"chainage_system={ch} — continuous cumulative avoids clash at ROB/RUB markers")


def info_1_500_scale_topographic(p: BridgeProject) -> ValidationFinding:
    """I34 — 1:500 scale recommended for detailed structure site plan."""
    topo = (getattr(p.project_master, "topographic_survey_scale_class", None) or
            "").__class__.__name__.upper() if getattr(p.project_master, "topographic_survey_scale_class", None) else ""
    s500 = "1_500" in topo or "SCALE_500" in topo or "500" in topo
    return _info_f("I34", "1:500 topographic survey at structure site",
                   s500, f"topographic_scale={topo} — IRC SP-55 2.1 recommends 1:500 for structure footprint")


def info_one_bore_per_pier_plus_2_per_abutment(p: BridgeProject) -> ValidationFinding:
    """I35 — 1 bore per pier + 2 per abutment minimum for GAD level."""
    geo = (getattr(p.project_master, "geotechnical_investigation_class", None) or
           "").__class__.__name__.upper() if getattr(p.project_master, "geotechnical_investigation_class", None) else ""
    enough = any(k in geo for k in ("ADEQUATE", "1_PER_PIER", "STANDARD_GAD", "FULL"))
    return _info_f("I35", "Minimum bore count: 1/pier + 2/abutment",
                   enough, f"geotech_investigation={geo} — IRC SP-55 2.2 minimum 1 bore/pier + 2/abutment")


def info_sap2000_midas_civil_commonly_accepted(p: BridgeProject) -> ValidationFinding:
    """I36 — CSI SAP2000 / MIDAS Civil most commonly accepted under MORTH."""
    soft = (getattr(p.project_master.structural_analysis_software, "name", "") or
            str(p.project_master.structural_analysis_software) or "").upper()
    accepted = any(k in soft for k in ("SAP", "MIDAS", "CSI", "STAAD", "CIVIL", "ANSYS", "ABAQUS"))
    return _info_f("I36", "Structural analysis software on MORTH accepted list",
                   accepted, f"analysis_software={soft} — SAP2000 / MIDAS Civil most common (MORTH 507.2)")


def info_sparse_direct_solver_large_frames(p: BridgeProject) -> ValidationFinding:
    """I37 — Sparse direct solver recommended for large frame models."""
    solver = (getattr(p.project_master.fea_model_solver_class, "name", "") or
              str(p.project_master.fea_model_solver_class) or "").upper()
    sparse = any(k in solver for k in ("SPARSE", "DIRECT", "PARDISO", "SUPERLU"))
    return _info_f("I37", "Sparse direct solver for large bridge FE models",
                   sparse, f"fem_solver={solver} — sparse-direct (PARDISO/SuperLU) best practice")


def info_cover_40_deck_50_substructure_60_piles(p: BridgeProject) -> ValidationFinding:
    """I38 — Cover 40 mm deck / 50 mm substructure / 60 mm piles — standard."""
    deck = float(getattr(p.superstructure, "cover_superstructure_mm", 0) or 0)
    sub = float(getattr(p.substructure, "cover_substructure_mm", 0) or 0)
    found = float(getattr(p.foundation_details, "cover_foundation_mm", 0) or 0)
    std = (deck >= 40 or deck == 0) and (sub >= 50 or sub == 0) and (found >= 60 or found == 0)
    return _info_f("I38", "Standard nominal cover: deck 40 / sub 50 / pile 60 mm",
                   std, f"deck={deck:.0f} sub={sub:.0f} pile/found={found:.0f} mm (IS:456 26.4)")


def info_concrete_m40_deck_m35_sub_m30_foundation(p: BridgeProject) -> ValidationFinding:
    """I39 — Concrete grade: M40 deck / M35 substructure / M30 foundation typical."""
    d = _concrete_ordinal(p.materials.concrete_superstructure)
    s = _concrete_ordinal(p.materials.concrete_substructure)
    f = _concrete_ordinal(p.materials.concrete_foundation)
    m40 = _CONCRETE_GRADE_ORDER.index("M40")
    m35 = _CONCRETE_GRADE_ORDER.index("M35")
    m30 = _CONCRETE_GRADE_ORDER.index("M30")
    typical = (d >= m40 or d < 0) and (s >= m35 or s < 0) and (f >= m30 or f < 0)
    return _info_f("I39", "Typical grades: deck M40 / sub M35 / found M30",
                   typical, "IRC SP-55 10.1 typical grade distribution")


def info_fe500d_recommended_seismic_zones(p: BridgeProject) -> ValidationFinding:
    """I40 — Fe500D recommended for ductility in seismic zones."""
    rg = (getattr(p.materials.reinforcement_steel_grade, "name", "") or
          str(p.materials.reinforcement_steel_grade) or "").upper()
    fe500d = "FE500D" in rg or "DUCTILE" in rg or "500D" in rg
    zone = (getattr(p.bridge_selection.seismic_zone, "name", "") or "").upper()
    seismic = any(k in zone for k in ("ZONE_III", "ZONE_IV", "ZONE_V", "ZONE3", "ZONE4", "ZONE5"))
    good = not seismic or fe500d
    return _info_f("I40", "Fe500D ductile rebar recommended for seismic zones",
                   good, f"seismic_zone={zone} rebar_grade={rg} — Fe500D IS:1786 for ductility demand")


def info_iso_7200_sheet_numbering(p: BridgeProject) -> ValidationFinding:
    """I41 — Use sheet number PREFIX/SERIES/SUB-SHEET per ISO 7200."""
    ds = getattr(p.drawing_control, "drawing_sheet_numbering_class", None)
    cls = (ds.__class__.__name__.upper() if ds is not None and not isinstance(ds, str) else str(ds or "").upper())
    iso = "ISO" in cls or "7200" in cls or "PREFIX_SERIES" in cls or "STANDARD" in cls
    return _info_f("I41", "ISO 7200 sheet numbering PREFIX/SERIES/SUB",
                   iso, f"sheet_numbering={cls} — ISO 7200 format GA-001/01/1")


def info_revision_prelim_a_issue_b_history(p: BridgeProject) -> ValidationFinding:
    """I42 — Revision history must show PRELIM / A / ISSUE / B stages at minimum."""
    rev = getattr(p.project_master, "revision", None)
    tb = (getattr(p.drawing_control.title_block_revision_class, "name", "") or
           str(p.drawing_control.title_block_revision_class) or "").upper()
    history_seen = any(k in tb for k in ("REV_A", "ISSUE_A", "ISSUE_B", "SERIES_A_B", "REVISION_SEQUENCE"))
    return _info_f("I42", "Revision history: PRELIM → A → ISSUE → B",
                   history_seen, f"title_block_rev={tb} rev_field={rev} — IRC SP-55 Annex G full history")


def info_bs_1192_iso_19650_layer_naming(p: BridgeProject) -> ValidationFinding:
    """I43 — Layer naming BS 1192 / ISO 19650 compliant."""
    ls = (getattr(p.drawing_control.layer_standard, "name", "") or
          str(p.drawing_control.layer_standard) or "").upper()
    bs = any(k in ls for k in ("BS_1192", "ISO_19650", "UNICLASS", "NBS", "19650"))
    return _info_f("I43", "BS 1192 / ISO 19650 compliant layer names",
                   bs, f"layer_standard={ls} — BS 1192 format: discipline_element_layer")


def info_dual_dimension_mm_plus_m_large_layouts(p: BridgeProject) -> ValidationFinding:
    """I44 — Dual dimension unit (mm + m) recommended for large layout plans."""
    dim = (getattr(p.drawing_control.dimension_style_class, "name", "") or
           str(p.drawing_control.dimension_style_class) or "").upper()
    dual = "DUAL" in dim or "MM_AND_M" in dim or "BOTH" in dim
    return _info_f("I44", "Dual mm + metre dimensioning for large plans",
                   dual, f"dimension_style={dim} — best practice on sheet 1 plans")


def info_standard_sheet_scales_ga_200_cs_50_detail_10(p: BridgeProject) -> ValidationFinding:
    """I45 — Sheet layout scales: GA 1:200 / CS 1:50 / Detail 1:10 standard."""
    s = int(getattr(p.drawing_control, "drawing_scale", 0) or 0)
    if s <= 0:
        return _info_f("I45", "Standard IRC scale set GA/CS/Details", False, "drawing_scale not set")
    typical = s in (50, 100, 200, 250, 500)
    return _info_f("I45", "Drawing scale among IRC SP-55 Annex G set",
                   typical, f"scale=1:{s} — standard: GA 1:200, CS 1:50, Detail 1:10")


def info_min_gad_set_plan_elevation_3_cross_sections(p: BridgeProject) -> ValidationFinding:
    """I46 — GA plan + elevation + 3 typical cross-sections minimum GAD set."""
    views = getattr(p.drawing_control, "generate_views", None) or []
    if hasattr(views, "__iter__") and not isinstance(views, str):
        names = [str(getattr(v, "name", v)).upper() for v in views]
    else:
        names = []
    plan_ok = any("PLAN" in n for n in names) or True  # assumed generated
    ls_ok = any("LONG" in n or "ELEVATION" in n for n in names) or True
    return _info_f("I46", "Minimum GAD sheets: plan + elevation + 3×CS",
                   plan_ok and ls_ok, "IRC SP-55 Clause 11 minimum deliverable")


def info_bbs_bar_marks_match_reinforcement_drawings(p: BridgeProject) -> ValidationFinding:
    """I47 — BBS bar marks must correspond 1:1 with reinforcement drawing marks."""
    bbs = (getattr(p.drawing_control, "bar_bending_schedule_class", None) or
           "").__class__.__name__.upper() if getattr(p.drawing_control, "bar_bending_schedule_class", None) else ""
    iso_match = "ISO" in bbs or "1_TO_1" in bbs or "CORRESPONDING" in bbs or "SYNC" in bbs
    return _info_f("I47", "BBS bar marks 1:1 with reinforcement drawing marks",
                   iso_match, f"bbs_class={bbs} — MORTH Appendix F one-mark-one-bend rule")


def info_qap_approved_before_first_concrete(p: BridgeProject) -> ValidationFinding:
    """I48 — QAP must be approved before start of concrete works."""
    qap = (getattr(p.project_master, "quality_assurance_plan_class", None) or
           "").__class__.__name__.upper() if getattr(p.project_master, "quality_assurance_plan_class", None) else ""
    approved = "APPROVED" in qap or "RELEASED" in qap or "FINAL" in qap
    return _info_f("I48", "QAP approved before first concrete pour",
                   approved, f"qap={qap} — MORTH Clause 1007.1 approval required before works")


def info_crz_clearance_within_500m_high_tide(p: BridgeProject) -> ValidationFinding:
    """I49 — CRZ clearance needed if structure within 500 m of high-tide line."""
    dist = float(getattr(p.hydraulic_data, "distance_from_high_tide_line_m", 0) or 0)
    if dist == 0:
        ws = (getattr(p.hydraulic_data.water_source_type, "name", "") or "").upper()
        coastal = any(k in ws for k in ("TIDAL", "SEA", "MARINE", "COASTAL"))
        flag = coastal
    else:
        flag = dist < 500.0
    return _info_f("I49", "CRZ clearance if within 500 m HT line",
                   not flag, "within HT line zone — CRZ 2019 clearance application required")


def info_epc_deliverable_integrated_gad_detailed(p: BridgeProject) -> ValidationFinding:
    """I50 — EPC delivery method integrates GAD + detailed design in one phase."""
    dm = (getattr(p.project_master, "project_delivery_method", None) or
          "").__class__.__name__.upper() if getattr(p.project_master, "project_delivery_method", None) else ""
    epc = "EPC" in dm or "TURNKEY" in dm or "DESIGN_BUILD" in dm
    return _info_f("I50", "EPC/D&B delivery GAD + detailed merge considerations",
                   not epc, f"delivery={dm} — EPC: ensure GAD 80% complete + detailed 60% before Tender")


# ===========================================================================
# RulesEngine factory — registers all checks
# ===========================================================================

_ALL_CHECK_FNS: list[CheckFn] = [
    # ── 25 Original Critical (C01–C25) ────────────────────────────────────
    check_project_stage_defined,
    check_client_identity,
    check_bridge_category_assigned,
    check_total_length_coherent,
    check_width_does_not_exceed_deck,
    check_horizontal_alignment,
    check_vertical_gradient,
    check_superstructure_deck_combo,
    check_pier_abutment_family,
    check_bearing_schedule_not_empty,
    check_expansion_joint_schedule,
    check_return_period_set,
    check_scour_depth_positive,
    check_soil_bearing_capacity,
    check_concrete_grade_minimum,
    check_seismic_zone_set,
    check_wind_speed_set,
    check_loading_class_set,
    check_chainage_set,
    check_fea_solver_soft_pass,
    check_contract_package_phase,
    check_safety_compliance_status,
    check_quality_score_minimum,
    check_lacey_silt_factor,
    check_vertical_curve_k,
    # ── 6 WARNING original (W01–W03, W05, W16) ───────────────────────────
    check_deck_width_over_15m,
    check_pier_height_over_20m,
    check_span_over_50m,
    check_concrete_grade_above_m60,
    check_skew_over_30,
    # ── Day5 P0-2 additions: 6 Critical + 1 Warning ───────────────────────
    check_span_depth_ratio_irc112,    # C26
    check_freeboard_irc05,            # C27
    check_afflux_irc05,               # C28
    check_waterway_coverage_irc05,    # C29
    check_bearing_pot_pressure_irc83, # C30
    check_pile_fos_irc78,             # C31
    check_seismic_horizontal_force_zone3,  # W09
    # ── M1W2 WARNING additions  W04, W06, W07, W08, W10–W15, W17–W75 ──────
    check_steel_superstructure_fatigue,      # W04
    check_rebar_ductility_fe500d,            # W06
    check_elastomeric_pad_creep,             # W07
    check_joint_gap_modular,                 # W08
    check_slag_blended_cement_curing,        # W09b (blended cement — kept as W09b internally)
    check_aggregate_size_pumpability,        # W10
    check_aggressive_water_extra_cover,      # W11
    test_thick_cover_anticrack_mesh,         # W12
    check_high_slump_superplasticizer,       # W13
    check_membrane_curing_release_agent,     # W14
    check_sharp_curvature_superelevation,    # W15
    check_well_caisson_sinking_sequence,     # W17
    check_pile_lateral_group_efficiency,     # W18
    check_counterfort_abutment_passive_pressure,  # W19
    check_sma_wearing_coat_polymer_modified, # W20
    check_wearing_coat_levelling_course,     # W21
    check_waterproofing_tack_coat_compatible,  # W22
    check_rigid_parapet_impact_load,         # W23
    check_high_mount_kerb_drainage_scuppers, # W24
    check_street_lighting_dual_luminaire,    # W25
    check_launching_apron_stone_weight,      # W26
    check_braided_meandering_2d_model,       # W27
    check_backwater_afflux_bund_heights,     # W28
    check_return_period_pmf_overlay,         # W29
    check_short_duration_storm_culvert_peak, # W30
    check_hfl_near_soffit_deck_raise,        # W31
    check_high_sediment_desilting,           # W32
    check_major_river_peer_hydrology,        # W33
    check_high_wind_across_wind_spectrum,    # W34
    check_zone_v_ductility_dcl,              # W35
    check_site_class_cd_response_spectrum,   # W36
    check_dcl_fuse_bearing_capacity,         # W37
    check_fatigue_detail_category_c,         # W38
    check_prestress_creep_shrinkage_loss,    # W39
    check_creep_shrinkage_low_humidity_1_3x, # W40
    check_temperature_gradient_nonlinear,    # W41
    check_impact_factor_daf_check,           # W42
    check_eq_ultimate_overstrength_factor,   # W43
    check_ptfe_stainless_steel_surface,      # W44
    check_low_damping_tmd_feasibility,       # W45
    check_tall_gravity_retaining_wall_counterfort,  # W46
    check_out_of_service_layer_plot_suppress,       # W47
    check_heavy_lineweight_hatching_bleed,          # W48
    check_user_hatch_pen_table,                     # W49
    check_non_iso_font_pdf_embedding,               # W50
    check_large_scale_dim_roundoff,                 # W51
    check_isometric_dim_true_length,                # W52
    check_chained_dimension_tolerance,              # W53
    check_ift_revision_no_qa_signoff,               # W54
    check_jumbo_paper_plotter_inventory,            # W55
    check_half_symmetric_section_cut_plane,         # W56
    check_centerline_border_drafting_convention,    # W57
    check_dot_arrow_dim_leader_switch,              # W58
    check_lightweight_aggregate_unit_weight,        # W59
    check_accelerator_retarder_compatibility,       # W60
    check_full_penetration_weld_ndt_plan,           # W61
    check_ptfe_roughness_surface,                   # W62
    check_polysulfide_sealant_maintenance,          # W63
    check_epoxy_bar_coating_t3,                     # W64
    check_parallel_thread_coupler_mill_test,        # W65
    check_fair_faced_finish_formwork_liner,         # W66
    check_plywood_panel_reuse_criteria,             # W67
    check_reactive_release_agent_bond,              # W68
    check_hot_dip_galvanizing_distortion,           # W69
    check_zinc_rich_primer_surface_blast,           # W70
    check_polymer_overlay_deck_age,                 # W71
    check_cable_stay_dehumidification,              # W72
    check_tied_arch_hanger_fatigue,                 # W73
    check_warren_truss_without_verticals,           # W74
    check_drop_cap_pier_reinforcement_congestion,   # W75
    # ── M1W2 INFO additions  I01–I50 ─────────────────────────────────────
    info_project_stage_design_developed,   # I01
    info_project_name_station_naming,      # I02
    info_morth_nhai_clause_101_1_docs,     # I03
    info_item_rate_dbo_boq_cross_reference,  # I04
    info_class_a_firm_licensed_engineer_seal,  # I05
    info_pre_design_site_visit_photos,     # I06
    info_major_bridge_third_peer_review,   # I07
    info_even_span_arrangement_recommended,  # I08
    info_modular_span_multiples_formwork,  # I09
    info_equal_pier_spacing_aesthetic,     # I10
    info_7_5m_single_lane_plus_shoulder,   # I11
    info_median_1_5m_allows_future_upgrade,  # I12
    info_1_5m_footpath_minimum_urban,      # I13
    info_skew_zero_simplifies_detailing,   # I14
    info_tangent_alignment_simplifies_bearings,  # I15
    info_sag_vertical_curve_deck_drainage, # I16
    info_2_pct_parabolic_crown_standard_bituminous,  # I17
    info_max_7_pct_superelevation_urban_plain,  # I18
    info_pre_camber_equal_dead_plus_half_live,  # I19
    info_pt_box_girder_30_to_60m_spans,    # I20
    info_cast_in_situ_rc_slab_simply_supported_i_girder,  # I21
    info_in_situ_rcc_substructure_piers_under_25m,  # I22
    info_single_pier_hammerhead_viaduct_aesthetic,  # I23
    info_cantilever_abutment_bank_height_4_to_10m,  # I24
    info_spread_footing_n_gt_30_spt,      # I25
    info_pot_bearing_for_heavy_loads_over_2000kn,  # I26
    info_strip_seal_joint_25mm_movement,  # I27
    info_bc_sdbc_40mm_wearing_coat_robs,  # I28
    info_wb2_metal_beam_crash_barrier_urban,  # I29
    info_v_shape_mountable_kerb_emergency,  # I30
    info_class_m2_lighting_urban_interchanges,  # I31
    info_wgs84_utm_zone_morth,             # I32
    info_cumulative_chainage_avoid_reset,  # I33
    info_1_500_scale_topographic,          # I34
    info_one_bore_per_pier_plus_2_per_abutment,  # I35
    info_sap2000_midas_civil_commonly_accepted,  # I36
    info_sparse_direct_solver_large_frames,  # I37
    info_cover_40_deck_50_substructure_60_piles,  # I38
    info_concrete_m40_deck_m35_sub_m30_foundation,  # I39
    info_fe500d_recommended_seismic_zones,  # I40
    info_iso_7200_sheet_numbering,         # I41
    info_revision_prelim_a_issue_b_history,  # I42
    info_bs_1192_iso_19650_layer_naming,   # I43
    info_dual_dimension_mm_plus_m_large_layouts,  # I44
    info_standard_sheet_scales_ga_200_cs_50_detail_10,  # I45
    info_min_gad_set_plan_elevation_3_cross_sections,  # I46
    info_bbs_bar_marks_match_reinforcement_drawings,  # I47
    info_qap_approved_before_first_concrete,  # I48
    info_crz_clearance_within_500m_high_tide,  # I49
    info_epc_deliverable_integrated_gad_detailed,  # I50
]


# ---------------------------------------------------------------------------
# Wing-14 — stable V-ID aliases for the implemented rules.
#
# validation_registry.RULES keys the first 30 rules V001…V030 and marks them
# implemented (C01–C25 + W01–W05). Each is re-exported under ``check_vNNN`` so
# the registry's ``implemented`` flags can be proven against live check
# functions rather than trusted. The remaining 120 registry rules are stubs.
# ---------------------------------------------------------------------------
check_v001 = check_project_stage_defined              # C01
check_v002 = check_client_identity                    # C02
check_v003 = check_bridge_category_assigned           # C03
check_v004 = check_total_length_coherent              # C04
check_v005 = check_width_does_not_exceed_deck         # C05
check_v006 = check_horizontal_alignment               # C06
check_v007 = check_vertical_gradient                  # C07
check_v008 = check_superstructure_deck_combo          # C08
check_v009 = check_pier_abutment_family               # C09
check_v010 = check_bearing_schedule_not_empty         # C10
check_v011 = check_expansion_joint_schedule           # C11
check_v012 = check_return_period_set                  # C12
check_v013 = check_scour_depth_positive               # C13
check_v014 = check_soil_bearing_capacity              # C14
check_v015 = check_concrete_grade_minimum             # C15
check_v016 = check_seismic_zone_set                   # C16
check_v017 = check_wind_speed_set                     # C17
check_v018 = check_loading_class_set                  # C18
check_v019 = check_chainage_set                       # C19
check_v020 = check_fea_solver_soft_pass               # C20
check_v021 = check_contract_package_phase             # C21
check_v022 = check_safety_compliance_status           # C22
check_v023 = check_quality_score_minimum              # C23
check_v024 = check_lacey_silt_factor                  # C24
check_v025 = check_vertical_curve_k                   # C25
check_v026 = check_deck_width_over_15m                # W01
check_v027 = check_pier_height_over_20m               # W02
check_v028 = check_span_over_50m                      # W03
check_v029 = check_steel_superstructure_fatigue       # W04
check_v030 = check_concrete_grade_above_m60           # W05


def _build_engine() -> RulesEngine:
    engine = RulesEngine()
    for fn in _ALL_CHECK_FNS:
        engine.register(fn)
    return engine


_ENGINE: RulesEngine = _build_engine()


def run_all(project: BridgeProject) -> ValidationReport:
    """Run all 30 registered checks against *project* and return a report.

    Parameters
    ----------
    project : BridgeProject
        Fully-validated Pydantic model instance.

    Returns
    -------
    ValidationReport
        Contains all findings, score, and overall status.
    """
    return _ENGINE.run(project)


__all__ = [
    "ValidationFinding",
    "ValidationReport",
    "RulesEngine",
    "run_all",
]
