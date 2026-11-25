"""
Ultimate Bridge GAD Generator - Integrated Application
Combines bridge drawing generation + bill generation + complete exports

Design: 2025 International Trends applied
  - Glassmorphism (frosted glass cards, translucent panels)
  - Dark Mode + Neon Accents (deep navy base, cyan/amber glows)
  - Neumorphism (soft-UI buttons and stat cards)
  - Bento Grid Layouts (compartmentalised dashboard sections)
  - Micro-interactions (CSS hover/active transitions on every interactive element)
  - Spatial depth (layered shadows, z-depth on cards)
"""

import os
import sys
import tempfile
from datetime import datetime
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))


@st.cache_resource
def _load_modules():
    from bridge_gad.advanced_features import (
        Bridge3DVisualizer,
        BridgeTemplates,
        DesignComparator,
        DesignQualityChecker,
    )
    from bridge_gad.ai_optimizer import AIDesignOptimizer, ReportGenerator
    from bridge_gad.bridge_canvas_features import (
        BRIDGE_TEMPLATES,
        batch_generate,
        batch_results_to_zip,
        cleanup_dxf_entities,
        make_phase_three_package_zip,
        make_phase_two_package_zip,
        make_template_excel,
    )
    from bridge_gad.bridge_canvas_features import (
        validate_bridge_parameters as bc_validate,
    )
    from bridge_gad.bridge_generator import BridgeGADGenerator
    from bridge_gad.multi_sheet_generator import DetailedSheetGenerator

    return (
        BridgeGADGenerator,
        BridgeTemplates,
        DesignQualityChecker,
        Bridge3DVisualizer,
        DesignComparator,
        DetailedSheetGenerator,
        AIDesignOptimizer,
        ReportGenerator,
        bc_validate,
        cleanup_dxf_entities,
        BRIDGE_TEMPLATES,
        make_template_excel,
        make_phase_two_package_zip,
        make_phase_three_package_zip,
        batch_generate,
        batch_results_to_zip,
    )


(
    BridgeGADGenerator,
    BridgeTemplates,
    DesignQualityChecker,
    Bridge3DVisualizer,
    DesignComparator,
    DetailedSheetGenerator,
    AIDesignOptimizer,
    ReportGenerator,
    bc_validate,
    cleanup_dxf_entities,
    BC_TEMPLATES,
    make_template_excel,
    make_phase_two_package_zip,
    make_phase_three_package_zip,
    batch_generate,
    batch_results_to_zip,
) = _load_modules()

st.set_page_config(
    page_title="Bridge GAD Generator",
    page_icon="🌉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# 2025 DESIGN SYSTEM — Dark Mode + Glassmorphism + Neumorphism + Bento Grid
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
/* ── 1. GLOBAL DARK BASE ─────────────────────────────────────────────────── */
:root {
    --bg-base:        #0d1117;
    --bg-surface:     #161b22;
    --bg-elevated:    #1c2333;
    --border-subtle:  rgba(255,255,255,0.08);
    --border-glow:    rgba(0,212,255,0.35);
    --neon-cyan:      #00d4ff;
    --neon-amber:     #ffb347;
    --neon-green:     #39ff14;
    --neon-purple:    #bf5fff;
    --text-primary:   #e6edf3;
    --text-secondary: #8b949e;
    --radius-lg:      16px;
    --radius-md:      10px;
    --shadow-neu-out: 6px 6px 14px rgba(0,0,0,0.6), -4px -4px 10px rgba(255,255,255,0.04);
    --shadow-neu-in:  inset 4px 4px 10px rgba(0,0,0,0.5), inset -3px -3px 8px rgba(255,255,255,0.03);
    --glass-bg:       rgba(22,27,34,0.72);
    --glass-blur:     blur(18px);
    --transition:     all 0.22s cubic-bezier(0.4,0,0.2,1);
}

/* Force dark background on Streamlit root */
.stApp, [data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0d1117 0%, #0f1923 50%, #0d1117 100%) !important;
    color: var(--text-primary) !important;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f1923 0%, #161b22 100%) !important;
    border-right: 1px solid var(--border-subtle) !important;
}

/* ── 2. GLASSMORPHISM CARDS ──────────────────────────────────────────────── */
.glass-card {
    background: var(--glass-bg);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.06);
    transition: var(--transition);
}
.glass-card:hover {
    border-color: var(--border-glow);
    box-shadow: 0 12px 40px rgba(0,212,255,0.12), inset 0 1px 0 rgba(255,255,255,0.08);
    transform: translateY(-2px);
}

/* ── 3. HERO HEADER ──────────────────────────────────────────────────────── */
.hero-header {
    background: linear-gradient(135deg, rgba(0,212,255,0.08) 0%, rgba(191,95,255,0.08) 100%);
    backdrop-filter: blur(24px);
    border: 1px solid rgba(0,212,255,0.2);
    border-radius: 20px;
    padding: 2.5rem 2rem 2rem;
    margin-bottom: 1.5rem;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.hero-header::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(ellipse at center, rgba(0,212,255,0.06) 0%, transparent 60%);
    animation: pulse-glow 4s ease-in-out infinite;
}
@keyframes pulse-glow {
    0%, 100% { opacity: 0.5; transform: scale(1); }
    50%       { opacity: 1;   transform: scale(1.05); }
}
.hero-title {
    font-size: 2.6rem;
    font-weight: 800;
    background: linear-gradient(90deg, var(--neon-cyan), var(--neon-purple), var(--neon-amber));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.5px;
    margin: 0;
    position: relative;
    z-index: 1;
    /* Reset h1 browser defaults */
    display: block;
    line-height: 1.2;
}
.hero-sub {
    color: var(--text-secondary);
    font-size: 1rem;
    margin-top: 0.5rem;
    position: relative;
    z-index: 1;
}

/* ── 4. NEUMORPHISM STAT CARDS (Bento Grid) ──────────────────────────────── */
.bento-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin: 1rem 0;
}
.neu-stat {
    background: var(--bg-elevated);
    border-radius: var(--radius-md);
    padding: 1.2rem 1rem;
    text-align: center;
    box-shadow: var(--shadow-neu-out);
    border: 1px solid var(--border-subtle);
    transition: var(--transition);
    cursor: default;
}
.neu-stat:hover {
    box-shadow: var(--shadow-neu-in);
    transform: scale(0.98);
}
.neu-stat .stat-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--neon-cyan);
    text-shadow: 0 0 12px rgba(0,212,255,0.5);
    line-height: 1;
}
.neu-stat .stat-label {
    font-size: 0.75rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.3rem;
}

/* ── 5. NEON BADGE PILLS ─────────────────────────────────────────────────── */
.badge-cyan   { display:inline-block; padding:0.2rem 0.7rem; border-radius:999px; font-size:0.72rem; font-weight:600; background:rgba(0,212,255,0.12); color:var(--neon-cyan); border:1px solid rgba(0,212,255,0.3); }
.badge-amber  { display:inline-block; padding:0.2rem 0.7rem; border-radius:999px; font-size:0.72rem; font-weight:600; background:rgba(255,179,71,0.12); color:var(--neon-amber); border:1px solid rgba(255,179,71,0.3); }
.badge-green  { display:inline-block; padding:0.2rem 0.7rem; border-radius:999px; font-size:0.72rem; font-weight:600; background:rgba(57,255,20,0.10); color:var(--neon-green); border:1px solid rgba(57,255,20,0.25); }
.badge-purple { display:inline-block; padding:0.2rem 0.7rem; border-radius:999px; font-size:0.72rem; font-weight:600; background:rgba(191,95,255,0.12); color:var(--neon-purple); border:1px solid rgba(191,95,255,0.3); }

/* ── 6. SECTION DIVIDERS WITH GLOW ──────────────────────────────────────── */
.section-title {
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--neon-cyan);
    text-shadow: 0 0 8px rgba(0,212,255,0.4);
    margin: 1.5rem 0 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(0,212,255,0.4), transparent);
}

/* ── 7. MICRO-INTERACTION BUTTONS ────────────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, rgba(0,212,255,0.15), rgba(191,95,255,0.15)) !important;
    color: var(--text-primary) !important;
    border: 1px solid rgba(0,212,255,0.3) !important;
    border-radius: var(--radius-md) !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
    transition: var(--transition) !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3) !important;
    position: relative !important;
    overflow: hidden !important;
}
.stButton > button::before {
    content: '';
    position: absolute;
    top: 0; left: -100%;
    width: 100%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent);
    transition: left 0.4s ease;
}
.stButton > button:hover {
    border-color: var(--neon-cyan) !important;
    box-shadow: 0 0 16px rgba(0,212,255,0.3), 0 4px 12px rgba(0,0,0,0.4) !important;
    transform: translateY(-1px) !important;
    color: var(--neon-cyan) !important;
}
.stButton > button:hover::before { left: 100%; }
.stButton > button:active {
    transform: translateY(0) scale(0.98) !important;
    box-shadow: var(--shadow-neu-in) !important;
}
/* Primary button — neon cyan fill */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, rgba(0,212,255,0.25), rgba(0,150,200,0.25)) !important;
    border-color: var(--neon-cyan) !important;
    box-shadow: 0 0 12px rgba(0,212,255,0.2), 0 2px 8px rgba(0,0,0,0.3) !important;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, rgba(0,212,255,0.4), rgba(0,150,200,0.4)) !important;
    box-shadow: 0 0 24px rgba(0,212,255,0.5), 0 4px 16px rgba(0,0,0,0.4) !important;
}

/* ── 8. TABS ─────────────────────────────────────────────────────────────── */
[data-testid="stTabs"] [role="tablist"] {
    background: var(--bg-elevated) !important;
    border-radius: var(--radius-md) !important;
    padding: 0.25rem !important;
    border: 1px solid var(--border-subtle) !important;
    gap: 0.15rem !important;
}
[data-testid="stTabs"] [role="tab"] {
    border-radius: 8px !important;
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    transition: var(--transition) !important;
    padding: 0.4rem 0.8rem !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, rgba(0,212,255,0.2), rgba(191,95,255,0.15)) !important;
    color: var(--neon-cyan) !important;
    box-shadow: 0 0 10px rgba(0,212,255,0.2) !important;
    border: 1px solid rgba(0,212,255,0.25) !important;
}
[data-testid="stTabs"] [role="tab"]:hover:not([aria-selected="true"]) {
    background: rgba(255,255,255,0.04) !important;
    color: var(--text-primary) !important;
}

/* ── 9. INPUTS ───────────────────────────────────────────────────────────── */
.stTextInput input, .stNumberInput input, .stSelectbox select,
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-md) !important;
    color: var(--text-primary) !important;
    transition: var(--transition) !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: var(--neon-cyan) !important;
    box-shadow: 0 0 0 2px rgba(0,212,255,0.15) !important;
}

/* ── 10. METRICS ─────────────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-md) !important;
    padding: 0.8rem 1rem !important;
    box-shadow: var(--shadow-neu-out) !important;
    transition: var(--transition) !important;
}
[data-testid="stMetric"]:hover {
    border-color: rgba(0,212,255,0.3) !important;
    box-shadow: 0 0 16px rgba(0,212,255,0.1) !important;
}
[data-testid="stMetricValue"] {
    color: var(--neon-cyan) !important;
    text-shadow: 0 0 10px rgba(0,212,255,0.4) !important;
}

/* ── 11. DATAFRAME ───────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-md) !important;
    overflow: hidden !important;
}

/* ── 12. EXPANDER ────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-md) !important;
    transition: var(--transition) !important;
}
[data-testid="stExpander"]:hover {
    border-color: rgba(0,212,255,0.2) !important;
}

/* ── 13. FILE UPLOADER ───────────────────────────────────────────────────── */
[data-testid="stFileUploader"] {
    background: var(--bg-elevated) !important;
    border: 2px dashed rgba(0,212,255,0.25) !important;
    border-radius: var(--radius-lg) !important;
    transition: var(--transition) !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--neon-cyan) !important;
    box-shadow: 0 0 20px rgba(0,212,255,0.1) !important;
}

/* ── 14. SUCCESS / ERROR / INFO ALERTS ───────────────────────────────────── */
[data-testid="stAlert"][data-baseweb="notification"] {
    border-radius: var(--radius-md) !important;
    backdrop-filter: blur(8px) !important;
}

/* ── 15. SIDEBAR WIDGETS ─────────────────────────────────────────────────── */
[data-testid="stSidebar"] .stSelectbox > div,
[data-testid="stSidebar"] .stRadio > div {
    background: var(--bg-elevated) !important;
    border-radius: var(--radius-md) !important;
}

/* ── 16. SCROLLBAR ───────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-base); }
::-webkit-scrollbar-thumb { background: rgba(0,212,255,0.3); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--neon-cyan); }

/* ── 17. DOWNLOAD BUTTON ─────────────────────────────────────────────────── */
[data-testid="stDownloadButton"] > button {
    background: linear-gradient(135deg, rgba(57,255,20,0.12), rgba(0,212,255,0.12)) !important;
    border: 1px solid rgba(57,255,20,0.3) !important;
    color: var(--neon-green) !important;
    border-radius: var(--radius-md) !important;
    font-weight: 600 !important;
    transition: var(--transition) !important;
}
[data-testid="stDownloadButton"] > button:hover {
    box-shadow: 0 0 16px rgba(57,255,20,0.25) !important;
    transform: translateY(-1px) !important;
}

/* ── 18. PROGRESS / SPINNER ──────────────────────────────────────────────── */
[data-testid="stSpinner"] { color: var(--neon-cyan) !important; }

/* ── 19. DIVIDER ─────────────────────────────────────────────────────────── */
hr { border-color: var(--border-subtle) !important; }

/* ── 20. FOOTER ──────────────────────────────────────────────────────────── */
.footer-bar {
    background: var(--glass-bg);
    backdrop-filter: var(--glass-blur);
    border-top: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: 1rem 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 2rem;
    font-size: 0.78rem;
    color: var(--text-secondary);
}
.footer-bar .footer-brand {
    color: var(--neon-cyan);
    font-weight: 700;
    text-shadow: 0 0 8px rgba(0,212,255,0.4);
}

/* ── 21. STATUS INDICATOR DOTS ───────────────────────────────────────────── */
.status-dot {
    display: inline-block;
    width: 8px; height: 8px;
    border-radius: 50%;
    margin-right: 6px;
    animation: blink 2s ease-in-out infinite;
}
.status-dot.green  { background: var(--neon-green);  box-shadow: 0 0 6px var(--neon-green); }
.status-dot.cyan   { background: var(--neon-cyan);   box-shadow: 0 0 6px var(--neon-cyan); }
.status-dot.amber  { background: var(--neon-amber);  box-shadow: 0 0 6px var(--neon-amber); }
@keyframes blink {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.4; }
}

/* ── 22. SIDEBAR BRAND CARD ──────────────────────────────────────────────── */
.sidebar-brand {
    background: linear-gradient(135deg, rgba(0,212,255,0.08), rgba(191,95,255,0.08));
    border: 1px solid rgba(0,212,255,0.15);
    border-radius: var(--radius-md);
    padding: 0.9rem 1rem;
    margin-top: 0.5rem;
    font-size: 0.8rem;
    color: var(--text-secondary);
    line-height: 1.7;
}
.sidebar-brand strong { color: var(--neon-cyan); }

/*  23. VOICE UI BUTTON  */
.voice-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: linear-gradient(135deg, rgba(191,95,255,0.15), rgba(0,212,255,0.1));
    border: 1px solid rgba(191,95,255,0.35);
    border-radius: 999px;
    padding: 0.45rem 1.1rem;
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--neon-purple);
    cursor: pointer;
    transition: var(--transition);
    user-select: none;
}
.voice-btn:hover {
    box-shadow: 0 0 16px rgba(191,95,255,0.4);
    border-color: var(--neon-purple);
    transform: scale(1.03);
}
.voice-btn.listening {
    background: linear-gradient(135deg, rgba(191,95,255,0.3), rgba(0,212,255,0.2));
    box-shadow: 0 0 20px rgba(191,95,255,0.6);
    animation: voice-pulse 1s ease-in-out infinite;
}
@keyframes voice-pulse {
    0%, 100% { box-shadow: 0 0 12px rgba(191,95,255,0.4); }
    50%       { box-shadow: 0 0 28px rgba(191,95,255,0.8); }
}
/*  24. AI SUGGESTIONS PANEL  */
.ai-suggestion {
    background: linear-gradient(135deg, rgba(0,212,255,0.06), rgba(191,95,255,0.06));
    border: 1px solid rgba(0,212,255,0.15);
    border-left: 3px solid var(--neon-cyan);
    border-radius: 0 var(--radius-md) var(--radius-md) 0;
    padding: 0.6rem 0.9rem;
    margin: 0.35rem 0;
    font-size: 0.78rem;
    color: var(--text-secondary);
    transition: var(--transition);
}
.ai-suggestion:hover {
    border-left-color: var(--neon-purple);
    color: var(--text-primary);
    background: linear-gradient(135deg, rgba(0,212,255,0.1), rgba(191,95,255,0.1));
}
.ai-suggestion strong { color: var(--neon-cyan); }
/*  25. 3D CHART CONTAINER  */
.plotly-3d-wrap {
    background: var(--glass-bg);
    backdrop-filter: var(--glass-blur);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: 0.5rem;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}

</style>
""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# HERO HEADER
# ─────────────────────────────────────────────────────────────────────────────
# WINDSURF-001 fix: use role="banner" + aria-label so screen readers
# announce the heading correctly instead of bypassing the accessibility tree.
st.markdown(
    """
<div class="hero-header" role="banner" aria-label="Bridge GAD Generator application header">
  <h1 class="hero-title" aria-level="1">🌉 Bridge GAD Generator</h1>
  <p class="hero-sub" aria-label="Feature highlights">
    <span class="badge-cyan">DXF Drawing</span>&nbsp;
    <span class="badge-amber">Bill Generation</span>&nbsp;
    <span class="badge-green">10+ Exports</span>&nbsp;
    <span class="badge-purple">AI Optimizer</span>
  </p>
</div>
""",
    unsafe_allow_html=True,
)


# PII from env vars
_contact_email = os.environ.get("CONTACT_EMAIL", "contact@example.com")
_contact_phone = os.environ.get("CONTACT_PHONE", "+91XXXXXXXXXX")

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
    <div style="text-align:center; padding:0.5rem 0 1rem;">
        <span style="font-size:2rem;">🌉</span><br>
        <span style="font-size:0.9rem; font-weight:700; color:#00d4ff; letter-spacing:0.05em;">
            BRIDGE GAD
        </span><br>
        <span style="font-size:0.7rem; color:#8b949e;">Professional Drawing Suite</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown('<p class="section-title">⚙ Configuration</p>', unsafe_allow_html=True)

    acad_version = st.selectbox(
        "AutoCAD Version",
        ["R2010", "R2006"],
        help="R2010 = DXF AC1024 (recommended). R2006 = DXF AC1018 (older CAD software).",
    )

    export_format = st.selectbox(
        "Default Export Format",
        ["dxf", "pdf", "png", "svg", "excel", "html", "csv"],
        help="Select default output file format",
    )

    drawing_standard = st.radio(
        "Drawing Standard",
        ["Modern / Generic", "PMGSY 2-Sheet Minor Bridge"],
        help=(
            "Modern = flexible single-sheet or 4/7/11-sheet package with generic "
            "title block.  PMGSY 2-Sheet = Civil 3D 2016 minor bridge layout "
            "(Sect Elev + Plan on Sheet 1, Sections + Soil Profile + Schedule + "
            "13 NOTES on Sheet 2; bearing = TAR PAPER; live load Class A-3/70R+A; "
            "scour IRC-78; weep holes 100 @ 1000c/c)."
        ),
        key="drawing_standard_radio",
    )

    st.markdown('<p class="section-title">📡 System Status</p>', unsafe_allow_html=True)
    st.markdown(
        """
    <div style="font-size:0.78rem; color:#8b949e; line-height:2;">
        <span class="status-dot green"></span>Drawing Engine &nbsp;<strong style="color:#39ff14;">Online</strong><br>
        <span class="status-dot cyan"></span>Bill Generator &nbsp;<strong style="color:#00d4ff;">Ready</strong><br>
        <span class="status-dot amber"></span>AI Optimizer &nbsp;<strong style="color:#ffb347;">Active</strong>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown('<p class="section-title">🏢 About</p>', unsafe_allow_html=True)
    st.markdown(
        f"""
    <div class="sidebar-brand">
        <strong>RKS LEGAL</strong><br>
        Techno Legal Consultants<br>
        📍 303 Vallabh Apartment, Udaipur<br>
        📧 {_contact_email}<br>
        📱 {_contact_phone}
    </div>
    """,
        unsafe_allow_html=True,
    )


# Initialize session state
if "bill_items" not in st.session_state:
    st.session_state.bill_items = []
if "history" not in st.session_state:
    st.session_state.history = []
if "drafts" not in st.session_state:
    st.session_state.drafts = []
if "usage_counts" not in st.session_state:
    st.session_state.usage_counts = {"drawing": 0, "bill": 0, "template": 0, "export": 0, "ai": 0}
if "last_params" not in st.session_state:
    st.session_state.last_params = {}
if "voice_cmd" not in st.session_state:
    st.session_state.voice_cmd = ""


#  Trend 7: Voice UI — Web Speech API (browser-native, no extra deps)
_VOICE_JS = """
<script>
(function() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return;

  let recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.lang = 'en-US';
  recognition.interimResults = false;

  const btn = document.getElementById('voice-trigger');
  if (!btn) return;

  btn.addEventListener('click', () => {
    btn.classList.add('listening');
    btn.textContent = ' Listening...';
    recognition.start();
  });

  recognition.onresult = (e) => {
    const cmd = e.results[0][0].transcript.toLowerCase().trim();
    btn.classList.remove('listening');
    btn.textContent = ' Voice Command';
    // Map spoken commands to tab indices
    const tabMap = {
      'drawing': 0, 'generate': 0, 'bill': 1, 'invoice': 1,
      'template': 2, 'quality': 3, 'check': 3, 'three d': 4,
      '3d': 4, 'compare': 5, 'ai': 6, 'optimize': 6,
      'export': 7, 'history': 8, 'help': 9
    };
    for (const [kw, idx] of Object.entries(tabMap)) {
      if (cmd.includes(kw)) {
        const tabs = document.querySelectorAll('[role=tab]');
        if (tabs[idx]) { tabs[idx].click(); break; }
      }
    }
    // Show transcript in a toast-style div
    let toast = document.getElementById('voice-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'voice-toast';
      toast.style.cssText = 'position:fixed;bottom:80px;right:24px;background:rgba(191,95,255,0.9);color:#fff;padding:0.6rem 1.2rem;border-radius:999px;font-size:0.82rem;font-weight:600;z-index:9999;transition:opacity 0.4s;';
      document.body.appendChild(toast);
    }
    toast.textContent = ' ' + cmd;
    toast.style.opacity = '1';
    setTimeout(() => { toast.style.opacity = '0'; }, 2500);
  };

  recognition.onerror = () => {
    btn.classList.remove('listening');
    btn.textContent = ' Voice Command';
  };
})();
</script>
"""

# Main interface - 10 tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs(
    [
        "📊 Drawing",
        "💰 Bill",
        "📋 Templates",
        "✅ Quality",
        "🎨 3D",
        "📊 Compare",
        "🤖 AI",
        "📤 Export",
        "📜 History",
        "ℹ️ Help",
    ]
)

# TAB 1: Drawing Generation
with tab1:
    st.markdown('<p class="section-title">📐 Bridge Drawing Generation</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1], gap="large")

    with col1:
        uploaded_file = st.file_uploader(
            "Upload Excel file with bridge parameters",
            type=["xlsx", "xls"],
            help="Excel file should contain VALUE, VARIABLE, DESCRIPTION columns",
            key="drawing_upload",
        )

        if uploaded_file:
            st.success("✅ File uploaded successfully")
            _df_raw = pd.read_excel(uploaded_file, header=None)
            uploaded_file.seek(0)

            with st.expander("👁️ Preview Data"):
                st.dataframe(_df_raw.head(20), use_container_width=True)

    with col2:
        st.markdown('<p class="section-title">📊 Quick Stats</p>', unsafe_allow_html=True)
        if uploaded_file:
            try:
                _df_stats = _df_raw.copy()
                _df_stats.columns = ["Value", "Variable", "Description"]
                var_dict = _df_stats.set_index("Variable")["Value"].to_dict()
                _spans = int(var_dict.get("NSPAN", 0))
                _span_len = float(var_dict.get("SPAN1", 0))
                _width = float(var_dict.get("CCBR", 0))
                st.markdown(
                    f"""
                <div class="bento-grid">
                    <div class="neu-stat">
                        <div class="stat-value">{_spans}</div>
                        <div class="stat-label">Spans</div>
                    </div>
                    <div class="neu-stat">
                        <div class="stat-value">{_span_len:.0f}<span style="font-size:0.9rem">m</span></div>
                        <div class="stat-label">Span Len</div>
                    </div>
                    <div class="neu-stat">
                        <div class="stat-value">{_width:.1f}<span style="font-size:0.9rem">m</span></div>
                        <div class="stat-label">Width</div>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
            except Exception as _e:
                st.warning(f"Could not parse stats: {_e}")
        else:
            st.markdown(
                """
            <div class="glass-card" style="text-align:center;padding:2rem 1rem;">
                <span style="font-size:2.5rem;">📂</span><br>
                <span style="color:#8b949e;font-size:0.85rem;">Upload an Excel file<br>to see bridge stats</span>
            </div>
            """,
                unsafe_allow_html=True,
            )

    if uploaded_file:
        st.markdown('<p class="section-title">🚀 Generate</p>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            generate_btn = st.button(
                "🚀 Generate Drawing", use_container_width=True, key="gen_drawing", type="primary"
            )
        with col2:
            batch_mode = st.checkbox("📦 Batch Mode (All Formats)")
        with col3:
            multi_sheet = st.checkbox("📋 4-Sheet Package")

        if generate_btn:
            with st.spinner("🔄 Generating bridge drawing..."):
                try:
                    with tempfile.TemporaryDirectory() as temp_dir:
                        temp_path = Path(temp_dir)
                        excel_path = temp_path / Path(uploaded_file.name).name
                        with Path(excel_path).open("wb") as f:
                            f.write(uploaded_file.getbuffer())

                        gen = BridgeGADGenerator(acad_version=acad_version)

                        # ── PMGSY route: produce 2-sheet ZIP (Sheet 01 OF 02 + Sheet 02 OF 02)
                        is_pmgsy = drawing_standard == "PMGSY 2-Sheet Minor Bridge"
                        if is_pmgsy:
                            try:
                                from bridge_gad.bridge_canvas_features import (
                                    make_phase_two_package_zip,
                                )
                                from bridge_gad.io_utils import (
                                    read_input_excel,
                                )

                                # Read variables from uploaded Excel to merge with
                                # pmgsy_7x9 defaults (user sheet wins on overlap)
                                _raw = read_input_excel(str(excel_path))
                                _user_vars: dict[str, object] = {}
                                for _r in _raw.itertuples(index=False):
                                    if len(_r) < 2:
                                        continue
                                    _v, _k = _r[0], _r[1]
                                    if _k in ("Variable", None, "") or pd.isna(_k):
                                        continue
                                    _user_vars[str(_k)] = _v
                                # Prefer pmgsy_7x9 template baseline, then overlay user file
                                _tmpl = BC_TEMPLATES.get("pmgsy_7x9", {}).get("parameters", {})
                                _merged = dict(_tmpl)
                                _merged.update(_user_vars) if hasattr(_merged, "update") else None
                                _pkg_bytes = make_phase_two_package_zip(_merged)
                                st.success("✅ PMGSY 2-Sheet Package generated successfully!")
                                _download_label = "📦 Download PMGSY 2-Sheet Package (ZIP)"
                                _download_bytes = _pkg_bytes
                                _download_name = (
                                    f"01-GAD-AT-CH-{_merged.get('PROJECT_CODE', 'XXXX')}-7X9-0"
                                    f"_PMGSY_package.zip"
                                )
                                _download_mime = "application/zip"
                                _file_size_kb = len(_pkg_bytes) / 1024
                                _display_name = Path(_download_name).name
                                st.session_state.history.append(
                                    {
                                        "type": "PMGSY Package",
                                        "name": uploaded_file.name,
                                        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                        "format": "ZIP (2 sheets)",
                                        "size": _file_size_kb,
                                    }
                                )
                                # Store merged params for downstream tabs
                                try:
                                    from bridge_gad.calc_engine import CalcEngine

                                    _eng = CalcEngine.with_bridge_defaults()
                                    _eng.load(_merged)
                                    st.session_state.last_params = _eng.recalculate()
                                except Exception:
                                    st.session_state.last_params = dict(_merged)
                            except Exception as _pge:
                                st.warning(
                                    f"PMGSY package route fell back to single sheet "
                                    f"({_pge.__class__.__name__}: {_pge}).  Reverting to "
                                    "generic generator."
                                )
                                is_pmgsy = False

                        if not is_pmgsy:
                            # ── Generic / Modern route ───────────────────────────────
                            output_file = temp_path / f"bridge_gad.{export_format}"
                            if gen.generate_complete_drawing(excel_path, output_file):
                                st.success("✅ Drawing generated successfully!")
                                _file_size_kb = output_file.stat().st_size / 1024
                                st.markdown(
                                    f"""
                                <div class="glass-card" style="display:flex;align-items:center;gap:1rem;">
                                    <span style="font-size:2rem;">📁</span>
                                    <div>
                                        <div style="color:#00d4ff;font-weight:700;">bridge_gad.{export_format}</div>
                                        <div style="color:#8b949e;font-size:0.8rem;">{_file_size_kb:.1f} KB &nbsp;·&nbsp; {acad_version}</div>
                                    </div>
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )

                                with Path(output_file).open("rb") as f:
                                    _file_bytes = f.read()
                                _mime_map = {
                                    "dxf": "application/dxf",
                                    "pdf": "application/pdf",
                                    "png": "image/png",
                                    "svg": "image/svg+xml",
                                    "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    "csv": "text/csv",
                                    "html": "text/html",
                                }
                                _download_label = f"⬇️ Download {export_format.upper()}"
                                _download_bytes = _file_bytes
                                _download_name = f"bridge_drawing.{export_format}"
                                _download_mime = _mime_map.get(
                                    export_format, "application/octet-stream"
                                )
                                _display_name = _download_name

                                st.session_state.history.append(
                                    {
                                        "type": "Drawing",
                                        "name": uploaded_file.name,
                                        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                        "format": export_format,
                                        "size": _file_size_kb,
                                    }
                                )
                                # Phase 6: store params for CalcEngine / Quality / 3D tabs
                                try:
                                    from bridge_gad.calc_engine import CalcEngine

                                    _engine = CalcEngine.with_bridge_defaults()
                                    _engine.load(gen.variables if hasattr(gen, "variables") else {})
                                    _calc = _engine.recalculate()
                                    st.session_state.last_params = _calc
                                except Exception:
                                    st.session_state.last_params = getattr(gen, "variables", {})
                                # BridgeCanvas DXF cleanup — remove orphan/degenerate entities
                                try:
                                    _cleanup = cleanup_dxf_entities(gen.doc)
                                    _total_cleaned = sum(_cleanup.values())
                                    if _total_cleaned:
                                        st.caption(
                                            f"🧹 Cleaned {_total_cleaned} degenerate entities from DXF"
                                        )
                                except Exception:
                                    pass
                            else:
                                st.error("❌ Failed to generate drawing")
                                _download_bytes = None

                        # Render the one and only download result (from either route)
                        if not is_pmgsy and locals().get("_download_bytes") is None:
                            pass  # failed above — already shown error
                        else:
                            st.download_button(
                                label=_download_label,
                                data=_download_bytes,
                                file_name=_download_name,
                                mime=_download_mime,
                                type="primary",
                                use_container_width=True,
                            )
                except Exception as e:
                    st.error(f"❌ Error: {e!s}")

# TAB 2: Bill Generation
with tab2:
    st.markdown(
        '<p class="section-title">💰 Professional Bill Generation</p>', unsafe_allow_html=True
    )
    st.markdown(
        """
    <div class="glass-card" style="padding:0.8rem 1.2rem; margin-bottom:0.5rem;">
        <span class="badge-amber">Statutory Compliant</span>&nbsp;
        <span class="badge-cyan">Hierarchical Items</span>&nbsp;
        <span class="badge-green">Multi-format Export</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown('<p class="section-title">📋 Project Details</p>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        project_name = st.text_input("Project Name *", key="bill_project")
        contractor_name = st.text_input("Contractor Name *", key="bill_contractor")
    with col2:
        bill_date = st.date_input("Bill Date", key="bill_date")
        tender_premium = st.number_input(
            "Tender Premium (%)", value=4.0, min_value=0.0, max_value=100.0, key="bill_premium"
        )

    # Fast Mode — FIX LOVABLE-002: wire up test file selection
    st.markdown("### ⚡ Fast Mode")
    _FAST_MODE_TEMPLATES = {
        "Sample Bridge Bill": [
            {
                "itemNo": "001",
                "description": "Earthwork in excavation",
                "quantity": 150.0,
                "rate": 250.0,
                "level": 0,
            },
            {
                "itemNo": "002",
                "description": "PCC M15 in foundation",
                "quantity": 45.0,
                "rate": 4800.0,
                "level": 0,
            },
            {
                "itemNo": "003",
                "description": "RCC M30 in pier",
                "quantity": 30.0,
                "rate": 6500.0,
                "level": 0,
            },
        ],
        "Highway Project": [
            {
                "itemNo": "001",
                "description": "Subgrade preparation",
                "quantity": 500.0,
                "rate": 120.0,
                "level": 0,
            },
            {
                "itemNo": "002",
                "description": "WMM layer 250mm",
                "quantity": 200.0,
                "rate": 850.0,
                "level": 0,
            },
        ],
        "Urban Development": [
            {
                "itemNo": "001",
                "description": "Box culvert 2x2m",
                "quantity": 10.0,
                "rate": 45000.0,
                "level": 0,
            },
            {
                "itemNo": "002",
                "description": "Approach road",
                "quantity": 80.0,
                "rate": 1200.0,
                "level": 0,
            },
        ],
    }
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_test = st.selectbox(
            "Load test file", ["", *list(_FAST_MODE_TEMPLATES.keys())], key="fast_mode"
        )
        if selected_test and st.button("📂 Load", key="load_fast"):
            st.session_state.bill_items = [dict(i) for i in _FAST_MODE_TEMPLATES[selected_test]]
            st.rerun()
    with col2:
        if st.button("🎲 Random Quantities", key="random_qty"):
            import random

            for item in st.session_state.bill_items:
                item["quantity"] = round(random.uniform(10, 500), 1)
                item["rate"] = round(random.uniform(100, 10000), 0)
            st.rerun()

    # Bill Items
    st.markdown("### 📋 Bill Items")
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("➕ Add Item", key="add_item"):
            st.session_state.bill_items.append(
                {
                    "itemNo": f"{len(st.session_state.bill_items) + 1:03d}",
                    "description": "",
                    "quantity": 0.0,
                    "rate": 0.0,
                    "unit": "",
                    "level": 0,
                }
            )
            st.rerun()

    # FIX WINDSURF-002: use visible labels (not collapsed) for accessibility
    if st.session_state.bill_items:
        _level_names = ["Main Item", "Sub-item", "Sub-sub-item"]
        for idx, item in enumerate(st.session_state.bill_items):
            with st.expander(
                f"Item {item['itemNo']} — {item['description'] or '(no description)'}",
                expanded=True,
            ):
                c1, c2, c3, c4, c5, c6 = st.columns([1, 3, 1, 1, 1, 1])
                with c1:
                    item["itemNo"] = st.text_input(
                        "Item No.", value=item["itemNo"], key=f"no_{idx}"
                    )
                with c2:
                    item["description"] = st.text_input(
                        "Description", value=item["description"], key=f"desc_{idx}"
                    )
                with c3:
                    item["quantity"] = st.number_input(
                        "Qty", value=item["quantity"], key=f"qty_{idx}", min_value=0.0
                    )
                with c4:
                    item["rate"] = st.number_input(
                        "Rate (₹)", value=item["rate"], key=f"rate_{idx}", min_value=0.0
                    )
                with c5:
                    item["level"] = st.selectbox(
                        "Level",
                        [0, 1, 2],
                        index=item.get("level", 0),
                        key=f"level_{idx}",
                        format_func=lambda x: _level_names[x],
                    )
                with c6:
                    st.write("")
                    if st.button("🗑️ Delete", key=f"del_{idx}"):
                        st.session_state.bill_items.pop(idx)
                        st.rerun()
    else:
        st.info("No items added yet. Click 'Add Item' to start.")

    # Calculate totals
    if st.session_state.bill_items:
        valid_items = [i for i in st.session_state.bill_items if i["quantity"] > 0]
        subtotal = sum(i["quantity"] * i["rate"] for i in valid_items)
        premium = subtotal * (tender_premium / 100)
        net_payable = subtotal + premium

        st.markdown("### 💰 Bill Summary")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Items", len(valid_items))
        with c2:
            st.metric("Subtotal", f"₹{subtotal:,.2f}")
        with c3:
            st.metric("Premium", f"₹{premium:,.2f}")
        with c4:
            st.metric("Net Payable", f"₹{net_payable:,.2f}")

        # FIX LOVABLE-003: export buttons produce real files
        st.markdown("### 📤 Export Bill")
        _bill_df = pd.DataFrame(
            [
                {
                    "Item No": i["itemNo"],
                    "Description": i["description"],
                    "Qty": i["quantity"],
                    "Rate (₹)": i["rate"],
                    "Amount (₹)": i["quantity"] * i["rate"],
                    "Level": _level_names[i.get("level", 0)],
                }
                for i in valid_items
            ]
        )
        _summary_row = pd.DataFrame(
            [
                {
                    "Item No": "",
                    "Description": "SUBTOTAL",
                    "Qty": "",
                    "Rate (₹)": "",
                    "Amount (₹)": subtotal,
                    "Level": "",
                }
            ]
        )
        _premium_row = pd.DataFrame(
            [
                {
                    "Item No": "",
                    "Description": f"Premium @ {tender_premium}%",
                    "Qty": "",
                    "Rate (₹)": "",
                    "Amount (₹)": premium,
                    "Level": "",
                }
            ]
        )
        _total_row = pd.DataFrame(
            [
                {
                    "Item No": "",
                    "Description": "NET PAYABLE",
                    "Qty": "",
                    "Rate (₹)": "",
                    "Amount (₹)": net_payable,
                    "Level": "",
                }
            ]
        )
        _full_df = pd.concat([_bill_df, _summary_row, _premium_row, _total_row], ignore_index=True)

        _excel_buf = BytesIO()
        with pd.ExcelWriter(_excel_buf, engine="openpyxl") as _w:
            _full_df.to_excel(_w, index=False, sheet_name="Bill")
        _excel_buf.seek(0)

        _csv_data = _full_df.to_csv(index=False).encode("utf-8")

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.download_button(
                "📊 Excel",
                data=_excel_buf.getvalue(),
                file_name=f"{project_name or 'bill'}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="export_excel",
            )
        with c2:
            st.info("PDF export requires reportlab — use Excel for now.")
        with c3:
            _html_data = _full_df.to_html(index=False).encode("utf-8")
            st.download_button(
                "🌐 HTML",
                data=_html_data,
                file_name=f"{project_name or 'bill'}.html",
                mime="text/html",
                key="export_html",
            )
        with c4:
            st.download_button(
                "📋 CSV",
                data=_csv_data,
                file_name=f"{project_name or 'bill'}.csv",
                mime="text/csv",
                key="export_csv",
            )
        with c5:
            import io as _io
            import zipfile

            _zip_buf = _io.BytesIO()
            with zipfile.ZipFile(_zip_buf, "w") as _zf:
                _zf.writestr(f"{project_name or 'bill'}.xlsx", _excel_buf.getvalue())
                _zf.writestr(f"{project_name or 'bill'}.csv", _csv_data)
            _zip_buf.seek(0)
            st.download_button(
                "📦 ZIP",
                data=_zip_buf.getvalue(),
                file_name=f"{project_name or 'bill'}.zip",
                mime="application/zip",
                key="export_zip",
            )

    # Draft management — FIX REPLIT-003: load draft actually restores items
    st.markdown("### 💾 Draft Management")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("💾 Save Draft", key="save_draft"):
            if project_name and contractor_name:
                st.session_state.drafts.append(
                    {
                        "name": project_name,
                        "contractor": contractor_name,
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "items": [dict(i) for i in st.session_state.bill_items],
                    }
                )
                st.success("Draft saved!")
                st.session_state.usage_counts["bill"] += 1  # Trend 5
            else:
                st.error("Project and contractor names required")
    with c2:
        if st.session_state.drafts:
            draft_names = [d["name"] for d in st.session_state.drafts]
            selected_draft = st.selectbox("Load Draft", ["", *draft_names], key="load_draft")
            if selected_draft and st.button("📂 Restore", key="restore_draft"):
                _draft = next(
                    (d for d in st.session_state.drafts if d["name"] == selected_draft), None
                )
                if _draft:
                    st.session_state.bill_items = [dict(i) for i in _draft["items"]]
                    st.rerun()
    with c3:
        if st.button("🗑️ Clear All", key="clear_all"):
            st.session_state.bill_items = []
            st.rerun()


# TAB 3: Templates
with tab3:
    st.markdown('<p class="section-title">🎯 Quick-Start Templates</p>', unsafe_allow_html=True)
    st.markdown(
        """
    <div class="glass-card" style="padding:0.8rem 1.2rem; margin-bottom:0.5rem;">
        5 standard bridge templates from BridgeCanvas. Download as Excel, modify if needed, then upload in Tab 1.
    </div>
    """,
        unsafe_allow_html=True,
    )

    _t3_col1, _t3_col2 = st.columns([2, 1])
    with _t3_col1:
        _t3_sel = st.selectbox(
            "Choose Template",
            list(BC_TEMPLATES.keys()),
            format_func=lambda x: BC_TEMPLATES[x]["name"],
            key="bc_template_sel",
        )
    if _t3_sel:
        _t3_tmpl = BC_TEMPLATES[_t3_sel]
        with _t3_col2:
            st.metric("Parameters", len(_t3_tmpl["parameters"]))
        st.markdown(f"**{_t3_tmpl['description']}**")

        # IRC quick-validate the template
        _t3_valid = bc_validate(_t3_tmpl["parameters"])
        _t3_score = _t3_valid["score"]
        _t3_color = "#39ff14" if _t3_score >= 80 else "#ffb347" if _t3_score >= 60 else "#ff4444"
        st.markdown(
            f'<span style="color:{_t3_color};font-weight:700;">IRC Compliance: {_t3_score}/100</span>',
            unsafe_allow_html=True,
        )

        with st.expander("📊 Parameters"):
            st.dataframe(
                pd.DataFrame(
                    [{"Parameter": k, "Value": v} for k, v in _t3_tmpl["parameters"].items()]
                ),
                use_container_width=True,
            )

        st.download_button(
            f"📥 Download {_t3_tmpl['name']} Excel",
            data=make_template_excel(_t3_tmpl["parameters"]),
            file_name=f"{_t3_sel}_bridge.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )

        _t3_include_p3 = st.checkbox(
            "Include Phase 3 Detail Sheets (11-sheet submission bundle)",
            value=False,
            help=(
                "Adds 4 consultant-grade detail sheets after the standard 7-sheet "
                "GAD set: BRG-DET Bearing Plan+Section, EXPJ-DET Expansion Joint, "
                "WING-DET Wing/Return Wall + Rebar, DRN-DET Scupper + Downtake. "
                "All indicative proportions on sheets 8–11 are ring-fenced with a "
                "TBC_BY_ENGINEER stamp so no invented data reaches the reviewer."
            ),
            key=f"p3_toggle_{_t3_sel}",
        )

        if _t3_include_p3:
            _t3_pkg_bytes = make_phase_three_package_zip(_t3_tmpl["parameters"])
            _t3_pkg_label = "📦 Download Phase 3 ZIP (11-sheet + Details)"
            _t3_pkg_fname = f"{_t3_sel}_bridge_phase3.zip"
        else:
            _t3_pkg_bytes = make_phase_two_package_zip(_t3_tmpl["parameters"])
            _t3_pkg_label = "📦 Download Phase 2 ZIP (7-sheet)"
            _t3_pkg_fname = f"{_t3_sel}_bridge_phase2.zip"

        st.download_button(
            _t3_pkg_label,
            data=_t3_pkg_bytes,
            file_name=_t3_pkg_fname,
            mime="application/zip",
            key=f"pkg_dl_{_t3_sel}",
        )

    st.markdown('<p class="section-title">📦 Batch Processing</p>', unsafe_allow_html=True)
    _t3_batch_files = st.file_uploader(
        "Upload multiple Excel files for batch DXF generation",
        type=["xlsx", "xls"],
        accept_multiple_files=True,
        key="batch_upload",
    )
    if _t3_batch_files:
        st.info(f"{len(_t3_batch_files)} file(s) queued")
        if st.button("🚀 Generate All (Batch)", key="batch_gen", type="primary"):
            with st.spinner(f"Generating {len(_t3_batch_files)} drawings…"):
                _t3_inputs = [(f.name, f.read()) for f in _t3_batch_files]
                _t3_results = batch_generate(_t3_inputs)
                _t3_ok = sum(1 for r in _t3_results if r["success"])
                st.success(f"✅ {_t3_ok}/{len(_t3_results)} generated")
                if _t3_ok:
                    _t3_zip = batch_results_to_zip(_t3_results)
                    st.download_button(
                        "📦 Download All DXF (ZIP)",
                        data=_t3_zip,
                        file_name=f"batch_bridge_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                        mime="application/zip",
                    )
                for _r in _t3_results:
                    _icon = "✅" if _r["success"] else "❌"
                    with st.expander(f"{_icon} {_r['filename']}"):
                        if _r["success"]:
                            st.download_button(
                                "📥 Download DXF",
                                data=_r["dxf_bytes"],
                                file_name=Path(_r["filename"]).stem + ".dxf",
                                mime="application/dxf",
                                key=f"batch_dl_{_r['filename']}",
                            )
                        else:
                            st.error(_r["error"])

# FIX LOVABLE-001: Tabs 4-7 now show real content instead of blank placeholders
with tab4:
    st.markdown('<p class="section-title">✅ Design Quality Checker</p>', unsafe_allow_html=True)
    st.markdown("Validate your bridge design against IRC & IS standards.")
    _t7_params = st.session_state.get("last_params", {})
    if _t7_params:
        checker = DesignQualityChecker(var_dict)
        result = checker.validate()
        score = result.get("compliance_score", 0)
        st.metric("Compliance Score", f"{score}/100")
        if result.get("critical_issues"):
            st.error("Critical Issues")
            for issue in result["critical_issues"]:
                st.write(f"❌ {issue}")
        if result.get("warnings"):
            st.warning("Warnings")
            for w in result["warnings"]:
                st.write(f"⚠️ {w}")
        if not result.get("critical_issues") and not result.get("warnings"):
            st.success("✅ Design passes all checks!")

        # BridgeCanvas IRC/IS validator — second opinion
        st.markdown(
            '<p class="section-title">🏛️ IRC/IS Standards Check (BridgeCanvas)</p>',
            unsafe_allow_html=True,
        )
        _bc_result = bc_validate(var_dict)
        _bc_score = _bc_result["score"]
        _bc_color = "#39ff14" if _bc_score >= 80 else "#ffb347" if _bc_score >= 60 else "#ff4444"
        st.markdown(
            f'<span style="color:{_bc_color};font-weight:700;font-size:1.1rem;">IRC Score: {_bc_score}/100</span>',
            unsafe_allow_html=True,
        )
        for _ci in _bc_result["critical_issues"]:
            st.error(_ci)
        for _wi in _bc_result["warnings"]:
            st.warning(_wi)
        if not _bc_result["critical_issues"] and not _bc_result["warnings"]:
            st.success("✅ Passes all IRC/IS checks")
    else:
        st.info(
            "Upload and generate a drawing in Tab 1 first, then return here for quality checks."
        )

with tab5:
    st.markdown(
        '<p class="section-title"> Spatial 3D Bridge Visualization</p>', unsafe_allow_html=True
    )
    _v = st.session_state.get("last_params", {})
    if _v:
        try:
            import numpy as np
            import plotly.graph_objects as go

            _nspan = int(_v.get("NSPAN", 3))
            _span1 = float(_v.get("SPAN1", 12))
            _ccbr = float(_v.get("CCBR", 11.1))
            _slbthe = float(_v.get("SLBTHE", 0.75))
            _rtl = float(_v.get("RTL", 110.98))
            _datum = float(_v.get("DATUM", 100))
            _piertw = float(_v.get("PIERTW", 1.2))
            _futd = float(_v.get("FUTD", 1.0))
            _futw = float(_v.get("FUTW", 4.5))

            _total_len = _nspan * _span1
            _deck_h = _rtl - _datum

            #  Deck slab surface
            _xs = np.linspace(0, _total_len, max(_nspan * 8, 16))
            _ys = np.linspace(0, _ccbr, 8)
            _Xd, _Yd = np.meshgrid(_xs, _ys)
            _Zd_top = np.full_like(_Xd, _deck_h)
            _Zd_bot = np.full_like(_Xd, _deck_h - _slbthe)

            _fig = go.Figure()

            # Deck top surface
            _fig.add_trace(
                go.Surface(
                    x=_Xd,
                    y=_Yd,
                    z=_Zd_top,
                    colorscale=[[0, "rgba(0,212,255,0.7)"], [1, "rgba(0,150,200,0.9)"]],
                    showscale=False,
                    name="Deck Top",
                    lighting={"ambient": 0.6, "diffuse": 0.8, "specular": 0.3},
                    contours={"z": {"show": True, "color": "rgba(255,255,255,0.15)", "width": 1}},
                )
            )
            # Deck soffit
            _fig.add_trace(
                go.Surface(
                    x=_Xd,
                    y=_Yd,
                    z=_Zd_bot,
                    colorscale=[[0, "rgba(0,100,150,0.5)"], [1, "rgba(0,80,120,0.6)"]],
                    showscale=False,
                    name="Deck Soffit",
                    opacity=0.6,
                )
            )

            #  Piers
            for _i in range(1, _nspan):
                _px = _i * _span1
                _pier_xs = [
                    _px - _piertw / 2,
                    _px + _piertw / 2,
                    _px + _piertw / 2,
                    _px - _piertw / 2,
                    _px - _piertw / 2,
                ]
                _pier_ys_l = [_ccbr * 0.3] * 5
                _pier_ys_r = [_ccbr * 0.7] * 5
                _pier_zs = [0, 0, _deck_h - _slbthe, _deck_h - _slbthe, 0]
                for _py_val in [_ccbr * 0.3, _ccbr * 0.7]:
                    _fig.add_trace(
                        go.Scatter3d(
                            x=_pier_xs,
                            y=[_py_val] * 5,
                            z=_pier_zs,
                            mode="lines",
                            line={"color": "#ffb347", "width": 4},
                            name=f"Pier {_i}",
                            showlegend=(_i == 1 and _py_val == _ccbr * 0.3),
                        )
                    )
                # Pier cap
                _fig.add_trace(
                    go.Mesh3d(
                        x=[
                            _px - _piertw / 2,
                            _px + _piertw / 2,
                            _px + _piertw / 2,
                            _px - _piertw / 2,
                        ]
                        * 2,
                        y=[_ccbr * 0.2, _ccbr * 0.2, _ccbr * 0.8, _ccbr * 0.8] * 2,
                        z=[_deck_h - _slbthe - 0.3] * 4 + [_deck_h - _slbthe] * 4,
                        color="#ffb347",
                        opacity=0.85,
                        name="Pier Cap",
                        showlegend=False,
                    )
                )

            #  Abutments
            for _ax, _label in [(0, "Left Abt"), (_total_len, "Right Abt")]:
                _fig.add_trace(
                    go.Mesh3d(
                        x=[_ax - 0.75, _ax + 0.75, _ax + 0.75, _ax - 0.75] * 2,
                        y=[0, 0, _ccbr, _ccbr] * 2,
                        z=[0] * 4 + [_deck_h] * 4,
                        color="#39ff14",
                        opacity=0.5,
                        name=_label,
                        showlegend=True,
                    )
                )

            #  Footing outlines
            for _i in range(1, _nspan):
                _px = _i * _span1
                _fig.add_trace(
                    go.Scatter3d(
                        x=[
                            _px - _futw / 2,
                            _px + _futw / 2,
                            _px + _futw / 2,
                            _px - _futw / 2,
                            _px - _futw / 2,
                        ],
                        y=[_ccbr * 0.1, _ccbr * 0.1, _ccbr * 0.9, _ccbr * 0.9, _ccbr * 0.1],
                        z=[-_futd] * 5,
                        mode="lines",
                        line={"color": "rgba(191,95,255,0.7)", "width": 3},
                        name="Footing",
                        showlegend=(_i == 1),
                    )
                )

            #  Layout
            _fig.update_layout(
                paper_bgcolor="rgba(13,17,23,0)",
                plot_bgcolor="rgba(13,17,23,0)",
                scene={
                    "bgcolor": "rgba(13,17,23,0.95)",
                    "xaxis": {
                        "title": "Length (m)",
                        "gridcolor": "rgba(255,255,255,0.06)",
                        "showbackground": True,
                        "backgroundcolor": "rgba(0,0,0,0.3)",
                        "color": "#8b949e",
                    },
                    "yaxis": {
                        "title": "Width (m)",
                        "gridcolor": "rgba(255,255,255,0.06)",
                        "showbackground": True,
                        "backgroundcolor": "rgba(0,0,0,0.3)",
                        "color": "#8b949e",
                    },
                    "zaxis": {
                        "title": "Height (m)",
                        "gridcolor": "rgba(255,255,255,0.06)",
                        "showbackground": True,
                        "backgroundcolor": "rgba(0,0,0,0.3)",
                        "color": "#8b949e",
                    },
                    "camera": {"eye": {"x": 1.6, "y": -1.6, "z": 0.9}},
                    "aspectmode": "data",
                },
                legend={
                    "bgcolor": "rgba(22,27,34,0.8)",
                    "bordercolor": "rgba(0,212,255,0.2)",
                    "borderwidth": 1,
                    "font": {"color": "#8b949e", "size": 11},
                },
                margin={"l": 0, "r": 0, "t": 0, "b": 0},
                height=520,
            )

            # Bento stats row
            _vol = _total_len * _ccbr * _slbthe
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Total Length", f"{_total_len:.0f} m")
            with c2:
                st.metric("Deck Width", f"{_ccbr:.1f} m")
            with c3:
                st.metric("Deck Volume", f"{_vol:.0f} m3")
            with c4:
                st.metric("Piers", _nspan - 1)

            st.markdown('<div class="plotly-3d-wrap">', unsafe_allow_html=True)
            st.plotly_chart(
                _fig,
                use_container_width=True,
                config={
                    "displayModeBar": True,
                    "modeBarButtonsToRemove": ["toImage"],
                    "displaylogo": False,
                    "scrollZoom": True,
                },
            )
            st.markdown("</div>", unsafe_allow_html=True)
            st.caption("Drag to rotate    Scroll to zoom    Double-click to reset view")

        except Exception as _e3d:
            st.error(f"3D render error: {_e3d}")
    else:
        st.markdown(
            """
        <div class="glass-card" style="text-align:center;padding:3rem 1rem;">
            <span style="font-size:3rem;"></span><br><br>
            <span style="color:#8b949e;">Generate a drawing in Tab 1 first<br>
            to see the interactive 3D bridge model here.</span>
        </div>
        """,
            unsafe_allow_html=True,
        )
with tab6:
    st.markdown('<p class="section-title">📊 Design Comparison</p>', unsafe_allow_html=True)
    st.markdown("Compare two bridge parameter sets side by side.")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Design A** — upload Excel")
        file_a = st.file_uploader("Design A", type=["xlsx", "xls"], key="cmp_a")
    with c2:
        st.markdown("**Design B** — upload Excel")
        file_b = st.file_uploader("Design B", type=["xlsx", "xls"], key="cmp_b")
    if file_a and file_b:

        def _read_vars(f):
            df = pd.read_excel(f, header=None)
            if df.shape[1] >= 3:
                df.columns = ["Value", "Variable", "Description"]
                return df.set_index("Variable")["Value"].to_dict()
            return {}

        d1, d2 = _read_vars(file_a), _read_vars(file_b)
        comparator = DesignComparator(d1, d2)
        st.text(comparator.get_summary())
    else:
        st.info("Upload two Excel files above to compare designs.")

with tab7:
    st.markdown('<p class="section-title">🤖 AI Design Optimizer</p>', unsafe_allow_html=True)
    st.markdown("Get optimization recommendations based on IRC standards.")
    if "var_dict" in dir() and var_dict:
        optimizer = AIDesignOptimizer(_t7_params)
        analysis = optimizer.analyze_design()
        opt_result = optimizer.optimize()
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Efficiency Score", f"{analysis.get('efficiency_score', 0)}/100")
        with c2:
            st.metric("Cost Potential Saving", f"{analysis.get('cost_potential', 0)}%")
        with c3:
            st.metric("Safety Margin", f"{analysis.get('safety_margin', 0)}%")
        st.markdown("**Recommendations**")
        for rec in opt_result.recommendations:
            st.write(f"• {rec}")
        st.metric("Estimated Cost", f"₹{int(opt_result.cost_estimate):,}")
    else:
        st.info("Upload and generate a drawing in Tab 1 first.")

# TAB 8: Export Manager
with tab8:
    st.markdown('<p class="section-title">📤 Unified Export Manager</p>', unsafe_allow_html=True)

    data_source = st.radio(
        "Data Source", ["Current Drawing", "Current Bill", "Both"], horizontal=True
    )

    st.markdown("### Select Export Formats")
    c1, c2, c3 = st.columns(3)
    with c1:
        export_dxf = st.checkbox("DXF (AutoCAD)", value=True)
        export_excel = st.checkbox("Excel (Styled)", value=True)
        export_pdf = st.checkbox("PDF (Print)", value=False)
    with c2:
        export_html = st.checkbox("HTML (Web)", value=False)
        export_csv = st.checkbox("CSV (Data)", value=False)
        export_svg = st.checkbox("SVG (Vector)", value=False)
    with c3:
        export_png = st.checkbox("PNG (Raster)", value=False)
        export_zip = st.checkbox("ZIP (Bundle)", value=False)

    st.markdown("### Export Options")
    c1, c2 = st.columns(2)
    with c1:
        filename_prefix = st.text_input("Filename Prefix", value="export")
        add_timestamp = st.checkbox("Add Timestamp", value=True)
    with c2:
        bundle_all = st.checkbox("Bundle All in ZIP", value=False)

    if st.button("🚀 Export All Selected Formats", type="primary", key="export_all"):
        _ts = datetime.now().strftime("%Y%m%d_%H%M%S") if add_timestamp else ""
        _prefix = f"{filename_prefix}_{_ts}" if _ts else filename_prefix

        # Build bill DataFrame from session state if available
        _bill_items = st.session_state.get("bill_items", [])
        _bill_df = (
            pd.DataFrame(
                [
                    {
                        "Item No": i["itemNo"],
                        "Description": i["description"],
                        "Qty": i["quantity"],
                        "Rate": i["rate"],
                        "Amount": i["quantity"] * i["rate"],
                    }
                    for i in _bill_items
                    if i.get("quantity", 0) > 0
                ]
            )
            if _bill_items
            else pd.DataFrame(columns=["Item No", "Description", "Qty", "Rate", "Amount"])
        )

        _downloads = {}

        if export_excel:
            _buf = BytesIO()
            with pd.ExcelWriter(_buf, engine="openpyxl") as _w:
                _bill_df.to_excel(_w, index=False, sheet_name="Bill")
            _buf.seek(0)
            _downloads["xlsx"] = (
                _buf.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        if export_csv:
            _downloads["csv"] = (_bill_df.to_csv(index=False).encode("utf-8"), "text/csv")

        if export_html:
            _downloads["html"] = (_bill_df.to_html(index=False).encode("utf-8"), "text/html")

        if export_zip or bundle_all:
            import io as _io
            import zipfile

            _zbuf = _io.BytesIO()
            with zipfile.ZipFile(_zbuf, "w") as _zf:
                for ext, (data, _) in _downloads.items():
                    _zf.writestr(f"{_prefix}.{ext}", data)
            _zbuf.seek(0)
            _downloads["zip"] = (_zbuf.getvalue(), "application/zip")

        st.session_state.usage_counts["export"] += 1  # Trend 5
        if _downloads:
            st.success(f"✅ {len(_downloads)} format(s) ready for download")
            for ext, (data, mime) in _downloads.items():
                st.download_button(
                    f"⬇️ Download {ext.upper()}",
                    data=data,
                    file_name=f"{_prefix}.{ext}",
                    mime=mime,
                    key=f"dl_export_{ext}",
                )
        else:
            st.info("Select at least one format and ensure bill items exist.")


# TAB 9: History
with tab9:
    st.markdown('<p class="section-title">📜 Generation History</p>', unsafe_allow_html=True)

    # FIX WINDSURF-004: use explicit mapping instead of fragile rstrip('s')
    _HISTORY_FILTER_MAP = {"All": None, "Drawings": "Drawing", "Bills": "Bill"}
    history_type = st.radio("Show", list(_HISTORY_FILTER_MAP.keys()), horizontal=True)
    _filter_val = _HISTORY_FILTER_MAP[history_type]

    if st.session_state.history:
        for idx, entry in enumerate(st.session_state.history):
            if _filter_val is None or entry.get("type") == _filter_val:
                with st.expander(f"{entry['type']} - {entry['name']} ({entry['date']})"):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.write(f"**Type:** {entry['type']}")
                        st.write(f"**Date:** {entry['date']}")
                    with c2:
                        st.write(f"**Format:** {entry.get('format', 'N/A')}")
                        st.write(f"**Size:** {entry.get('size', 0):.1f} KB")
                    with c3:
                        if st.button("🗑️ Delete", key=f"del_history_{idx}"):
                            st.session_state.history.pop(idx)
                            st.rerun()
    else:
        st.info("No history yet. Generate drawings or bills to see them here.")


# TAB 10: Help
with tab10:
    st.markdown('<p class="section-title">ℹ️ Help & Documentation</p>', unsafe_allow_html=True)

    with st.expander("🌉 About This Application"):
        st.markdown("""
        **Ultimate Bridge GAD Generator** is a complete solution for:
        - Bridge drawing generation (AutoCAD DXF)
        - Professional bill generation
        - Multi-format exports (10+ formats)
        - Quality checking and compliance
        - 3D visualization
        - AI-powered optimization

        **Integrated from 4 trial apps into one unified solution!**
        """)

    with st.expander("📊 Drawing Generation"):
        st.markdown("""
        1. Upload Excel file with bridge parameters
        2. Select AutoCAD version (2006 or 2010)
        3. Choose export format
        4. Generate drawing
        5. Download result

        **Supported formats**: DXF, PDF, PNG, SVG
        """)

    with st.expander("💰 Bill Generation"):
        st.markdown("""
        1. Enter project and contractor details
        2. Add bill items (supports hierarchy)
        3. Set quantities and rates
        4. Calculate totals with premium
        5. Export in multiple formats

        **Features**:
        - Hierarchical items (main/sub/sub-sub)
        - Draft management
        - Fast mode with test files
        - 7 export formats
        """)

    with st.expander("📤 Export Manager"):
        st.markdown("""
        Unified export system supporting:
        - DXF (AutoCAD)
        - Excel (styled)
        - PDF (print-ready)
        - HTML (web view)
        - CSV (data)
        - SVG (vector)
        - PNG (raster)
        - ZIP (bundled)
        - Deviation reports
        - Statement generation
        """)

    with st.expander("🌉 About RKS LEGAL"):
        st.markdown(f"""
        **RKS LEGAL - Techno Legal Consultants**

        📍 303 Vallabh Apartment, Navratna Complex, Bhuwana
        Udaipur - 313001

        📧 Email: {_contact_email}
        📱 Mobile: {_contact_phone}

        Professional bridge design and engineering consultancy
        """)

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
<div class="footer-bar">
    <span><span class="footer-brand">🌉 Bridge GAD Generator</span> &nbsp;v3.0</span>
    <span style="color:#8b949e;">
        <span class="badge-cyan">DXF</span>&nbsp;
        <span class="badge-amber">Bill</span>&nbsp;
        <span class="badge-green">Export</span>&nbsp;
        <span class="badge-purple">AI</span>
    </span>
    <span>RKS LEGAL &nbsp;·&nbsp; {_contact_email}</span>
</div>
""",
    unsafe_allow_html=True,
)
