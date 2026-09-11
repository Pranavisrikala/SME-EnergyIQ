"""
SME-EnergyIQ: Industrial Utility and Configuration Module
Contains physical threshold constants, ISO 10816 vibration standards,
Time-of-Day tariff rules, and data validation helpers for Indian textile SMEs.
"""

import os
import json
import logging
import pandas as pd

# Setup structured logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('SME-EnergyIQ')

# Physical plausibility limits for industrial sensors
SENSOR_BOUNDS = {
    'Power_kW': {'min': 0.0, 'max': 150.0},
    'Voltage_V': {'min': 340.0, 'max': 480.0},        # 415V nominal +/- 15%
    'Current_A': {'min': 0.0, 'max': 250.0},
    'Temperature_C': {'min': 10.0, 'max': 130.0},     # Stator/bearing insulation limits
    'Vibration_mm_s': {'min': 0.0, 'max': 25.0},      # RMS velocity mm/s
    'RPM': {'min': 0.0, 'max': 4000.0}
}

# Centralized Machine Physical Baseline Specifications
MACHINE_SPECS = {
    "MOTOR_01": {
        "name": "Ring Spinning Frame Motor",
        "type": "Spinning Motor",
        "rated_power": 55.0,
        "nominal_power": 45.0,
        "idle_power": 12.0,
        "nominal_temp": 62.0,
        "nominal_vib": 1.8,
        "nominal_rpm": 1485.0,
        "unit_name": "kg_yarn",
        "base_output_per_15m": 48.0
    },
    "COMPRESSOR_01": {
        "name": "Screw Air Compressor",
        "type": "Air Compressor",
        "rated_power": 45.0,
        "nominal_power": 38.0,
        "idle_power": 16.0,
        "nominal_temp": 75.0,
        "nominal_vib": 2.2,
        "nominal_rpm": 2950.0,
        "unit_name": "Nm3_air",
        "base_output_per_15m": 210.0
    },
    "PUMP_01": {
        "name": "Dyeing Liquor Circulation Pump",
        "type": "Water Pump",
        "rated_power": 22.0,
        "nominal_power": 18.0,
        "idle_power": 4.5,
        "nominal_temp": 52.0,
        "nominal_vib": 1.4,
        "nominal_rpm": 1450.0,
        "unit_name": "m3_liquor",
        "base_output_per_15m": 28.0
    },
    "HVAC_01": {
        "name": "Humidification & Climate Plant",
        "type": "HVAC System",
        "rated_power": 60.0,
        "nominal_power": 48.0,
        "idle_power": 15.0,
        "nominal_temp": 45.0,
        "nominal_vib": 1.6,
        "nominal_rpm": 980.0,
        "unit_name": "m3_conditioned",
        "base_output_per_15m": 1200.0
    }
}

# Centralized Production Scheduling & Dispatch Parameters (Simulation Assumptions)
OPTIMIZATION_SPECS = {
    "MOTOR_01": {
        "daily_target": 4500.0,           # kg yarn/day
        "max_hourly_rate": 230.0,
        "min_hourly_rate": 120.0,
        "marginal_kw_per_unit": 0.155,
        "flexibility": "MEDIUM"
    },
    "COMPRESSOR_01": {
        "daily_target": 19200.0,          # Nm3 air/day
        "max_hourly_rate": 1100.0,
        "min_hourly_rate": 350.0,
        "marginal_kw_per_unit": 0.024,
        "flexibility": "HIGH"
    },
    "PUMP_01": {
        "daily_target": 2500.0,           # m3 liquor/day
        "max_hourly_rate": 180.0,
        "min_hourly_rate": 0.0,
        "marginal_kw_per_unit": 0.105,
        "flexibility": "VERY_HIGH"
    },
    "HVAC_01": {
        "daily_target": 110000.0,         # m3 conditioned air/day
        "max_hourly_rate": 5800.0,
        "min_hourly_rate": 2500.0,
        "marginal_kw_per_unit": 0.006,
        "flexibility": "MEDIUM"
    }
}

# ISO 10816-3 Vibration Severity Standards for Industrial Machines (15kW - 300kW)
# Category: Medium-sized machines (Class II: 15-75 kW) mounted on rigid/flexible foundations
ISO_10816_THRESHOLDS = {
    'ZONE_A_GOOD': 2.3,            # Newly commissioned / excellent condition
    'ZONE_B_SATISFACTORY': 4.5,    # Normal unrestricted long-term operation
    'ZONE_C_UNSATISFACTORY': 7.1,  # Restricted operation; remedial action required
    'ZONE_D_UNACCEPTABLE': 7.1     # Danger of imminent damage; stop machine
}

# Simulation benchmark assumption: 0.82 kg CO2e/kWh.
# This emission factor is used for synthetic benchmarking and demonstration.
# It is not an independently audited plant-specific electricity emission factor.
DEFAULT_GRID_EMISSION_FACTOR = 0.82  # kg CO2e / kWh

# Environmental Equivalency Factors (EPA / BEE Benchmark Assumptions — Display/Interpretation Only)
# These are display-only interpretation metrics and do NOT affect CO2 emissions, carbon avoided, SEC, or optimization objectives.
TREE_CO2_ABSORPTION_KG_PER_YEAR = 21.77  # kg CO2 absorbed per mature tree per year
CAR_CO2_KG_PER_KM = 0.192                # kg CO2 emitted per passenger car-kilometer

# Standard Indian Industrial Time-of-Day (ToD) Tariff Structure (DISCOM standard)
TOD_TARIFF_SLABS = {
    'PEAK': {'rate': 10.00, 'hours': [(18, 22)], 'description': 'Evening Peak (18:00-22:00)', 'color': '#d62728'},
    'NORMAL': {'rate': 7.50, 'hours': [(6, 18)], 'description': 'Day Normal (06:00-18:00)', 'color': '#1f77b4'},
    'OFF_PEAK': {'rate': 5.50, 'hours': [(22, 24), (0, 6)], 'description': 'Night Off-Peak (22:00-06:00)', 'color': '#2ca02c'}
}

# Consistent Severity-to-Health coupling bounds (Defensible Industrial Mapping)
# CRITICAL: Severe abnormal condition, health substantially degraded (Health <= 45, Risk: HIGH)
# HIGH    : Significant abnormal operating condition (Health <= 65, Risk: HIGH)
# MEDIUM  : Mild abnormal behavior / early warning (Health <= 80, Risk: MEDIUM)
# NORMAL  : Normal operating behavior (Health >= 85, Risk: LOW)
SEVERITY_HEALTH_LIMITS = {
    "CRITICAL": {"max_health": 45, "risk": "HIGH"},
    "HIGH": {"max_health": 65, "risk": "HIGH"},
    "MEDIUM": {"max_health": 80, "risk": "MEDIUM"},
    "NORMAL": {"min_health": 85, "risk": "LOW"}
}

# Centralized Health-Aware Scheduling Policy
# Simulation assumptions for operational risk derating (not measured factory data)
HEALTH_SCHEDULING_POLICY = {
    "NORMAL": {
        "capacity_derating": 1.00,  # 100% of physical capacity
        "allow_scheduling": True,
        "operational_risk": "LOW",
        "description": "Asset in nominal operating condition; normal scheduling capability."
    },
    "MEDIUM": {
        "capacity_derating": 1.00,  # 100% of physical capacity (early warning monitoring)
        "allow_scheduling": True,
        "operational_risk": "MEDIUM",
        "description": "Mild abnormal behavior; normal scheduling allowed, conservative operation recommended."
    },
    "HIGH": {
        "capacity_derating": 0.85,  # Simulation assumption: Derated to 85% of max hourly capacity to limit mechanical/thermal stress
        "allow_scheduling": True,
        "operational_risk": "HIGH",
        "description": "Significant degradation / elevated stress; apply conservative maximum load restriction."
    },
    "CRITICAL": {
        "capacity_derating": 0.00,  # Simulation assumption: 0% capacity (restricted from scheduling pending maintenance)
        "allow_scheduling": False,
        "operational_risk": "CRITICAL",
        "description": "Severe abnormal condition / ISO Zone D vibration; machine restricted from normal production."
    }
}

# Centralized Process Dependency Specifications (Simulation Assumptions)
# Links supporting utility systems to primary textile manufacturing processes
PROCESS_DEPENDENCY_SPECS = {
    "HVAC_SPINNING_COUPLING": {
        "description": "Spinning hall humidification & climate control dependency for ring spinning frame",
        "primary_asset": "MOTOR_01",
        "support_asset": "HVAC_01",
        "support_ratio_k": 0.90,  # Simulation assumption: Normalized HVAC utilization must be >= 90% of spinning utilization
        "rationale": "Yarn moisture and static control require proportional relative humidity control in the spinning hall."
    }
}

# Centralized Dyeing Batch Scheduling Specifications (Simulation Assumptions)
# Enforces continuous multi-hour discrete batch execution for wet textile processing
DYEING_BATCH_SPECS = {
    "PUMP_01": {
        "batch_duration_hours": 3,               # Simulation assumption — not measured factory data
        "min_operating_rate_m3_h": 80.0,         # Simulation assumption — not measured factory data
        "max_hourly_rate_m3_h": 180.0,           # Physical hydraulic pump maximum
        "daily_target_m3": 2500.0,               # Preserved daily production quota
        "base_power_kw": 4.5,                    # Active-batch auxiliary/base power component (0 kW when inactive)
        "marginal_kw_per_unit": 0.105,           # Active pumping power per m3/h circulation rate
        "allow_horizon_wrap": False,             # Strictly forbid batch starts > hour 21
        "rationale": (
            "Simulation assumption — not measured factory data. Standard 3-hour exhaust dyeing cycle "
            "for cotton yarn/fabric liquor circulation (pre-treatment, migration, fixation, and rinsing). "
            "Prevents unphysical intermittent pump cycling."
        )
    }
}

def load_v2_health_state(snapshot_path="results/machine_health_snapshot.json", target_date=None, enriched_path="results/factory_data_enriched.csv"):
    """
    Read-only interface retrieving V2 health, severity, and availability states for the optimizer.
    Preserves V2 health calculation as the single authoritative source.
    """
    hours = list(range(24))
    health_state = {}

    # Case A: Date-specific telemetry query (e.g. historical day or maintenance schedule)
    if target_date is not None and os.path.exists(enriched_path):
        try:
            df = pd.read_csv(enriched_path)
            df_day = df[df["Timestamp"].str.startswith(str(target_date))].copy()
            if not df_day.empty:
                df_day["Hour"] = pd.to_datetime(df_day["Timestamp"]).dt.hour
                for m_id in MACHINE_SPECS:
                    m_df = df_day[df_day["Machine_ID"] == m_id]
                    hourly_avail = []
                    hourly_sev = []
                    hourly_score = []
                    hourly_status = []
                    for h in hours:
                        h_df = m_df[m_df["Hour"] == h]
                        if not h_df.empty:
                            is_maint = h_df["Machine_Status"].apply(is_maintenance_state).any()
                            sevs = h_df["Severity"].tolist()
                            # Rank: CRITICAL > HIGH > MEDIUM > NORMAL
                            if "CRITICAL" in sevs:
                                sev = "CRITICAL"
                            elif "HIGH" in sevs:
                                sev = "HIGH"
                            elif "MEDIUM" in sevs:
                                sev = "MEDIUM"
                            else:
                                sev = "NORMAL"
                            score = int(round(h_df["Health_Score"].mean()))
                            status = "MAINTENANCE" if is_maint else h_df["Machine_Status"].iloc[0]
                            avail = 0.0 if (is_maint or sev == "CRITICAL") else 1.0
                        else:
                            avail, sev, score, status = 1.0, "NORMAL", 100, "RUNNING_OPTIMAL"
                        hourly_avail.append(avail)
                        hourly_sev.append(sev)
                        hourly_score.append(score)
                        hourly_status.append(status)

                    day_sevs = hourly_sev
                    overall_sev = "CRITICAL" if "CRITICAL" in day_sevs else ("HIGH" if "HIGH" in day_sevs else ("MEDIUM" if "MEDIUM" in day_sevs else "NORMAL"))
                    overall_status = "MAINTENANCE" if any(s == "MAINTENANCE" for s in hourly_status) else "RUNNING_OPTIMAL"
                    health_state[m_id] = {
                        "name": MACHINE_SPECS[m_id]["name"],
                        "health_score": min(hourly_score),
                        "risk_level": SEVERITY_HEALTH_LIMITS.get(overall_sev, {}).get("risk", "LOW"),
                        "severity": overall_sev,
                        "status": overall_status,
                        "operational_availability": "MAINTENANCE" if overall_status == "MAINTENANCE" else ("UNAVAILABLE" if overall_sev == "CRITICAL" else "AVAILABLE"),
                        "hourly_availability": hourly_avail,
                        "hourly_severity": hourly_sev,
                        "hourly_health_score": hourly_score,
                        "hourly_status": hourly_status
                    }
                return health_state
        except Exception as e:
            logger.warning(f"Could not load date-specific health for {target_date}: {e}. Falling back to snapshot.")

    # Case B: Latest snapshot from results/machine_health_snapshot.json
    snapshot = {}
    if os.path.exists(snapshot_path):
        try:
            snapshot = load_json(snapshot_path)
        except Exception as e:
            logger.warning(f"Error loading {snapshot_path}: {e}")

    for m_id in MACHINE_SPECS:
        m_data = snapshot.get(m_id, {})
        h_score = m_data.get("health_score", 100)
        risk = m_data.get("risk_level", "LOW")
        sev = m_data.get("severity", "NORMAL")
        status = m_data.get("status", "RUNNING_OPTIMAL")

        if is_maintenance_state(status):
            op_avail = "MAINTENANCE"
            h_avail = [0.0] * 24
        elif sev == "CRITICAL":
            op_avail = "UNAVAILABLE"
            h_avail = [0.0] * 24
        else:
            op_avail = "AVAILABLE"
            h_avail = [1.0] * 24

        health_state[m_id] = {
            "name": MACHINE_SPECS[m_id]["name"],
            "health_score": h_score,
            "risk_level": risk,
            "severity": sev,
            "status": status,
            "operational_availability": op_avail,
            "hourly_availability": h_avail,
            "hourly_severity": [sev] * 24,
            "hourly_health_score": [h_score] * 24,
            "hourly_status": [status] * 24
        }

    return health_state

def is_maintenance_state(status):
    """Returns True if machine is in scheduled/planned maintenance."""
    return str(status).strip().upper() == "MAINTENANCE"

def is_voltage_out_of_bounds(voltage):
    """Checks if line voltage violates physical grid tolerance [340V, 480V]."""
    if pd.isna(voltage):
        return False
    return (voltage < SENSOR_BOUNDS['Voltage_V']['min']) or (voltage > SENSOR_BOUNDS['Voltage_V']['max'])

def classify_iso_vibration(vib_val):
    """
    Maps vibration reading (mm/s RMS) to ISO 10816-3 severity zone.
    """
    if pd.isna(vib_val):
        return 'UNKNOWN'
    if vib_val <= ISO_10816_THRESHOLDS['ZONE_A_GOOD']:
        return 'ZONE_A_GOOD'
    elif vib_val <= ISO_10816_THRESHOLDS['ZONE_B_SATISFACTORY']:
        return 'ZONE_B_SATISFACTORY'
    elif vib_val <= ISO_10816_THRESHOLDS['ZONE_C_UNSATISFACTORY']:
        return 'ZONE_C_UNSATISFACTORY'
    else:
        return 'ZONE_D_UNACCEPTABLE'


def get_tariff_rate(timestamp):
    """
    Calculates applicable ToD tariff (Rs/kWh) for a given timestamp.
    """
    h = timestamp.hour
    if 18 <= h < 22:
        return TOD_TARIFF_SLABS['PEAK']['rate'], 'PEAK'
    elif 6 <= h < 18:
        return TOD_TARIFF_SLABS['NORMAL']['rate'], 'NORMAL'
    else:
        return TOD_TARIFF_SLABS['OFF_PEAK']['rate'], 'OFF_PEAK'

def save_json(obj, filepath):
    """Saves Python dictionary to formatted JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(obj, f, indent=4)

def load_json(filepath):
    """Loads JSON file into Python dictionary."""
    with open(filepath, 'r') as f:
        return json.load(f)
