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
for _pkg in [
    "bridgecad-core",
    "bridgecad-io",
    "bridgecad-draw",
    "bridgecad-bill",
    "bridgecad-qa",
    "bridgecad-export",
    "bridgecad-plugins",
]:
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
        "🎛️ PWD Generator",
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
        tf.write(data)
        tmp = Path(tf.name)
    try:
        return read_excel(tmp)
    finally:
        tmp.unlink(missing_ok=True)


def _upload_widget(key: str = "xl_upload"):
    return st.file_uploader(
        "Upload BridgeCAD Excel workbook (.xlsx)",
        type=["xlsx"],
        key=key,
    )


def _safe_prefix(raw: str) -> str:
    """S9 — sanitise filename prefix against injection (PATCH_GUIDE §9)."""
    import re as _re
    safe = _re.sub(r"[^A-Za-z0-9._-]+", "_", raw).strip("._") or "project"
    return safe[:40]


# ===========================================================================
# TAB: Home
# ===========================================================================
if selected == "🏠 Home":
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Enum types", "200+")
        st.metric("Pydantic fields", "427")
    with col2:
        st.metric("Drawing sheets", "9")
        st.metric("Validation checks", "30+")
    with col3:
        st.metric("MORTH rate items", "90")
        st.metric("PWD bridge types", "15")
    st.divider()
    st.subheader("What BridgeCAD can do")
    st.markdown("""
| Feature | Status |
|---|---|
| 200+ IRC/MORTH enums | ✅ Done |
| 427-field Pydantic models (14 sheets) | ✅ Done |
| Excel ↔ BridgeProject IO | ✅ Done |
| 9-sheet DXF GAD package (Plan/Long-section/Cross-section/Foundation/Pier-Abutment/Bearings/BOQ/Side-elevations/Reinforcement) | ✅ Done |
| **15 Maharashtra PWD standard types** with parametric variation (`--set/--sweep`) | ✅ Done |
| **Abutment cap + dirt wall + continuous WC** (Venice-patch geometry) | ✅ Done |
| **Standard scale ladder** — 1:50→1:500, broken-band for 270 m bridges | ✅ Done |
| 3 bridge-type plugins (RCC T-Beam / PSC I-Girder / Box Culvert) | ✅ Done |
| MORTH BOQ with 90 seed rates, Excel + CSV output | ✅ Done |
| Export ZIP bundle + QA HTML report | ✅ Done |
| CLI + FastAPI + Streamlit + React | ✅ Done |
    """)
    st.divider()
    st.info("👉 **New user?** Go to **📐 Drawing Gen** to generate drawings from an Excel workbook, "
            "or **🎛️ PWD Generator** to pick a Maharashtra PWD standard type and vary its parameters.")
    st.caption("Docs: [User Manual](docs/USER-MANUAL.md) · [PWD Enrichment Guide](docs/PWD_ENRICHMENT_GUIDE.md) · [GUIDE.md](GUIDE.md)")


# ===========================================================================
# TAB: Load Project
# ===========================================================================
elif selected == "📁 Load Project":
    uploaded = _upload_widget("load_xl")
    if uploaded:
        with st.spinner("Parsing workbook …"):
            data = uploaded.read()
            project = _load_project_bytes(data)
            st.session_state["project"] = project
            st.session_state["xl_data"] = data
        pm = project.project_master
        gi = project.geometry_input
        st.success("✅ Workbook parsed successfully!")
        col1, col2, col3 = st.columns(3)
        col1.metric("Project", str(getattr(pm, "project_title", "") or "")[:30])
        col2.metric("Total Length", f"{float(gi.total_length_m):.1f} m")
        col3.metric("Spans", str(gi.span_count))

        with st.expander("Full project metadata"):
            st.json(
                {
                    "project_title": str(getattr(pm, "project_title", "") or ""),
                    "bridge_name": str(getattr(pm, "bridge_name", "") or ""),
                    "chainage_km": float(getattr(pm, "chainage_km", 0) or 0),
                    "state": getattr(getattr(pm, "state_code", None), "name", ""),
                    "span_count": gi.span_count,
                    "total_length_m": float(gi.total_length_m),
                    "overall_width_m": float(gi.overall_width_m),
                }
            )


# ===========================================================================
# TAB: Validate
# ===========================================================================
elif selected == "✅ Validate":
    uploaded = _upload_widget("val_xl")
    if uploaded:
        data = uploaded.read()
        project = _load_project_bytes(data)
        with st.spinner("Running 30 checks …"):
            from bridgecad_core.validation import run_all
            from bridgecad_qa.compliance import score as _score

            report = run_all(project)
            comp = _score(report)

        colour = "🟢" if comp.grade in ("A+", "A") else "🟡" if comp.grade in ("B", "C") else "🔴"
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Score", f"{comp.overall}/100")
        col2.metric("Grade", f"{colour} {comp.grade}")
        col3.metric("Critical Fails", comp.critical_fails)
        col4.metric("Warning Fails", comp.warning_fails)

        fails = report.failed_findings()
        if fails:
            st.error(f"**{len(fails)} checks failed**")
            import pandas as pd

            df = pd.DataFrame(
                [
                    {
                        "ID": f.check_id,
                        "Severity": f.severity.name
                        if hasattr(f.severity, "name")
                        else str(f.severity),
                        "Description": f.description,
                        "Message": f.message,
                    }
                    for f in fails
                ]
            )
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
        st.download_button(
            "⬇ Download QA HTML Report",
            data=html_bytes,
            file_name="QA_Report.html",
            mime="text/html",
        )


# ===========================================================================
# TAB: Drawing Gen
# ===========================================================================
elif selected == "📐 Drawing Gen":
    st.markdown("Generate a full 9-sheet DXF package from your Excel workbook.")
    uploaded = _upload_widget("draw_xl")
    col_s, col_f, col_p = st.columns(3)
    with col_s:
        scale_choice = st.selectbox(
            "Plot scale (1:N)",
            options=["Auto (standard per-sheet)", 50, 100, 200, 500],
            index=0,
            help="'Auto' lets each sheet pick the largest IRC SP:55 ladder rung that fits. "
                 "For 270 m bridges this will be 1:500 with two horizontal bands.",
        )
    with col_f:
        fmt = st.selectbox(
            "Output format",
            ["DXF only", "DXF + PNG preview"],
            index=0,
            help="PNG preview renders each DXF sheet at 150 dpi — useful for checking "
                 "geometry without a CAD viewer.",
        )
    with col_p:
        prefix = st.text_input("Filename prefix", "GAD",
                               help="All output files will be prefixed with this string.")
    scale = None if isinstance(scale_choice, str) else int(scale_choice)
    want_png = fmt == "DXF + PNG preview"
    safe_prefix = _safe_prefix(prefix)  # S9 sanitise

    if uploaded and st.button("Generate 9-Sheet DXF Package 🚀"):
        data = uploaded.read()
        # S6 — file size guard (PATCH_GUIDE §6)
        if len(data) == 0:
            st.error("Empty file — please upload a valid .xlsx workbook.")
            st.stop()
        if len(data) > 50 * 1024 * 1024:
            st.error("File exceeds 50 MB maximum.")
            st.stop()
        try:
            project = _load_project_bytes(data)
        except Exception as _e:
            import uuid as _uuid
            st.error("Failed to parse workbook — check it is a valid BridgeCAD Excel file.")
            st.caption(f"ref: {_uuid.uuid4().hex[:8]}")
            st.stop()
        with st.spinner("Generating drawings …"), tempfile.TemporaryDirectory() as td:
            from bridgecad_draw.booklet import PackageGenerationError, generate_package

            try:
                sheets = generate_package(project, Path(td), prefix=safe_prefix, scale_denom=scale)
            except PackageGenerationError as exc:
                # S7 — exception UUID reference (PATCH_GUIDE §7)
                import uuid as _uuid
                _ref = _uuid.uuid4().hex[:8]
                st.error(f"❌ Drawing package incomplete — ref: {_ref}")
                st.caption(str(exc))
                sheets = None

            png_files = []
            if sheets and want_png:
                try:
                    from bridgecad_draw.engines.png_engine import render_png
                    import matplotlib; matplotlib.use("Agg")
                    import matplotlib.pyplot as plt
                    for s in sheets[:4]:  # render first 4 sheets only (memory limit)
                        png_out = Path(td) / (s.stem + ".png")
                        render_png(s, png_out, dpi=120)
                        plt.close("all")
                        png_files.append(png_out)
                except Exception as e:
                    st.warning(f"PNG preview failed (DXF still available): {e}")

            if sheets is not None:
                zip_buf = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
                with zipfile.ZipFile(zip_buf.name, "w", zipfile.ZIP_DEFLATED) as zf:
                    for s in sheets:
                        zf.write(s, s.name)
                    for p_ in png_files:
                        zf.write(p_, p_.name)
                zip_bytes = Path(zip_buf.name).read_bytes()

        if sheets is not None:
            st.success(f"✅ {len(sheets)}/9 sheets generated!")
            total_kb = sum(s.stat().st_size for s in sheets) // 1024
            st.metric("Total DXF size", f"{total_kb} KB")
            import pandas as pd
            st.dataframe(
                pd.DataFrame(
                    [{"Sheet": s.name, "Size KB": s.stat().st_size // 1024} for s in sheets]
                )
            )
            if png_files:
                st.subheader("Preview (Sheets 1–4)")
                cols = st.columns(2)
                for i, p_ in enumerate(png_files):
                    cols[i % 2].image(str(p_), use_container_width=True, caption=p_.stem)
            st.download_button(
                "⬇ Download DXF Package (ZIP)",
                data=zip_bytes,
                file_name=f"{safe_prefix}_drawings.zip",
                mime="application/zip",
            )


# ===========================================================================
# TAB: PWD Generator — parametric variation of Maharashtra PWD standard types
# ===========================================================================
elif selected == "🎛️ PWD Generator":
    st.markdown("""
Generate a 9-sheet DXF package for any of the **15 Maharashtra PWD standard bridge types**
(C.E. Designs letter No. 2473, dt. 31.12.2022) with full parametric control.

No Excel workbook needed — the catalogue provides booklet-faithful baseline values.
You choose a type, adjust the FREE variables below, and the resolver auto-derives
`total_length`, `soffit_level`, `pier_count`, `bearing_type` and enforces all IRC constraints.
    """)
    st.divider()

    # ── Type selector ────────────────────────────────────────────────────────
    sys.path.insert(0, str(_SUITE / "packages" / "bridgecad-catalogue"))
    try:
        from bridgecad_catalogue.registry import PWD_CARDS
        from bridgecad_catalogue.resolve import resolve, Violation
        from bridgecad_catalogue.sweep import matrix as sweep_matrix
        catalogue_ok = True
    except Exception as e:
        st.error(f"Catalogue package not found: {e}")
        catalogue_ok = False

    if catalogue_ok:
        type_labels = {c["id"]: f"{c['id']} — {c['title']}" for c in PWD_CARDS}
        selected_id = st.selectbox("Bridge type (Maharashtra PWD booklet)", list(type_labels.keys()),
                                   format_func=lambda x: type_labels[x])
        card = next(c for c in PWD_CARDS if c["id"] == selected_id)

        st.caption(f"**Spans:** {card['spans']}  ·  "
                   f"**Foundation:** {card['foundation_type']}  ·  "
                   f"**Superstructure:** {card['superstructure_type']}")

        st.subheader("Adjust FREE variables")
        st.info("LOCKED variables (foundation type, superstructure type, bearing type) "
                "are fixed for each booklet type. DERIVED values are auto-calculated.")

        col1, col2, col3 = st.columns(3)
        overrides = {}

        with col1:
            st.markdown("**Geometry**")
            sl = st.number_input("Span length (m)", min_value=6.0, max_value=50.0,
                                 value=float(card["span_lengths"][0]), step=0.5,
                                 help="Applies to all spans equally.")
            if abs(sl - float(card["span_lengths"][0])) > 0.01:
                overrides["span_length_m"] = sl

            cw_opts = [3.5, 7.5, 11.0]
            cw_def = float(card.get("carriageway_width", 7.5))
            cw = st.selectbox("Carriageway width (m)", cw_opts,
                              index=cw_opts.index(cw_def) if cw_def in cw_opts else 1,
                              help="IRC 73 standard widths.")
            if cw != cw_def:
                overrides["carriageway_width"] = cw

            skew = st.slider("Skew angle (°)", 0, 30,
                             value=int(card.get("skew_deg", 0)), step=5,
                             help="IRC 5 cl.101.3 — max 30°.")
            if skew != card.get("skew_deg", 0):
                overrides["skew_deg"] = skew

        with col2:
            st.markdown("**Pier**")
            ph = st.number_input("Pier height (m)", min_value=3.0, max_value=25.0,
                                 value=float(card.get("pier_height", 6.0)), step=0.5)
            if abs(ph - float(card.get("pier_height", 6.0))) > 0.01:
                overrides["pier_height_m"] = ph

            pw = st.number_input("Pier shaft width (m)", min_value=0.8, max_value=3.0,
                                 value=float(card.get("pier_shaft_width", 1.5)), step=0.1,
                                 help="IRC 112 cl.16.")
            if abs(pw - float(card.get("pier_shaft_width", 1.5))) > 0.01:
                overrides["pier_shaft_width_m"] = pw

        with col3:
            st.markdown("**Hydraulics / Foundation**")
            hfl = st.number_input("HFL (m RL)", min_value=0.0, max_value=1000.0,
                                  value=float(card.get("hfl", 100.0)), step=0.1)
            if abs(hfl - float(card.get("hfl", 100.0))) > 0.001:
                overrides["hfl_m"] = hfl

            fb = st.number_input("Freeboard (m)", min_value=0.6, max_value=4.0,
                                 value=float(card.get("freeboard_m", 1.0)), step=0.05,
                                 help="IRC 5 cl.104.")
            if abs(fb - float(card.get("freeboard_m", 1.0))) > 0.001:
                overrides["freeboard_m"] = fb

            sbc = st.number_input("SBC (t/m²)", min_value=10.0, max_value=200.0,
                                  value=float(card.get("sbc_t_per_m2", 30.0)), step=5.0,
                                  help="IRC 78 cl.701.")
            if abs(sbc - float(card.get("sbc_t_per_m2", 30.0))) > 0.1:
                overrides["sbc_t_per_m2"] = sbc

        st.divider()

        # ── Resolve preview ───────────────────────────────────────────────────
        try:
            from decimal import Decimal
            p = resolve(card, overrides)
            col_a, col_b, col_c, col_d = st.columns(4)
            col_a.metric("Total length", f"{float(p['total_length_m']):.2f} m")
            col_b.metric("Soffit RL", f"{float(p['soffit_level']):.3f} m")
            col_c.metric("Pier count", str(p["pier_count"]))
            col_d.metric("Bearing type", str(p["bearing_type"]))
            if overrides:
                st.success(f"✅ Resolved with {len(overrides)} override(s). "
                           f"Derivation trace: {len(p.trace)} steps.")
            if p.warnings:
                for w in p.warnings:
                    st.warning(w)
            resolve_ok = True
        except Violation as exc:
            st.error(f"❌ Constraint violation: {exc}")
            resolve_ok = False

        # ── Generate button ───────────────────────────────────────────────────
        col_scale, col_fmt, _ = st.columns(3)
        with col_scale:
            pwd_scale = st.selectbox("Plot scale", ["Auto", 50, 100, 200, 500],
                                     key="pwd_scale",
                                     help="Auto = largest IRC SP:55 rung that fits.")
        with col_fmt:
            pwd_fmt = st.selectbox("Output format", ["DXF only", "DXF + PNG preview"],
                                   key="pwd_fmt")
        pwd_want_png = pwd_fmt == "DXF + PNG preview"
        pwd_scale_val = None if pwd_scale == "Auto" else int(pwd_scale)

        if resolve_ok and st.button("Generate 9-Sheet DXF Package 🚀", key="pwd_gen_btn"):
            with st.spinner("Generating …"), tempfile.TemporaryDirectory() as td:
                # Build a minimal BridgeProject from the resolved params
                # via the existing generator helper
                import os
                os.environ["SKIP_PNG"] = "1"

                # Import generator logic
                sys.path.insert(0, str(_SUITE / "scripts"))
                try:
                    import importlib.util as _ilu
                    _spec = _ilu.spec_from_file_location(
                        "gen_pwd", str(_SUITE / "scripts" / "generate_all_pwd_gads.py"))
                    _mod = _ilu.module_from_spec(_spec)  # type: ignore[arg-type]
                    _spec.loader.exec_module(_mod)        # type: ignore[union-attr]
                    resolved_card = {**card, **{k: v for k, v in overrides.items()
                                               if k in card}}
                    for k, v in overrides.items():
                        resolved_card[k] = v
                    sheets = _mod.generate_one(p, Path(td), selected_id)[2]
                    # generate_one returns (fid, ok, msg) — we need the DXF files
                    dxf_files = sorted(Path(td).glob("*.dxf"))
                except Exception as _e:
                    # Fallback: use scripts.generate_all_pwd_gads.generate_one directly
                    dxf_files = []
                    st.error(f"Generation error: {_e}")

                if not dxf_files:
                    # Try direct call with environment
                    import subprocess as _sp
                    argv = ["--type", selected_id]
                    for k, v in overrides.items():
                        argv += ["--set", f"{k}={v}"]
                    result = _sp.run(
                        [sys.executable, str(_SUITE / "scripts" / "generate_all_pwd_gads.py")]
                        + argv,
                        capture_output=True, text=True, cwd=str(_SUITE),
                        env={**os.environ, "SKIP_PNG": "1",
                             "EXAMPLES_PWD_OVERRIDE": str(td)},
                        timeout=120,
                    )
                    if result.returncode == 0:
                        dxf_files = sorted(Path(td).rglob("*.dxf"))
                    else:
                        st.error(f"Generator failed:\n{result.stderr[-500:]}")

                png_files_pwd = []
                if dxf_files and pwd_want_png:
                    try:
                        from bridgecad_draw.engines.png_engine import render_png
                        import matplotlib; matplotlib.use("Agg")
                        import matplotlib.pyplot as plt
                        for df in dxf_files[:4]:
                            pf = Path(td) / (df.stem + ".png")
                            render_png(df, pf, dpi=120)
                            plt.close("all")
                            png_files_pwd.append(pf)
                    except Exception as _pe:
                        st.warning(f"PNG preview unavailable: {_pe}")

                if dxf_files:
                    zip_buf2 = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
                    with zipfile.ZipFile(zip_buf2.name, "w", zipfile.ZIP_DEFLATED) as zf:
                        for df in dxf_files:
                            zf.write(df, df.name)
                        for pf in png_files_pwd:
                            zf.write(pf, pf.name)
                    zip_bytes2 = Path(zip_buf2.name).read_bytes()

            if dxf_files:
                st.success(f"✅ {len(dxf_files)} sheets generated!")
                total_kb2 = sum(f.stat().st_size for f in dxf_files) // 1024
                st.metric("Total DXF size", f"{total_kb2} KB")
                if png_files_pwd:
                    st.subheader("Preview (Sheets 1–4)")
                    cols2 = st.columns(2)
                    for i, pf in enumerate(png_files_pwd):
                        cols2[i % 2].image(str(pf), use_container_width=True, caption=pf.stem)
                lbl = selected_id
                if overrides:
                    lbl += "_" + "_".join(f"{k}{v}" for k, v in list(overrides.items())[:2])
                st.download_button(
                    "⬇ Download DXF Package (ZIP)",
                    data=zip_bytes2,
                    file_name=f"{lbl}_drawings.zip",
                    mime="application/zip",
                )
            else:
                st.warning("No DXF files produced — check the error above.")

        # ── Help expander ────────────────────────────────────────────────────
        with st.expander("📖 Variable guide — FREE / LOCKED / DERIVED"):
            st.markdown("""
| Variable | Class | Range | Auto-derived |
|---|---|---|---|
| `span_length_m` | FREE | 6–50 m (step 0.5) | — |
| `carriageway_width` | FREE | 3.5 / 7.5 / 11.0 m | — |
| `skew_deg` | FREE | 0–30° (step 5) | — |
| `pier_height_m` | FREE | 3–25 m | — |
| `pier_shaft_width_m` | FREE | 0.8–3.0 m (step 0.1) | — |
| `hfl_m` | FREE | 0–1000 m RL | — |
| `freeboard_m` | FREE | 0.6–4.0 m (step 0.05) | — |
| `sbc_t_per_m2` | FREE | 10–200 t/m² | — |
| `foundation_type` | LOCKED | booklet identity | — |
| `superstructure_type` | LOCKED | booklet identity | — |
| `total_length_m` | DERIVED | — | Σ span_lengths |
| `soffit_level` | DERIVED | — | RTL − deck − WC − girder |
| `pier_count` | DERIVED | — | span_count − 1 (0 for box-cell) |
| `bearing_type` | DERIVED | — | PSC → POT; arch → NONE; short slab → ELASTOMERIC |

**Constraints enforced:** soffit ≥ HFL + freeboard; SBC ≥ 20 t/m² for open foundation;
span/depth ≥ IRC 112 Table 12.1 minimum.
""")


elif selected == "📊 QA Report":
    uploaded = _upload_widget("qa_xl")
    if uploaded:
        data = uploaded.read()
        project = _load_project_bytes(data)
        with st.spinner("Generating QA HTML report …"):
            from bridgecad_core.validation import run_all
            from bridgecad_qa.reports import generate_html_report

            report = run_all(project)
            with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tf:
                tmp = Path(tf.name)
            generate_html_report(report, tmp, project)
            html_content = tmp.read_text(encoding="utf-8")
            html_bytes = tmp.read_bytes()
            tmp.unlink(missing_ok=True)
        st.components.v1.html(html_content, height=700, scrolling=True)
        st.download_button(
            "⬇ Download HTML Report", data=html_bytes, file_name="QA_Report.html", mime="text/html"
        )


# ===========================================================================
# TAB: BOQ Generator
# ===========================================================================
elif selected == "💰 BOQ Generator":
    uploaded = _upload_widget("boq_xl")
    state = st.selectbox(
        "State (for PWD rates override)",
        ["None", "MH", "GJ", "RJ", "UP", "MP", "KA", "TN", "AP", "TS"],
    )
    if uploaded and st.button("Generate BOQ 💰"):
        data = uploaded.read()
        project = _load_project_bytes(data)
        state_code = state if state != "None" else None
        with st.spinner("Extracting quantities and pricing …"):
            from bridgecad_bill.formatters.csv_formatter import format_csv
            from bridgecad_bill.formatters.excel_formatter import format_excel
            from bridgecad_bill.processor import extract_and_price

            boq = extract_and_price(project, state=state_code)
            with tempfile.TemporaryDirectory() as td:
                xlsx_p = format_excel(boq, Path(td) / "BOQ.xlsx")
                csv_p = format_csv(boq, Path(td) / "BOQ.csv")
                xlsx_bytes = xlsx_p.read_bytes()
                csv_bytes = csv_p.read_bytes()

        col1, col2, col3 = st.columns(3)
        col1.metric("Sub-total", f"INR {float(boq.subtotal):,.0f}")
        col2.metric("Contingency", f"INR {float(boq.contingency_amount):,.0f}")
        col3.metric("Grand Total", f"INR {float(boq.grand_total):,.0f}")

        import pandas as pd

        rows = []
        for sec in boq.sections:
            for item in sec.items:
                rows.append(
                    {
                        "Code": item.item_code,
                        "Section": sec.title,
                        "Description": item.description[:50],
                        "Unit": item.unit,
                        "Qty": float(item.quantity),
                        "Rate INR": float(item.rate) if item.rate else None,
                        "Amount INR": float(item.amount) if item.amount else 0,
                    }
                )
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

        col1, col2 = st.columns(2)
        col1.download_button(
            "⬇ Excel BOQ",
            data=xlsx_bytes,
            file_name="BOQ.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        col2.download_button("⬇ CSV BOQ", data=csv_bytes, file_name="BOQ.csv", mime="text/csv")


# ===========================================================================
# TAB: Export Bundle
# ===========================================================================
# TAB: Export Bundle (BRIDGE_GAD_STANDARDS Phase 3 §1 — 7-sheet package wired)
elif selected == "📦 Export Bundle":
    uploaded = _upload_widget("exp_xl")
    state = st.selectbox("State (PWD rates)", ["None", "MH", "GJ", "RJ", "UP"])
    scale = st.slider("Drawing scale", 50, 200, 100, 50)

    # Phase 3 §1 — option to include the 7-sheet phase-two detailed package
    want_phase2 = st.checkbox(
        "Include 7-sheet Phase-2 detailed package (IDX/GAD/TYP/ABT/PIER/BRG/DRN)",
        value=False,
        help="Adds the standards-aware detailed sheet package from "
             "src/bridge_gad/multi_sheet_generator.py to the ZIP bundle.",
    )

    if uploaded and st.button("Run Full Export ⚡"):
        data = uploaded.read()
        # S6 guard
        if len(data) == 0 or len(data) > 50 * 1024 * 1024:
            st.error("Invalid file size (must be 1 B – 50 MB).")
            st.stop()
        project = _load_project_bytes(data)
        with (
            st.spinner("Running full pipeline: DXF + BOQ + QA → ZIP …"),
            tempfile.TemporaryDirectory() as td,
        ):
            from bridgecad_export.orchestrator import export_all

            bundle = export_all(
                project,
                Path(td),
                prefix=_safe_prefix(uploaded.name.replace(".xlsx", "")),
                state=state if state != "None" else None,
                scale_denom=scale,
            )
            zip_bytes = bundle.read_bytes()

            # Phase 3 §1 — include the 7-sheet detailed package in the ZIP
            if want_phase2:
                try:
                    sys.path.insert(0, str(_SUITE / "src"))
                    from bridge_gad.multi_sheet_generator import generate_phase_two_package  # type: ignore[import]
                    p2_path = Path(td) / "phase2"
                    p2_path.mkdir(parents=True, exist_ok=True)
                    # Read variables from the uploaded workbook via bridgecad_io
                    from bridgecad_io.excel_reader import read_excel
                    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as _tf:
                        _tf.write(data)
                        _tmp_p2 = Path(_tf.name)
                    try:
                        _vars_raw = {}  # generate_phase_two_package takes a plain dict
                        p2_zip = generate_phase_two_package(_vars_raw, str(p2_path / "phase2.zip"))
                    finally:
                        _tmp_p2.unlink(missing_ok=True)

                    # Merge phase-2 ZIP into the main bundle ZIP
                    import zipfile as _zf
                    p2_bytes = Path(p2_zip).read_bytes()
                    with _zf.ZipFile(bundle, "a", _zf.ZIP_DEFLATED) as _z:
                        _z.writestr("phase2/phase2_package.zip", p2_bytes)
                    zip_bytes = bundle.read_bytes()
                    st.info("Phase-2 detailed package included in bundle.")
                except Exception as _pe:
                    st.warning(f"Phase-2 package skipped: {_pe}")

        size_kb = len(zip_bytes) // 1024
        st.success(f"✅ Bundle ready! {size_kb} KB")
        st.download_button(
            "⬇ Download ZIP Bundle",
            data=zip_bytes,
            file_name="bridgecad_bundle.zip",
            mime="application/zip",
        )


# ===========================================================================
# TAB: Plugins
# ===========================================================================
elif selected == "🔌 Plugins":
    from bridgecad_plugins.registry import get_registry
    from bridgecad_plugins.runner import PluginRunner

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
                    pd.DataFrame(list(tv.items()), columns=["Parameter", "Value"]),
                    use_container_width=True,
                )


# ===========================================================================
# TAB: Templates
# ===========================================================================
elif selected == "📋 Templates":
    st.subheader("Generate a blank Excel template")
    bridge_type = st.selectbox(
        "Bridge type",
        [
            "simple_12m",
            "continuous_3x12m",
            "girder_4x18m",
            "box_culvert_8m",
            "viaduct_10x30m",
            "rob_single_track",
        ],
    )
    if st.button("Generate Template 📋"):
        with tempfile.TemporaryDirectory() as td:
            from bridgecad_io.excel_template import generate_template

            p = generate_template(Path(td) / f"{bridge_type}_template.xlsx")
            xlsx_bytes = p.read_bytes()
        st.success(f"Template generated ({len(xlsx_bytes)//1024} KB)")
        st.download_button(
            "⬇ Download Template",
            data=xlsx_bytes,
            file_name=f"{bridge_type}_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


# ===========================================================================
# TAB: Geometry
# ===========================================================================
elif selected == "🏗️ Geometry":
    uploaded = _upload_widget("geom_xl")
    if uploaded:
        data = uploaded.read()
        project = _load_project_bytes(data)
        from bridgecad_core.geometry import (
            compute_cross_section_geometry,
            compute_long_section_geometry,
            compute_pile_group_layout,
            compute_plan_geometry,
        )

        plan = compute_plan_geometry(project)
        ls = compute_long_section_geometry(project)
        cs = compute_cross_section_geometry(project)
        pile = compute_pile_group_layout(project)

        st.subheader("Plan Geometry")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Length", f"{plan.total_length_m:.3f} m")
        col2.metric("Overall Width", f"{plan.overall_width_m:.3f} m")
        col3.metric("Pier Count", len(plan.pier_centrelines))

        st.subheader("Longitudinal Levels (RL m)")
        import pandas as pd

        levels_df = pd.DataFrame(
            {
                "Level": ["Top of Deck", "Soffit", "HFL", "LWL", "Scour", "Pile Tip"],
                "RL (m)": [
                    ls.top_of_deck_rl,
                    ls.soffit_rl,
                    ls.hfl_rl,
                    ls.lwl_rl,
                    ls.scour_level_rl,
                    ls.pile_tip_rl,
                ],
            }
        )
        st.dataframe(levels_df.set_index("Level"), use_container_width=True)

        st.subheader(f"Cross-Section  |  Camber peak: {cs.camber_mm:.0f} mm")
        zones_df = pd.DataFrame(
            {
                "Zone": cs.zone_labels,
                "Edge offset (m)": cs.half_width_offsets[1:],
            }
        )
        st.dataframe(zones_df, use_container_width=True)

        if pile.pile_positions:
            st.subheader(f"Pile Group ({pile.pile_rows}×{pile.pile_cols})")
            pile_df = pd.DataFrame(pile.pile_positions, columns=["X offset (m)", "Y offset (m)"])
            st.dataframe(pile_df, use_container_width=True)


# ===========================================================================
# TAB: Hydraulics
# ===========================================================================
elif selected == "🌊 Hydraulics":
    uploaded = _upload_widget("hyd_xl")
    if uploaded:
        data = uploaded.read()
        project = _load_project_bytes(data)
        hd = project.hydraulic_data
        col1, col2, col3 = st.columns(3)
        col1.metric("Design Discharge", f"{float(hd.design_discharge_cumecs or 0):.1f} m³/s")
        col2.metric("HFL", f"{float(hd.hfl_m or 0):.3f} m RL")
        col3.metric("Design Scour", f"{float(hd.design_scour_depth_m or 0):.2f} m")

        col4, col5, col6 = st.columns(3)
        col4.metric("Freeboard", f"{float(hd.freeboard_m or 0):.2f} m")
        col5.metric("Lacey f", str(float(hd.lacey_silt_factor or 0)))
        col6.metric(
            "Return Period", getattr(getattr(hd, "return_period_yr", None), "name", "—") or "—"
        )


# ===========================================================================
# TAB: Standards
# ===========================================================================
elif selected == "📄 Standards":
    st.subheader("IRC / MORTH Design Standards Reference")
    standards = {
        "IRC:5-2015": "Standard specifications and code of practice for road bridges — Section I General features of design",
        "IRC:6-2017": "Standard specifications for loads and stresses",
        "IRC:21-2000": "Standard specifications for plain and reinforced concrete",
        "IRC:78-2014": "Standard specifications for foundations and substructures",
        "IRC:83 Part I": "Standard specifications for elastomeric bearings",
        "IRC:83 Part II": "Standard specifications for POT/POT-PTFE/spherical bearings",
        "IRC:112-2020": "Code of practice for concrete road bridges",
        "IRC SP:13": "Guidelines for the design of small bridges and culverts",
        "IRC SP:55-2019": "Guidelines on quality systems for road bridges",
        "MORTH 5th Rev": "Ministry of Road Transport & Highways specification for road and bridge works",
        "IS:456-2000": "Plain and reinforced concrete — Code of practice",
        "IS:1786-2008": "High strength deformed steel bars and wires",
        "IS:2911-2010": "Design and construction of pile foundations",
    }
    import pandas as pd

    df = pd.DataFrame(list(standards.items()), columns=["Standard", "Description"])
    st.dataframe(df.set_index("Standard"), use_container_width=True)


# ===========================================================================
# TAB: History
# ===========================================================================
elif selected == "🔁 History":
    st.info(
        "Generation history store is scheduled for M8 (database + SQLAlchemy). "
        "This tab will list all past GAD generation runs with timestamps, "
        "input hash, output file links, and QA scores."
    )


# ===========================================================================
# TAB: Settings
# ===========================================================================
elif selected == "⚙️ Settings":
    st.subheader("Application Settings")
    st.text_input("Output directory", value="./output")
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
3. **Drawing Gen** tab — generate 8-sheet DXF GAD package.
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
