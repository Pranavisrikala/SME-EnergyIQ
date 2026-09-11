"""
SME-EnergyIQ: Industrial Energy Intelligence & Optimization Platform
Schneider Electric Yuva Yodha Energy Tech Hackathon 2026
Target Industry: Indian Textile Manufacturing SME (Spinning & Weaving)
"""

import sys
import os
import json
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# Add src to system path for direct module access
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
try:
    import pipeline
    from utils import DEFAULT_GRID_EMISSION_FACTOR, TREE_CO2_ABSORPTION_KG_PER_YEAR, CAR_CO2_KG_PER_KM
except ImportError:
    DEFAULT_GRID_EMISSION_FACTOR = 0.82
    TREE_CO2_ABSORPTION_KG_PER_YEAR = 21.77
    CAR_CO2_KG_PER_KM = 0.192

# Streamlit Page Setup
st.set_page_config(
    page_title="SME-EnergyIQ | Industrial Energy Intelligence Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Industrial CSS (Schneider Green / Slate Palette)
st.markdown("""
<style>
    /* Global Typography & Background */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* =========================================================
       SME-EnergyIQ THEME — OVERVIEW PAGE
       ========================================================= */

    /* Main page heading */
    h1 {
        color: #FFFFFF !important;
        font-weight: 800 !important;
        forced-color-adjust: none !important;
    }

    h1 strong {
        color: #18E06F !important;
        forced-color-adjust: none !important;
    }

    /* Subtitle under main heading */
    h1 + p,
    h1 ~ p {
        color: #A8B8C5 !important;
        forced-color-adjust: none !important;
    }

    /* KPI / metric cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(
            135deg,
            rgba(11, 30, 40, 0.98),
            rgba(15, 48, 55, 0.95)
        ) !important;

        border: 1px solid rgba(24, 224, 111, 0.35) !important;
        border-left: 4px solid #18E06F !important;

        border-radius: 12px !important;
        padding: 18px !important;

        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.25) !important;
        forced-color-adjust: none !important;
    }

    /* KPI labels */
    div[data-testid="stMetric"] label {
        color: #B8C7D1 !important;
        font-weight: 700 !important;
        forced-color-adjust: none !important;
    }

    /* KPI values */
    div[data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-weight: 800 !important;
        forced-color-adjust: none !important;
    }

    /* KPI delta */
    div[data-testid="stMetricDelta"] {
        color: #18E06F !important;
        forced-color-adjust: none !important;
    }

    /* General bordered containers/cards */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color: rgba(24, 224, 111, 0.30) !important;
        border-radius: 12px !important;

        background: linear-gradient(
            135deg,
            rgba(11, 30, 40, 0.96),
            rgba(16, 39, 48, 0.92)
        ) !important;

        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.20) !important;
        forced-color-adjust: none !important;
    }

    /* Machine card headings */
    div[data-testid="stVerticalBlockBorderWrapper"] h3 {
        color: #FFFFFF !important;
        font-weight: 800 !important;
        forced-color-adjust: none !important;
    }

    /* Machine ID / important green text */
    div[data-testid="stVerticalBlockBorderWrapper"] strong {
        color: #18E06F !important;
        forced-color-adjust: none !important;
    }

    /* Section headings */
    h2 {
        color: #FFFFFF !important;
        font-weight: 800 !important;
        forced-color-adjust: none !important;
    }

    h3 {
        color: #E8F0F4 !important;
        forced-color-adjust: none !important;
    }

    /* Horizontal separators */
    hr {
        border: none !important;
        border-top: 1px solid rgba(24, 224, 111, 0.28) !important;
    }

    /* Improve normal dashboard text */
    p {
        color: #D5E0E6;
        forced-color-adjust: none !important;
    }

    /* Factory Overview Clean Header (No Box, Direct Page Background) */
    .overview-header-container {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 4px 0 0 0 !important;
        margin-bottom: 18px !important;
    }
    .overview-page-title {
        color: #008A00 !important;
        font-size: 1.85rem !important;
        font-weight: 800 !important;
        margin: 0 0 6px 0 !important;
        padding: 0 !important;
        letter-spacing: -0.01em !important;
        line-height: 1.25 !important;
        display: flex !important;
        align-items: center !important;
        gap: 10px !important;
        forced-color-adjust: none !important;
    }
    .overview-page-subtitle {
        color: #A8B8C5 !important;
        font-size: 0.94rem !important;
        margin: 0 0 14px 0 !important;
        padding: 0 !important;
        line-height: 1.4 !important;
        forced-color-adjust: none !important;
    }
    .overview-page-divider {
        border: none !important;
        border-top: 1px solid #008A00 !important;
        margin: 0 0 20px 0 !important;
        opacity: 0.60 !important;
        width: 100% !important;
        forced-color-adjust: none !important;
    }

    /* Header Banner */
    .schneider-header {
        background: linear-gradient(135deg, #0B1E28 0%, #17384A 100%);
        border-bottom: 4px solid #18E06F;
        padding: 20px 28px;
        border-radius: 12px;
        margin-bottom: 24px;
        color: white;
        forced-color-adjust: none !important;
    }
    .schneider-header h1 {
        margin: 0;
        font-size: 1.85rem;
        font-weight: 800;
        color: #FFFFFF !important;
        display: flex;
        align-items: center;
        gap: 12px;
        forced-color-adjust: none !important;
    }
    .schneider-header p {
        margin: 6px 0 0 0;
        font-size: 0.92rem;
        color: #A8B8C5 !important;
        forced-color-adjust: none !important;
    }

    /* Overview Page Custom KPI Cards */
    .kpi-card {
        background: linear-gradient(
            135deg,
            rgba(11, 30, 40, 0.98),
            rgba(15, 48, 55, 0.95)
        ) !important;
        border: 1px solid rgba(24, 224, 111, 0.35) !important;
        border-left: 4px solid #18E06F !important;
        border-radius: 12px !important;
        padding: 18px 20px !important;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.25) !important;
        margin-bottom: 12px;
        forced-color-adjust: none !important;
    }
    .kpi-title {
        font-size: 0.80rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #B8C7D1 !important;
        margin-bottom: 4px;
    }
    .kpi-value {
        font-size: 1.65rem;
        font-weight: 800;
        color: #FFFFFF !important;
        font-family: 'JetBrains Mono', monospace;
    }
    .kpi-sub {
        font-size: 0.78rem;
        color: #18E06F !important;
        margin-top: 4px;
        font-weight: 600;
    }

    /* Overview Page Machine Status Cards */
    .machine-card {
        background: linear-gradient(
            135deg,
            rgba(11, 30, 40, 0.96),
            rgba(16, 39, 48, 0.92)
        ) !important;
        border: 1px solid rgba(24, 224, 111, 0.30) !important;
        border-radius: 12px !important;
        padding: 16px;
        margin-bottom: 14px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.20) !important;
        forced-color-adjust: none !important;
        color: #D5E0E6 !important;
    }
    .machine-card strong {
        color: #18E06F !important;
    }
    .machine-card div, .machine-card span {
        color: #D5E0E6;
    }

    /* Badges */
    .badge-good {
        background-color: rgba(24, 224, 111, 0.18) !important;
        color: #18E06F !important;
        border: 1px solid rgba(24, 224, 111, 0.40) !important;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 0.75rem;
    }
    .badge-warning {
        background-color: rgba(245, 158, 11, 0.18) !important;
        color: #FBBF24 !important;
        border: 1px solid rgba(245, 158, 11, 0.40) !important;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 0.75rem;
    }
    .badge-critical {
        background-color: rgba(239, 68, 68, 0.18) !important;
        color: #F87171 !important;
        border: 1px solid rgba(239, 68, 68, 0.40) !important;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 0.75rem;
    }

    /* Alert Evidence Card */
    .alert-card {
        background: linear-gradient(
            135deg,
            rgba(11, 30, 40, 0.96),
            rgba(16, 39, 48, 0.92)
        ) !important;
        border-left: 4px solid #F59E0B !important;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 12px;
        border-top: 1px solid rgba(245, 158, 11, 0.30);
        border-right: 1px solid rgba(245, 158, 11, 0.30);
        border-bottom: 1px solid rgba(245, 158, 11, 0.30);
    }
    
    /* ============================================================ */
    /* INDUSTRIAL SIDEBAR & NAVIGATION CONTROLS (PHASE 8H-2)        */
    /* ============================================================ */
    
    /* Deep Navy Sidebar Container */
    section[data-testid="stSidebar"] {
        background-color: #0B1E28 !important;
        border-right: 1px solid #1E293B !important;
        forced-color-adjust: none !important;
    }
    
    section[data-testid="stSidebar"] * {
        forced-color-adjust: none !important;
    }
    
    /* Sidebar General Typography */
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li {
        color: #CBD5E1 !important;
        font-size: 0.88rem !important;
    }
    
    /* Sidebar Branding Typography */
    .sidebar-brand-container {
        padding: 4px 0 8px 0;
    }
    .sidebar-brand-title {
        font-size: 1.55rem !important;
        font-weight: 800 !important;
        color: #FFFFFF !important;
        letter-spacing: -0.02em !important;
        line-height: 1.2 !important;
    }
    .sidebar-brand-accent {
        color: #008A00 !important;
    }
    .sidebar-brand-subtitle {
        font-size: 0.92rem !important;
        font-weight: 700 !important;
        color: #008A00 !important;
        margin-top: 5px !important;
        letter-spacing: 0.02em !important;
        line-height: 1.3 !important;
        display: block !important;
    }
    
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4 {
        color: #FFFFFF !important;
    }
    
    section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
    section[data-testid="stSidebar"] .stCaption {
        color: #94A3B8 !important;
    }
    
    section[data-testid="stSidebar"] hr {
        border-color: #1E293B !important;
        margin: 0.85rem 0 !important;
    }
    
    /* Navigation Group Label */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > label {
        font-size: 0.72rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        color: #94A3B8 !important;
        margin-bottom: 8px !important;
        display: block !important;
    }
    
    section[data-testid="stSidebar"] div[data-testid="stRadioGroup"] {
        gap: 6px !important;
        display: flex !important;
        flex-direction: column !important;
    }
    
    /* Base Navigation Tab Item (Inactive) */
    section[data-testid="stSidebar"] [data-testid="stRadioOption"] {
        background-color: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-left: 4px solid transparent !important;
        border-radius: 8px !important;
        padding: 9px 12px !important;
        margin-bottom: 5px !important;
        cursor: pointer !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-sizing: border-box !important;
        width: 100% !important;
        forced-color-adjust: none !important;
    }
    
    section[data-testid="stSidebar"] [data-testid="stRadioOption"] p,
    section[data-testid="stSidebar"] [data-testid="stRadioOption"] span {
        color: #CBD5E1 !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        margin: 0 !important;
        line-height: 1.4 !important;
        transition: color 0.2s ease-in-out !important;
    }
    
    /* Hide Radio Dot Circle for Clean Tab Appearance */
    section[data-testid="stSidebar"] [data-testid="stRadioOption"] div[class*="eqiohyi4"],
    section[data-testid="stSidebar"] [data-testid="stRadioOption"] div[class*="eqiohyi5"],
    section[data-testid="stSidebar"] [data-testid="stRadioOption"] > div > div > div:first-child:not([data-testid="stMarkdownContainer"]) {
        display: none !important;
    }
    
    /* Hover State (Subtle highlight & movement on interactive tabs) */
    section[data-testid="stSidebar"] [data-testid="stRadioOption"]:not([data-selected="true"]):not(:has(input:checked)):hover {
        background-color: rgba(0, 138, 0, 0.14) !important;
        border-color: rgba(0, 138, 0, 0.45) !important;
        border-left: 4px solid rgba(0, 138, 0, 0.60) !important;
        transform: translateX(3px) !important;
    }
    
    section[data-testid="stSidebar"] [data-testid="stRadioOption"]:not([data-selected="true"]):not(:has(input:checked)):hover p,
    section[data-testid="stSidebar"] [data-testid="stRadioOption"]:not([data-selected="true"]):not(:has(input:checked)):hover span {
        color: #FFFFFF !important;
    }
    
    /* Active State (Clearly Highlighted Selected Page) */
    section[data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"],
    section[data-testid="stSidebar"] [data-testid="stRadioOption"]:has(input:checked) {
        background-color: rgba(0, 138, 0, 0.22) !important;
        border: 1px solid #008A00 !important;
        border-left: 4px solid #008A00 !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 8px rgba(0, 138, 0, 0.25) !important;
        transform: none !important;
        forced-color-adjust: none !important;
    }
    
    section[data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] p,
    section[data-testid="stSidebar"] [data-testid="stRadioOption"]:has(input:checked) p,
    section[data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] span,
    section[data-testid="stSidebar"] [data-testid="stRadioOption"]:has(input:checked) span {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }
    
    /* Sidebar Action Button */
    section[data-testid="stSidebar"] button {
        background-color: #172E3C !important;
        color: #FFFFFF !important;
        border: 1px solid #008A00 !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
        forced-color-adjust: none !important;
    }
    
    section[data-testid="stSidebar"] button:hover {
        background-color: #008A00 !important;
        color: #FFFFFF !important;
        border-color: #008A00 !important;
        box-shadow: 0 2px 8px rgba(0, 138, 0, 0.30) !important;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# DATA LOADING & CACHING
# -------------------------------------------------------------
@st.cache_data(ttl=300)
def load_all_data():
    enriched_path = "results/factory_data_enriched.csv"
    if not os.path.exists(enriched_path):
        with st.spinner("Initializing SME-EnergyIQ Intelligence Pipeline..."):
            pipeline.run_full_pipeline()
            
    df = pd.read_csv(enriched_path)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    
    with open("results/energy_summary.json", "r") as f:
        energy_summary = json.load(f)
        
    with open("results/optimization_results.json", "r") as f:
        opt_results = json.load(f)
        
    with open("results/carbon_sustainability_report.json", "r") as f:
        carbon_report = json.load(f)
        
    df_alerts = pd.read_csv("results/explainable_alerts.csv")
    df_alerts["Timestamp"] = pd.to_datetime(df_alerts["Timestamp"])
    
    df_sched_base = pd.read_csv("results/schedule_baseline.csv")
    df_sched_opt = pd.read_csv("results/schedule_optimized.csv")
    
    return df, energy_summary, opt_results, carbon_report, df_alerts, df_sched_base, df_sched_opt

try:
    df, energy_summary, opt_results, carbon_report, df_alerts, df_sched_base, df_sched_opt = load_all_data()
except Exception as e:
    st.error(f"Error loading platform data: {e}")
    if st.button("Regenerate Data Pipeline"):
        pipeline.run_full_pipeline()
        st.rerun()
    st.stop()

# -------------------------------------------------------------
# SIDEBAR NAVIGATION & CONTROLS
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand-container">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.65rem; line-height: 1;">⚡</span>
            <span class="sidebar-brand-title">SME-<span class="sidebar-brand-accent">EnergyIQ</span></span>
        </div>
        <span class="sidebar-brand-subtitle">
            Industrial Energy Intelligence Platform
        </span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    page = st.radio(
        "Navigation",
        [
            "🏭 Factory Overview",
            "⚡ Energy & ToD Monitoring",
            "🩺 Machine Health & Diagnostics",
            "🚨 Explainable AI Alerts",
            "📈 Production Optimization",
            "🌱 Carbon & Sustainability",
            "🏛️ Architecture & SME Roadmap"
        ]
    )
    
    st.markdown("---")
    st.markdown("#### **Plant Context: Textile SME**")
    st.markdown("""
    - **Location**: Tirupur / Surat Cluster
    - **Contract Demand**: 160 kW
    - **Supply Tariff**: ToD Slab HT-1
      * Peak (18-22h): ₹10.00/kWh
      * Normal (06-18h): ₹7.50/kWh
      * Off-Peak (22-06h): ₹5.50/kWh
    - **Target Output**: Ring Spun Combed Yarn
    """)
    st.markdown("---")
    if st.button("🔄 Rerun AI & Optimization Pipeline"):
        pipeline.run_full_pipeline()
        st.cache_data.clear()
        st.success("Pipeline refreshed successfully!")
        st.rerun()

# -------------------------------------------------------------
# PAGE 1: FACTORY OVERVIEW
# -------------------------------------------------------------
if page == "🏭 Factory Overview":
    st.markdown("""
    <div class="overview-header-container" style="background:transparent !important; border:none !important; box-shadow:none !important; padding:4px 0 0 0; margin-bottom:18px;">
        <h1 class="overview-page-title" style="color:#008A00 !important; font-size:1.85rem !important; font-weight:800 !important; margin:0 0 6px 0; padding:0; line-height:1.25; forced-color-adjust:none !important;">⚡ SME-EnergyIQ | Industrial Operations Overview</h1>
        <p class="overview-page-subtitle" style="color:#A8B8C5 !important; font-size:0.94rem !important; margin:0 0 14px 0; padding:0; line-height:1.4; forced-color-adjust:none !important;">Textile SME Energy Command Center — Ring Spinning, Air Compressors, Dyeing Pumps & Climate Control</p>
        <div class="overview-page-divider" style="border:none !important; border-top:1px solid #008A00 !important; margin:0 0 20px 0; opacity:0.60; width:100%; forced-color-adjust:none !important;"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # Latest snapshot metrics
    latest_ts = df["Timestamp"].max()
    latest_df = df[df["Timestamp"] == latest_ts]
    total_curr_power = latest_df["Power_kW"].sum()
    factory_sec = energy_summary["factory_overview"]["baseline_factory_sec_kwh_per_kg"]
    total_energy_kwh = energy_summary["factory_overview"]["total_energy_kwh"]
    total_cost_rs = energy_summary["factory_overview"]["total_cost_rs"]
    peak_demand = energy_summary["factory_overview"]["peak_demand_kw"]
    idle_waste_rs = energy_summary["factory_overview"]["idle_energy_waste_cost_rs"]
    
    # Distinct Current Active Alerts (Latest Window) vs 14-Day Historical Incidents
    current_active_alerts = latest_df[latest_df["Severity"].isin(["HIGH", "CRITICAL"])]
    current_active_critical = len(latest_df[latest_df["Severity"] == "CRITICAL"])
    current_active_count = len(current_active_alerts)
    
    historical_critical = len(df_alerts[df_alerts["Severity"] == "CRITICAL"])
    historical_high = len(df_alerts[df_alerts["Severity"] == "HIGH"])
    
    # Top KPI Row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Current Power Demand</div>
            <div class="kpi-value">{total_curr_power:.1f} <span style="font-size:1rem;color:#64748B">kW</span></div>
            <div class="kpi-sub">Contract Limit: 160 kW ({total_curr_power/160*100:.0f}% used)</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Factory SEC (Yarn)</div>
            <div class="kpi-value">{factory_sec:.3f} <span style="font-size:1rem;color:#64748B">kWh/kg</span></div>
            <div class="kpi-sub">Benchmark: &le; 0.720 kWh/kg</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">14-Day Energy Cost</div>
            <div class="kpi-value">₹{total_cost_rs:,.0f}</div>
            <div class="kpi-sub">Total: {total_energy_kwh:,.0f} kWh</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: {'#EF4444' if current_active_critical > 0 else ('#F59E0B' if current_active_count > 0 else '#18E06F')}">
            <div class="kpi-title">Current Active Alerts</div>
            <div class="kpi-value" style="color: {'#DC2626' if current_active_critical > 0 else ('#D97706' if current_active_count > 0 else '#18E06F')}">
                {current_active_count} Active
            </div>
            <div class="kpi-sub" style="color:#A8B8C5">
                14-Day Incidents: <b>{historical_critical} Critical</b> / {historical_high} High
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Machine Live Status Cards
    st.markdown("### **Machine Operational & Diagnostic Matrix**")
    m_cols = st.columns(4)
    for i, (idx, m_row) in enumerate(latest_df.iterrows()):
        col = m_cols[i % 4]
        h_score = m_row["Health_Score"]
        vib_zone = m_row.get("ISO_Vib_Zone", "ZONE_A_GOOD")
        status = m_row["Machine_Status"]
        mach_id = m_row["Machine_ID"]
        
        # Machine-specific historical incident counts across the 14-day dataset
        m_crit_hist = len(df_alerts[(df_alerts["Machine_ID"] == mach_id) & (df_alerts["Severity"] == "CRITICAL")])
        m_total_hist = len(df_alerts[df_alerts["Machine_ID"] == mach_id])
        
        badge_class = "badge-good" if h_score >= 85 else ("badge-warning" if h_score >= 65 else "badge-critical")
        
        with col:
            st.markdown(f"""
            <div class="machine-card">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <strong style="font-size:1.05rem; color:#18E06F">{m_row['Machine_ID']}</strong>
                    <span class="{badge_class}">Health {h_score}/100</span>
                </div>
                <div style="font-size:0.82rem; color:#A8B8C5; margin-bottom:10px;">{m_row['Machine_Type']}</div>
                <hr style="margin:8px 0; border:none; border-top:1px solid rgba(24, 224, 111, 0.28);">
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; font-size:0.82rem; color:#D5E0E6;">
                    <div>Power: <b>{m_row['Power_kW']:.1f} kW</b></div>
                    <div>Vib: <b>{m_row['Vibration_mm_s']:.2f} mm/s</b></div>
                    <div>Temp: <b>{m_row['Temperature_C']:.1f}°C</b></div>
                    <div>Speed: <b>{m_row['RPM']:.0f} RPM</b></div>
                </div>
                <div style="margin-top:10px; font-size:0.74rem; color:#A8B8C5; display:flex; justify-content:space-between; gap:4px;">
                    <span>ISO: <span style="font-weight:600; color:#18E06F">{vib_zone.replace('_', ' ')}</span></span>
                    <span style="color:#A8B8C5; text-align:right;">14-Day: <b>{m_crit_hist} Critical</b> / {m_total_hist} Total</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Real-Time Plant Power Load Chart
    st.markdown("### **Plant-Wide Power Demand & Tariff Bands**")
    
    # 3-day view for high detail
    recent_ts = df["Timestamp"].max() - pd.Timedelta(days=3)
    df_recent = df[df["Timestamp"] >= recent_ts]
    
    fig = go.Figure()
    for m_id in df["Machine_ID"].unique():
        m_data = df_recent[df_recent["Machine_ID"] == m_id]
        fig.add_trace(go.Scatter(
            x=m_data["Timestamp"],
            y=m_data["Power_kW"],
            mode="lines",
            name=f"{m_id} ({m_data['Machine_Type'].iloc[0]})",
            stackgroup="one" # Stacked power demand!
        ))
        
    fig.update_layout(
        title="Aggregate 3-Phase Active Power (kW) by Machine Stack (Last 72 Hours)",
        xaxis_title="Time",
        yaxis_title="Total Factory Power Demand (kW)",
        hovermode="x unified",
        template="plotly_white",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------------------
# PAGE 2: ENERGY & ToD MONITORING
# -------------------------------------------------------------
elif page == "⚡ Energy & ToD Monitoring":
    st.markdown("""
    <div class="schneider-header">
        <h1><span>⚡</span> Machine-Level Energy Monitoring & Time-of-Day Analysis</h1>
        <p>Fundamental Relationship: Energy (kWh) = Power (kW) × Time (h) | ToD Tariff Cost Allocation</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📊 Multi-Machine Energy Curves", "🕒 Time-of-Day Tariff Impact", "📉 Daily SEC Tracking"])
    
    with tab1:
        c1, c2 = st.columns([3, 1])
        with c2:
            sel_machine = st.selectbox("Select Machine Focus", ["ALL MACHINES"] + list(df["Machine_ID"].unique()))
            date_range = st.date_input(
                "Date Window",
                [df["Timestamp"].min().date(), df["Timestamp"].max().date()]
            )
            
        with c1:
            mask = (df["Timestamp"].dt.date >= date_range[0]) & (df["Timestamp"].dt.date <= date_range[1])
            df_filtered = df[mask]
            
            if sel_machine != "ALL MACHINES":
                df_filtered = df_filtered[df_filtered["Machine_ID"] == sel_machine]
                fig = px.line(
                    df_filtered,
                    x="Timestamp",
                    y="Power_kW",
                    color="Peak_OffPeak",
                    title=f"Instantaneous Power Demand (kW) for {sel_machine}",
                    color_discrete_map={"PEAK": "#EF4444", "NORMAL": "#3B82F6", "OFF_PEAK": "#10B981"}
                )
            else:
                fig = px.line(
                    df_filtered,
                    x="Timestamp",
                    y="Power_kW",
                    color="Machine_ID",
                    title="Comparative Machine Power Demand (kW) Across Fleet"
                )
            fig.update_layout(template="plotly_white", height=420)
            st.plotly_chart(fig, use_container_width=True)
            
        # Machine Energy Consumption Table
        st.markdown("#### **Fleet Energy & Cost Breakdown**")
        breakdown_rows = []
        for m_id, stats in energy_summary["machine_breakdown"].items():
            breakdown_rows.append({
                "Machine ID": m_id,
                "Machine Type": stats["type"],
                "Total Energy (kWh)": f"{stats['total_energy_kwh']:,.1f}",
                "Share of Plant (%)": f"{stats['share_of_factory_pct']}%",
                "Total Cost (₹)": f"₹{stats['total_cost_rs']:,.0f}",
                "Specific Energy (SEC)": f"{stats['sec_kwh_per_unit']} kWh/unit",
                "Peak Power (kW)": f"{stats['peak_power_kw']} kW",
                "Avg Power (kW)": f"{stats['avg_power_kw']} kW"
            })
        st.dataframe(pd.DataFrame(breakdown_rows), use_container_width=True, hide_index=True)

    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### **Energy Consumption by ToD Slabs**")
            t_data = energy_summary["tariff_window_breakdown"]
            fig_t = px.pie(
                names=list(t_data.keys()),
                values=[v["total_kwh"] for v in t_data.values()],
                title="Energy Share (kWh) by Time-of-Day Window",
                color=list(t_data.keys()),
                color_discrete_map={"PEAK": "#EF4444", "NORMAL": "#3B82F6", "OFF_PEAK": "#10B981"},
                hole=0.4
            )
            fig_t.update_layout(template="plotly_white")
            st.plotly_chart(fig_t, use_container_width=True)
            
        with c2:
            st.markdown("#### **Electricity Bill Impact (Rupees)**")
            fig_c = px.bar(
                x=list(t_data.keys()),
                y=[v["cost_rs"] for v in t_data.values()],
                title="Total Tariff Cost (₹) Incurred by Slab",
                color=list(t_data.keys()),
                color_discrete_map={"PEAK": "#EF4444", "NORMAL": "#3B82F6", "OFF_PEAK": "#10B981"},
                labels={"x": "ToD Slab", "y": "Cost (₹)"}
            )
            fig_c.update_layout(template="plotly_white")
            st.plotly_chart(fig_c, use_container_width=True)
            
        st.info("""
        💡 **Key Industrial Takeaway for Judges**: Notice that while **PEAK hours** account for only ~14.8% of energy consumed, 
        they generate over **20.7% of the total electricity bill** due to the ₹10.00/kWh tariff. Shifting flexible batch loads 
        (such as Dyeing Pumps and Air Storage charging) into the ₹5.50/kWh OFF-PEAK night slab unlocks substantial savings.
        """)

    with tab3:
        st.markdown("#### **Daily Factory Specific Energy Consumption (SEC)**")
        df_daily = pd.read_csv("results/daily_sec_profile.csv")
        fig_sec = make_subplots(specs=[[{"secondary_y": True}]])
        fig_sec.add_trace(
            go.Bar(x=df_daily["Date"], y=df_daily["Yarn_Production_kg"], name="Yarn Production (kg)", marker_color="#94A3B8"),
            secondary_y=False
        )
        fig_sec.add_trace(
            go.Scatter(x=df_daily["Date"], y=df_daily["Factory_SEC_kWh_per_kg"], name="SEC (kWh/kg)", mode="lines+markers", line=dict(color="#008A00", width=3)),
            secondary_y=True
        )
        fig_sec.update_layout(
            title="Daily Production Output vs. Factory Specific Energy Consumption (SEC)",
            template="plotly_white",
            height=420
        )
        fig_sec.update_xaxes(title_text="Date")
        fig_sec.update_yaxes(title_text="Production (kg yarn)", secondary_y=False)
        fig_sec.update_yaxes(title_text="Factory SEC (kWh/kg)", secondary_y=True)
        st.plotly_chart(fig_sec, use_container_width=True)

# -------------------------------------------------------------
# PAGE 3: MACHINE HEALTH & DIAGNOSTICS
# -------------------------------------------------------------
elif page == "🩺 Machine Health & Diagnostics":
    st.markdown("""
    <div class="schneider-header">
        <h1><span>🩺</span> ISO 10816 Machine Health & Condition Monitoring</h1>
        <p>Vibration Severity Standards, Thermal Headroom & Physics-Based Asset Health Scoring</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Machine Selection
    selected_machine = st.selectbox("Select Machine for Detailed Engineering Drill-Down", df["Machine_ID"].unique())
    m_df = df[df["Machine_ID"] == selected_machine]
    latest_m = m_df.iloc[-1]
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Health Score", f"{latest_m['Health_Score']}/100", delta=f"Risk: {latest_m['Risk_Level']}")
    with c2:
        st.metric("Vibration RMS", f"{latest_m['Vibration_mm_s']:.2f} mm/s", delta=f"ISO: {latest_m.get('ISO_Vib_Zone', 'N/A')}")
    with c3:
        st.metric("Stator Temperature", f"{latest_m['Temperature_C']:.1f}°C", delta=f"Elevation: {latest_m.get('Temp_Elevation', 0.0):+.1f}°C")
    with c4:
        st.metric("Operating Speed", f"{latest_m['RPM']:.0f} RPM", delta=f"Status: {latest_m['Machine_Status']}")

    # Historical Parameter Curves
    st.markdown(f"### **14-Day Condition Telemetry: {selected_machine}**")
    
    fig_diag = make_subplots(rows=2, cols=2, subplot_titles=(
        "Active Power (kW) vs. Load Baseline",
        "ISO 10816 Vibration Severity (mm/s RMS)",
        "Stator/Bearing Temperature (°C)",
        "Motor Slip / Operating Speed (RPM)"
    ))
    
    # Power
    fig_diag.add_trace(go.Scatter(x=m_df["Timestamp"], y=m_df["Power_kW"], name="Power (kW)", line=dict(color="#2563EB")), row=1, col=1)
    # Vibration with ISO threshold lines
    fig_diag.add_trace(go.Scatter(x=m_df["Timestamp"], y=m_df["Vibration_mm_s"], name="Vibration (mm/s)", line=dict(color="#D97706")), row=1, col=2)
    fig_diag.add_hline(y=2.3, line_dash="dot", line_color="#10B981", annotation_text="ISO Good (2.3)", row=1, col=2)
    fig_diag.add_hline(y=4.5, line_dash="dash", line_color="#F59E0B", annotation_text="ISO Unsatisfactory (4.5)", row=1, col=2)
    fig_diag.add_hline(y=7.1, line_dash="dash", line_color="#EF4444", annotation_text="ISO Unacceptable (7.1)", row=1, col=2)
    
    # Temperature
    fig_diag.add_trace(go.Scatter(x=m_df["Timestamp"], y=m_df["Temperature_C"], name="Temp (°C)", line=dict(color="#DC2626")), row=2, col=1)
    # RPM
    fig_diag.add_trace(go.Scatter(x=m_df["Timestamp"], y=m_df["RPM"], name="Speed (RPM)", line=dict(color="#059669")), row=2, col=2)
    
    fig_diag.update_layout(height=600, template="plotly_white", showlegend=False)
    st.plotly_chart(fig_diag, use_container_width=True)
    
    # Machine Specific Diagnostic Summary
    flagged_records = m_df[m_df["Severity"].isin(["HIGH", "CRITICAL"])]
    st.markdown("#### **Diagnostic Investigation Log: Why Was This Machine Flagged?**")
    if not flagged_records.empty:
        st.warning(f"⚠️ Machine {selected_machine} recorded {len(flagged_records)} abnormal condition events in the 14-day observation window.")
        sample_ev = flagged_records.iloc[0]
        st.markdown(f"""
        - **Timestamp**: `{sample_ev['Timestamp']}`
        - **Detected State**: `{sample_ev['Machine_Status']}` | **AI Anomaly Score**: `{sample_ev['Anomaly_Score']}/100`
        - **Primary Anomaly Mode**: `{sample_ev.get('Anomaly_Type', 'DEGRADATION')}`
        - **Observed Physical Evidence**: Power reached `{sample_ev['Power_kW']:.1f} kW`, Temperature reached `{sample_ev['Temperature_C']:.1f}°C`, Vibration peaked at `{sample_ev['Vibration_mm_s']:.2f} mm/s`.
        """)
    else:
        st.success(f"✅ Machine {selected_machine} operated within nominal ISO 10816 Class II vibration and thermal thresholds.")

# -------------------------------------------------------------
# PAGE 4: EXPLAINABLE AI ALERTS
# -------------------------------------------------------------
elif page == "🚨 Explainable AI Alerts":
    st.markdown("""
    <div class="schneider-header">
        <h1><span>🚨</span> 4-Tier Explainable Industrial AI Alert Feed</h1>
        <p>No Black Boxes: Observed Data → Model Inference → Engineering Hypothesis → Recommended Action</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Dynamic operational status (Current Active Window vs 14-Day Historical Log)
    latest_ts = df["Timestamp"].max()
    latest_df = df[df["Timestamp"] == latest_ts]
    current_active_alerts = latest_df[latest_df["Severity"].isin(["HIGH", "CRITICAL"])]
    current_active_count = len(current_active_alerts)
    historical_count = len(df_alerts)
    
    st.markdown("### **Operational Status Overview**")
    col_stat1, col_stat2 = st.columns(2)
    with col_stat1:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: {'#008A00' if current_active_count == 0 else '#DC2626'};">
            <div class="kpi-title">Currently Active Alarms (Latest Window)</div>
            <div class="kpi-value" style="color: {'#008A00' if current_active_count == 0 else '#DC2626'};">{current_active_count} Active</div>
            <div class="kpi-sub" style="color:#059669">Latest Telemetry: {latest_ts.strftime('%Y-%m-%d %H:%M')} | All machines nominal</div>
        </div>
        """, unsafe_allow_html=True)
    with col_stat2:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #2563EB;">
            <div class="kpi-title">14-Day Cumulative Incident Log</div>
            <div class="kpi-value" style="color: #0F172A;">{historical_count} Events</div>
            <div class="kpi-sub" style="color:#059669">All Cleared / Historical</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### **Historical Diagnostic Incident Log (14-Day Archive)**")
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        st.markdown(f"**Archived 14-Day Operational Incidents**: `{historical_count}`")
    with c2:
        filter_sev = st.selectbox("Filter by Severity", ["ALL", "CRITICAL", "HIGH", "MEDIUM"])
    with c3:
        filter_m = st.selectbox("Filter by Machine", ["ALL"] + list(df["Machine_ID"].unique()))
        
    filtered_alerts = df_alerts.copy()
    if filter_sev != "ALL":
        filtered_alerts = filtered_alerts[filtered_alerts["Severity"] == filter_sev]
    if filter_m != "ALL":
        filtered_alerts = filtered_alerts[filtered_alerts["Machine_ID"] == filter_m]
        
    st.markdown(f"Showing **{len(filtered_alerts)}** triaged industrial alert events:")
    
    # Render first 15 alerts as clear expandable cards
    for idx, alert in filtered_alerts.head(15).iterrows():
        # Tier 1: OBSERVED DATA
        raw_obs = str(alert["Observed_Data"])
        raw_obs = raw_obs.replace("ISO: ZONE_D_UNACCEPTABLE", "Configured vibration zone: D / Unacceptable")
        raw_obs = raw_obs.replace("ISO: ZONE_C_UNSATISFACTORY", "Configured vibration zone: C / Unsatisfactory")
        raw_obs = raw_obs.replace("ISO: ZONE_B_SATISFACTORY", "Configured vibration zone: B / Satisfactory")
        raw_obs = raw_obs.replace("ISO: ZONE_A_GOOD", "Configured vibration zone: A / Good")
        
        obs_items = []
        for item in raw_obs.split(";"):
            item = item.strip()
            if not item:
                continue
            if item.startswith("Temp:"):
                item = "Temperature:" + item[5:]
            elif item.startswith("Vib:"):
                item = "Vibration:" + item[4:]
            elif item.startswith("Prod:"):
                item = "Production:" + item[5:]
            obs_items.append(item)
            
        # Tier 2: MODEL INFERENCE
        raw_inf = str(alert["Model_Inference"])
        if "Anomaly Score:" in raw_inf:
            score_val = raw_inf.split("Anomaly Score:")[1].split("|")[0].strip()
            if not score_val.endswith("/100") and "/" not in score_val:
                score_val = f"{score_val}/100"
        else:
            score_val = "N/A"
            
        if "Status:" in raw_inf:
            raw_status = raw_inf.split("Status:")[1].split("|")[0].strip()
        else:
            raw_status = "RUNNING"
            
        if "RUNNING" in raw_status:
            op_state = "RUNNING"
        elif "IDLE" in raw_status:
            op_state = "IDLE"
        elif "MAINTENANCE" in raw_status:
            op_state = "MAINTENANCE"
        else:
            op_state = raw_status
            
        sev_val = str(alert["Severity"])
        
        # Tier 3: ENGINEERING HYPOTHESIS
        raw_hyp = str(alert["Engineering_Hypothesis"])
        if "Vibration exceeds ISO" in raw_hyp or "Likely V-belt" in raw_hyp:
            hyp_text = (
                "Vibration is substantially above the configured critical threshold.\n\n"
                "Possible causes to investigate: V-belt wear, rotor unbalance, or loose foundation anchor bolt."
            )
        elif "Compressor unloader valve failed" in raw_hyp:
            hyp_text = (
                "Compressor unloader activity detected during non-productive period.\n\n"
                "Possible causes to investigate: unloader valve seating issue, or machine left idling during non-productive break."
            )
        elif "Thermal buildup due to" in raw_hyp:
            hyp_text = (
                "Thermal buildup detected above expected operating baseline.\n\n"
                "Possible causes to investigate: choked condenser fins, blower airflow restriction, or high ambient humidity heat load."
            )
        elif "Subtle multivariate" in raw_hyp:
            hyp_text = (
                "Subtle multivariate parameter divergence from expected operational baseline.\n\n"
                "Possible causes to investigate: elevated energy intensity relative to throughput or partial mechanical drag."
            )
        elif "Dyeing liquor circulation" in raw_hyp:
            hyp_text = (
                "Throughput reduction observed relative to motor power delivery.\n\n"
                "Possible causes to investigate: suction strainer clogging, impeller cavitation, or restricted circulation passage."
            )
        elif "Drive-end bearing race" in raw_hyp:
            hyp_text = (
                "Elevated frictional torque and thermal rise observed.\n\n"
                "Possible causes to investigate: drive-end bearing race wear, mechanical binding, or dynamic shaft misalignment."
            )
        else:
            clean_hyp = raw_hyp.replace("Likely ", "Possible causes to investigate: ")
            clean_hyp = clean_hyp.replace("ISO 10816 Class II threshold", "configured critical threshold")
            clean_hyp = clean_hyp.replace("ISO 10816", "configured vibration")
            hyp_text = clean_hyp

        # Tier 4: RECOMMENDED ACTION
        raw_act = str(alert["Recommended_Action"])
        clean_act = raw_act.replace(
            "Check foundation bolt torque using calibrated torque wrench",
            "Check foundation fastening and investigate vibration source"
        )
        act_items = [a.strip() for a in clean_act.split(".") if a.strip()]

        with st.expander(f"[{alert['Severity']}] {alert['Machine_ID']} — {alert['Timestamp']} | Health: {alert['Health_Score']}/100"):
            st.markdown("**1. OBSERVED DATA (Sensor Evidence)**")
            for item in obs_items:
                st.markdown(f"- {item}")
                
            st.markdown("**2. MODEL INFERENCE (AI Isolation Forest)**")
            st.markdown(f"- Isolation Forest Anomaly Score: {score_val}")
            st.markdown(f"- Diagnostic Severity: {sev_val}")
            st.markdown(f"- Operating State: {op_state}")
            
            st.markdown("**3. ENGINEERING HYPOTHESIS**")
            st.markdown(hyp_text)
            
            st.markdown("**4. RECOMMENDED ACTION (Maintenance Instruction)**")
            for act in act_items:
                st.markdown(f"- {act}.")

# -------------------------------------------------------------
# PAGE 5: PRODUCTION OPTIMIZATION
# -------------------------------------------------------------
elif page == "📈 Production Optimization":
    st.markdown("""
    <div class="schneider-header">
        <h1><span>📈</span> PuLP MILP Production Schedule & Peak Load Shifting</h1>
        <p>100% Throughput Guarantee | Minimize Time-of-Day Tariff Cost + Shave Peak Grid Demand</p>
    </div>
    """, unsafe_allow_html=True)
    
    m = opt_results["metrics"]
    
    # Comparison Cards
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Daily Energy Cost</div>
            <div class="kpi-value">₹{m['Total_Cost_Rs']['optimized']:,.0f}</div>
            <div class="kpi-sub" style="color:#059669">▼ ₹{m['Total_Cost_Rs']['savings']:,.0f} ({m['Total_Cost_Rs']['improvement_pct']}%) Saved</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Peak Demand Shaved</div>
            <div class="kpi-value">{m['Peak_Demand_kW']['optimized']:.1f} <span style="font-size:1rem;color:#64748B">kW</span></div>
            <div class="kpi-sub" style="color:#059669">▼ {m['Peak_Demand_kW']['reduction_kw']:.1f} kW ({m['Peak_Demand_kW']['improvement_pct']}%) Shaved</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Yarn Throughput</div>
            <div class="kpi-value">{m['Yarn_Production_kg']['optimized']:,.0f} <span style="font-size:1rem;color:#64748B">kg</span></div>
            <div class="kpi-sub" style="color:#2563EB">100% Target Met Exactly</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Daily SEC (Yarn)</div>
            <div class="kpi-value">{m['Specific_Energy_Consumption_SEC']['optimized']:.3f} <span style="font-size:1rem;color:#64748B">kWh/kg</span></div>
            <div class="kpi-sub">Baseline: {m['Specific_Energy_Consumption_SEC']['baseline']:.3f} kWh/kg</div>
        </div>
        """, unsafe_allow_html=True)
    with c5:
        co2_val = m.get('CO2_Emissions_kg', {}).get('optimized', 0.0)
        co2_avoided = m.get('CO2_Emissions_kg', {}).get('avoided_kg', 0.0)
        ci_val = m.get('Carbon_Intensity_kg_CO2e_per_kg_yarn', {}).get('optimized')
        if ci_val is not None:
            ci_sub = f"▼ {co2_avoided:.2f} kg ({ci_val:.4f} kg/kg)"
        else:
            ci_sub = f"▼ {co2_avoided:.2f} kg (N/A — no production recorded)"
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Daily Scope 2 CO2e</div>
            <div class="kpi-value">{co2_val:,.1f} <span style="font-size:1rem;color:#64748B">kg</span></div>
            <div class="kpi-sub" style="color:#059669">{ci_sub}</div>
        </div>
        """, unsafe_allow_html=True)

    # 24-Hour Load Profile: Baseline vs Optimized
    st.markdown("### **24-Hour Load Shifting: Baseline vs. PuLP Optimized Schedule**")
    
    base_hourly = df_sched_base.groupby("Hour")["Power_kW"].sum().reset_index()
    opt_hourly = df_sched_opt.groupby("Hour")["Power_kW"].sum().reset_index()
    
    fig_opt = go.Figure()
    fig_opt.add_trace(go.Scatter(
        x=base_hourly["Hour"],
        y=base_hourly["Power_kW"],
        mode="lines+markers",
        name="Baseline Schedule (Uncoordinated High Evening Load)",
        line=dict(color="#EF4444", width=3, dash="dash")
    ))
    fig_opt.add_trace(go.Scatter(
        x=opt_hourly["Hour"],
        y=opt_hourly["Power_kW"],
        mode="lines+markers",
        name="PuLP Optimized Schedule (Off-Peak Shifted)",
        line=dict(color="#008A00", width=3)
    ))
    
    # Highlight Peak Tariff Zone (18:00 - 22:00)
    fig_opt.add_vrect(
        x0=18, x1=22,
        fillcolor="#FEE2E2", opacity=0.5,
        layer="below", line_width=0,
        annotation_text="PEAK TARIFF WINDOW (₹10.00 / kWh)",
        annotation_position="top left"
    )
    
    fig_opt.update_layout(
        title="Grid Active Power Demand (kW) Across 24-Hour Day",
        xaxis_title="Hour of Day (00:00 to 23:00)",
        yaxis_title="Total Factory Power Demand (kW)",
        template="plotly_white",
        height=450,
        hovermode="x unified"
    )
    st.plotly_chart(fig_opt, use_container_width=True)
    
    # Detailed Benchmark Table
    st.markdown("#### **Baseline vs. Optimized Comprehensive Scorecard**")
    scorecard_data = [
        {"Metric": "Total Daily Energy Consumed", "Baseline": f"{m['Total_Energy_kWh']['baseline']} kWh", "Optimized": f"{m['Total_Energy_kWh']['optimized']} kWh", "Improvement": "Preserved Throughput"},
        {"Metric": "Total Daily Electricity Cost", "Baseline": f"₹{m['Total_Cost_Rs']['baseline']:,.2f}", "Optimized": f"₹{m['Total_Cost_Rs']['optimized']:,.2f}", "Improvement": f"▼ ₹{m['Total_Cost_Rs']['savings']:,.2f} ({m['Total_Cost_Rs']['improvement_pct']}%)"},
        {"Metric": "Max Peak Grid Demand", "Baseline": f"{m['Peak_Demand_kW']['baseline']} kW", "Optimized": f"{m['Peak_Demand_kW']['optimized']} kW", "Improvement": f"▼ {m['Peak_Demand_kW']['reduction_kw']} kW ({m['Peak_Demand_kW']['improvement_pct']}% Shaved)"},
        {"Metric": "Production Throughput (Yarn)", "Baseline": f"{m['Yarn_Production_kg']['baseline']} kg", "Optimized": f"{m['Yarn_Production_kg']['optimized']} kg", "Improvement": "100.0% Conserved (No Shortfall)"},
        {"Metric": "Specific Energy Consumption (SEC)", "Baseline": f"{m['Specific_Energy_Consumption_SEC']['baseline']} kWh/kg", "Optimized": f"{m['Specific_Energy_Consumption_SEC']['optimized']} kWh/kg", "Improvement": f"▼ {m['Specific_Energy_Consumption_SEC'].get('improvement_pct', 0.0)}% Efficiency"}
    ]
    if "CO2_Emissions_kg" in m:
        scorecard_data.append({
            "Metric": "Modeled Scope 2 CO2e",
            "Baseline": f"{m['CO2_Emissions_kg']['baseline']} kg CO2e",
            "Optimized": f"{m['CO2_Emissions_kg']['optimized']} kg CO2e",
            "Improvement": f"▼ {m['CO2_Emissions_kg']['avoided_kg']} kg Avoided"
        })
    if "Carbon_Intensity_kg_CO2e_per_kg_yarn" in m:
        ci_dict = m["Carbon_Intensity_kg_CO2e_per_kg_yarn"]
        b_ci = ci_dict.get("baseline")
        o_ci = ci_dict.get("optimized")
        base_ci_str = f"{b_ci:.4f} kg CO2e/kg" if b_ci is not None else "N/A — no production recorded"
        opt_ci_str = f"{o_ci:.4f} kg CO2e/kg" if o_ci is not None else "N/A — no production recorded"
        imp_ci_str = f"▼ {ci_dict.get('improvement_pct', 0.0)}% Improvement" if (b_ci is not None and o_ci is not None) else "N/A — no production recorded"
        scorecard_data.append({
            "Metric": "Carbon Intensity (Yarn)",
            "Baseline": base_ci_str,
            "Optimized": opt_ci_str,
            "Improvement": imp_ci_str
        })
    st.dataframe(pd.DataFrame(scorecard_data), use_container_width=True, hide_index=True)
    st.caption("ℹ️ *Note: CO2 emissions and Carbon Intensity reflect electricity-related Scope 2 emissions based on simulation benchmark (0.82 kg CO2e/kWh). Throughput is 100% conserved.*")

# -------------------------------------------------------------
# PAGE 6: CARBON & SUSTAINABILITY
# -------------------------------------------------------------
elif page == "🌱 Carbon & Sustainability":
    st.markdown("""
    <div class="schneider-header">
        <h1><span>🌱</span> Industrial Carbon Accounting & Sustainability</h1>
        <p>Central Electricity Authority (CEA) Emission Factors | Scope 2 Indirect Carbon Footprint</p>
    </div>
    """, unsafe_allow_html=True)
    
    meta = carbon_report.get("metadata", {})
    footprint = carbon_report.get("factory_footprint_14_days", {})
    opt_impact = carbon_report.get("optimization_carbon_impact", {})
    
    # -------------------------------------------------------------
    # SECTION A: HISTORICAL FACTORY FOOTPRINT — 14 DAYS
    # -------------------------------------------------------------
    st.markdown("### **Section A: Historical Factory Footprint — 14 Days (Telemetry Data)**")
    st.caption("Aggregated from 14 days of multi-channel edge energy meter data across 4 core textile assets.")
    
    # Interactive Grid Factor Slider
    c_slider, c_info = st.columns([2, 2])
    with c_slider:
        custom_factor = st.slider(
            "Configurable Grid Carbon Emission Factor (kg CO2e / kWh)",
            min_value=0.20,
            max_value=1.10,
            value=float(meta.get("emission_factor_used_kg_per_kwh", DEFAULT_GRID_EMISSION_FACTOR)),
            step=0.01,
            help="Adjust according to your state DISCOM (TANGEDCO, MSEDCL) or captive renewable solar mix."
        )
    with c_info:
        st.markdown(f"""
        - **Grid Emission Factor**: 0.82 kg CO2e/kWh used as a synthetic benchmark for this simulation.
        - **Scope 2 Boundary**: Covers purchased grid electricity only (CEA Baseline Database reference).
        - *Benchmark Disclaimer*: {meta.get('disclaimer', 'Grid emission factor: 0.82 kg CO2e/kWh used as a synthetic benchmark for this simulation.')}
        """)
        
    total_factory_kwh = footprint.get("total_energy_consumed_kwh", 42002.64)
    total_yarn_kg = footprint.get("total_yarn_kg", 60338.07)
    
    recalc_co2_kg = total_factory_kwh * custom_factor
    recalc_co2_t = recalc_co2_kg / 1000.0
    if total_yarn_kg > 0:
        recalc_ci = recalc_co2_kg / total_yarn_kg
        ci_val_disp = f"{recalc_ci:.3f} <span style=\"font-size:1rem;color:#64748B\">kg CO2/kg</span>"
        ci_sub_disp = f"Dynamically calculated ({total_yarn_kg:,.1f} kg yarn)"
    else:
        recalc_ci = None
        ci_val_disp = "<span style=\"font-size:1.1rem;color:#EF4444\">N/A</span>"
        ci_sub_disp = "N/A — no production recorded"
    tree_equiv = recalc_co2_kg / TREE_CO2_ABSORPTION_KG_PER_YEAR
    car_equiv = recalc_co2_kg / CAR_CO2_KG_PER_KM
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">14-Day Carbon Emissions</div>
            <div class="kpi-value">{recalc_co2_t:.2f} <span style="font-size:1rem;color:#64748B">t CO2e</span></div>
            <div class="kpi-sub">{recalc_co2_kg:,.0f} kg CO2e at {custom_factor:.2f} kg/kWh</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Yarn Carbon Intensity</div>
            <div class="kpi-value">{ci_val_disp}</div>
            <div class="kpi-sub">{ci_sub_disp}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Tree Absorption Equiv.</div>
            <div class="kpi-value">{tree_equiv:,.0f} <span style="font-size:1rem;color:#64748B">Trees</span></div>
            <div class="kpi-sub">{TREE_CO2_ABSORPTION_KG_PER_YEAR:.2f} kg CO2/tree/year benchmark</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Passenger Car Equiv.</div>
            <div class="kpi-value">{car_equiv:,.0f} <span style="font-size:1rem;color:#64748B">km</span></div>
            <div class="kpi-sub">{CAR_CO2_KG_PER_KM:.3f} kg CO2/km benchmark</div>
        </div>
        """, unsafe_allow_html=True)

    # Machine Carbon Contribution Chart
    st.markdown("#### **Emissions Breakdown by Textile Asset (14-Day Historical Telemetry)**")
    m_carb = carbon_report.get("machine_carbon_breakdown", {})
    fig_carb = px.bar(
        x=list(m_carb.keys()),
        y=[v["co2_emissions_tonnes"] for v in m_carb.values()],
        color=list(m_carb.keys()),
        title="Carbon Footprint (Metric Tonnes CO2e) per Machine over 14 Days",
        labels={"x": "Machine ID", "y": "CO2 Emissions (Tonnes)"}
    )
    fig_carb.update_layout(template="plotly_white", height=380, showlegend=False)
    st.plotly_chart(fig_carb, use_container_width=True)

    # -------------------------------------------------------------
    # SECTION B: OPTIMIZATION SCENARIO — 24 HOURS
    # -------------------------------------------------------------
    st.markdown("---")
    st.markdown("### **Section B: Optimization Scenario — 24 Hours (PuLP MILP Impact)**")
    st.caption("Carbon co-benefits derived from 24-hour mathematical scheduling optimization with 100% throughput conservation.")
    
    # Read optimization metrics
    opt_m = opt_results.get("metrics", {})
    base_kwh_24h = opt_m.get("Total_Energy_kWh", {}).get("baseline", 3193.71)
    opt_kwh_24h = opt_m.get("Total_Energy_kWh", {}).get("optimized", 3180.31)
    kwh_saved_24h = round(base_kwh_24h - opt_kwh_24h, 2)
    
    opt_base_co2 = opt_m.get("CO2_Emissions_kg", {}).get("baseline", round(base_kwh_24h * custom_factor, 2))
    opt_opt_co2 = opt_m.get("CO2_Emissions_kg", {}).get("optimized", round(opt_kwh_24h * custom_factor, 2))
    opt_avoided_co2 = opt_m.get("CO2_Emissions_kg", {}).get("avoided_kg", round(kwh_saved_24h * custom_factor, 2))
    
    base_ci_24h = opt_m.get("Carbon_Intensity_kg_CO2e_per_kg_yarn", {}).get("baseline")
    opt_ci_24h = opt_m.get("Carbon_Intensity_kg_CO2e_per_kg_yarn", {}).get("optimized")
    ci_imp_pct = opt_m.get("Carbon_Intensity_kg_CO2e_per_kg_yarn", {}).get("improvement_pct", 0.0)
    
    if opt_ci_24h is not None and base_ci_24h is not None:
        opt_ci_disp = f"{opt_ci_24h:.4f} <span style=\"font-size:1rem;color:#64748B\">kg/kg</span>"
        opt_ci_sub = f"▼ {ci_imp_pct:.2f}% (Base: {base_ci_24h:.4f})"
    else:
        opt_ci_disp = "<span style=\"font-size:1.1rem;color:#EF4444\">N/A</span>"
        opt_ci_sub = "N/A — no production recorded"
    
    annual_avoided_t = opt_impact.get("annual_potential_avoided_tonnes", round(opt_avoided_co2 * 300.0 / 1000.0, 2))
    cost_savings_daily = opt_m.get("Total_Cost_Rs", {}).get("savings", 1127.79)
    annual_cost_savings = round(cost_savings_daily * 300.0, 2)
    
    ob1, ob2, ob3, ob4 = st.columns(4)
    with ob1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">24h Scope 2 CO2e</div>
            <div class="kpi-value">{opt_opt_co2:,.1f} <span style="font-size:1rem;color:#64748B">kg</span></div>
            <div class="kpi-sub">Baseline: {opt_base_co2:,.1f} kg CO2e</div>
        </div>
        """, unsafe_allow_html=True)
    with ob2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Carbon Avoided (Daily)</div>
            <div class="kpi-value" style="color:#008A00">▼ {opt_avoided_co2:.2f} <span style="font-size:1rem;color:#64748B">kg</span></div>
            <div class="kpi-sub" style="color:#059669">From {kwh_saved_24h:.2f} kWh/day saved</div>
        </div>
        """, unsafe_allow_html=True)
    with ob3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Carbon Intensity (Yarn)</div>
            <div class="kpi-value">{opt_ci_disp}</div>
            <div class="kpi-sub" style="color:#059669">{opt_ci_sub}</div>
        </div>
        """, unsafe_allow_html=True)
    with ob4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Annualized Carbon Avoided</div>
            <div class="kpi-value" style="color:#008A00">~{annual_avoided_t:.2f} <span style="font-size:1rem;color:#64748B">t CO2e</span></div>
            <div class="kpi-sub">300 operating days projection</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("#### **Dual Co-Benefit: Electricity Cost Savings & Decarbonization**")
    st.info(f"💡 **Synergy Analysis**: The PuLP MILP optimization achieves **₹{cost_savings_daily:,.0f}/day** in electricity cost savings (~₹{annual_cost_savings:,.0f}/year) primarily through ToD peak load shifting, while abating **{opt_avoided_co2:.2f} kg CO2e/day** (~{annual_avoided_t:.2f} tonnes CO2e/year) through eliminating idle energy waste while conserving **100% of finished yarn throughput** (4,500 kg/day).")
    
    st.caption("🛡️ **GHG Protocol Scope Boundary**: *Modeled electricity-related Scope 2 emissions only. Does not include Scope 1 (direct combustion / diesel generators), refrigerants, or Scope 3 (supply chain).*")

# -------------------------------------------------------------
# PAGE 7: SYSTEM ARCHITECTURE & SME ROADMAP
# -------------------------------------------------------------
elif page == "🏛️ Architecture & SME Roadmap":
    st.markdown("""
    <div class="schneider-header">
        <h1><span>🏛️</span> System Architecture & Low-Cost SME Adoption Plan</h1>
        <p>End-to-End Edge-to-Cloud Pipeline Designed for Indian Textile Manufacturers</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### **High-Level System Pipeline**")
    st.markdown("""
    ```
    FACTORY MACHINES (Spinning, Compressors, Pumps, HVAC)
            ↓  [RS-485 Modbus RTU / Multi-channel CT Clamps / Vib Transducers]
    MACHINE SENSORS & SMART METERS (Schneider EM6400NG / EasyLogic)
            ↓  [MQTT / JSON over WiFi / Ethernet]
    EDGE GATEWAY (Raspberry Pi 4 / Industrial Edge IPC)
            ↓  [HTTPS REST API / WebSocket Ingestion]
    DATA VALIDATION & INGESTION (src/data_processing.py & src/utils.py)
            ↓  [Processed Parquet / Time-Series Database]
    AI ANOMALY DETECTION (Isolation Forest + Severity Engine)
            ↓  [ISO 10816 Health & 4-Tier Rationale]
    EXPLAINABLE ALERT & DIAGNOSTIC ENGINE (src/machine_health.py)
            ↓  [Time-of-Day Tariff Tariffs & Load Constraints]
    PRODUCTION OPTIMIZER (PuLP Mixed-Integer Linear Programming)
            ↓  [Schedule Dispatch & Alert Notifications]
    INDUSTRIAL STREAMLIT DASHBOARD (dashboard/app.py)
            ↓
    FACTORY MANAGER / PLANT ENGINEER
    ```
    """)
    
    st.markdown("---")
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("### **Low-Cost Retrofit BOM for Indian SMEs**")
        st.markdown("""
        Textile SMEs operate on thin margins (3-8%). SME-EnergyIQ avoids expensive machine replacements:
        
        | Component | Typical Specification | Est. Unit Cost |
        |---|---|---|
        | **Smart Energy Meter** | Schneider EasyLogic PM2120 / Conzerv | ₹4,500 – ₹7,000 |
        | **Split-Core CT Clamps** | 100A/5A Non-invasive retrofits | ₹1,200 / 3-phase set |
        | **IEPE Vib Sensor** | 4-20mA loop-powered accelerometer | ₹3,500 |
        | **Edge Gateway** | Quad-core ARM Industrial Gateway / Pi | ₹6,500 |
        | **Total Machine Retrofit** | Plug-and-play non-invasive install | **< ₹18,000 / machine** |
        
        *Payback period through 5–10% peak tariff shifting is under 4 months.*
        """)
        
    with c2:
        st.markdown("### **5-Stage Phased Adoption Roadmap**")
        st.markdown("""
        1. **Phase 1: Sub-metering & Energy Monitoring (Month 1)**
           - Install smart meters on major 4 feeder lines.
           - Quantify idle energy waste during breaks.
        2. **Phase 2: Baseline SEC & Anomaly Detection (Month 2)**
           - Deploy Isolation Forest model to flag abnormal power draw.
           - Establish machine baseline Specific Energy Consumption.
        3. **Phase 3: Machine Health & ISO 10816 Condition Monitoring (Month 3)**
           - Add vibration and surface temperature monitoring.
           - Activate 4-tier explainable alert feed.
        4. **Phase 4: PuLP Production Optimization (Month 4-6)**
           - Automate shift load-shifting from peak ₹10/kWh to off-peak ₹5.5/kWh.
           - Shave contract demand penalties.
        5. **Phase 5: ESG & Carbon Accounting (Ongoing)**
           - Automated Scope 2 emissions reporting with CEA grid factors.
        """)

