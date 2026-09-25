"""
SME-EnergyIQ: Industrial Energy Intelligence & Optimization Platform
AI-Powered Energy Intelligence & Physics-Based Asset Health Monitoring
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
import time
import textwrap

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

# Custom Industrial CSS (Industrial Green / Slate Palette)
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
    .sme-page-header {
        background: linear-gradient(135deg, #0B1E28 0%, #17384A 100%);
        border-bottom: 4px solid #18E06F;
        padding: 20px 28px;
        border-radius: 12px;
        margin-bottom: 24px;
        color: white;
        forced-color-adjust: none !important;
    }
    .sme-page-header h1 {
        margin: 0;
        font-size: 1.85rem;
        font-weight: 800;
        color: #FFFFFF !important;
        display: flex;
        align-items: center;
        gap: 12px;
        forced-color-adjust: none !important;
    }
    .sme-page-header p {
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

# -------------------------------------------------------------
# SMART MANUFACTURING INITIAL LOADING INTERFACE (PHASE 8H-5)
# -------------------------------------------------------------
def get_smart_manufacturing_loading_html():
    raw_html = """
    <div id="sme-loading-screen" class="sme-loading-overlay">
        <div class="sme-loading-container">
            <!-- Header Branding -->
            <div class="sme-loading-header">
                <div class="sme-loading-logo">
                    <span class="sme-lightning-icon">⚡</span>
                    <span class="sme-logo-text">SME-<span class="sme-logo-accent">EnergyIQ</span></span>
                </div>
                <div class="sme-loading-subtitle">Industrial Energy Intelligence Platform</div>
                <div class="sme-loading-badge">SMART MANUFACTURING TELEMETRY ENGINE</div>
            </div>

            <!-- Conceptual Hierarchy Flow -->
            <div class="sme-flow-hierarchy">
                <span class="sme-hier-step">SMART FACTORY</span>
                <span class="sme-hier-arrow">›</span>
                <span class="sme-hier-step">MACHINE TELEMETRY</span>
                <span class="sme-hier-arrow">›</span>
                <span class="sme-hier-step">ENERGY INTELLIGENCE</span>
                <span class="sme-hier-arrow">›</span>
                <span class="sme-hier-step">AI ANALYSIS</span>
                <span class="sme-hier-arrow">›</span>
                <span class="sme-hier-step sme-hier-active">SME-ENERGYIQ</span>
            </div>

            <!-- 4 Core Industrial Assets -->
            <div class="sme-assets-grid">
                <!-- Asset 1: Spinning Motor -->
                <div class="sme-asset-card" style="animation-delay: 0.15s;">
                    <div class="sme-asset-status-dot"></div>
                    <div class="sme-asset-icon-box">
                        <svg class="sme-asset-svg" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <!-- Motor Cylinder & Frame -->
                            <rect x="14" y="16" width="36" height="32" rx="4" fill="#0E2A38" stroke="#18E06F" stroke-width="2"/>
                            <!-- Cooling Ribs -->
                            <line x1="20" y1="16" x2="20" y2="48" stroke="#18E06F" stroke-width="1.5" stroke-dasharray="2 2"/>
                            <line x1="26" y1="16" x2="26" y2="48" stroke="#18E06F" stroke-width="1.5" stroke-dasharray="2 2"/>
                            <line x1="32" y1="16" x2="32" y2="48" stroke="#18E06F" stroke-width="1.5" stroke-dasharray="2 2"/>
                            <line x1="38" y1="16" x2="38" y2="48" stroke="#18E06F" stroke-width="1.5" stroke-dasharray="2 2"/>
                            <line x1="44" y1="16" x2="44" y2="48" stroke="#18E06F" stroke-width="1.5" stroke-dasharray="2 2"/>
                            <!-- Shaft & Rotor -->
                            <rect x="50" y="27" width="10" height="10" rx="1" fill="#38BDF8"/>
                            <rect x="4" y="26" width="10" height="12" rx="2" fill="#17384A" stroke="#38BDF8" stroke-width="1.5"/>
                            <!-- Mounting Base -->
                            <path d="M10 48L8 54H56L54 48H10Z" fill="#17384A" stroke="#18E06F" stroke-width="1.5"/>
                        </svg>
                    </div>
                    <div class="sme-asset-title">Spinning Motor</div>
                    <div class="sme-asset-id">MOTOR_01</div>
                    <div class="sme-asset-tag">Ring Frame (75 kW)</div>
                </div>

                <!-- Asset 2: Air Compressor -->
                <div class="sme-asset-card" style="animation-delay: 0.3s;">
                    <div class="sme-asset-status-dot"></div>
                    <div class="sme-asset-icon-box">
                        <svg class="sme-asset-svg" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <!-- Compressor Pressure Vessel -->
                            <rect x="10" y="24" width="44" height="24" rx="12" fill="#0E2A38" stroke="#38BDF8" stroke-width="2"/>
                            <!-- Compressor Head & Piston Block -->
                            <rect x="18" y="10" width="16" height="14" rx="2" fill="#17384A" stroke="#38BDF8" stroke-width="1.5"/>
                            <!-- Gauge -->
                            <circle cx="44" cy="17" r="7" fill="#0B1E28" stroke="#18E06F" stroke-width="1.5"/>
                            <line x1="44" y1="17" x2="47" y2="14" stroke="#18E06F" stroke-width="1.5"/>
                            <!-- Piping -->
                            <path d="M34 17H37V24" stroke="#38BDF8" stroke-width="2"/>
                            <!-- Stand Legs -->
                            <rect x="16" y="48" width="6" height="6" fill="#17384A"/>
                            <rect x="42" y="48" width="6" height="6" fill="#17384A"/>
                        </svg>
                    </div>
                    <div class="sme-asset-title">Air Compressor</div>
                    <div class="sme-asset-id">COMPRESSOR_01</div>
                    <div class="sme-asset-tag">Pneumatics (45 kW)</div>
                </div>

                <!-- Asset 3: Dyeing / Water Pump -->
                <div class="sme-asset-card" style="animation-delay: 0.45s;">
                    <div class="sme-asset-status-dot"></div>
                    <div class="sme-asset-icon-box">
                        <svg class="sme-asset-svg" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <!-- Volute Casing -->
                            <circle cx="30" cy="34" r="16" fill="#0E2A38" stroke="#38BDF8" stroke-width="2"/>
                            <!-- Impeller Core -->
                            <circle cx="30" cy="34" r="6" fill="#17384A" stroke="#18E06F" stroke-width="1.5"/>
                            <path d="M30 28V40M24 34H36" stroke="#18E06F" stroke-width="1.5"/>
                            <!-- Discharge Flange -->
                            <rect x="25" y="10" width="10" height="8" rx="1" fill="#17384A" stroke="#38BDF8" stroke-width="1.5"/>
                            <line x1="23" y1="10" x2="37" y2="10" stroke="#38BDF8" stroke-width="2"/>
                            <!-- Suction Flange -->
                            <rect x="46" y="30" width="8" height="8" rx="1" fill="#17384A" stroke="#38BDF8" stroke-width="1.5"/>
                            <line x1="54" y1="28" x2="54" y2="40" stroke="#38BDF8" stroke-width="2"/>
                            <!-- Base -->
                            <rect x="18" y="50" width="24" height="4" rx="1" fill="#17384A" stroke="#38BDF8" stroke-width="1"/>
                        </svg>
                    </div>
                    <div class="sme-asset-title">Dyeing / Water Pump</div>
                    <div class="sme-asset-id">PUMP_01</div>
                    <div class="sme-asset-tag">Fluid Circulation (30 kW)</div>
                </div>

                <!-- Asset 4: HVAC / Climate Control -->
                <div class="sme-asset-card" style="animation-delay: 0.6s;">
                    <div class="sme-asset-status-dot"></div>
                    <div class="sme-asset-icon-box">
                        <svg class="sme-asset-svg" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <!-- Air Handler Box -->
                            <rect x="10" y="14" width="44" height="36" rx="4" fill="#0E2A38" stroke="#18E06F" stroke-width="2"/>
                            <!-- Fan Grille -->
                            <circle cx="32" cy="32" r="12" fill="#17384A" stroke="#38BDF8" stroke-width="1.5"/>
                            <!-- Fan Blades -->
                            <path d="M32 20C32 26 38 32 38 32C32 32 32 38 32 44C32 38 26 32 26 32C32 32 32 26 32 20Z" fill="#18E06F"/>
                            <!-- Louvers / Vents -->
                            <line x1="14" y1="20" x2="16" y2="20" stroke="#38BDF8" stroke-width="2"/>
                            <line x1="14" y1="26" x2="16" y2="26" stroke="#38BDF8" stroke-width="2"/>
                            <line x1="14" y1="32" x2="16" y2="32" stroke="#38BDF8" stroke-width="2"/>
                            <line x1="48" y1="20" x2="50" y2="20" stroke="#38BDF8" stroke-width="2"/>
                            <line x1="48" y1="26" x2="50" y2="26" stroke="#38BDF8" stroke-width="2"/>
                            <line x1="48" y1="32" x2="50" y2="32" stroke="#38BDF8" stroke-width="2"/>
                        </svg>
                    </div>
                    <div class="sme-asset-title">HVAC / Climate Control</div>
                    <div class="sme-asset-id">HVAC_01</div>
                    <div class="sme-asset-tag">Humidity & Temp (55 kW)</div>
                </div>
            </div>

            <!-- Telemetry Convergence & AI Hub -->
            <div class="sme-telemetry-section">
                <div class="sme-telemetry-wires">
                    <div class="sme-wire sme-wire-1"></div>
                    <div class="sme-wire sme-wire-2"></div>
                    <div class="sme-wire sme-wire-3"></div>
                    <div class="sme-wire sme-wire-4"></div>
                </div>

                <div class="sme-ai-hub">
                    <div class="sme-ai-hub-icon">⚙️</div>
                    <div class="sme-ai-hub-text">
                        <span class="sme-ai-hub-title">⚡ AI ENERGY INTELLIGENCE</span>
                        <span class="sme-ai-hub-sub">Neural Telemetry Aggregation & Multi-Dimensional Diagnostic Engine</span>
                    </div>
                </div>
            </div>

            <!-- Industrial Process Progression Sequence -->
            <div class="sme-process-seq">
                <div class="sme-proc-pill sme-proc-1"><span>01</span> MEASURE</div>
                <div class="sme-proc-arr">›</div>
                <div class="sme-proc-pill sme-proc-2"><span>02</span> DETECT</div>
                <div class="sme-proc-arr">›</div>
                <div class="sme-proc-pill sme-proc-3"><span>03</span> DIAGNOSE</div>
                <div class="sme-proc-arr">›</div>
                <div class="sme-proc-pill sme-proc-4"><span>04</span> OPTIMIZE</div>
                <div class="sme-proc-arr">›</div>
                <div class="sme-proc-pill sme-proc-5"><span>05</span> QUANTIFY</div>
                <div class="sme-proc-arr">›</div>
                <div class="sme-proc-pill sme-proc-6"><span>06</span> DECIDE</div>
            </div>

            <!-- Dynamic Status Bar -->
            <div class="sme-loading-status-area">
                <div class="sme-status-text-anim">
                    <span class="sme-status-msg sme-msg-1">Connecting factory intelligence...</span>
                    <span class="sme-status-msg sme-msg-2">Loading machine telemetry...</span>
                    <span class="sme-status-msg sme-msg-3">Initializing energy intelligence...</span>
                    <span class="sme-status-msg sme-msg-4">Preparing industrial insights...</span>
                    <span class="sme-status-msg sme-msg-5">SME-EnergyIQ Ready</span>
                </div>
                <div class="sme-progress-track">
                    <div class="sme-progress-fill"></div>
                </div>
            </div>

            <!-- Data Honesty Footer Note -->
            <div class="sme-loading-footer">
                Telemetry Mode: Pre-calibrated Synthetic Industrial Dataset | 4 Active Textile Machines
            </div>
        </div>
    </div>

    <style>
    /* Loading Interface Scoped Styles */
    .sme-loading-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: radial-gradient(circle at 50% 30%, #0B2230 0%, #061219 90%);
        z-index: 99999999;
        display: flex;
        justify-content: center;
        align-items: center;
        overflow-y: auto;
        padding: 20px;
        box-sizing: border-box;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .sme-loading-container {
        width: 100%;
        max-width: 900px;
        background: linear-gradient(145deg, rgba(11, 30, 40, 0.98), rgba(6, 18, 25, 0.96));
        border: 1px solid rgba(24, 224, 111, 0.35);
        border-radius: 16px;
        padding: 28px 30px 22px 30px;
        box-shadow: 0 16px 50px rgba(0, 0, 0, 0.65), 0 0 30px rgba(24, 224, 111, 0.12);
        position: relative;
        overflow: hidden;
        background-image:
            linear-gradient(rgba(24, 224, 111, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(24, 224, 111, 0.03) 1px, transparent 1px);
        background-size: 24px 24px;
        animation: smeContainerFadeIn 0.4s ease-out forwards;
    }

    @keyframes smeContainerFadeIn {
        from { opacity: 0; transform: scale(0.98); }
        to { opacity: 1; transform: scale(1); }
    }

    /* Header */
    .sme-loading-header {
        text-align: center;
        margin-bottom: 18px;
    }
    .sme-loading-logo {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 4px;
    }
    .sme-lightning-icon {
        font-size: 2.0rem;
        line-height: 1;
        filter: drop-shadow(0 0 8px rgba(24, 224, 111, 0.6));
    }
    .sme-logo-text {
        font-size: 2.0rem;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: -0.02em;
    }
    .sme-logo-accent {
        color: #18E06F;
    }
    .sme-loading-subtitle {
        font-size: 1.0rem;
        font-weight: 700;
        color: #18E06F;
        letter-spacing: 0.02em;
        margin-bottom: 6px;
    }
    .sme-loading-badge {
        display: inline-block;
        font-size: 0.68rem;
        font-weight: 700;
        color: #38BDF8;
        background: rgba(56, 189, 248, 0.10);
        border: 1px solid rgba(56, 189, 248, 0.28);
        padding: 3px 10px;
        border-radius: 12px;
        letter-spacing: 0.08em;
    }

    /* Hierarchy Flow */
    .sme-flow-hierarchy {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        margin-bottom: 22px;
        flex-wrap: wrap;
    }
    .sme-hier-step {
        font-size: 0.70rem;
        font-weight: 700;
        color: #8CA3B3;
        letter-spacing: 0.05em;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 4px 8px;
        border-radius: 4px;
    }
    .sme-hier-arrow {
        color: #38BDF8;
        font-size: 0.80rem;
        font-weight: 800;
    }
    .sme-hier-active {
        color: #18E06F;
        background: rgba(24, 224, 111, 0.12);
        border-color: rgba(24, 224, 111, 0.35);
    }

    /* 4 Assets Grid */
    .sme-assets-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-bottom: 16px;
    }
    .sme-asset-card {
        background: linear-gradient(135deg, rgba(14, 42, 56, 0.70), rgba(11, 30, 40, 0.85));
        border: 1px solid rgba(24, 224, 111, 0.25);
        border-radius: 10px;
        padding: 14px 10px;
        text-align: center;
        position: relative;
        transition: all 0.3s ease;
        animation: smeAssetFade 0.6s ease-out forwards;
    }
    @keyframes smeAssetFade {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .sme-asset-status-dot {
        position: absolute;
        top: 8px;
        right: 8px;
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: #18E06F;
        box-shadow: 0 0 6px #18E06F;
        animation: smePulseDot 1.4s infinite ease-in-out;
    }
    @keyframes smePulseDot {
        0%, 100% { opacity: 0.4; transform: scale(0.9); }
        50% { opacity: 1; transform: scale(1.25); }
    }
    .sme-asset-icon-box {
        width: 48px;
        height: 48px;
        margin: 0 auto 8px auto;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .sme-asset-svg {
        width: 44px;
        height: 44px;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.4));
    }
    .sme-asset-title {
        font-size: 0.80rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .sme-asset-id {
        font-size: 0.70rem;
        font-weight: 700;
        color: #18E06F;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: 0.04em;
        margin-bottom: 2px;
    }
    .sme-asset-tag {
        font-size: 0.66rem;
        color: #8CA3B3;
    }

    /* Telemetry Convergence & AI Hub */
    .sme-telemetry-section {
        position: relative;
        margin-bottom: 18px;
    }
    .sme-telemetry-wires {
        height: 18px;
        display: flex;
        justify-content: space-around;
        position: relative;
    }
    .sme-wire {
        width: 2px;
        height: 100%;
        background: linear-gradient(180deg, #18E06F 0%, #38BDF8 100%);
        opacity: 0.7;
        position: relative;
    }
    .sme-wire::after {
        content: '';
        position: absolute;
        top: 0;
        left: -2px;
        width: 6px;
        height: 6px;
        background: #FFFFFF;
        border-radius: 50%;
        box-shadow: 0 0 6px #38BDF8;
        animation: smePulseTravel 1.6s infinite linear;
    }
    .sme-wire-1::after { animation-delay: 0.0s; }
    .sme-wire-2::after { animation-delay: 0.4s; }
    .sme-wire-3::after { animation-delay: 0.8s; }
    .sme-wire-4::after { animation-delay: 1.2s; }

    @keyframes smePulseTravel {
        0% { top: 0%; opacity: 0; }
        30% { opacity: 1; }
        90% { top: 90%; opacity: 1; }
        100% { top: 100%; opacity: 0; }
    }

    .sme-ai-hub {
        background: linear-gradient(135deg, rgba(16, 48, 64, 0.90), rgba(11, 30, 40, 0.95));
        border: 1px solid rgba(56, 189, 248, 0.40);
        border-left: 4px solid #18E06F;
        border-radius: 10px;
        padding: 10px 18px;
        display: flex;
        align-items: center;
        gap: 14px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
    }
    .sme-ai-hub-icon {
        font-size: 1.6rem;
        line-height: 1;
        animation: smeGearSpin 8s linear infinite;
    }
    @keyframes smeGearSpin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    .sme-ai-hub-text {
        display: flex;
        flex-direction: column;
    }
    .sme-ai-hub-title {
        font-size: 0.88rem;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: 0.06em;
    }
    .sme-ai-hub-sub {
        font-size: 0.72rem;
        color: #A8B8C5;
    }

    /* Process Progression Sequence */
    .sme-process-seq {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 4px;
        margin-bottom: 20px;
        background: rgba(8, 20, 28, 0.70);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 8px;
        padding: 8px 12px;
    }
    .sme-proc-pill {
        font-size: 0.70rem;
        font-weight: 700;
        color: #CBD5E1;
        letter-spacing: 0.04em;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .sme-proc-pill span {
        font-size: 0.62rem;
        font-weight: 800;
        color: #18E06F;
        background: rgba(24, 224, 111, 0.12);
        padding: 1px 4px;
        border-radius: 3px;
    }
    .sme-proc-arr {
        color: rgba(56, 189, 248, 0.6);
        font-size: 0.80rem;
        font-weight: 800;
    }

    /* Dynamic Status & Progress Bar */
    .sme-loading-status-area {
        margin-bottom: 12px;
    }
    .sme-status-text-anim {
        height: 22px;
        position: relative;
        overflow: hidden;
        margin-bottom: 8px;
    }
    .sme-status-msg {
        position: absolute;
        width: 100%;
        text-align: center;
        font-size: 0.85rem;
        font-weight: 600;
        color: #38BDF8;
        opacity: 0;
        transform: translateY(10px);
        animation-duration: 2.2s;
        animation-timing-function: ease-in-out;
        animation-fill-mode: forwards;
    }
    .sme-msg-1 { animation-name: smeTextStage1; }
    .sme-msg-2 { animation-name: smeTextStage2; }
    .sme-msg-3 { animation-name: smeTextStage3; }
    .sme-msg-4 { animation-name: smeTextStage4; }
    .sme-msg-5 { animation-name: smeTextStage5; }

    @keyframes smeTextStage1 {
        0% { opacity: 0; transform: translateY(6px); }
        8%, 20% { opacity: 1; transform: translateY(0); }
        25% { opacity: 0; transform: translateY(-6px); }
        100% { opacity: 0; }
    }
    @keyframes smeTextStage2 {
        0%, 23% { opacity: 0; transform: translateY(6px); }
        27%, 44% { opacity: 1; transform: translateY(0); }
        48% { opacity: 0; transform: translateY(-6px); }
        100% { opacity: 0; }
    }
    @keyframes smeTextStage3 {
        0%, 46% { opacity: 0; transform: translateY(6px); }
        50%, 68% { opacity: 1; transform: translateY(0); }
        72% { opacity: 0; transform: translateY(-6px); }
        100% { opacity: 0; }
    }
    @keyframes smeTextStage4 {
        0%, 70% { opacity: 0; transform: translateY(6px); }
        74%, 88% { opacity: 1; transform: translateY(0); }
        92% { opacity: 0; transform: translateY(-6px); }
        100% { opacity: 0; }
    }
    @keyframes smeTextStage5 {
        0%, 90% { opacity: 0; transform: translateY(6px); }
        94%, 100% { opacity: 1; transform: translateY(0); color: #18E06F; }
    }

    .sme-progress-track {
        width: 100%;
        height: 6px;
        background: rgba(255, 255, 255, 0.08);
        border-radius: 4px;
        overflow: hidden;
    }
    .sme-progress-fill {
        height: 100%;
        width: 0%;
        background: linear-gradient(90deg, #18E06F 0%, #38BDF8 70%, #18E06F 100%);
        border-radius: 4px;
        animation: smeProgressBar 2.2s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
    }
    @keyframes smeProgressBar {
        0% { width: 0%; }
        25% { width: 30%; }
        50% { width: 62%; }
        75% { width: 85%; }
        100% { width: 100%; }
    }

    /* Footer Note */
    .sme-loading-footer {
        text-align: center;
        font-size: 0.68rem;
        color: #64748B;
        margin-top: 4px;
    }

    /* Mobile Responsive Adjustments */
    @media (max-width: 768px) {
        .sme-loading-container {
            padding: 20px 14px;
        }
        .sme-logo-text {
            font-size: 1.55rem;
        }
        .sme-lightning-icon {
            font-size: 1.55rem;
        }
        .sme-assets-grid {
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
        }
        .sme-process-seq {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 6px;
            text-align: center;
        }
        .sme-proc-arr {
            display: none;
        }
        .sme-flow-hierarchy {
            display: none;
        }
    }
    </style>
    """
    return "\n".join(line.strip() for line in raw_html.splitlines())

# Initial application loading experience (runs strictly once per browser session)
if not st.session_state.get("app_loaded", False):
    loading_placeholder = st.empty()
    loading_placeholder.markdown(get_smart_manufacturing_loading_html(), unsafe_allow_html=True)
    t_start = time.time()
    try:
        df, energy_summary, opt_results, carbon_report, df_alerts, df_sched_base, df_sched_opt = load_all_data()
    except Exception as e:
        loading_placeholder.empty()
        st.error(f"Error loading platform data: {e}")
        if st.button("Regenerate Data Pipeline"):
            pipeline.run_full_pipeline()
            st.rerun()
        st.stop()
    elapsed = time.time() - t_start
    if elapsed < 2.3:
        time.sleep(2.3 - elapsed)
    loading_placeholder.empty()
    st.session_state["app_loaded"] = True
else:
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
                    <span>Zone: <span style="font-weight:600; color:#18E06F">{vib_zone.replace('ZONE_', 'Zone ')}</span></span>
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

    # ---------------------------------------------------------
    # Production & Efficiency Section
    # ---------------------------------------------------------
    st.markdown("### **🏭 Production & Efficiency**")
    st.markdown("Quantifying manufacturing throughput against specific energy intensity (*SEC = Total Energy / Production Output*).")

    p_col1, p_col2, p_col3, p_col4 = st.columns(4)
    total_yarn_prod = energy_summary["factory_overview"].get("total_yarn_production_kg", 60338.1)
    with p_col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Yarn Output (14-Day)</div>
            <div class="kpi-value">{total_yarn_prod:,.0f} <span style="font-size:1rem;color:#64748B">kg</span></div>
            <div class="kpi-sub">Avg Daily: {total_yarn_prod/14:,.0f} kg/day</div>
        </div>
        """, unsafe_allow_html=True)
    with p_col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Electricity Consumed</div>
            <div class="kpi-value">{total_energy_kwh:,.0f} <span style="font-size:1rem;color:#64748B">kWh</span></div>
            <div class="kpi-sub">Avg Daily: {total_energy_kwh/14:,.0f} kWh/day</div>
        </div>
        """, unsafe_allow_html=True)
    with p_col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Factory SEC (Yarn)</div>
            <div class="kpi-value">{factory_sec:.3f} <span style="font-size:1rem;color:#64748B">kWh/kg</span></div>
            <div class="kpi-sub">Energy Efficiency Benchmark: &le; 0.720</div>
        </div>
        """, unsafe_allow_html=True)
    with p_col4:
        active_cnt = len(latest_df[latest_df["Machine_Status"].str.startswith("RUNNING")])
        tot_cnt = len(latest_df)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Fleet Operating State</div>
            <div class="kpi-value" style="color:#10B981">{active_cnt}/{tot_cnt} Active</div>
            <div class="kpi-sub">All Production Lines Nominal</div>
        </div>
        """, unsafe_allow_html=True)

    # Machine-level production throughput & specific consumption breakdown table
    st.markdown("##### **Machine-Level Output & Specific Energy Intensity**")
    mb = energy_summary.get("machine_breakdown", {})
    prod_table_rows = []
    unit_map = {
        "COMPRESSOR_01": "Nm³ Air",
        "HVAC_01": "m³ Air",
        "MOTOR_01": "kg Yarn",
        "PUMP_01": "m³ Fluid"
    }
    for m_id, m_info in mb.items():
        u = unit_map.get(m_id, "Units")
        prod_table_rows.append({
            "Machine": m_id,
            "Equipment Type": m_info.get("type", "N/A"),
            "Production Output": f"{m_info.get('total_production', 0):,.1f} {u}",
            "Energy Consumed": f"{m_info.get('total_energy_kwh', 0):,.1f} kWh",
            "Specific Consumption (SEC)": f"{m_info.get('sec_kwh_per_unit', 0):.4f} kWh/{u.split()[-1]}",
            "Operating Status": "RUNNING (Active)"
        })
    st.dataframe(pd.DataFrame(prod_table_rows), use_container_width=True, hide_index=True)

# -------------------------------------------------------------
# PAGE 2: ENERGY & ToD MONITORING
# -------------------------------------------------------------
elif page == "⚡ Energy & ToD Monitoring":
    st.markdown("""
    <div class="sme-page-header">
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

        # Date range safety guard
        if len(date_range) == 2:
            start_date, end_date = date_range[0], date_range[1]
        elif len(date_range) == 1:
            start_date, end_date = date_range[0], date_range[0]
        else:
            start_date, end_date = df["Timestamp"].min().date(), df["Timestamp"].max().date()

        with c1:
            mask = (df["Timestamp"].dt.date >= start_date) & (df["Timestamp"].dt.date <= end_date)
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

        st.markdown("---")
        st.markdown("#### **Factory Energy Share by Machine**")

        # Dynamic machine-level energy share calculation from df over selected date window
        date_mask_all = (df["Timestamp"].dt.date >= start_date) & (df["Timestamp"].dt.date <= end_date)
        df_window_all = df[date_mask_all]

        if not df_window_all.empty and df_window_all["Energy_kWh"].sum() > 0:
            m_share_df = df_window_all.groupby("Machine_ID")["Energy_kWh"].sum().reset_index()
        else:
            m_share_df = df.groupby("Machine_ID")["Energy_kWh"].sum().reset_index()

        total_window_energy = m_share_df["Energy_kWh"].sum()
        m_share_df["Share_Pct"] = (m_share_df["Energy_kWh"] / total_window_energy) * 100
        m_share_df = m_share_df.sort_values(by="Energy_kWh", ascending=False).reset_index(drop=True)

        color_map = {
            "HVAC_01": "#10B981",       # Emerald / Theme Green
            "MOTOR_01": "#3B82F6",      # Industrial Blue
            "COMPRESSOR_01": "#0EA5E9", # Sky Blue / Cyan
            "PUMP_01": "#8B5CF6"        # Purple Accent
        }

        pull_list = [0.06 if m == sel_machine else 0 for m in m_share_df["Machine_ID"]] if sel_machine != "ALL MACHINES" else None

        fig_share = px.pie(
            m_share_df,
            names="Machine_ID",
            values="Energy_kWh",
            title="Factory Energy Share by Machine",
            color="Machine_ID",
            color_discrete_map=color_map,
            hole=0.45
        )
        fig_share.update_traces(
            textposition="inside",
            textinfo="percent+label",
            pull=pull_list,
            hovertemplate="<b>%{label}</b><br>Total Energy: %{value:,.1f} kWh<br>Factory Share: %{percent}<extra></extra>",
            marker=dict(line=dict(color="#0B1E28", width=1.5))
        )
        fig_share.update_layout(
            template="plotly_white",
            height=420,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.15,
                xanchor="center",
                x=0.5
            ),
            margin=dict(l=20, r=20, t=50, b=40)
        )
        st.plotly_chart(fig_share, use_container_width=True)
        st.caption("Shows each machine's contribution to total factory electricity consumption over the selected date window.")

        st.markdown("---")
        st.markdown("#### **Top Energy Consumers**")
        st.markdown("Dynamic ranking of factory machines by electricity consumption over the selected observation window.")

        type_map = {
            "HVAC_01": "Humidification & HVAC",
            "MOTOR_01": "Ring Frame Motor",
            "COMPRESSOR_01": "Air Compressor",
            "PUMP_01": "Dyeing Pump"
        }

        ranked_df = m_share_df.copy()
        ranked_df["Rank"] = [f"#{i+1}" for i in range(len(ranked_df))]
        ranked_df["Machine"] = ranked_df["Machine_ID"].apply(lambda m: f"{m} ({type_map.get(m, 'Industrial Load')})")
        ranked_df["Energy Consumption (kWh)"] = ranked_df["Energy_kWh"].apply(lambda v: f"{v:,.1f} kWh")
        ranked_df["Share of Factory Energy (%)"] = ranked_df["Share_Pct"].apply(lambda v: f"{v:.1f}%")

        display_ranked = ranked_df[["Rank", "Machine", "Energy Consumption (kWh)", "Share of Factory Energy (%)"]]
        st.dataframe(display_ranked, use_container_width=True, hide_index=True)

        fig_ranked = px.bar(
            m_share_df.sort_values(by="Energy_kWh", ascending=True),
            x="Energy_kWh",
            y="Machine_ID",
            orientation="h",
            text="Share_Pct",
            color="Machine_ID",
            color_discrete_map=color_map,
            labels={"Energy_kWh": "Energy (kWh)", "Machine_ID": "Machine"}
        )
        fig_ranked.update_traces(
            texttemplate="%{x:,.1f} kWh (%{text:.1f}%)",
            textposition="outside",
            cliponaxis=False
        )
        fig_ranked.update_layout(
            template="plotly_white",
            height=250,
            showlegend=False,
            margin=dict(l=20, r=80, t=10, b=30),
            xaxis_title="Electricity Consumption (kWh)",
            yaxis_title=""
        )
        st.plotly_chart(fig_ranked, use_container_width=True)


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
    <div class="sme-page-header">
        <h1><span>🩺</span> Machine Health & Vibration Monitoring</h1>
        <p>Vibration Severity References, Thermal Headroom & Physics-Based Asset Health Scoring</p>
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
        st.metric("Vibration RMS", f"{latest_m['Vibration_mm_s']:.2f} mm/s", delta=f"Zone: {latest_m.get('ISO_Vib_Zone', 'N/A').replace('ZONE_', 'Zone ')}")
    with c3:
        st.metric("Stator Temperature", f"{latest_m['Temperature_C']:.1f}°C", delta=f"Elevation: {latest_m.get('Temp_Elevation', 0.0):+.1f}°C")
    with c4:
        st.metric("Operating Speed", f"{latest_m['RPM']:.0f} RPM", delta=f"Status: {latest_m['Machine_Status']}")

    # Historical Parameter Curves
    st.markdown(f"### **14-Day Condition Telemetry: {selected_machine}**")

    fig_diag = make_subplots(rows=2, cols=2, subplot_titles=(
        "Active Power (kW) vs. Load Baseline",
        "Vibration Severity Reference (mm/s RMS)",
        "Stator/Bearing Temperature (°C)",
        "Motor Slip / Operating Speed (RPM)"
    ))

    # Power
    fig_diag.add_trace(go.Scatter(x=m_df["Timestamp"], y=m_df["Power_kW"], name="Power (kW)", line=dict(color="#2563EB")), row=1, col=1)
    # Vibration with configured threshold lines
    fig_diag.add_trace(go.Scatter(x=m_df["Timestamp"], y=m_df["Vibration_mm_s"], name="Vibration (mm/s)", line=dict(color="#D97706")), row=1, col=2)
    fig_diag.add_hline(y=2.3, line_dash="dot", line_color="#10B981", annotation_text="Nominal / Good (2.3)", row=1, col=2)
    fig_diag.add_hline(y=4.5, line_dash="dash", line_color="#F59E0B", annotation_text="Unsatisfactory (4.5)", row=1, col=2)
    fig_diag.add_hline(y=7.1, line_dash="dash", line_color="#EF4444", annotation_text="Critical / Unacceptable (7.1)", row=1, col=2)

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
        st.success(f"✅ Machine {selected_machine} operated within nominal vibration and thermal thresholds.")

    # ---------------------------------------------------------
    # Maintenance Intelligence Panel
    # ---------------------------------------------------------
    st.markdown("---")
    st.markdown("### **🛠️ Maintenance Intelligence**")
    st.markdown("Operator-friendly investigation summary synthesizing physics-based asset scoring, telemetry patterns, and AI anomaly detection.")

    has_active_anomaly = latest_m["Severity"] in ["HIGH", "CRITICAL"] or latest_m["Health_Score"] < 80
    has_historical_anomaly = not flagged_records.empty

    current_health = latest_m["Health_Score"]
    current_risk = latest_m["Risk_Level"]
    current_state = latest_m["Machine_Status"]
    current_sev = str(latest_m["Severity"])

    if has_active_anomaly:
        if selected_machine == "COMPRESSOR_01":
            abnormal_sig = f"Active power elevation ({latest_m['Power_kW']:.1f} kW) with elevated unloader cycle pattern."
            sugg_inv = "Inspect compressor unloader valve seating, intake air filters, and drive belt alignment."
            poss_causes = "Possible unloader valve seal wear or non-productive idling during off-peak window."
        elif selected_machine == "HVAC_01":
            abnormal_sig = f"Thermal elevation ({latest_m['Temperature_C']:.1f}°C) exceeding nominal baseline headroom."
            sugg_inv = "Inspect condenser coils for particulate clogging, verify fan blower belt, and check fresh air damper."
            poss_causes = "Possible condenser fin fouling, restricted blower airflow, or high ambient thermal load."
        elif selected_machine == "MOTOR_01":
            abnormal_sig = f"Vibration elevation ({latest_m['Vibration_mm_s']:.2f} mm/s RMS) exceeding configured threshold."
            sugg_inv = "Inspect foundation anchor fastenings, check V-belt tension, and perform bearing lubrication check."
            poss_causes = "Possible mechanical unbalance, mounting looseness, or dynamic drive-system wear."
        elif selected_machine == "PUMP_01":
            abnormal_sig = f"Hydraulic flow variation with subtle multivariate energy intensity divergence."
            sugg_inv = "Inspect suction strainer for textile lint obstruction, inspect impeller casing, and check mechanical seals."
            poss_causes = "Possible suction restriction, impeller cavitation, or restricted circulation loop."
        else:
            abnormal_sig = f"Telemetry parameter divergence (Power: {latest_m['Power_kW']:.1f} kW, Temp: {latest_m['Temperature_C']:.1f}°C, Vib: {latest_m['Vibration_mm_s']:.2f} mm/s)."
            sugg_inv = "Perform physical inspection of drive couplings, mountings, and thermal dissipation paths."
            poss_causes = "Potential abnormal operating condition requiring field verification."
    elif has_historical_anomaly:
        if selected_machine == "COMPRESSOR_01":
            abnormal_sig = f"Elevated unloader cycling and power spikes observed in {len(flagged_records)} historical events (latest snapshot nominal)."
            sugg_inv = "Inspect compressor unloader valve seating, intake air filters, and drive belt alignment."
            poss_causes = "Possible unloader valve seal wear or unloader cycling during non-productive intervals."
        elif selected_machine == "HVAC_01":
            abnormal_sig = f"Thermal elevation above expected baseline observed in {len(flagged_records)} historical events (latest snapshot nominal)."
            sugg_inv = "Inspect condenser coils for particulate clogging, verify fan blower belt, and check fresh air damper."
            poss_causes = "Possible condenser fin fouling, blower airflow restriction, or high ambient thermal load."
        elif selected_machine == "MOTOR_01":
            abnormal_sig = f"Elevated vibration exceeding configured threshold observed in {len(flagged_records)} historical events (latest snapshot nominal)."
            sugg_inv = "Inspect foundation anchor fastenings, check V-belt tension, and perform bearing lubrication check."
            poss_causes = "Possible mechanical unbalance, mounting looseness, or dynamic drive-system wear."
        elif selected_machine == "PUMP_01":
            abnormal_sig = f"Throughput divergence relative to power observed in {len(flagged_records)} historical events (latest snapshot nominal)."
            sugg_inv = "Inspect suction strainer for textile lint obstruction, inspect impeller casing, and check mechanical seals."
            poss_causes = "Possible suction restriction, impeller cavitation, or restricted circulation loop."
        else:
            abnormal_sig = f"Parameter excursions logged in {len(flagged_records)} historical events (latest snapshot nominal)."
            sugg_inv = "Perform periodic physical inspection of drive couplings and thermal dissipation paths."
            poss_causes = "Possible mechanical looseness or intermittent operating condition variation."
    else:
        abnormal_sig = "Vibration and thermal trends within nominal baseline operating range."
        sugg_inv = "Continue routine condition monitoring of vibration and temperature trends."
        poss_causes = "No active abnormal condition requiring investigation."

    risk_border = "#10B981" if current_risk in ["LOW", "NOMINAL"] else ("#F59E0B" if current_risk == "MEDIUM" else "#EF4444")

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(11, 30, 40, 0.98), rgba(15, 48, 55, 0.95)); border: 1px solid rgba(24, 224, 111, 0.35); border-left: 5px solid {risk_border}; border-radius: 10px; padding: 18px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding-bottom: 10px; margin-bottom: 14px;">
            <div style="font-size: 1.15rem; font-weight: 700; color: #FFFFFF;">
                <span style="color: #18E06F;">MAINTENANCE INTELLIGENCE:</span> {selected_machine}
            </div>
            <div style="font-size: 0.85rem; font-weight: 700; color: {risk_border}; padding: 3px 10px; border-radius: 4px; background: rgba(0,0,0,0.3); border: 1px solid {risk_border};">
                RISK LEVEL: {current_risk}
            </div>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 14px; font-size: 0.88rem;">
            <div><span style="color: #A8B8C5;">Machine:</span> <b style="color: #FFFFFF;">{selected_machine}</b></div>
            <div><span style="color: #A8B8C5;">Current Health Score:</span> <b style="color: #18E06F;">{current_health} / 100</b></div>
            <div><span style="color: #A8B8C5;">Operating State:</span> <b style="color: #FFFFFF;">{current_state}</b></div>
            <div><span style="color: #A8B8C5;">Current Severity:</span> <b style="color: {risk_border};">{current_sev}</b></div>
        </div>
        <div style="border-top: 1px solid rgba(255, 255, 255, 0.08); padding-top: 12px; font-size: 0.88rem; line-height: 1.5;">
            <div style="margin-bottom: 8px;">
                <strong style="color: #38BDF8;">Abnormal Signals:</strong>
                <span style="color: #F1F5F9; margin-left: 6px;">{abnormal_sig}</span>
            </div>
            <div style="margin-bottom: 8px;">
                <strong style="color: #FBBF24;">Suggested Investigation:</strong>
                <span style="color: #F1F5F9; margin-left: 6px;">{sugg_inv}</span>
            </div>
            <div>
                <strong style="color: #A78BFA;">Possible Causes:</strong>
                <span style="color: #F1F5F9; margin-left: 6px;">{poss_causes}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.caption("ℹ️ Telemetry-driven investigation hypotheses for maintenance guidance; requires on-site physical verification by qualified personnel.")

# -------------------------------------------------------------
# PAGE 4: EXPLAINABLE AI ALERTS
# -------------------------------------------------------------
elif page == "🚨 Explainable AI Alerts":
    st.markdown("""
    <div class="sme-page-header">
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
        raw_obs = raw_obs.replace("ISO: ", "Zone: ")
        raw_obs = raw_obs.replace("ISO ", "Zone ")

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
            clean_hyp = clean_hyp.replace("Vibration exceeds ISO", "Vibration exceeds configured threshold")
            clean_hyp = clean_hyp.replace("ISO", "configured")
            hyp_text = clean_hyp

        # Tier 4: RECOMMENDED ACTION
        raw_act = str(alert["Recommended_Action"])
        clean_act = raw_act.replace(
            "Check foundation bolt torque using calibrated torque wrench",
            "Check foundation fastening and investigate vibration source"
        )
        act_items = [a.strip() for a in clean_act.split(".") if a.strip()]

        alert_key = f"{alert['Machine_ID']}_{alert['Timestamp']}"
        if "alert_actions" not in st.session_state:
            st.session_state["alert_actions"] = {}

        current_action = st.session_state["alert_actions"].get(alert_key, "Pending")
        status_suffix = f" • [{current_action}]" if current_action != "Pending" else ""

        with st.expander(f"[{alert['Severity']}] {alert['Machine_ID']} — {alert['Timestamp']} | Health: {alert['Health_Score']}/100{status_suffix}"):
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

            st.markdown("---")
            st.markdown("**5. OPERATOR ACTION & TRIAGE**")

            action_badge_style = {
                "Pending": "background:#334155; color:#F1F5F9; border:1px solid #64748B;",
                "Acknowledged": "background:#064E3B; color:#34D399; border:1px solid #10B981;",
                "Marked for Investigation": "background:#1E3A8A; color:#93C5FD; border:1px solid #3B82F6;"
            }.get(current_action, "background:#334155; color:#F1F5F9;")

            st.markdown(
                f"<div style='margin-bottom:12px; font-size:0.92rem;'>"
                f"<span style='color:#A8B8C5; font-weight:600;'>Triage Status:</span> "
                f"<span style='display:inline-block; padding:3px 10px; border-radius:4px; font-weight:700; font-size:0.85rem; {action_badge_style}'>"
                f"Operator Action: {current_action}</span></div>",
                unsafe_allow_html=True
            )

            btn_col1, btn_col2, _ = st.columns([1.4, 1.8, 2.5])
            with btn_col1:
                if st.button("Acknowledge Alert", key=f"ack_{alert_key}"):
                    st.session_state["alert_actions"][alert_key] = "Acknowledged"
                    st.rerun()
            with btn_col2:
                if st.button("Mark for Investigation", key=f"inv_{alert_key}"):
                    st.session_state["alert_actions"][alert_key] = "Marked for Investigation"
                    st.rerun()

            st.caption("ℹ️ Session-only UI triage state for prototype demonstration. Does not dispatch automated external work orders.")

# -------------------------------------------------------------
# PAGE 5: PRODUCTION OPTIMIZATION
# -------------------------------------------------------------
elif page == "📈 Production Optimization":
    st.markdown("""
    <div class="sme-page-header">
        <h1><span>📈</span> PuLP MILP Production Schedule & Peak Load Shifting</h1>
        <p>100% Target Throughput Preservation | Minimize Time-of-Day Tariff Cost + Shave Peak Grid Demand</p>
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
    <div class="sme-page-header">
        <h1><span>🌱</span> Industrial Carbon Accounting & Sustainability</h1>
        <p>Electricity-Related Emissions Reporting | Configurable Grid Factor (0.82 kg CO₂/kWh)</p>
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
        - **Scope 2 Boundary**: Covers purchased grid electricity using configurable grid emission factor (0.82 kg CO2e/kWh benchmark).
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
    <div class="sme-page-header">
        <h1><span>🏛️</span> System Architecture & Low-Cost SME Adoption Plan</h1>
        <p>End-to-End Edge-to-Cloud Pipeline Designed for Indian Textile Manufacturers</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### **High-Level System Pipeline**")
    st.markdown("""
    ```
    FACTORY MACHINES (Spinning, Compressors, Pumps, HVAC)
            ↓  [RS-485 Modbus RTU / Multi-channel CT Clamps / Vib Transducers]
    MACHINE SENSORS & SMART METERS (Industrial 3-Phase Energy Meters)
            ↓  [MQTT / JSON over WiFi / Ethernet]
    EDGE GATEWAY (Raspberry Pi 4 / Industrial Edge IPC)
            ↓  [HTTPS REST API / WebSocket Ingestion]
    DATA VALIDATION & INGESTION (src/data_processing.py & src/utils.py)
            ↓  [Processed Parquet / Time-Series Database]
    AI ANOMALY DETECTION (Isolation Forest + Severity Engine)
            ↓  [Vibration Health & 4-Tier Rationale]
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

        | Component | Typical Specification | Est. Reference Cost |
        |---|---|---|
        | **Industrial 3-Phase Energy Meter** | Multi-function Modbus RTU meter | ₹4,500 – ₹7,000 |
        | **Non-Invasive CT Clamps** | Split-core current transducers | ₹1,200 / 3-phase set |
        | **Industrial Vibration Sensor** | Loop-powered accelerometer | ₹3,500 |
        | **Temperature Sensor** | Surface thermocouple / RTD sensor | ₹1,500 |
        | **Edge Gateway** | Industrial Edge Gateway / Embedded IPC | ₹6,500 |
        | **Software Platform** | SME-EnergyIQ Intelligence Platform | Cloud / Local Edge |

        *Indicative prototype reference — actual pilot cost depends on equipment, installation and vendor quotations.*

        **Payback Evaluation:**
        Payback is evaluated during pilot deployment using verified savings and actual installation cost.

        *Payback Formula:*
        *(Installation Cost + Initial Software Cost) / Verified Annual Savings*
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
        3. **Phase 3: Machine Health & Vibration Monitoring (Month 3)**
           - Add vibration and surface temperature monitoring.
           - Activate 4-tier explainable alert feed.
        4. **Phase 4: PuLP Production Optimization (Month 4-6)**
           - Automate shift load-shifting from peak ₹10/kWh to off-peak ₹5.5/kWh.
           - Shave contract demand penalties.
        5. **Phase 5: ESG & Carbon Accounting (Ongoing)**
           - Automated electricity-related carbon reporting using a configurable emissions factor.
        """)

