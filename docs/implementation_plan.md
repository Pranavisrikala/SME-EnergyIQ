# Implementation Plan: SME-EnergyIQ Platform

SME-EnergyIQ is an AI-powered Industrial Energy Intelligence & Optimization Platform designed for Indian Small and Medium Enterprise (SME) textile manufacturing factories for the **Schneider Electric Yuva Yodha Energy Tech Hackathon 2026**.

---

## 1. Project Audit & Current State Analysis

### 1.1 Existing Project Inventory
- `src/generate_data.py`: Generates 1,000 synthetic rows for a single machine (`MOTOR_01`) with Gaussian noise and 30 simultaneous 4-parameter extreme outliers.
- `src/inspect_data.py`: Loads and prints data shape, column names, sample rows, and summary statistics.
- `src/visualize_data.py`: Generates a Matplotlib plot of `Power_kW` vs `Timestamp` and saves it to `results/power_consumption.png`.
- `src/anomaly_detection.py`: Fits an `IsolationForest(contamination=0.03)` on 4 features (`Power_kW`, `Temperature_C`, `Vibration_mm_s`, `RPM`), achieves 100% accuracy on the current synthetic dataset, and outputs `results/anomaly_results.csv`.
- `venv`: Fully provisioned with `pandas`, `numpy`, `scikit-learn`, `scipy`, `matplotlib`, `plotly`, `PuLP`, `streamlit`, and `joblib`.
- `dashboard/`, `docs/`, `models/`, `diagrams/`: Currently empty directories ready for implementation.

### 1.2 Identified Limitations & Engineering Gaps
1. **Single Machine vs. Real Textile Factory**: Currently only models `MOTOR_01`. Real textile mills rely on an ecosystem: Spinning Motors, Air Compressors (for air-jet looms/pneumatics), Water Circulation Pumps (for dyeing/bleaching), and HVAC/Humidification systems (critical for yarn moisture control).
2. **Simplified Anomaly Injection**: Current anomalies inject extreme deviations across all 4 parameters simultaneously, leading to an unrealistic 100% classification accuracy. Real industrial anomalies include single-sensor failures, subtle mechanical degradation, energy waste during idle periods, and power factor drops.
3. **Missing Industrial & Operational Metrics**: Lacks `Energy_kWh`, `Voltage_V`, `Current_A`, `Production_Units`, `Tariff_Rs_per_kWh`, `Peak_OffPeak` (Time-of-Day ToD tariffs), `Specific Energy Consumption (SEC)`, and `Machine_Status`.
4. **No Explainability Layer**: The existing Isolation Forest flags binary anomalies (-1 or 1) without explaining *why* or distinguishing between normal high-load production and true mechanical degradation.
5. **No Optimization Engine**: No production schedule optimization or peak-demand load shifting implemented yet.
6. **No Carbon Accounting**: No regional grid carbon emission calculations (e.g., CEA baseline factor for India).
7. **No Interactive Industrial UI**: Streamlit dashboard is not yet implemented.

---

## 2. Proposed System Architecture & Core Intelligence Loop

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        TEXTILE SME FACTORY FLOOR (SIMULATION)                          │
│   [MOTOR_01: Spinning]  [COMPRESSOR_01: Air Jet]  [PUMP_01: Dyeing]  [HVAC_01: Humid] │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Sensors: Power, V, I, Temp, Vib, RPM, Units
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                    EDGE GATEWAY & DATA VALIDATION PIPELINE                             │
│   • Modbus/MQTT Data Ingestion Simulator  • Data Quality Checks (Nulls, Out-of-bounds) │
│   • Multi-tariff & Time-of-Day (ToD) Tagging • Cumulative Energy Integration           │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Clean Ingested Stream
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 AI & ANALYTICS LAYER                                   │
│   1. DETECT: Isolation Forest Anomaly Detection (Trained & Persisted)                  │
│   2. UNDERSTAND: Explainable AI Alert Engine (Observed Data → Model Inference          │
│                  → Physical Hypothesis → Recommended Action)                           │
│   3. PREDICT & DIAGNOSE: ISO 10816 Machine Health Scoring (0–100)                      │
│   4. MEASURE & BENCHMARK: Specific Energy Consumption (SEC = kWh / Production Unit)    │
│   5. EMISSIONS: Indian Grid (CEA) Carbon Accounting (kg CO2e/kWh)                      │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Health, Alerts, Tariffs & Baseline Profiles
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                    OPTIMIZATION ENGINE (PuLP LINEAR PROGRAMMING)                       │
│   • Objective: Min(Energy Cost + Peak Demand Penalty)                                  │
│   • Constraints: Production Quotas Met, Machine Capacity, Maintenance Windows         │
│   • Action: Load Shifting (Peak ₹10/kWh → Off-Peak ₹5.5/kWh) without throughput loss   │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Baseline vs. Optimized Solutions
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                    SCHNEIDER SME-EnergyIQ INDUSTRIAL DASHBOARD                         │
│   • Factory Overview & KPIs   • Energy Monitoring & Tariffs   • Machine Health Cards   │
│   • Explainable AI Alert Feed • PuLP Production Optimizer     • Carbon & Sustainability│
│   • System Architecture & SME Phased Adoption Roadmap                                  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Phased Implementation Strategy

Following your engineering guidelines and teaching approach, the project will be constructed systematically in **12 distinct, verified phases**:

### Phase 1: Baseline Audit & Validation (COMPLETED)
- Verified working scripts (`src/generate_data.py`, `src/inspect_data.py`, `src/visualize_data.py`, `src/anomaly_detection.py`).
- Verified dependencies in `venv` (`streamlit`, `plotly`, `PuLP`, `scikit-learn`, `pandas`, `numpy`).

### Phase 2: Enhanced Synthetic Industrial Data Generator (`src/generate_data.py`)
- Expand dataset to 4 distinct textile machines over 7–14 days (several thousand observations at 15-minute or 1-minute intervals):
  - **MOTOR_01 (Spinning Motor)**: 55 kW rated, continuous steady load, sensitive to yarn tension & bearing friction.
  - **COMPRESSOR_01 (Pneumatics & Air-Jet Loom)**: 45 kW rated, cyclic load/unload behavior, sensitive to valve leakage.
  - **PUMP_01 (Dyeing Liquor Circulation Pump)**: 22 kW rated, fluid load, impeller cavitation/clogging profile.
  - **HVAC_01 (Spinning Humidification Plant)**: 60 kW rated, diurnal ambient temperature correlation, filter blockage profile.
- Add realistic columns:
  `Timestamp`, `Machine_ID`, `Machine_Type`, `Power_kW`, `Energy_kWh`, `Voltage_V`, `Current_A`, `Temperature_C`, `Vibration_mm_s`, `RPM`, `Operating_Hours`, `Production_Units`, `Production_Target`, `Machine_Status`, `Ground_Truth`, `Anomaly_Type`, `Tariff_Rs_per_kWh`, `Peak_OffPeak`, `Maintenance_Status`.
- Inject 7 realistic anomaly classes:
  - **Type A**: Energy Anomaly (High power without production gain)
  - **Type B**: Thermal Anomaly (Heat accumulation from poor cooling)
  - **Type C**: Vibration Anomaly (Mechanical unbalance/misalignment)
  - **Type D**: Combined Machine Health Degradation (Power ↑, Temp ↑, Vib ↑, RPM ↓)
  - **Type E**: Sensor Glitch/Unrealistic Spike (Data quality test)
  - **Type F**: Inefficient Operation (Low power factor / poor mechanical efficiency)
  - **Type G**: Idle Energy Waste (Machine drawing high power with 0 production during breaks)

### Phase 3: Data Quality, Ingestion & Validation Pipeline (`src/data_processing.py` & `src/utils.py`)
- Handle edge data quality issues: missing readings, timestamp jitter, physical range violations ($P < 0$, $T > 180^\circ C$).
- Ingestion logger that flags quality issues rather than silently dropping rows.
- Feature engineering: Instantaneous SEC proxy ($\text{Power} / \max(\text{Production}, 1)$), temperature rate of change ($\Delta T / \Delta t$), vibration severity categorization according to ISO 10816.

### Phase 4: AI Anomaly Detection & Model Persistence (`src/anomaly_detection.py`)
- Preserve Isolation Forest as the core ML detector, but train per machine type or with normalized operational features.
- Compute continuous anomaly scores (`decision_function`) and assign severity ratings (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- Save trained model artifacts (`models/anomaly_model.pkl`) and schema (`models/model_metadata.json`).
- Evaluate with Confusion Matrix, Precision, Recall, F1-Score; document synthetic vs. field performance boundaries honestly.

### Phase 5: Machine Health Intelligence & Explainable Alert Engine (`src/machine_health.py`)
- Implement a multi-factor Health Score ($0 - 100$ scale) based on:
  - Vibration severity score (ISO 10816-3 standard: Class II/III industrial machinery).
  - Thermal headroom relative to rated operating temperature.
  - Electrical operating efficiency and load factor.
- Generate structured 4-tier explainable alerts:
  1. **Observed Data**: Exact parameter deviations (e.g., Vibration $2.1 \to 5.4\text{ mm/s}$, Power $52 \to 68\text{ kW}$).
  2. **Model Inference**: Isolation Forest outlier score ($0.88$, severity: HIGH).
  3. **Engineering Hypothesis**: "Likely drive-end bearing race wear or coupling misalignment."
  4. **Recommended Action**: "Schedule mechanical alignment and bearing greasing during next shift change."

### Phase 6: Energy & Specific Energy Consumption (SEC) Engine (`src/energy_analysis.py`)
- Calculate machine-level and factory-level energy metrics ($E = P \times \Delta t$).
- Compute Specific Energy Consumption ($\text{SEC} = \text{Energy (kWh)} / \text{Production (Units)}$).
- Track SEC variation across shifts, machines, and operational states (Running vs. Idle Waste).

### Phase 7: Production Schedule Optimization Engine (`src/optimization.py`)
- Formulate a Mixed Integer Linear Programming (MILP) optimization model using `PuLP`.
- Realistic Indian Industrial Tariff structure:
  - Peak Hours (18:00–22:00): ₹10.00 / kWh
  - Normal Hours (06:00–18:00): ₹7.50 / kWh
  - Off-Peak / Night (22:00–06:00): ₹5.50 / kWh
- Objective: Minimize Total Energy Cost + Peak Demand Charges + Idle Waste, subject to:
  - Achieving 100% of daily production targets (no throughput reduction!).
  - Respecting machine rated capacities and operational limits.
  - Accounting for maintenance downtime windows.
- Compare: **Baseline Schedule** vs. **Optimized Schedule**, calculating real rupee savings, peak kW shaved, and SEC improvement percentage.

### Phase 8: Carbon & Sustainability Engine (`src/carbon_analysis.py`)
- Configurable Indian Central Electricity Authority (CEA Version 19) grid emission factor (default: $0.82\text{ kg CO}_2\text{e/kWh}$).
- Compute Baseline vs. Optimized $\text{CO}_2$ emissions and Avoided Carbon Footprint ($\Delta \text{CO}_2$).
- Provide carbon intensity benchmarking per unit of textile output.

### Phase 9: Industrial Streamlit Dashboard (`dashboard/app.py`)
- Multi-page industrial UI using Schneider Electric inspired theme (Industrial Green `#008A00` / Slate Dark `#1E242B`):
  - **Page 1: Factory Overview**: Live power gauge, today's energy & cost, factory SEC, carbon counter, active health alert ticker.
  - **Page 2: Energy Monitoring & Tariffs**: Interactive Plotly multi-machine time series, Time-of-Day tariff cost analysis, running vs. idle energy breakdown.
  - **Page 3: Machine Health & Diagnostics**: ISO 10816 vibration heatmaps, thermal profiles, 0–100 health dials for each of the 4 machines.
  - **Page 4: Explainable AI Alerts**: Filterable alert log with the 4-tier rationale (Data $\to$ Inference $\to$ Hypothesis $\to$ Action).
  - **Page 5: Production Optimization**: Side-by-side Gantt charts and load profiles showing Baseline vs. PuLP-optimized schedules, ₹ savings, peak demand reduction, and SEC improvement.
  - **Page 6: Carbon & Sustainability**: Carbon emissions dashboard with configurable CEA grid factor slider, avoided carbon certificates, and intensity metrics.
  - **Page 7: System Architecture & SME Roadmap**: Interactive architecture diagram, edge-to-cloud hardware specs for Indian SMEs, and 5-stage adoption roadmap.
  - **Machine Detail View**: Deep drill-down for any selected machine with historical plots and diagnostic reasoning.

### Phase 10: End-to-End Pipeline Integration & Automation
- Build an orchestrator script (`run_pipeline.py` or `src/pipeline.py`) that runs data generation, processing, ML inference, health scoring, optimization, and generates all results cleanly.

### Phase 11: Comprehensive Verification & Stress Testing
- Automated checks:
  - Zero crashes across data ingestion, model fitting, and PuLP optimization.
  - Validation that production targets are strictly preserved in optimization.
  - Streamlit dashboard pages render error-free with interactive widgets.

### Phase 12: Professional Documentation & Presentation Assets
- Complete engineering documentation:
  - `docs/architecture.md`: Edge-to-cloud IoT pipeline, Modbus/MQTT gateway specs.
  - `docs/methodology.md`: ML Isolation Forest, ISO 10816 health scoring, PuLP MILP formulation.
  - `docs/assumptions.md`: Tariffs, machine specs, CEA carbon factor, SME operational context.
  - `docs/deployment_plan.md`: Low-cost hardware BOM for Indian SMEs (< ₹50,000 edge retrofit).
  - `README.md`: Hackathon submission summary, quickstart guide, project narrative, and pitch guide for judges.

---

## 4. User Review & Approval Checkpoints

> [!IMPORTANT]
> **Key Architectural Decisions for User Review:**
> 1. **Time Resolution & Horizon**: We plan to generate 7 days of operations at 15-minute intervals (672 intervals per machine $\times$ 4 machines = 2,688 comprehensive observations) or 1-minute intervals. 15-minute intervals align directly with standard industrial utility Time-of-Day (ToD) billing meters in India.
> 2. **Machine Mix**: The proposed 4 machines are Spinning Motor (`MOTOR_01`), Air Compressor (`COMPRESSOR_01`), Dyeing Pump (`PUMP_01`), and Humidification HVAC (`HVAC_01`).
> 3. **Preservation**: All existing code (`src/generate_data.py`, `src/inspect_data.py`, `src/visualize_data.py`, `src/anomaly_detection.py`) will be preserved, modularized, and enhanced.
> 4. **Teaching Mode**: Each step will provide clear engineering explanations, formulas, and presentation talking points tailored for the Schneider Electric hackathon judges.

---

## 5. Verification Plan

### Automated Testing
- Execute data generator and verify dataset shapes, columns, and anomaly labels:
  `python src/generate_data.py`
- Validate data processing and quality metrics:
  `python src/data_processing.py`
- Run anomaly detection and ensure model artifacts (`anomaly_model.pkl`) are saved:
  `python src/anomaly_detection.py`
- Run PuLP optimization and verify mathematical feasibility and cost reduction:
  `python src/optimization.py`
- Run carbon calculations:
  `python src/carbon_analysis.py`

### Interactive Testing
- Launch Streamlit dashboard on local port:
  `streamlit run dashboard/app.py`
- Verify all 7 pages, machine drill-downs, dynamic sliders, and Plotly charts.
