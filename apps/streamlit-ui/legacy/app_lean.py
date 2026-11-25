"""
Bridge GAD Generator - Lean Version
Following BridgeCanvas's winning pattern: Simple, Fast, Works
"""

import sys
import tempfile
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from bridge_gad.bridge_generator import BridgeGADGenerator

# Page config
st.set_page_config(page_title="Bridge GAD Generator", page_icon="🌉", layout="wide")

# Simple CSS
st.markdown(
    """
<style>
    .main {padding: 2rem;}
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 2rem;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Templates (from BridgeCanvas)
TEMPLATES = {
    "simple_12m": {
        "name": "Simple Span 12m",
        "description": "Single span RCC slab bridge (12m)",
        "parameters": {
            "SCALE1": 186,
            "SCALE2": 1,
            "SKEW": 0,
            "DATUM": 95,
            "TOPRL": 100,
            "LEFT": 0,
            "RIGHT": 100,
            "XINCR": 5,
            "YINCR": 1,
            "NOCH": 2,
            "NSPAN": 1,
            "LBRIDGE": 12,
            "ABTL": 0,
            "RTL": 100.5,
            "SOFL": 99.5,
            "KERBW": 0.23,
            "KERBD": 0.15,
            "CCBR": 8.0,
            "SLBTHC": 0.6,
            "SLBTHE": 0.6,
            "SLBTHT": 0.6,
            "CAPT": 100.5,
            "CAPB": 99.3,
            "CAPW": 1.2,
            "PIERTW": 1.2,
            "BATTR": 10,
            "PIERST": 5,
            "PIERN": 0,
            "SPAN1": 12,
            "FUTRL": 90,
            "FUTD": 2,
            "FUTW": 2.5,
            "FUTL": 3.5,
            "DWTH": 0.3,
            "ALCW": 0.75,
            "ALCD": 1.2,
            "ALFB": 10,
            "ALFBL": 101,
            "ALTB": 10,
            "ALTBL": 100.5,
            "ALFO": 0.5,
            "ALBB": 5,
            "ALBBL": 101.5,
            "ABTLEN": 8.46,
            "LASLAB": 3.5,
            "APWTH": 8.46,
            "APTHK": 0.2,
            "WCTH": 0.08,
            "ALFL": 95,
            "ARFL": 95,
            "ALFBR": 100.75,
            "ALTBR": 100.5,
            "ALFD": 1.5,
            "ALBBR": 101.5,
        },
    },
    "continuous_3x12m": {
        "name": "Continuous 3×12m",
        "description": "3-span continuous RCC slab (3×12m)",
        "parameters": {
            "SCALE1": 186,
            "SCALE2": 1,
            "SKEW": 0,
            "DATUM": 95,
            "TOPRL": 100,
            "LEFT": 0,
            "RIGHT": 100,
            "XINCR": 5,
            "YINCR": 1,
            "NOCH": 2,
            "NSPAN": 3,
            "LBRIDGE": 36,
            "ABTL": 0,
            "RTL": 100.98,
            "SOFL": 99.5,
            "KERBW": 0.23,
            "KERBD": 0.15,
            "CCBR": 10.5,
            "SLBTHC": 0.75,
            "SLBTHE": 0.75,
            "SLBTHT": 0.75,
            "CAPT": 100.5,
            "CAPB": 99.3,
            "CAPW": 1.2,
            "PIERTW": 1.5,
            "BATTR": 10,
            "PIERST": 5,
            "PIERN": 2,
            "SPAN1": 12,
            "FUTRL": 90,
            "FUTD": 2,
            "FUTW": 4.5,
            "FUTL": 3.5,
            "DWTH": 0.3,
            "ALCW": 0.75,
            "ALCD": 1.2,
            "ALFB": 10,
            "ALFBL": 101,
            "ALTB": 10,
            "ALTBL": 100.5,
            "ALFO": 0.5,
            "ALBB": 5,
            "ALBBL": 101.5,
            "ABTLEN": 11.0,
            "LASLAB": 3.5,
            "APWTH": 11.0,
            "APTHK": 0.2,
            "WCTH": 0.08,
            "ALFL": 95,
            "ARFL": 95,
            "ALFBR": 100.75,
            "ALTBR": 100.5,
            "ALFD": 1.5,
            "ALBBR": 101.5,
        },
    },
}

# Initialize session state
if "result" not in st.session_state:
    st.session_state.result = None


def create_template_excel(params):
    """Create Excel from template"""
    data = [[v, k, k] for k, v in params.items()]
    df = pd.DataFrame(data, columns=["Value", "Variable", "Description"])
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Parameters")
    output.seek(0)
    return output


def main():
    # Header
    st.title("🌉 Bridge GAD Generator")
    st.markdown("### Professional Bridge Design - Lean & Fast")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        mode = st.radio("Mode", ["Single File", "Templates"], help="Choose mode")

        st.divider()
        st.info("""
        **Lean Version**
        - Excel → DXF generation
        - Standard templates
        - Fast & reliable

        **No bloat, just works!**
        """)

    # Main content
    if mode == "Templates":
        st.header("📋 Bridge Templates")

        selected = st.selectbox(
            "Choose Template", list(TEMPLATES.keys()), format_func=lambda x: TEMPLATES[x]["name"]
        )

        if selected:
            template = TEMPLATES[selected]
            st.markdown(f"**{template['description']}**")

            with st.expander("📊 Parameters"):
                params_df = pd.DataFrame(
                    [{"Parameter": k, "Value": v} for k, v in template["parameters"].items()]
                )
                st.dataframe(params_df, use_container_width=True)

            excel_file = create_template_excel(template["parameters"])
            st.download_button(
                f"📥 Download {template['name']}",
                data=excel_file.getvalue(),
                file_name=f"{selected}_bridge.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
            )

    else:  # Single File mode
        st.header("📁 Upload Bridge Parameters")

        project_name = st.text_input(
            "Project Name", value=f"Bridge_{datetime.now().strftime('%Y%m%d')}"
        )

        uploaded_file = st.file_uploader(
            "Upload Excel File", type=["xlsx", "xls"], help="Excel file with bridge parameters"
        )

        if uploaded_file:
            st.success(f"✅ File uploaded: {uploaded_file.name}")

            # Preview
            with st.expander("📊 Preview Data"):
                df = pd.read_excel(uploaded_file, header=None)
                st.dataframe(df.head(20), use_container_width=True)
                uploaded_file.seek(0)

            # Generate button
            if st.button("🚀 Generate Bridge Design", type="primary"):
                with st.spinner("Generating..."):
                    try:
                        # FIX BOLT-002: use tempfile.TemporaryDirectory instead of
                        # hardcoded temp/ dir — auto-cleaned on exit, even on error
                        with tempfile.TemporaryDirectory() as _tmp:
                            tmp_path = Path(_tmp)
                            safe_name = Path(uploaded_file.name).name
                            temp_file = tmp_path / safe_name

                            with Path(temp_file).open("wb") as f:
                                f.write(uploaded_file.getbuffer())

                            gen = BridgeGADGenerator()
                            output_file = tmp_path / "bridge.dxf"

                            if gen.generate_complete_drawing(temp_file, output_file):
                                st.success("✅ Generated successfully!")
                                with Path(output_file).open("rb") as f:
                                    dxf_bytes = f.read()
                                st.download_button(
                                    "📥 Download DXF",
                                    data=dxf_bytes,
                                    file_name=f"{project_name}.dxf",
                                    mime="application/dxf",
                                )
                                st.session_state.result = {
                                    "success": True,
                                    "filename": output_file.name,
                                }
                            else:
                                st.error("❌ Generation failed")
                        # TemporaryDirectory auto-deleted here — no manual unlink needed

                    except Exception as e:
                        st.error(f"❌ Error: {e!s}")

    # Footer
    st.divider()
    st.markdown(
        """
    <div style="text-align: center; color: gray;">
        🌉 Bridge GAD Generator - Lean Version | RKS LEGAL
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
