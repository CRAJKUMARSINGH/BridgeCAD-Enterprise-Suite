"""
BridgeCAD Enterprise — Streamlit UI (M7).
15 tabs covering the full workflow.

Run:
    cd "BridgeCAD Enterprise Suite/apps/streamlit-ui"
    streamlit run app.py
"""
from __future__ import annotations

import sys
import tempfile
import zipfile
from pathlib import Path

import streamlit as st

# ── package path bootstrap ────────────────────────────────────────────────
_SUITE = Path(__file__).parents[2]
for _pkg in ["bridgecad-core", "bridgecad-io", "bridgecad-draw",
             "bridgecad-bill", "bridgecad-qa",  "bridgecad-export",
             "bridgecad-plugins"]:
    _p = _SUITE / "packages" / _pkg
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BridgeCAD Enterprise",
    page_icon="🌉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/bridge.png", width=64)
    st.title("BridgeCAD Enterprise")
    st.caption("v0.1.0 · BRIDGECAD-OSS-1.0")
    st.divider()
    tab_names = [
        "🏠 Home",
        "📁 Load Project",
        "✅ Validate",
        "📐 Drawing Gen",
        "📊 QA Report",
        "💰 BOQ Generator",
        "📦 Export Bundle",
        "🔌 Plugins",
        "📋 Templates",
        "🏗️ Geometry",
        "🌊 Hydraulics",
        "📄 Standards",
        "🔁 History",
        "⚙️ Settings",
        "❓ Help",
    ]
    selected = st.radio("Navigate", tab_names, label_visibility="collapsed")

st.title(selected)
st.divider()


# ── Helper: load project from uploaded file ────────────────────────────────
@st.cache_data(show_spinner=False)
def _load_project_bytes(data: bytes):
    from bridgecad_io.excel_reader import read_excel
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tf:
        tf.write(data); tmp = Path(tf.name)
    try:
        return read_excel(tmp)
    finally:
        tmp.unlink(missing_ok=True)


def _upload_widget(key: str = "xl_upload"):
    return st.file_uploader(
        "Upload BridgeCAD Excel workbook (.xlsx)",
        type=["xlsx"], key=key,
    )


# ===========================================================================
# TAB: Home
# ===========================================================================
if selected == "🏠 Home":
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Enum types",       "200+")
        st.metric("Pydantic fields",   "427")
    with col2:
        st.metric("Drawing sheets",    "7")
        st.metric("Validation checks", "30/150")
    with col3:
        st.metric("MORTH rate items",  "90")
        st.metric("Plugins",           "3")
    st.divider()
    st.subheader("What BridgeCAD can do")
    st.markdown("""
| Feature | Status |
|---|---|
| 200+ IRC/MORTH enums | ✅ M1 Done |
| 427-field Pydantic models (14 sheets) | ✅ M1 Done |
| Excel ↔ BridgeProject IO | ✅ M2 Done |
| 7-sheet DXF GAD package (Plan/Long-section/Cross-section/Foundation/Pier-Abutment/Bearings/BOQ) | ✅ M3 Done |
| 3 bridge-type plugins (RCC T-Beam / PSC I-Girder / Box Culvert) | ✅ M4 Done |
| MORTH BOQ with 90 seed rates, Excel + CSV output | ✅ M5 Done |
| Export ZIP bundle + QA HTML report | ✅ M6 Done |
| CLI + FastAPI + Streamlit | ✅ M7 Done |
| AI optimizer / infra / DB | 🔄 M8 Pending |
| 28 E2E fixtures + benchmarks | 🔄 M9 Pending |
    """)


# ===========================================================================
# TAB: Load Project
# ===========================================================================
elif selected == "📁 Load Project":
    uploaded = _upload_widget("load_xl")
    if uploaded:
        with st.spinner("Parsing workbook …"):
            data    = uploaded.read()
            project = _load_project_bytes(data)
            st.session_state["project"] = project
            st.session_state["xl_data"] = data
        pm = project.project_master
        gi = project.geometry_input
        st.success("✅ Workbook parsed successfully!")
        col1, col2, col3 = st.columns(3)
        col1.metric("Project",    str(getattr(pm, "project_title", "") or "")[:30])
        col2.metric("Total Length", f"{float(gi.total_length_m):.1f} m")
        col3.metric("Spans",      str(gi.span_count))

        with st.expander("Full project metadata"):
            st.json({
                "project_title":  str(getattr(pm, "project_title", "") or ""),
                "bridge_name":    str(getattr(pm, "bridge_name",   "") or ""),
                "chainage_km":    float(getattr(pm, "chainage_km", 0) or 0),
                "state":          getattr(getattr(pm, "state_code", None), "name", ""),
                "span_count":     gi.span_count,
                "total_length_m": float(gi.total_length_m),
                "overall_width_m":float(gi.overall_width_m),
            })


# ===========================================================================
# TAB: Validate
# ===========================================================================
elif selected == "✅ Validate":
    uploaded = _upload_widget("val_xl")
    if uploaded:
        data    = uploaded.read()
        project = _load_project_bytes(data)
        with st.spinner("Running 30 checks …"):
            from bridgecad_core.validation import run_all
            from bridgecad_qa.compliance   import score as _score
            report = run_all(project)
            comp   = _score(report)

        colour = "🟢" if comp.grade in ("A+","A") else \
                 "🟡" if comp.grade in ("B","C")  else "🔴"
        col1,col2,col3,col4 = st.columns(4)
        col1.metric("Score",          f"{comp.overall}/100")
        col2.metric("Grade",          f"{colour} {comp.grade}")
        col3.metric("Critical Fails", comp.critical_fails)
        col4.metric("Warning Fails",  comp.warning_fails)

        fails = report.failed_findings()
        if fails:
            st.error(f"**{len(fails)} checks failed**")
            import pandas as pd
            df = pd.DataFrame([{
                "ID": f.check_id,
                "Severity": f.severity.name if hasattr(f.severity,"name") else str(f.severity),
                "Description": f.description,
                "Message": f.message,
            } for f in fails])
            st.dataframe(df, use_container_width=True)
        else:
            st.success("All checks passed!")

        # HTML report download
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tf:
            tmp = Path(tf.name)
        from bridgecad_qa.reports import generate_html_report
        generate_html_report(report, tmp, project)
        html_bytes = tmp.read_bytes()
        tmp.unlink(missing_ok=True)
        st.download_button("⬇ Download QA HTML Report",
                           data=html_bytes, file_name="QA_Report.html",
                           mime="text/html")


# ===========================================================================
# TAB: Drawing Gen
# ===========================================================================
elif selected == "📐 Drawing Gen":
    uploaded = _upload_widget("draw_xl")
    scale    = st.slider("Plot scale (1:N)", 50, 500, 100, 50)
    prefix   = st.text_input("Output prefix", "GAD")
    if uploaded and st.button("Generate 7-Sheet DXF Package 🚀"):
        data    = uploaded.read()
        project = _load_project_bytes(data)
        with st.spinner("Generating drawings …"):
            with tempfile.TemporaryDirectory() as td:
                from bridgecad_draw.booklet import generate_package
                sheets = generate_package(project, Path(td),
                                          prefix=prefix, scale_denom=scale)
                # ZIP for download
                zip_buf = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
                with zipfile.ZipFile(zip_buf.name, "w", zipfile.ZIP_DEFLATED) as zf:
                    for s in sheets:
                        zf.write(s, s.name)
                zip_bytes = Path(zip_buf.name).read_bytes()
        st.success(f"✅ {len(sheets)}/7 sheets generated!")
        total_kb = sum(s.stat().st_size for s in sheets) // 1024
        st.metric("Total DXF size", f"{total_kb} KB")
        import pandas as pd
        st.dataframe(pd.DataFrame(
            [{"Sheet": s.name, "Size KB": s.stat().st_size//1024} for s in sheets]
        ))
        st.download_button("⬇ Download DXF Package (ZIP)",
                           data=zip_bytes, file_name=f"{prefix}_drawings.zip",
                           mime="application/zip")


# ===========================================================================
# TAB: QA Report
# ===========================================================================
elif selected == "📊 QA Report":
    uploaded = _upload_widget("qa_xl")
    if uploaded:
        data    = uploaded.read()
        project = _load_project_bytes(data)
        with st.spinner("Generating QA HTML report …"):
            from bridgecad_core.validation import run_all
            from bridgecad_qa.reports       import generate_html_report
            report = run_all(project)
            with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tf:
                tmp = Path(tf.name)
            generate_html_report(report, tmp, project)
            html_content = tmp.read_text(encoding="utf-8")
            html_bytes   = tmp.read_bytes()
            tmp.unlink(missing_ok=True)
        st.components.v1.html(html_content, height=700, scrolling=True)
        st.download_button("⬇ Download HTML Report",
                           data=html_bytes, file_name="QA_Report.html",
                           mime="text/html")


# ===========================================================================
# TAB: BOQ Generator
# ===========================================================================
elif selected == "💰 BOQ Generator":
    uploaded = _upload_widget("boq_xl")
    state    = st.selectbox("State (for PWD rates override)",
                             ["None","MH","GJ","RJ","UP","MP","KA","TN","AP","TS"])
    if uploaded and st.button("Generate BOQ 💰"):
        data    = uploaded.read()
        project = _load_project_bytes(data)
        state_code = state if state != "None" else None
        with st.spinner("Extracting quantities and pricing …"):
            from bridgecad_bill.processor                  import extract_and_price
            from bridgecad_bill.formatters.excel_formatter import format_excel
            from bridgecad_bill.formatters.csv_formatter   import format_csv
            boq = extract_and_price(project, state=state_code)
            with tempfile.TemporaryDirectory() as td:
                xlsx_p = format_excel(boq, Path(td) / "BOQ.xlsx")
                csv_p  = format_csv(boq,   Path(td) / "BOQ.csv")
                xlsx_bytes = xlsx_p.read_bytes()
                csv_bytes  = csv_p.read_bytes()

        col1,col2,col3 = st.columns(3)
        col1.metric("Sub-total",   f"INR {float(boq.subtotal):,.0f}")
        col2.metric("Contingency", f"INR {float(boq.contingency_amount):,.0f}")
        col3.metric("Grand Total", f"INR {float(boq.grand_total):,.0f}")

        import pandas as pd
        rows = []
        for sec in boq.sections:
            for item in sec.items:
                rows.append({
                    "Code": item.item_code, "Section": sec.title,
                    "Description": item.description[:50], "Unit": item.unit,
                    "Qty": float(item.quantity),
                    "Rate INR": float(item.rate) if item.rate else None,
                    "Amount INR": float(item.amount) if item.amount else 0,
                })
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

        col1,col2 = st.columns(2)
        col1.download_button("⬇ Excel BOQ", data=xlsx_bytes,
                              file_name="BOQ.xlsx",
                              mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        col2.download_button("⬇ CSV BOQ", data=csv_bytes,
                              file_name="BOQ.csv", mime="text/csv")


# ===========================================================================
# TAB: Export Bundle
# ===========================================================================
elif selected == "📦 Export Bundle":
    uploaded = _upload_widget("exp_xl")
    state    = st.selectbox("State (PWD rates)", ["None","MH","GJ","RJ","UP"])
    scale    = st.slider("Drawing scale", 50, 200, 100, 50)
    if uploaded and st.button("Run Full Export ⚡"):
        data    = uploaded.read()
        project = _load_project_bytes(data)
        with st.spinner("Running full pipeline: DXF + BOQ + QA → ZIP …"):
            with tempfile.TemporaryDirectory() as td:
                from bridgecad_export.orchestrator import export_all
                bundle = export_all(
                    project, Path(td),
                    prefix=uploaded.name.replace(".xlsx",""),
                    state=state if state != "None" else None,
                    scale_denom=scale,
                )
                zip_bytes = bundle.read_bytes()
        size_kb = len(zip_bytes) // 1024
        st.success(f"✅ Bundle ready! {size_kb} KB")
        st.download_button("⬇ Download ZIP Bundle",
                           data=zip_bytes,
                           file_name="bridgecad_bundle.zip",
                           mime="application/zip")


# ===========================================================================
# TAB: Plugins
# ===========================================================================
elif selected == "🔌 Plugins":
    from bridgecad_plugins.registry import get_registry
    from bridgecad_plugins.runner   import PluginRunner
    reg = get_registry()
    st.metric("Installed plugins", len(reg))
    for p in reg.all():
        with st.expander(f"🔌 {p.name}  ·  `{p.plugin_id}`  v{p.version}"):
            runner = PluginRunner(p)
            st.code(runner.describe())
            tv = runner.get_typical_values()
            if tv:
                import pandas as pd
                st.dataframe(
                    pd.DataFrame(list(tv.items()), columns=["Parameter","Value"]),
                    use_container_width=True,
                )


# ===========================================================================
# TAB: Templates
# ===========================================================================
elif selected == "📋 Templates":
    st.subheader("Generate a blank Excel template")
    bridge_type = st.selectbox("Bridge type",
        ["simple_12m", "continuous_3x12m", "girder_4x18m",
         "box_culvert_8m", "viaduct_10x30m", "rob_single_track"])
    if st.button("Generate Template 📋"):
        with tempfile.TemporaryDirectory() as td:
            from bridgecad_io.excel_template import generate_template
            p = generate_template(Path(td) / f"{bridge_type}_template.xlsx")
            xlsx_bytes = p.read_bytes()
        st.success(f"Template generated ({len(xlsx_bytes)//1024} KB)")
        st.download_button("⬇ Download Template",
                           data=xlsx_bytes,
                           file_name=f"{bridge_type}_template.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ===========================================================================
# TAB: Geometry
# ===========================================================================
elif selected == "🏗️ Geometry":
    uploaded = _upload_widget("geom_xl")
    if uploaded:
        data    = uploaded.read()
        project = _load_project_bytes(data)
        from bridgecad_core.geometry import (
            compute_plan_geometry,
            compute_long_section_geometry,
            compute_cross_section_geometry,
            compute_pile_group_layout,
        )
        plan  = compute_plan_geometry(project)
        ls    = compute_long_section_geometry(project)
        cs    = compute_cross_section_geometry(project)
        pile  = compute_pile_group_layout(project)

        st.subheader("Plan Geometry")
        col1,col2,col3 = st.columns(3)
        col1.metric("Total Length",  f"{plan.total_length_m:.3f} m")
        col2.metric("Overall Width", f"{plan.overall_width_m:.3f} m")
        col3.metric("Pier Count",    len(plan.pier_centrelines))

        st.subheader("Longitudinal Levels (RL m)")
        import pandas as pd
        levels_df = pd.DataFrame({
            "Level": ["Top of Deck","Soffit","HFL","LWL","Scour","Pile Tip"],
            "RL (m)": [ls.top_of_deck_rl, ls.soffit_rl, ls.hfl_rl,
                       ls.lwl_rl, ls.scour_level_rl, ls.pile_tip_rl],
        })
        st.dataframe(levels_df.set_index("Level"), use_container_width=True)

        st.subheader(f"Cross-Section  |  Camber peak: {cs.camber_mm:.0f} mm")
        zones_df = pd.DataFrame({
            "Zone": cs.zone_labels,
            "Edge offset (m)": cs.half_width_offsets[1:],
        })
        st.dataframe(zones_df, use_container_width=True)

        if pile.pile_positions:
            st.subheader(f"Pile Group ({pile.pile_rows}×{pile.pile_cols})")
            pile_df = pd.DataFrame(pile.pile_positions,
                                   columns=["X offset (m)", "Y offset (m)"])
            st.dataframe(pile_df, use_container_width=True)


# ===========================================================================
# TAB: Hydraulics
# ===========================================================================
elif selected == "🌊 Hydraulics":
    uploaded = _upload_widget("hyd_xl")
    if uploaded:
        data    = uploaded.read()
        project = _load_project_bytes(data)
        hd = project.hydraulic_data
        col1,col2,col3 = st.columns(3)
        col1.metric("Design Discharge", f"{float(hd.design_discharge_cumecs or 0):.1f} m³/s")
        col2.metric("HFL",              f"{float(hd.hfl_m or 0):.3f} m RL")
        col3.metric("Design Scour",     f"{float(hd.design_scour_depth_m or 0):.2f} m")

        col4,col5,col6 = st.columns(3)
        col4.metric("Freeboard",        f"{float(hd.freeboard_m or 0):.2f} m")
        col5.metric("Lacey f",          str(float(hd.lacey_silt_factor or 0)))
        col6.metric("Return Period",    getattr(getattr(hd,"return_period_yr",None),"name","—") or "—")


# ===========================================================================
# TAB: Standards
# ===========================================================================
elif selected == "📄 Standards":
    st.subheader("IRC / MORTH Design Standards Reference")
    standards = {
        "IRC:5-2015":    "Standard specifications and code of practice for road bridges — Section I General features of design",
        "IRC:6-2017":    "Standard specifications for loads and stresses",
        "IRC:21-2000":   "Standard specifications for plain and reinforced concrete",
        "IRC:78-2014":   "Standard specifications for foundations and substructures",
        "IRC:83 Part I": "Standard specifications for elastomeric bearings",
        "IRC:83 Part II":"Standard specifications for POT/POT-PTFE/spherical bearings",
        "IRC:112-2020":  "Code of practice for concrete road bridges",
        "IRC SP:13":     "Guidelines for the design of small bridges and culverts",
        "IRC SP:55-2019":"Guidelines on quality systems for road bridges",
        "MORTH 5th Rev": "Ministry of Road Transport & Highways specification for road and bridge works",
        "IS:456-2000":   "Plain and reinforced concrete — Code of practice",
        "IS:1786-2008":  "High strength deformed steel bars and wires",
        "IS:2911-2010":  "Design and construction of pile foundations",
    }
    import pandas as pd
    df = pd.DataFrame(list(standards.items()), columns=["Standard","Description"])
    st.dataframe(df.set_index("Standard"), use_container_width=True)


# ===========================================================================
# TAB: History
# ===========================================================================
elif selected == "🔁 History":
    st.info("Generation history store is scheduled for M8 (database + SQLAlchemy). "
            "This tab will list all past GAD generation runs with timestamps, "
            "input hash, output file links, and QA scores.")


# ===========================================================================
# TAB: Settings
# ===========================================================================
elif selected == "⚙️ Settings":
    st.subheader("Application Settings")
    st.text_input("Output directory",  value="./output")
    st.text_input("Default state code (for rates)", value="MH")
    st.selectbox("Default plot scale", [100, 50, 200], index=0)
    st.selectbox("Default sheet size", ["A1", "A0", "A2"], index=0)
    st.toggle("Enable verbose logging", value=False)
    st.button("Save Settings (M8 — not yet persisted)")


# ===========================================================================
# TAB: Help
# ===========================================================================
elif selected == "❓ Help":
    st.subheader("How to use BridgeCAD Enterprise")
    st.markdown("""
### Quick Start
1. **Load Project** tab — upload your BridgeCAD Excel workbook.
2. **Validate** tab — check all 30 IRC/MORTH compliance rules.
3. **Drawing Gen** tab — generate 7-sheet DXF GAD package.
4. **BOQ Generator** tab — get priced Bill of Quantities.
5. **Export Bundle** tab — one click → full ZIP (DXF + BOQ + QA report).

### Excel Workbook Format
The 14-sheet workbook must have sheets named:
`PROJECT_MASTER`, `BRIDGE_SELECTION`, `GEOMETRY_INPUT`, `SUPERSTRUCTURE`,
`SUBSTRUCTURE`, `FOUNDATION_DETAILS`, `APPROACHES`, `HYDRAULIC_DATA`,
`MATERIALS`, `BEARINGS_JOINTS`, `COMPONENTS_LIB`, `DRAWING_CONTROL`,
`CALCULATIONS`, `VALIDATION`

Generate a blank template in the **Templates** tab.

### CLI Usage
```bash
bridgecad draw gad input.xlsx -o ./drawings
bridgecad validate input.xlsx --report QA.html
bridgecad bill gen input.xlsx -o ./bill
bridgecad export all input.xlsx -o ./output
bridgecad plugin list
```

### API Usage
```
POST /bridges/parse      (upload .xlsx → metadata)
POST /bridges/validate   (upload .xlsx → QA JSON)
POST /draw/gad           (upload .xlsx → DXF ZIP)
POST /bills/generate     (upload .xlsx → BOQ JSON)
POST /qa/report          (upload .xlsx → HTML)
POST /exports/bundle     (upload .xlsx → full ZIP)
GET  /plugins/           (list plugins)
```

### Support
Issues: https://github.com/bridgecad/enterprise-suite/issues
    """)
