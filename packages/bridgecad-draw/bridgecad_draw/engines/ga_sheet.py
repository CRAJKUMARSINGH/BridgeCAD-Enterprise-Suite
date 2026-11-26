"""A1 general-arrangement preview for straight, level slab and girder bridges."""
from itertools import accumulate
from math import isfinite
from pathlib import Path

from bridgecad_core.geometry.abutment_profiles import battered_side_outline, family_for, longitudinal_outline
from bridgecad_core.geometry.long_section import compute_long_section_geometry
from bridgecad_core.types import AbutmentType, SpanConfiguration, SuperstructureType

from ..deck_joints import deck_intervals, pier_joints
from ..fit import LADDER


class GALayoutError(ValueError):
    """The project cannot be represented by this GA layout."""


def generate_ga_pdf(
    project, output_pdf: str | Path, scale_denom: int | None = None,
    *, abutment_type: AbutmentType | None = None,
) -> Path:
    from reportlab.lib.colors import HexColor
    from reportlab.lib.units import mm
    from reportlab.pdfgen.canvas import Canvas

    g, s, h = project.geometry_input, project.superstructure, project.hydraulic_data
    family_names = {
        SuperstructureType.SOLID_SLAB: "RCC SOLID SLAB",
        SuperstructureType.RCC_TBEAM: "RCC T-BEAM",
        SuperstructureType.PSC_IGIRDER: "PSC I-GIRDER",
        SuperstructureType.PSC_I_GIRDER_COMPOSITE: "PSC I-GIRDER",
    }
    if s.type not in family_names:
        raise GALayoutError("A1 GA supports solid slab, RCC T-beam and PSC I-girder bridges.")
    is_slab = s.type == SuperstructureType.SOLID_SLAB
    is_psc_i = s.type in (SuperstructureType.PSC_IGIRDER, SuperstructureType.PSC_I_GIRDER_COMPOSITE)
    if (float(g.skew_angle_deg or 0)
            or float(g.gradient_pct or 0) or g.curved_bridge_flag
            or getattr(g.alignment_type, "name", "") != "STRAIGHT"):
        raise GALayoutError("A1 GA currently supports straight, level, zero-skew bridges.")
    spans = [float(n) for n in g.span_lengths_m]
    stations = [0.0, *accumulate(spans)]
    width = float(g.overall_width_m)
    cw = float(g.carriageway_width_m)
    left_kerb = float(g.kerb_width_left_m or 0)
    clear0 = left_kerb + float(g.footpath_left_m or 0) + float(g.crash_barrier_width_left_m or 0)
    span_configuration = project.bridge_selection.span_configuration
    if span_configuration not in (SpanConfiguration.SIMPLY_SUPPORTED, SpanConfiguration.CONTINUOUS):
        raise GALayoutError("Select simply supported or continuous articulation for A1 GA.")
    if float(g.median_width_m or 0) or float(g.median_barrier_width_m or 0):
        raise GALayoutError("A1 GA currently supports undivided carriageways.")
    levels = (project.project_master.road_level_rl_m, h.actual_soffit_level_m,
              h.hfl_m, h.lwl_m, h.scour_level_m)
    if any(v is None or not isfinite(float(v)) for v in levels):
        raise GALayoutError("Supply finite road, structural soffit, HFL, LWL and scour levels.")
    road, soffit, hfl, lwl, scour = map(float, levels)
    wear = float(s.wearing_coat_thickness_mm or 0) / 1000
    slab = float(s.deck_thickness_mm or 0) / 1000
    depth = 0.0 if is_slab else float(s.girder_depth_mm or 0) / 1000
    if slab <= 0 or (not is_slab and depth <= 0) or abs(road - wear - slab - depth - soffit) > 0.001:
        raise GALayoutError("Road, surfacing and structural depth must reconcile with the supplied soffit RL.")
    count = 0 if is_slab else int(s.girders_per_deck_count or 0)
    spacing = 0.0 if is_slab else float(s.girder_spacing_m or 0)
    if not is_slab and (count < 1 or not isfinite(spacing) or spacing <= 0
                        or (count - 1) * spacing >= width):
        raise GALayoutError("Girder centres must fit within the declared overall deck width.")
    girder_axes = [width / 2 + (i - (count - 1) / 2) * spacing for i in range(count)]
    if not spans or min(spans) <= 0 or not scour < lwl <= hfl:
        raise GALayoutError("Positive spans and ordered scour, low-water and high-water levels are required.")

    ground = project.project_master.ground_level_rl_m
    # A ground line may be shown as a single datum when the model supplies
    # one. A shaft ending at that line is a symbol, not a founding level.
    show_ground = ground is not None and scour <= float(ground) < soffit
    ground_rl = float(ground) if show_ground else None

    sub = project.substructure
    selected_abutment = abutment_type or sub.abutment_type
    abutment_labels = {
        AbutmentType.CANTILEVER: "Cantilever",
        AbutmentType.GRAVITY: "Gravity",
        AbutmentType.FULL_HEIGHT_WALL: "Full-height wall",
    }
    if selected_abutment not in abutment_labels:
        raise GALayoutError("A1 GA supports Cantilever, Gravity and Full-height wall abutments.")
    abutment_label = abutment_labels[selected_abutment]
    abutment_width = float(sub.abutment_width_m or 1.5)
    abutment_length = float(sub.abutment_length_m or width)
    abutment_base = soffit - float(sub.abutment_height_m or 2)
    outline = [
        ((x - .5) * abutment_width, abutment_base + y * (soffit - abutment_base))
        for x, y in longitudinal_outline(family_for(selected_abutment))
    ]
    battered = selected_abutment == AbutmentType.GRAVITY
    if battered:
        abutment_cap_depth = (sub.abutment_cap_depth_mm or 450) / 1000
        stem_height = soffit - abutment_base - abutment_cap_depth
        if stem_height < .5:
            raise GALayoutError("Gravity abutment requires at least 0.5 m between cap soffit and footing top.")
        face = float(sub.abutment_face_batter_1n or 10)
        back = float(sub.abutment_back_batter_1n or 3)
        profile = battered_side_outline(
            stem_height, cap_w_m=abutment_width, cap_d_m=abutment_cap_depth,
            face_batter_1n=face, back_batter_1n=back,
            above_m=float(sub.dirt_wall_height_m or .98),
            dirt_w_m=(sub.dirt_wall_thickness_mm or 300) / 1000,
            toe_m=1.5, foot_d_m=1.0,
        )
        outline = [(x - abutment_width / 2, soffit + y - profile.cap_top_y)
                   for x, y in profile.points]
    min_x = min(x for x, _ in outline)
    max_x = max(x for x, _ in outline)
    vertical_top = max(road, hfl, *(rl for _, rl in outline))
    pier_width = float(sub.pier_shaft_width_m or sub.pier_diameter_m or 1.5)
    cap_width = float(sub.pier_cap_width_m or max(pier_width, 2))
    cap_length = float(sub.pier_cap_length_m or width)
    cap_depth = float(sub.pier_cap_depth_m or 0.8)
    pier_levels = []
    if len(spans) > 1:
        for record in compute_long_section_geometry(project).support_level_records:
            cap_top = float(record.cap_top_rl_m) if record.cap_top_rl_m is not None else soffit
            shaft_top = float(record.shaft_top_rl_m) if record.shaft_top_rl_m is not None else cap_top-cap_depth
            shaft_base = float(record.shaft_base_rl_m) if record.shaft_base_rl_m is not None else None
            pier_levels.append((cap_top, shaft_top, shaft_base))
    known_bases = [base for _, _, base in pier_levels if base is not None]
    vertical_base = min(scour, *known_bases, *(rl for _, rl in outline))
    joints = pier_joints(project, stations[1:-1])
    joint_by_station = {joint.station: joint for joint in joints}
    half_gaps = {joint.station: joint.half_gap_m for joint in joints}
    deck_runs = list(deck_intervals(0, stations[-1], joints))
    if any(end <= start for start, end in deck_runs):
        raise GALayoutError("The scheduled pier joint gaps must leave a positive deck length in each span.")

    def pick_scale(candidates, extents):
        for denom in candidates:
            if denom > 0 and all(m * 1000 / denom <= limit for m, limit in extents):
                return denom
        raise GALayoutError("The bridge does not fit GA-01 at the requested plot scale. Use Auto or a smaller drawing scale.")

    ga_denom = pick_scale((scale_denom,) if scale_denom is not None else LADDER,
                         ((stations[-1], 565), (max(-min_x, max_x), 40 if battered else 14),
                          (max(width, abutment_length, cap_length if len(spans) > 1 else 0), 118),
                          (vertical_top - vertical_base, 130)))
    section_denom = pick_scale(LADDER, ((width, 420), (slab + depth, 68)))

    ink, accent, water, light = map(HexColor,("#152638","#004e64","#1872aa","#e6edf1"))
    out = Path(output_pdf)
    c = Canvas(str(out), pagesize=(841*mm,594*mm))
    c.setTitle("BridgeCAD | General arrangement | Review draft")

    def ln(x,y,x2,y2,color=ink,w=.24):
        c.setStrokeColor(color); c.setLineWidth(w*mm);c.line(x*mm,y*mm,x2*mm,y2*mm)

    def box(x,y,w,h,fill=None):
        c.setStrokeColor(ink);c.setLineWidth(.24*mm)
        if fill: c.setFillColor(fill)
        c.rect(x*mm,y*mm,w*mm,h*mm,fill=bool(fill))

    def tx(x,y,st,size=3,color=ink,center=False,bold=False):
        c.setFillColor(color);c.setFont("Helvetica-Bold" if bold else "Helvetica",size*mm)
        (c.drawCentredString if center else c.drawString)(x*mm,y*mm,st)

    def hd(x,y,x2,label):
        ln(x,y,x2,y)
        for a in (x,x2):ln(a-1.5,y-1.5,a+1.5,y+1.5)
        tx((x+x2)/2,y+2.5,label,center=True)

    box(10,10,821,574)
    tx(21,566,f"GENERAL ARRANGEMENT  /  {family_names[s.type]} BRIDGE",7,accent,bold=True)
    framing = "solid slab" if is_slab else f"{count} girders per span"
    tx(21,553,f"{project.project_master.project_code}  |  {len(spans)} spans  |  {framing}  |  {stations[-1]:.3f} m end support c/c",4)
    tx(21,543,"REVIEW DRAFT   /   VERIFY PROJECT INPUTS   /   PRINT A1 AT 100%",3.6,accent,bold=True)
    ln(21,536,819,536)

    x0=100
    sx = 1000 / ga_denom
    min_span_on_paper = min(spans)*sx
    span_schedule = min_span_on_paper < 12
    X=lambda m:x0+m*sx
    x1=X(stations[-1])
    label_indices = {0, len(spans)}
    last_label = x0
    for index, station in enumerate(stations[1:-1], 1):
        if X(station)-last_label >= 9 and x1-X(station) >= 9:
            label_indices.add(index)
            last_label = X(station)

    def support_name(index):
        return "A1" if index == 0 else "A2" if index == len(spans) else f"P{index}"

    tx(21,521,f"01  PLAN  /  1:{ga_denom}",4,accent,bold=True)
    plan_center = 436
    py = plan_center - width*sx/2
    abutment_ink = HexColor("#c4d6df")
    joint_ink = HexColor("#963d2d")
    # The battered profile's dirt wall is on its negative-x side.
    a1_direction = 1 if battered else -1
    end_supports = ((stations[0], a1_direction), (stations[-1], -a1_direction))
    for start, end in deck_runs:
        box(X(start), py, (end-start)*sx, width*sx, light)
        for edge in (clear0, clear0+cw):
            ln(X(start), py+edge*sx, X(end), py+edge*sx)
    c.setDash(2*mm, 1.5*mm)
    for station, direction in end_supports:
        y0 = plan_center - abutment_length*sx/2
        y1 = y0 + abutment_length*sx
        left = X(station) + min(direction * min_x, direction * max_x)*sx
        box(left, y0, (max_x - min_x)*sx, y1 - y0, abutment_ink)
        if battered:
            for index in (1, 2, 4, 5, 10, 13):
                x = X(station) + direction * outline[index][0]*sx
                ln(x, y0, x, y1, accent, .2)
    for station in stations[1:-1]:
        box(X(station)-cap_width*sx/2, plan_center-cap_length*sx/2, cap_width*sx, cap_length*sx)
    c.setDash([5*mm, 2*mm, 1*mm, 2*mm])
    ln(x0-5, plan_center, x1+5, plan_center, accent, .18)
    c.setDash()
    if girder_axes:
        c.setDash(2*mm, 2*mm)
        for axis in girder_axes:
            for start, end in zip(stations, stations[1:]):
                ln(X(start+half_gaps.get(start, 0)), py+axis*sx,
                   X(end-half_gaps.get(end, 0)), py+axis*sx, accent, .15)
        c.setDash()
    support_extent = max(width, abutment_length, cap_length if len(spans) > 1 else 0)*sx/2
    support_top = plan_center + support_extent
    support_bottom = plan_center - support_extent
    for i,ch in enumerate(stations):
        x = X(ch)
        ln(x, support_bottom-4, x, 360, accent, .18)
        ln(x, support_top+1, x, support_top+5, accent, .18)
        if i in label_indices:
            tx(x, support_top+7, support_name(i), center=True, bold=True)
        joint = joint_by_station.get(ch)
        if joint:
            for face in joint.faces:
                ln(X(face), py, X(face), py+width*sx, joint_ink, .32)
    if span_schedule:
        tx(681, 493, "SPAN LENGTHS IN ORDER FROM A1 (m)", 3.1, accent, bold=True)
        for index, span in enumerate(spans):
            column, row = divmod(index, 20)
            tx(681+28*column, 485-5.1*row, f"{index+1}. {span:.3f}", 2.5)
    else:
        stagger = 6 if min_span_on_paper < 18 else 0
        for i, (a, b) in enumerate(zip(stations, stations[1:])):
            hd(X(a), 360+(i%2)*stagger, X(b), f"{b-a:.3f} m")
    hd(x0,349,x1,f"{stations[-1]:.3f} m c/c end supports")
    tx(233,521,f"Deck {width:.2f} m overall   |   Carriageway {cw:.2f} m clear",3.2)
    tx(449,521,"Dashed outlines: supports below deck",3.2)
    if girder_axes:
        tx(681,521,f"{count} girders at {spacing:.2f} m c/c",3.2)

    ln(21,337,819,337)
    tx(21,324,f"02  LONGITUDINAL ELEVATION  /  H 1:{ga_denom}  |  V 1:{ga_denom}",4,accent,bold=True)
    tx(681, 324, f"A1 / A2: {abutment_label}", 3.2, bold=True)
    if joints:
        tx(449, 324, "Deck joint / span break", 3.2, color=joint_ink)
        known = [f"P{joint.pier} {joint.gap_mm} mm" for joint in joints if joint.gap_mm is not None]
        if len(known) <= 4 and known:
            tx(498, 29, "Installation gaps  |  " + ", ".join(known), 3.1, color=joint_ink)
        elif known:
            tx(498, 29, "Installation gaps in workbook joint schedule", 3.1, color=joint_ink)

    elevation_height = (vertical_top - vertical_base) * sx
    elevation_base = 174 + (130 - elevation_height) / 2
    Y = lambda rl: elevation_base + (rl - vertical_base) * sx
    # Dimension only the declared envelope. Support silhouettes stop short of any
    # founding RL and do not imply an approved pile group or wall design.
    for start, end in deck_runs:
        box(X(start), Y(soffit), (end-start)*sx, (road-wear-soffit)*sx, light)
        ln(X(start), Y(road), X(end), Y(road), ink, .42)
        if not is_slab:
            ln(X(start), Y(road-wear-slab), X(end), Y(road-wear-slab), ink, .18)
    for joint in joints:
        for face in joint.faces:
            ln(X(face), Y(soffit), X(face), Y(road if joint.scheduled else road-wear), joint_ink, .32)
    support_label_y = Y(vertical_top) + 6
    for i, station in enumerate(stations):
        if i in label_indices:
            tx(X(station), support_label_y, support_name(i), center=True, bold=True)
    for station, direction in end_supports:
        path = c.beginPath()
        for index, (local_x, rl) in enumerate(outline):
            vertex = ((X(station) + direction * local_x * sx) * mm, Y(rl) * mm)
            (path.moveTo if index == 0 else path.lineTo)(*vertex)
        path.close()
        c.setFillColor(abutment_ink)
        c.setStrokeColor(ink)
        c.setLineWidth(.24 * mm)
        c.drawPath(path, fill=1)
    for ch, (cap_top, shaft_top, shaft_base) in zip(stations[1:-1], pier_levels):
        x = X(ch)
        if shaft_base is None:
            c.setDash(2*mm, 1*mm)
            for face in (x-pier_width*sx/2, x+pier_width*sx/2):
                ln(face, Y(shaft_top), face, Y(shaft_top)-8)
            c.setDash()
        else:
            box(x-pier_width*sx/2, Y(shaft_base), pier_width*sx, (shaft_top-shaft_base)*sx, light)
        box(x-cap_width*sx/2, Y(shaft_top), cap_width*sx, (cap_top-shaft_top)*sx, light)
        if cap_top < soffit:
            seat_width = min(pier_width, cap_width)*sx
            box(x-seat_width/2, Y(cap_top), seat_width, (soffit-cap_top)*sx, light)
    tx(21,151,"Support profiles are schematic. See separate sheets for foundations, bearings and wing walls.",3.2)
    if any(base is None for _, _, base in pier_levels):
        tx(449,151,"Dashed pier stems indicate unresolved base levels.",3.2)
    if battered:
        tx(21,146,f"Gravity batter: river 1:{face:g}, earth 1:{back:g}. "
           "Footing 1.0 m thick and 1.5 m projections assumed.",3)
    level_marks = [(hfl, "HFL", water), (lwl, "LWL", water), (scour, "SCOUR", water)]
    for rl, _, color in level_marks:
        c.setDash(4*mm, 2*mm)
        ln(x0-10, Y(rl), x1+8, Y(rl), color)
        c.setDash()
    if ground_rl is not None:
        ln(x0-10, Y(ground_rl), x1+8, Y(ground_rl), accent)
        level_marks.append((ground_rl, "MODEL GROUND", accent))
    level_marks.extend([(road, "ROAD", ink), (soffit, "SLAB SOFFIT" if is_slab else "GIRDER SOFFIT", ink)])
    label_y = 174
    for rl, label, color in sorted(level_marks, key=lambda item: item[0]):
        label_y = max(Y(rl), label_y+5.2)
        ln(x1+8, Y(rl), x1+18, label_y, color, .18)
        tx(x1+20, label_y-1, f"{label} RL {rl:.3f}", 3, color)
    tx(21,163,f"Input soffit minus HFL = {soffit-hfl:.2f} m. Hydraulic clearance acceptance pending.",3.2,color=water)

    ln(21,141,819,141)
    tx(21,128,f"03  TYPICAL CROSS-SECTION  /  1:{section_denom}",4,accent,bold=True)
    u = 1000 / section_denom
    bx=46
    by=103
    box(bx,by-slab*u,width*u,slab*u,light)
    ln(bx+clear0*u,by+wear*u,bx+(clear0+cw)*u,by+wear*u,accent,.45)
    if girder_axes:
        # Draw review symbols in model units and apply the section scale once.
        # No flange, haunch or web dimension here is a design input.
        edge_clearance = min(girder_axes[0], width - girder_axes[-1])
        flange_width = min(0.50, spacing / 2, 2 * edge_clearance)
        web_width = min(0.20, flange_width / 2)
        flange_depth = min(0.15, depth / 4)
        top = by - slab * u
        bottom = top - depth * u
        for i, axis in enumerate(girder_axes, start=1):
            x = bx + axis * u
            web_base = bottom
            if is_psc_i:
                box(x - flange_width*u/2, bottom, flange_width*u, flange_depth*u, light)
                web_base += flange_depth * u
            box(x - web_width*u/2, web_base, web_width*u, top - flange_depth*u - web_base, light)
            box(x - flange_width*u/2, top - flange_depth*u, flange_width*u, flange_depth*u, light)
            tx(x, bottom - 5, str(i), 2.3, center=True)
    hd(bx,112,bx+width*u,f"{width:.2f} m overall")
    if is_slab:
        tx(bx,23,f"Solid slab thickness {slab*1000:g} mm",3)
    else:
        tx(bx,23,f"{count} girders at {spacing:.2f} m c/c  |  flange and web profiles schematic",3)
    ln(486,18,486,132)
    for i,line in enumerate((
        "DRAWING BASIS AND RELEASE STATUS",
        (f"Slab {slab*1000:g} mm; surfacing {wear*1000:g} mm." if is_slab else
         f"Slab {slab*1000:g} mm; girder below slab {depth*1000:g} mm; surfacing {wear*1000:g} mm."),
        ("Deck breaks at pier centres. Installation gaps are taken from the workbook schedule."
         if joints else "Single span between A1 and A2."),
        (f"A1/A2 abutment symbols: {abutment_label}. "
         + ("Missing dimensions shown schematically." if any(v is None for v in (
             sub.abutment_width_m, sub.abutment_length_m, sub.abutment_height_m,
         )) else ("Body from workbook; footing assumed." if battered else "Envelope from workbook."))),
        "Confirm survey, hydraulic, foundation and detailing inputs before release.",
        "GA-01  /  A1  /  REVIEW DRAFT"
    )):
        tx(498,119-i*15,line,3.8 if i in (0,5) else 3.1,accent if i in (0,5) else ink,bold=i in (0,5))
    c.showPage();c.save()
    return out
