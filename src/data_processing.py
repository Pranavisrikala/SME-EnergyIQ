"""
SME-EnergyIQ: Industrial Data Processing & Validation Pipeline
Target Industry: Indian Textile Manufacturing SME

Performs:
- Rigorous data quality auditing (missing values, duplicates, range violations)
- Transparent reporting (avoids silent row dropping)
- Sensor boundary enforcement and anomaly tagging
- Industrial feature engineering:
  * SEC Proxy (kWh per unit equivalent)
  * Thermal drift relative to operational baseline
  * ISO 10816 vibration severity categorization
  * Machine loading ratios
"""

import os
import logging
import pandas as pd
import numpy as np

from utils import (
    MACHINE_SPECS,
    SENSOR_BOUNDS,
    classify_iso_vibration,
    get_tariff_rate,
    logger
)

def audit_data_quality(df):
    """
    Performs data quality checks without silently modifying or dropping rows.
    Returns audit summary dictionary.
    """
    total_rows = len(df)
    logger.info(f"Auditing data quality across {total_rows} industrial records...")
    
    missing_by_col = df.isnull().sum().to_dict()
    total_missing = int(df.isnull().sum().sum())
    
    # Check for duplicate timestamps per machine
    duplicates = int(df.duplicated(subset=["Timestamp", "Machine_ID"]).sum())
    
    # Boundary violations
    bounds_violations = {}
    total_violations = 0
    for col, bounds in SENSOR_BOUNDS.items():
        if col in df.columns:
            invalid_mask = (df[col] < bounds["min"]) | (df[col] > bounds["max"])
            count = int(invalid_mask.sum())
            bounds_violations[col] = count
            total_violations += count
            if count > 0:
                logger.warning(
                    f"Sensor range violation in '{col}': {count} readings outside "
                    f"[{bounds['min']}, {bounds['max']}]"
                )

    # Calculate Data Quality Index (DQI)
    clean_cells = (total_rows * len(df.columns)) - total_missing - total_violations
    dqi_score = round(max(0.0, (clean_cells / (total_rows * len(df.columns))) * 100.0), 2)
    
    report = {
        "total_records": total_rows,
        "total_missing_values": total_missing,
        "missing_by_column": missing_by_col,
        "duplicate_timestamps": duplicates,
        "sensor_bounds_violations": bounds_violations,
        "total_violations": total_violations,
        "data_quality_index_pct": dqi_score
    }
    
    logger.info(f"Data Quality Audit Completed. Data Quality Index: {dqi_score}%")
    return report

def clean_and_engineer_features(df):
    """
    Validates input dataset, handles missing data transparently,
    and constructs industrial diagnostic features.
    """
    df_clean = df.copy()
    
    # Ensure datetime format
    df_clean["Timestamp"] = pd.to_datetime(df_clean["Timestamp"])
    df_clean = df_clean.sort_values(by=["Machine_ID", "Timestamp"]).reset_index(drop=True)
    
    # Impute missing values with forward fill if present
    if df_clean.isnull().values.any():
        logger.warning("Missing values detected! Applying transparent forward-fill imputation.")
        df_clean = df_clean.ffill().bfill()
        
    # Feature 1: Machine Physical Baselines and Load Ratio
    df_clean["Rated_Power_kW"] = df_clean["Machine_ID"].map(lambda m: MACHINE_SPECS.get(m, {}).get("rated_power", 50.0))
    df_clean["Nominal_Power_kW"] = df_clean["Machine_ID"].map(lambda m: MACHINE_SPECS.get(m, {}).get("nominal_power", 40.0))
    df_clean["Expected_Idle_Power_kW"] = df_clean["Machine_ID"].map(lambda m: MACHINE_SPECS.get(m, {}).get("idle_power", 10.0))
    df_clean["Nominal_Temp_C"] = df_clean["Machine_ID"].map(lambda m: MACHINE_SPECS.get(m, {}).get("nominal_temp", 50.0))
    df_clean["Nominal_Vib_mm_s"] = df_clean["Machine_ID"].map(lambda m: MACHINE_SPECS.get(m, {}).get("nominal_vib", 1.8))
    df_clean["Nominal_RPM"] = df_clean["Machine_ID"].map(lambda m: MACHINE_SPECS.get(m, {}).get("nominal_rpm", 1450.0))
    
    df_clean["Load_Ratio"] = (df_clean["Power_kW"] / df_clean["Rated_Power_kW"]).clip(0.0, 1.5).round(3)
    
    # Feature 2: True Production Specific Energy Consumption (SEC)
    # Calculated strictly when meaningful production occurs; 0.0 otherwise
    # SEC (kWh/unit) = Energy_kWh / Production_Units
    df_clean["Production_SEC"] = np.where(
        df_clean["Production_Units"] > 0.05,
        (df_clean["Energy_kWh"] / df_clean["Production_Units"]).round(3),
        0.0
    )
    df_clean["SEC_Proxy"] = df_clean["Production_SEC"] # Maintain backwards compatibility
    
    # Feature 3: Machine-Specific Baseline Divergences (V2 AI Features)
    # Sustained thermal elevation relative to machine normal baseline (not rolling window)
    df_clean["Temp_Elevation"] = (df_clean["Temperature_C"] - df_clean["Nominal_Temp_C"]).round(2)
    
    # Rolling 1-hour mean kept for dashboard visualization
    df_clean["Temp_1h_Rolling_Mean"] = df_clean.groupby("Machine_ID")["Temperature_C"].transform(
        lambda x: x.rolling(window=4, min_periods=1).mean()
    ).round(2)
    
    # Excess Idle Power: Pinpoints unloader valve failure without penalizing normal meal breaks
    df_clean["Excess_Idle_Power"] = np.where(
        df_clean["Production_Units"] <= 0.05,
        np.maximum(0.0, df_clean["Power_kW"] - df_clean["Expected_Idle_Power_kW"] * 1.15).round(3),
        0.0
    )
    
    # Vibration elevation above baseline
    df_clean["Vib_Elevation"] = np.maximum(0.0, df_clean["Vibration_mm_s"] - df_clean["Nominal_Vib_mm_s"]).round(3)
    
    # Speed drop under mechanical friction/binding
    df_clean["RPM_Drop"] = np.where(
        df_clean["Power_kW"] > 5.0,
        np.maximum(0.0, df_clean["Nominal_RPM"] - df_clean["RPM"]).round(1),
        0.0
    )
    
    # Feature 4: ISO 10816 Vibration Severity Zone
    df_clean["ISO_Vib_Zone"] = df_clean["Vibration_mm_s"].apply(classify_iso_vibration)
    
    # Feature 5: Vibration to Power Ratio (normalized during active load)
    df_clean["Vib_to_Power_Ratio"] = (
        df_clean["Vibration_mm_s"] / (df_clean["Power_kW"] + 1.0)
    ).round(4)
    
    # Feature 6: Cumulative Energy Cost in INR
    df_clean["Energy_Cost_Rs"] = (df_clean["Energy_kWh"] * df_clean["Tariff_Rs_per_kWh"]).round(2)
    
    # Re-sort to chronological factory-wide order
    df_clean = df_clean.sort_values(by=["Timestamp", "Machine_ID"]).reset_index(drop=True)
    return df_clean

def run_pipeline():
    raw_path = os.path.join("data", "factory_data.csv")
    if not os.path.exists(raw_path):
        logger.error(f"Raw data file not found at {raw_path}. Run generate_data.py first!")
        return None, None
        
    df = pd.read_csv(raw_path)
    report = audit_data_quality(df)
    
    df_clean = clean_and_engineer_features(df)
    
    os.makedirs("data/processed", exist_ok=True)
    out_path = os.path.join("data", "processed", "factory_data_clean.csv")
    df_clean.to_csv(out_path, index=False)
    logger.info(f"Processed dataset saved to {out_path} ({len(df_clean)} rows, {len(df_clean.columns)} columns)")
    
    return report, df_clean

if __name__ == "__main__":
    report, df_clean = run_pipeline()
    if report:
        print("\n=== DATA QUALITY AUDIT REPORT ===")
        print(f"Total Records: {report['total_records']}")
        print(f"Data Quality Index: {report['data_quality_index_pct']}%")
        print(f"Duplicate Timestamps: {report['duplicate_timestamps']}")
        print(f"Sensor Range Violations: {report['sensor_bounds_violations']}")
        print("\n=== PROCESSED DATA SAMPLE ===")
        print(df_clean[["Timestamp", "Machine_ID", "Load_Ratio", "SEC_Proxy", "ISO_Vib_Zone", "Energy_Cost_Rs"]].head())

