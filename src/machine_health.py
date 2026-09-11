"""
SME-EnergyIQ: Machine Health Intelligence & Explainable Alert Engine
Target Industry: Indian Textile Manufacturing SME

Core Capabilities:
1. ISO 10816-aligned Machine Health Scoring (0 - 100 scale)
2. Rigorous coupling between Severity and Health Scores (prevents paradoxical healthy scores during critical alerts)
3. Planned Maintenance Context Awareness (excludes planned service from failure alerts)
4. 4-Tier Industrial Explainability:
   - OBSERVED DATA: Sensor baselines vs current deviations
   - MODEL INFERENCE: AI outlier score and confidence
   - ENGINEERING HYPOTHESIS: Physical mechanical/electrical failure mode
   - RECOMMENDED ACTION: Concrete, cost-effective maintenance action for SME technician
5. Decoupled Alert Feed: Production alerts are driven by detected anomalies, NOT ground-truth labels!
"""

import os
import pandas as pd
import numpy as np

from utils import (
    ISO_10816_THRESHOLDS,
    MACHINE_SPECS,
    SEVERITY_HEALTH_LIMITS,
    is_maintenance_state,
    is_voltage_out_of_bounds,
    logger,
    save_json
)

# Operational baselines mapped from centralized MACHINE_SPECS
MACHINE_BASELINES = {
    m_id: {
        "name": spec["name"],
        "rated_kW": spec["rated_power"],
        "base_power": spec["nominal_power"],
        "base_temp": spec["nominal_temp"],
        "base_vib": spec["nominal_vib"],
        "base_rpm": spec["nominal_rpm"],
        "idle_power": spec["idle_power"]
    }
    for m_id, spec in MACHINE_SPECS.items()
}

def calculate_machine_health_score(row):
    """
    Computes deterministic industrial health score (0 - 100) combining:
    - ISO 10816 vibration severity
    - Thermal headroom
    - Electrical loading and idle waste
    - AI anomaly score
    - Mathematically coupled with Severity to prevent paradoxical scores
    """
    status = row.get("Machine_Status", "RUNNING")
    
    # -------------------------------------------------------------
    # Context Rule 1: Planned Maintenance is NOT an equipment failure
    # -------------------------------------------------------------
    if is_maintenance_state(status):
        return 100, "LOW", {"maintenance": 0.0}
        
    m_id = row["Machine_ID"]
    baseline = MACHINE_BASELINES.get(m_id, {
        "base_power": 40.0, "base_temp": 60.0, "base_vib": 2.0, "base_rpm": 1500.0, "rated_kW": 50.0
    })
    
    health = 100.0
    penalties = {}
    
    # 1. Vibration Penalty (ISO 10816-3 Category II)
    vib = row.get("Vibration_mm_s", 0.0)
    if vib > ISO_10816_THRESHOLDS["ZONE_C_UNSATISFACTORY"]: # Zone D (> 7.1 mm/s: Unacceptable)
        vib_pen = 55.0 + min(15.0, (vib - 7.1) * 3.0)
    elif vib > ISO_10816_THRESHOLDS["ZONE_B_SATISFACTORY"]: # Zone C (4.5 - 7.1 mm/s: Unsatisfactory)
        vib_pen = 28.0 + (vib - 4.5) * 6.0
    elif vib > ISO_10816_THRESHOLDS["ZONE_A_GOOD"]: # Zone B (2.3 - 4.5 mm/s: Satisfactory)
        vib_pen = (vib - 2.3) * 4.0
    else: # Zone A (Good)
        vib_pen = 0.0
    health -= vib_pen
    penalties["vibration"] = round(vib_pen, 1)
    
    # 2. Thermal Penalty
    temp = row.get("Temperature_C", baseline["base_temp"])
    temp_diff = temp - baseline["base_temp"]
    if temp_diff > 15.0:
        temp_pen = min(25.0, 15.0 + (temp_diff - 15.0) * 1.0)
    elif temp_diff > 8.0:
        temp_pen = (temp_diff - 8.0) * 1.5
    else:
        temp_pen = 0.0
    health -= temp_pen
    penalties["thermal"] = round(temp_pen, 1)
    
    # 3. Idle Waste & Electrical Penalty
    power = row.get("Power_kW", 0.0)
    prod = row.get("Production_Units", 1.0)
    excess_idle = row.get("Excess_Idle_Power", 0.0)
    elec_pen = 0.0
    if prod < 0.1 and excess_idle >= 5.0:
        elec_pen = 25.0 # Penalty for confirmed non-productive idle energy waste
    elif power > baseline.get("rated_kW", 60.0) * 1.15:
        elec_pen = 15.0 # Motor overloading penalty
    health -= elec_pen
    penalties["electrical"] = round(elec_pen, 1)
    
    # 4. AI Anomaly Penalty
    ai_score = row.get("Anomaly_Score", 0.0)
    pred = row.get("Predicted_Anomaly", 0)
    if ai_score >= 80.0 and pred == 1:
        ai_pen = 20.0
    elif ai_score >= 65.0:
        ai_pen = 10.0
    else:
        ai_pen = 0.0
    health -= ai_pen
    penalties["ai_anomaly"] = round(ai_pen, 1)
    
    # -------------------------------------------------------------
    # Consistency Enforcement (Section 3)
    # Severe abnormal conditions CANNOT result in an obviously healthy score!
    # -------------------------------------------------------------
    severity = row.get("Severity", "NORMAL")
    raw_health = health
    
    if severity == "CRITICAL":
        # Critical conditions must be substantially degraded (Health <= 45, Risk: HIGH)
        final_health = min(raw_health, SEVERITY_HEALTH_LIMITS["CRITICAL"]["max_health"])
        risk = "HIGH"
    elif severity == "HIGH":
        # High conditions reflect meaningful degradation (Health <= 65, Risk: HIGH)
        final_health = min(raw_health, SEVERITY_HEALTH_LIMITS["HIGH"]["max_health"])
        risk = "HIGH"
    elif severity == "MEDIUM":
        # Medium conditions reflect mild degradation / early warning (Health <= 80, Risk: MEDIUM)
        final_health = min(raw_health, SEVERITY_HEALTH_LIMITS["MEDIUM"]["max_health"])
        risk = "MEDIUM"
    else:
        # Normal operations remain in healthy range (Health >= 85, Risk: LOW)
        final_health = max(raw_health, SEVERITY_HEALTH_LIMITS["NORMAL"]["min_health"])
        risk = "LOW"
        
    final_score = int(np.clip(round(final_health), 0, 100))
    return final_score, risk, penalties

def generate_explainable_alert(row):
    """
    Constructs a 4-tier industrial alert explaining:
    OBSERVED DATA -> MODEL INFERENCE -> ENGINEERING HYPOTHESIS -> RECOMMENDED ACTION
    Only called for genuine abnormal operational conditions.
    """
    m_id = row["Machine_ID"]
    baseline = MACHINE_BASELINES.get(m_id, {
        "name": m_id, "base_power": 40.0, "base_temp": 60.0, "base_vib": 2.0, "base_rpm": 1500.0
    })
    
    power = row["Power_kW"]
    temp = row["Temperature_C"]
    vib = row["Vibration_mm_s"]
    rpm = row.get("RPM", 0.0)
    prod = row.get("Production_Units", 0.0)
    anomaly_score = row.get("Anomaly_Score", 0.0)
    severity = row.get("Severity", "HIGH")
    voltage = row.get("Voltage_V", 415.0)
    is_volt_glitch = is_voltage_out_of_bounds(voltage)
    excess_idle = row.get("Excess_Idle_Power", 0.0)
    
    # Detect primary trigger pattern
    is_high_vib = vib > 4.5
    is_high_temp = (temp - baseline["base_temp"]) > 14.0
    is_high_power = power > baseline["base_power"] * 1.20
    is_rpm_drop = (baseline["base_rpm"] - rpm) > 60.0 and rpm > 100.0
    is_idle_waste = prod < 0.1 and excess_idle >= 5.0
    is_choked_fluid = (m_id == "PUMP_01") and is_high_power and prod < 15.0
    
    # Tier 1: OBSERVED DATA
    observed_data = (
        f"Power: {power:.1f} kW (Baseline: {baseline['base_power']:.1f} kW, "
        f"{(power-baseline['base_power'])/baseline['base_power']*100:+.0f}%); "
        f"Temp: {temp:.1f}°C (Baseline: {baseline['base_temp']:.1f}°C, {temp-baseline['base_temp']:+.1f}°C); "
        f"Vib: {vib:.2f} mm/s (Baseline: {baseline['base_vib']:.2f} mm/s, ISO: {row.get('ISO_Vib_Zone', 'N/A')}); "
        f"Speed: {rpm:.0f} RPM; Prod: {prod:.1f} units; Voltage: {voltage:.1f} V"
    )
    
    # Tier 2: MODEL INFERENCE
    model_inference = (
        f"Isolation Forest Anomaly Score: {anomaly_score:.1f}/100 | "
        f"Assigned Severity: {severity} | Status: {row.get('Machine_Status', 'RUNNING')}"
    )
    
    # Tier 3: ENGINEERING HYPOTHESIS & RECOMMENDED ACTION
    if is_volt_glitch:
        hypothesis = (
            f"Incoming 3-phase grid voltage anomaly ({voltage:.1f} V outside nominal 340-480V band). "
            "Internal machine mechanical drive components remain healthy."
        )
        action = (
            "Inspect main LT panel incoming busbar voltage and check 4-20mA transducer connections. "
            "No mechanical overhaul required."
        )
    elif is_high_vib and is_high_temp and is_rpm_drop:
        hypothesis = (
            "Drive-end bearing race fatigue, mechanical binding, or dynamic shaft misalignment. "
            "Frictional torque is causing thermal runaway and motor slip."
        )
        action = (
            "Schedule immediate shutdown at shift end. Inspect bearing lubrication, "
            "perform dial gauge alignment check, and test bearing acoustic ultrasound."
        )
    elif is_idle_waste:
        hypothesis = (
            "Compressor unloader valve failed to seat, or machine left idling during non-productive "
            "period, wasting electrical energy with zero pneumatic delivery."
        )
        action = (
            "Verify unloader valve solenoid and differential pressure switch. "
            "Activate edge gateway auto-standby command during idle meal breaks."
        )
    elif is_choked_fluid:
        hypothesis = (
            "Dyeing liquor circulation pump suction strainer clogged or impeller cavitation occurring. "
            "Motor working against blocked passage with steep throughput drop."
        )
        action = (
            "Backflush dyeing loop filter basket and verify suction head pressure. "
            "Check for air ingress in pump casing."
        )
    elif is_high_vib:
        hypothesis = (
            "Vibration exceeds ISO 10816 Class II threshold. Likely V-belt wear, rotor unbalance, "
            "or loose foundation anchor bolts."
        )
        action = (
            "Inspect belt tension and pulley alignment. Check foundation bolt torque using calibrated torque wrench."
        )
    elif is_high_temp:
        hypothesis = (
            "Thermal buildup due to choked condenser fins, blower airflow restriction, or high ambient humidity heat load."
        )
        action = (
            "Clean condenser coil matrix with low-pressure wash. Inspect air filter differential pressure manometer."
        )
    else:
        hypothesis = (
            "Subtle multivariate parameter divergence from expected operational baseline. Energy intensity elevated relative to throughput."
        )
        action = (
            "Perform general visual inspection of drive train and review electrical load profile during next maintenance window."
        )

    return {
        "Timestamp": row["Timestamp"],
        "Machine_ID": m_id,
        "Machine_Name": baseline["name"],
        "Health_Score": row.get("Health_Score", 45),
        "Risk_Level": row.get("Risk_Level", "HIGH"),
        "Severity": severity,
        "Observed_Data": observed_data,
        "Model_Inference": model_inference,
        "Engineering_Hypothesis": hypothesis,
        "Recommended_Action": action
    }

def process_machine_health_and_alerts(input_path="results/anomaly_results.csv"):
    if not os.path.exists(input_path):
        input_path = "data/processed/factory_data_clean.csv"
        
    logger.info(f"Loading anomaly detection results from {input_path}...")
    df = pd.read_csv(input_path)
    
    # Compute Health Scores across all records with severity coupling
    logger.info("Computing ISO 10816 machine health scores and risk classifications...")
    health_results = [calculate_machine_health_score(row) for _, row in df.iterrows()]
    df["Health_Score"] = [h[0] for h in health_results]
    df["Risk_Level"] = [h[1] for h in health_results]
    
    # -------------------------------------------------------------
    # Production Alert Generation (Section 4)
    # Only genuine detected abnormal conditions (Severity in ["HIGH", "CRITICAL"])
    # Normal records and planned maintenance are strictly excluded!
    # Ground_Truth is preserved for evaluation, NOT used to generate fake production alerts.
    # -------------------------------------------------------------
    maint_mask = df["Machine_Status"].apply(is_maintenance_state)
    alert_mask = (df["Severity"].isin(["HIGH", "CRITICAL"])) & (~maint_mask)
    abnormal_rows = df[alert_mask]
    
    logger.info(f"Generating 4-tier explainable alerts for {len(abnormal_rows)} genuine abnormal events...")
    alerts = [generate_explainable_alert(row) for _, row in abnormal_rows.iterrows()]
    df_alerts = pd.DataFrame(alerts)
    
    # Save alerts
    os.makedirs("results", exist_ok=True)
    alert_path = os.path.join("results", "explainable_alerts.csv")
    df_alerts.to_csv(alert_path, index=False)
    logger.info(f"Saved {len(df_alerts)} explainable alerts to {alert_path}")
    
    # Save enriched dataset with health scores
    enriched_path = os.path.join("results", "factory_data_enriched.csv")
    df.to_csv(enriched_path, index=False)
    logger.info(f"Saved enriched dataset to {enriched_path}")
    
    # Snapshot of latest machine health
    latest_ts = df["Timestamp"].max()
    latest_df = df[df["Timestamp"] == latest_ts]
    
    health_snapshot = {}
    for _, row in latest_df.iterrows():
        m_id = row["Machine_ID"]
        health_snapshot[m_id] = {
            "name": MACHINE_BASELINES.get(m_id, {}).get("name", m_id),
            "health_score": int(row["Health_Score"]),
            "risk_level": row["Risk_Level"],
            "power_kw": float(row["Power_kW"]),
            "temp_c": float(row["Temperature_C"]),
            "vib_mm_s": float(row["Vibration_mm_s"]),
            "iso_vib_zone": row.get("ISO_Vib_Zone", "N/A"),
            "status": row.get("Machine_Status", "RUNNING"),
            "severity": row.get("Severity", "NORMAL")
        }
        
    save_json(health_snapshot, os.path.join("results", "machine_health_snapshot.json"))
    return df, df_alerts, health_snapshot

if __name__ == "__main__":
    df_enriched, df_alerts, snapshot = process_machine_health_and_alerts()
    print("\n=== LATEST MACHINE HEALTH SNAPSHOT ===")
    for m_id, stats in snapshot.items():
        print(f"[{m_id}] {stats['name']}")
        print(f"  Health: {stats['health_score']}/100 | Risk: {stats['risk_level']} | Vib: {stats['vib_mm_s']} mm/s ({stats['iso_vib_zone']}) | Temp: {stats['temp_c']}°C")
        
    print(f"\nTotal Explainable Alerts Generated: {len(df_alerts)}")
    if not df_alerts.empty:
        print("\nAlerts by Severity:")
        print(df_alerts["Severity"].value_counts())
        print("\nAlerts by Risk Level:")
        print(df_alerts["Risk_Level"].value_counts())
        sample_alert = df_alerts.iloc[0]
        print("\n=== SAMPLE EXPLAINABLE ALERT ===")
        print(f"Machine: {sample_alert['Machine_ID']} at {sample_alert['Timestamp']}")
        print(f"Observed Data: {sample_alert['Observed_Data']}")
        print(f"Model Inference: {sample_alert['Model_Inference']}")
        print(f"Engineering Hypothesis: {sample_alert['Engineering_Hypothesis']}")
        print(f"Recommended Action: {sample_alert['Recommended_Action']}")
