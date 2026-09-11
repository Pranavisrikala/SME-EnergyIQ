# SME-EnergyIQ: System Architecture Document

**Platform**: SME-EnergyIQ  
**Target Industry**: Indian Textile Manufacturing Small & Medium Enterprises (Spinning & Weaving Mills)  
**Hackathon**: Schneider Electric Yuva Yodha Energy Tech Hackathon 2026  

---

## 1. High-Level Architecture Overview

The system bridges physical textile machinery with AI intelligence, linear programming optimization, and supervisory dashboard analytics through an open, modular edge-to-cloud architecture:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        TEXTILE SME FACTORY FLOOR (SIMULATION)                          │
│                                                                                        │
│  [MOTOR_01] Ring Spinning Frame Main Drive (55 kW, 4-Pole Induction)                  │
│  [COMPRESSOR_01] Screw Air Compressor for Looms & Pneumatics (45 kW, 2-Pole)           │
│  [PUMP_01] Dyeing & Bleaching Liquor Circulation Pump (22 kW, Centrifugal)             │
│  [HVAC_01] Spinning Hall Humidification & Climate Control (60 kW)                      │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Sensor Signals (Modbus RTU over RS-485)
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                    MACHINE SENSORS & INDUSTRIAL SMART METERS                           │
│  • Digital Power Meters: Schneider Electric EasyLogic PM2120 / Conzerv EM6400NG        │
│  • CT Clamps: Split-core 100A/5A (Non-invasive retrofit)                               │
│  • Vibration Transducers: Loop-powered 4-20mA / IEPE Piezoelectric Accelerometers      │
│  • Temperature: PT100 RTD surface probes on motor end-shields and compressor sumps     │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ MQTT / JSON over Local Industrial Wi-Fi
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                     EDGE GATEWAY & DATA INGESTION LAYER                                │
│  • Hardware: Industrial Raspberry Pi 4 / Advantech Edge IPC                            │
│  • Telemetry Rate: 15-minute interval logging (aligned with Indian DISCOM ToD meters)  │
│  • Protocol Adapter: Modbus-to-MQTT bridge                                             │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Ingested CSV / Parquet Stream
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                    DATA PROCESSING & AUDITING (src/data_processing.py)                 │
│  • Data Quality Auditor: Tracks missing values, duplicates, and range violations       │
│  • Feature Engineering: SEC Proxy, Temperature Elevation, ISO 10816 Zone Categorization│
│  • Output: data/processed/factory_data_clean.csv                                       │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Clean Telemetry & Engineered Features
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                     AI & MACHINE LEARNING (src/anomaly_detection.py)                   │
│  • Multi-variate Isolation Forest (scikit-learn) with continuous anomaly scoring (0-100)│
│  • Multi-attribute detection: Power, Temp, Vib, RPM, Production, Load Ratio, SEC Proxy │
│  • Artifacts: models/anomaly_model.pkl and models/model_metadata.json                  │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Outlier Probabilities & Machine Status
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                MACHINE HEALTH & EXPLAINABLE ALERTS (src/machine_health.py)             │
│  • ISO 10816-3 Industrial Vibration Severity Scoring (Zone A, B, C, D)                 │
│  • Composite Health Score (0 - 100) & Triaged Risk Levels (LOW, MEDIUM, HIGH)          │
│  • 4-Tier Explainability: Observed Data → Model Inference → Hypothesis → Action       │
│  • Artifact: results/explainable_alerts.csv                                            │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Telemetry, Health Scores & Tariff Rates
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│               PRODUCTION & LOAD OPTIMIZER (src/optimization.py - PuLP MILP)            │
│  • Mixed-Integer Linear Programming formulation                                       │
│  • Objective: Min(Time-of-Day Tariff Cost + Peak Demand Penalties)                     │
│  • 100% Strict Production Quota Preservation (No throughput reduction!)                │
│  • Smart Load Shifting: Peak (₹10/kWh) → Off-Peak (₹5.50/kWh)                          │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Baseline vs. Optimized Dispatch
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                   CARBON & SUSTAINABILITY (src/carbon_analysis.py)                     │
│  • Central Electricity Authority (CEA) Indian Grid Baseline (0.82 kg CO2e/kWh)         │
│  • Scope 2 Indirect Carbon Footprint & Avoided Emissions Calculation                  │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Visualizations & Analytics
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│             INDUSTRIAL STREAMLIT DASHBOARD (dashboard/app.py)                          │
│  • Schneider Electric Slate/Green Theme with Interactive Plotly Visualizations         │
│  • Factory Overview, ToD Energy Tracking, Health Gauges, Alerts Feed, Optimizer & ESG  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Intelligence Loop

The platform executes the closed-loop cycle:

$$\text{MEASURE} \longrightarrow \text{UNDERSTAND} \longrightarrow \text{DETECT} \longrightarrow \text{PREDICT} \longrightarrow \text{OPTIMIZE} \longrightarrow \text{VERIFY}$$

1. **MEASURE**: Instantaneous electrical telemetry ($V, I, P, pf$) and mechanical sensors ($T, \text{Vib}, \text{RPM}$) at 15-minute intervals.
2. **UNDERSTAND**: Relate energy consumption to production throughput using Specific Energy Consumption ($\text{SEC} = \text{kWh}/\text{unit}$).
3. **DETECT**: Unsupervised Isolation Forest isolates multi-parameter anomalies without requiring millions of labelled failure records.
4. **PREDICT & DIAGNOSE**: Map physical deviations using ISO 10816-3 to establish continuous 0–100 health scores.
5. **OPTIMIZE**: PuLP MILP shifts flexible batch operations into low-tariff windows without reducing factory production.
6. **VERIFY**: Real-time comparison between Baseline and Optimized schedules proves rupee savings, peak shaving, and avoided carbon.

