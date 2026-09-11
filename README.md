# SME-EnergyIQ ⚡

### AI-Powered Industrial Energy Intelligence & Optimization Platform for Indian Textile SMEs
**Schneider Electric Yuva Yodha Energy Tech Hackathon 2026**

---

## 📌 Executive Summary

Small and Medium Enterprises (SMEs) in India's textile hubs (Surat, Tirupur, Coimbatore) operate on thin margins (3–8%), with electricity accounting for up to 30% of operational costs. Most factories face:
- Aging legacy machinery without integrated telemetry.
- Punitive Time-of-Day (ToD) peak electricity surcharges (up to ₹10/kWh during 18:00–22:00).
- Idle energy waste during shift changeovers and unloader valve failures.
- Black-box AI tools that fail to provide actionable physical maintenance guidance.

**SME-EnergyIQ** is a plug-and-play, non-invasive software and IoT solution that executes the closed-loop cycle:

$$\mathbf{MEASURE} \longrightarrow \mathbf{UNDERSTAND} \longrightarrow \mathbf{DETECT} \longrightarrow \mathbf{PREDICT} \longrightarrow \mathbf{OPTIMIZE} \longrightarrow \mathbf{VERIFY}$$

---

## 🚀 Key Platform Features

1. **Realistic 4-Machine Textile Ecosystem**:
   - `MOTOR_01`: Ring Spinning Frame Motor (55 kW rated)
   - `COMPRESSOR_01`: Screw Air Compressor for Air-Jet Looms (45 kW rated)
   - `PUMP_01`: Dyeing & Bleaching Liquor Circulation Pump (22 kW rated)
   - `HVAC_01`: Humidification & Climate Control Plant (60 kW rated)
2. **Industrial Data Quality Pipeline (`src/data_processing.py`)**:
   - Transparent auditing of missing values, sensor bounds, and duplicates without silent row dropping.
   - Computes Instantaneous Specific Energy Consumption (`SEC_Proxy`), Thermal Elevation, and ISO Vibration Zones.
3. **Multi-Variate Isolation Forest AI (`src/anomaly_detection.py`)**:
   - Continuous anomaly scoring ($0 - 100$) and severity triaging (`NORMAL`, `MEDIUM`, `HIGH`, `CRITICAL`).
   - Saved model artifacts (`models/anomaly_model.pkl`, `models/model_metadata.json`).
4. **ISO 10816 Machine Health & 4-Tier Explainability (`src/machine_health.py`)**:
   - Industrial vibration severity scoring (Zones A, B, C, D) and 0–100 composite health scores.
   - Structured 4-tier alert feed: **Observed Data $\to$ Model Inference $\to$ Engineering Hypothesis $\to$ Recommended Action**.
5. **PuLP MILP Production Schedule Optimizer (`src/optimization.py`)**:
   - Shaves peak grid demand by **14.05%** and cuts daily energy costs by **5.27%** (₹1,241 / day = ~₹4.5 Lakhs / year).
   - **Guarantees 100% exact throughput conservation** (zero production shortfall).
6. **CEA Carbon & Sustainability Accounting (`src/carbon_analysis.py`)**:
   - Based on India's Central Electricity Authority (CEA) Baseline Database Version 19 (0.82 kg CO2e/kWh).
   - Interactive grid emission sensitivity slider and environmental equivalencies.
7. **Industrial Streamlit Dashboard (`dashboard/app.py`)**:
   - Professional Schneider Electric slate/green theme with interactive Plotly telemetry curves, machine drill-downs, and optimization scorecards.

---

## 📊 Verified Platform Benchmark (Baseline vs. Optimized)

| Metric | Baseline Schedule | PuLP Optimized Schedule | Verified Improvement |
|---|---|---|---|
| **Daily Electricity Cost** | ₹23,544.01 | ₹22,302.51 | **▼ ₹1,241.50 / day (5.27% Savings)** |
| **Peak Grid Demand** | 164.59 kW | 141.47 kW | **▼ 23.12 kW (14.05% Shaved)** |
| **Production Throughput (Yarn)** | 4,500.0 kg | 4,500.0 kg | **100.0% Conserved (Exact Match)** |
| **Factory SEC (Yarn)** | 0.7019 kWh/kg | 0.7020 kWh/kg | **Maintained Efficiency** |
| **Annualized Cost Savings** | — | — | **~ ₹3,87,000 / year** |
| **Hardware Payback Period** | — | — | **< 2.5 Months** |

---

## 🛠️ Project Structure

```
Schneider_electric/
│
├── dashboard/
│   └── app.py                     # Industrial Streamlit dashboard (7 interactive pages)
│
├── data/
│   ├── factory_data.csv           # 14-day 15-minute multi-machine dataset (5,376 records)
│   └── processed/
│       └── factory_data_clean.csv # Cleaned dataset with engineered ISO features
│
├── docs/
│   ├── architecture.md            # Edge-to-cloud IoT pipeline & network topology
│   ├── methodology.md             # ML, ISO 10816, PuLP MILP formulation, and SEC formulas
│   ├── assumptions.md             # Machinery specs, Indian ToD tariffs & CEA emission factors
│   └── deployment_plan.md         # SME retrofit BOM (< ₹18,000/machine), ROI & rollout
│
├── models/
│   ├── anomaly_model.pkl          # Trained Isolation Forest model artifact
│   └── model_metadata.json        # Hyperparameters, feature schema, and evaluation metrics
│
├── results/
│   ├── anomaly_results.csv        # Continuous anomaly scores and severity classes
│   ├── explainable_alerts.csv     # 4-tier explainable alert log
│   ├── factory_data_enriched.csv  # Enriched dataset with ISO 10816 health scores
│   ├── energy_summary.json        # Fleet energy breakdown and idle waste metrics
│   ├── daily_sec_profile.csv      # Daily Specific Energy Consumption trend
│   ├── schedule_baseline.csv      # Baseline 24-hour dispatch schedule
│   ├── schedule_optimized.csv     # PuLP MILP optimized 24-hour dispatch schedule
│   ├── optimization_results.json  # Quantitative comparison and savings scorecard
│   └── carbon_sustainability_report.json # Scope 2 indirect carbon accounting
│
├── src/
│   ├── generate_data.py           # Multi-machine synthetic generator (7 anomaly classes)
│   ├── inspect_data.py            # Dataset inspector and summary statistics
│   ├── visualize_data.py          # Multi-machine power profile visualization
│   ├── utils.py                   # Industrial bounds, ISO 10816 logic, and ToD tariffs
│   ├── data_processing.py         # Data quality auditor & feature engineering
│   ├── anomaly_detection.py       # Isolation Forest training and evaluation
│   ├── machine_health.py          # ISO 10816 health scoring and explainable alert engine
│   ├── energy_analysis.py         # Energy breakdown, SEC, and idle waste quantification
│   ├── optimization.py            # PuLP MILP production schedule optimizer
│   ├── carbon_analysis.py         # Carbon accounting with CEA grid factor
│   └── pipeline.py                # Master orchestrator running the full intelligence loop
│
├── requirements.txt               # Dependencies (streamlit, pulp, plotly, scikit-learn)
└── README.md                      # Complete project documentation and pitch guide
```

---

## 💻 Quick Start & Demonstration Guide

### 1. Environment Activation
```bash
# In Windows PowerShell:
.\venv\Scripts\Activate.ps1
```

### 2. Run the Full Intelligence Pipeline
To execute data generation, data quality auditing, AI model training, ISO health scoring, PuLP optimization, and carbon calculations:
```bash
python src/pipeline.py
```
*(Runs completely in under 3 seconds!)*

### 3. Launch the Industrial Streamlit Dashboard
```bash
streamlit run dashboard/app.py
```
Open your browser at `http://localhost:8501` to interact with the 7 pages:
1. **🏭 Factory Overview**: Real-time power gauges, factory SEC, active critical alert ticker.
2. **⚡ Energy & ToD Monitoring**: Machine power curves and Time-of-Day tariff cost allocation.
3. **🩺 Machine Health & Diagnostics**: ISO 10816 vibration severity curves and deep machine drill-down.
4. **🚨 Explainable AI Alerts**: 4-tier transparent alert feed.
5. **📈 Production Optimization**: Baseline vs. PuLP load shifting comparison and peak demand shaving.
6. **🌱 Carbon & Sustainability**: Configurable CEA grid factor slider and carbon intensity.
7. **🏛️ Architecture & SME Roadmap**: Low-cost IoT retrofit kit BOM (< ₹18,000/machine) and 5-phase rollout.

---

## 🎯 Talking Points for Schneider Electric Hackathon Judges

1. **Real-World SME Fit**: Rather than asking an SME to scrap their ₹40 Lakh spinning frame, we retrofit it with a ₹5,500 Schneider EasyLogic meter and a ₹3,800 vibration sensor, delivering payback in **under 2.5 months**.
2. **Production-First Optimization**: The PuLP optimizer strictly enforces daily production targets ($\sum X_{m,h} = \text{Target}$). Energy savings come from **smart load shifting away from the ₹10/kWh peak tariff**, not by shutting down the factory.
3. **Explainable AI (XAI)**: We replace black-box alarm fatigue with the **4-Tier Explainability Model** (*Observed Data $\to$ Model Inference $\to$ Engineering Hypothesis $\to$ Recommended Action*), giving electricians actionable instructions.
4. **Credible Physics & Standards**: All vibration diagnostics adhere strictly to **ISO 10816-3**, and carbon calculations explicitly cite the **Central Electricity Authority (CEA) Baseline Database v19**.

