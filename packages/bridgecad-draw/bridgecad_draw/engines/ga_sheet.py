"""A1 general-arrangement preview for straight, level slab and girder bridges."""
from itertools import accumulate
from math import isfinite
from pathlib import Path

from bridgecad_core.geometry.abutment_profiles import battered_side_outline, elevation_outline, family_for
from bridgecad_core.types import AbutmentType, SpanConfiguration, SuperstructureType

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
        for x, y in elevation_outline(family_for(selected_abutment))
    ]
    battered = selected_abutment == AbutmentType.GRAVITY
    if battered:
        cap_depth = (sub.abutment_cap_depth_mm or 450) / 1000
        stem_height = soffit - abutment_base - cap_depth
        if stem_height < .5:
            raise GALayoutError("Gravity abutment requires at least 0.5 m between cap soffit and footing top.")
        face = float(sub.abutment_face_batter_1n or 10)
        back = float(sub.abutment_back_batter_1n or 3)
        profile = battered_side_outline(
            stem_height, cap_w_m=abutment_width, cap_d_m=cap_depth,
            face_batter_1n=face, back_batter_1n=back,
            above_m=float(sub.dirt_wall_height_m or .98),
            dirt_w_m=(sub.dirt_wall_thickness_mm or 300) / 1000,
            toe_m=1.5, foot_d_m=1.0,
        )
        outline = [(x - abutment_width / 2, soffit + y - profile.cap_top_y)
                   for x, y in profile.points]
    min_x = min(x for x, _ in outline)
    max_x = max(x for x, _ in outline)
    vertical_base = min(scour, *(rl for _, rl in outline))
    vertical_top = max(road, hfl, *(rl for _, rl in outline))

    def pick_scale(candidates, extents):
        for denom in candidates:
            if denom > 0 and all(m * 1000 / denom <= limit for m, limit in extents):
                return denom
        raise GALayoutError("The bridge does not fit GA-01 at the requested plot scale. Use Auto or a smaller drawing scale.")

    ga_denom = pick_scale((scale_denom,) if scale_denom is not None else LADDER,
                         ((stations[-1], 565), (max(-min_x, max_x), 40),
                          (max(width, abutment_length), 127),
                          (vertical_top - vertical_base, 137)))
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
    X=lambda m:x0+m*sx
    x1=X(stations[-1])
    tx(21,521,f"01  PLAN  /  1:{ga_denom}",4,accent,bold=True)
    py=374
    box(x0,py,x1-x0,width*sx,light)
    abutment_ink = HexColor("#c4d6df")
    ends = ((stations[0], 1), (stations[-1], -1))
    for station, direction in ends:
        y0 = py + (width - abutment_length) * sx / 2
        y1 = y0 + abutment_length * sx
        left = X(station) + min(direction * min_x, direction * max_x) * sx
        box(left, y0, (max_x - min_x) * sx, y1 - y0, abutment_ink)
        if battered:
            # Dirt wall, cap and stem stations come from the elevation polygon.
            for index in (1, 2, 4, 5, 10, 13):
                x = X(station) + direction * outline[index][0] * sx
                ln(x, y0, x, y1, accent, .2)
    edges=[clear0, clear0+cw]
    for e in edges:ln(x0,py+e*sx,x1,py+e*sx)
    c.setDash(3*mm,2*mm);ln(x0,py+width*sx/2,x1,py+width*sx/2,accent);c.setDash()
    if girder_axes:
        c.setDash(2*mm, 2*mm)
        for axis in girder_axes:
            for start, end in zip(stations, stations[1:]):
                ln(X(start), py+axis*sx, X(end), py+axis*sx, accent, .15)
        c.setDash()
    tx((x0+x1)/2,py+width*sx/2+3,f"{cw:.2f} m clear carriageway",center=True)
    for i,ch in enumerate(stations):
        x=X(ch);ln(x,py-6,x,py+width*sx+9,accent)
        name = "A1" if i==0 else "A2" if i==len(spans) else f"P{i}"
        tx(x,py+width*sx+12,f"{name}  /  CH {ch:.2f}",center=True,bold=True)
    for a,b in zip(stations,stations[1:]):hd(X(a),360,X(b),f"{b-a:.3f} m")
    hd(x0,349,x1,f"{stations[-1]:.3f} m c/c end supports")
    tx(681,457,f"{width:.2f} m overall",3.6,bold=True)
    tx(681,446,"Zero skew assumed",3.2)
    tx(681,435,"Support axes shown" if is_slab else "Dashed girder axes",3.2)
    if girder_axes:
        tx(681,425,f"{count} girders at {spacing:.2f} m c/c",3.2)

    ln(21,337,819,337)
    tx(21,324,f"02  LONGITUDINAL ELEVATION  /  H 1:{ga_denom}  |  V 1:{ga_denom}",4,accent,bold=True)
    tx(681,410,f"A1 / A2: {abutment_label}",3.2,bold=True)

    elevation_height = (vertical_top - vertical_base) * sx
    elevation_base = 174 + (137 - elevation_height) / 2
    Y = lambda rl: elevation_base + (rl - vertical_base) * sx
    # Dimension only the declared envelope. Support silhouettes stop short of any
    # founding RL and do not imply an approved pile group or wall design.
    box(x0, Y(soffit), x1-x0, (road-wear-soffit)*sx, light)
    if span_configuration == SpanConfiguration.SIMPLY_SUPPORTED:
        for station in stations[1:-1]:
            ln(X(station), Y(soffit), X(station), Y(road-wear), ink, .38)
    ln(x0,Y(road),x1,Y(road),ink,.42)
    for station, direction in ends:
        path = c.beginPath()
        for index, (local_x, rl) in enumerate(outline):
            vertex = ((X(station) + direction * local_x * sx) * mm, Y(rl) * mm)
            (path.moveTo if index == 0 else path.lineTo)(*vertex)
        path.close()
        c.setFillColor(abutment_ink)
        c.setStrokeColor(ink)
        c.setLineWidth(.24 * mm)
        c.drawPath(path, fill=1)
    for ch in stations[1:-1]:
        x=X(ch)
        symbol_bottom = Y(ground_rl) if ground_rl is not None else Y(soffit) - 12
        box(x-7, symbol_bottom, 14, Y(soffit)-symbol_bottom, light)
        ln(x-9, symbol_bottom, x+9, symbol_bottom, accent, .38)
    if ground_rl is not None:
        ln(x0-10,Y(ground_rl),x1+8,Y(ground_rl),accent)
        tx(x1+13,Y(ground_rl)-1,f"MODEL GROUND RL {ground_rl:.3f}",color=accent)
    tx(21,151,"A1/A2 outlines are for review. Confirm wing walls, bearings and founding levels.",3.2)
    if battered:
        tx(21,146,f"Gravity batter: river 1:{face:g}, earth 1:{back:g}. "
           "Footing 1.0 m thick and 1.5 m projections assumed.",3)
    for rl,label in [(hfl,"HFL"),(lwl,"LWL"),(scour,"SCOUR")]:
        c.setDash(4*mm,2*mm);ln(x0-10,Y(rl),x1+8,Y(rl),water);c.setDash()
        tx(x1+13,Y(rl)-1,f"{label} RL {rl:.3f}",color=water)
    tx(x1+13,Y(road)+1,f"ROAD RL {road:.3f}")
    tx(x1+13,Y(soffit)-1,f"{'SLAB' if is_slab else 'GIRDER'} SOFFIT RL {soffit:.3f}")
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
        "Span separation marks apply to simply supported spans. Joint gap unspecified.",
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
