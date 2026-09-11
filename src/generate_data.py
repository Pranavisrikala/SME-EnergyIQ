"""
SME-EnergyIQ: Industrial Synthetic Data Generator
Target Industry: Indian Textile Manufacturing SME (Spinning & Weaving Mill)

Simulates 4 core machines:
1. MOTOR_01      : Ring Spinning Frame Main Drive Motor (55 kW rated)
2. COMPRESSOR_01 : Screw Air Compressor for Air-Jet Looms & Pneumatics (45 kW rated)
3. PUMP_01       : Dyeing & Bleaching Liquor Circulation Pump (22 kW rated)
4. HVAC_01       : Spinning Hall Humidification & Climate Control Plant (60 kW rated)

Captures:
- 15-minute industrial interval data (standard for Indian utility ToD metering)
- Time-of-Day (ToD) tariffs: Peak (₹10.0), Normal (₹7.5), Off-Peak (₹5.5)
- Electrical physics (P = sqrt(3) * V * I * pf)
- Machine operational states (RUNNING_OPTIMAL, IDLE_UNLOADED, RUNNING_DEGRADED, MAINTENANCE, OFF)
- 7 distinct industrial anomaly classes with ground truth
"""

import os
import numpy as np
import pandas as pd

# Set fixed seed for reproducibility across hackathon evaluations
np.random.seed(42)

def get_tariff(timestamp):
    """
    Returns Time-of-Day (ToD) tariff for Indian Industrial Consumers.
    Standard Indian DISCOM slab:
      - Peak (18:00 - 22:00): ₹10.00 / kWh
      - Normal (06:00 - 18:00): ₹7.50 / kWh
      - Off-Peak / Night (22:00 - 06:00): ₹5.50 / kWh
    """
    hour = timestamp.hour
    if 18 <= hour < 22:
        return 10.00, "PEAK"
    elif 6 <= hour < 18:
        return 7.50, "NORMAL"
    else:
        return 5.50, "OFF_PEAK"

def generate_textile_factory_dataset(
    days=14,
    freq="15min",
    start_date="2026-01-01 00:00:00"
):
    timestamps = pd.date_range(start=start_date, periods=days * 96, freq=freq)
    
    records = []

    # Machine baseline specifications
    machines = {
        "MOTOR_01": {
            "type": "Spinning Motor",
            "rated_power": 55.0,     # kW
            "nominal_power": 45.0,   # kW (at full production)
            "idle_power": 12.0,      # kW (unloaded spinning spindle draft)
            "nominal_temp": 62.0,    # °C
            "nominal_vib": 1.8,      # mm/s RMS (ISO 10816 Class II good zone)
            "nominal_rpm": 1485.0,   # 4-pole induction motor slip speed
            "unit_name": "kg_yarn",
            "base_output_per_15m": 48.0 # kg yarn per 15 min
        },
        "COMPRESSOR_01": {
            "type": "Air Compressor",
            "rated_power": 45.0,     # kW
            "nominal_power": 38.0,   # kW (loaded)
            "idle_power": 16.0,      # kW (unloaded running)
            "nominal_temp": 75.0,    # °C (oil & air delivery temp)
            "nominal_vib": 2.2,      # mm/s RMS
            "nominal_rpm": 2950.0,   # 2-pole screw drive
            "unit_name": "Nm3_air",
            "base_output_per_15m": 210.0 # Nm3 air per 15 min
        },
        "PUMP_01": {
            "type": "Water Pump",
            "rated_power": 22.0,     # kW
            "nominal_power": 18.0,   # kW (pumping dye liquor)
            "idle_power": 4.5,       # kW (recirculation throttled)
            "nominal_temp": 52.0,    # °C
            "nominal_vib": 1.4,      # mm/s RMS
            "nominal_rpm": 1450.0,   # 4-pole centrifugal pump
            "unit_name": "m3_liquor",
            "base_output_per_15m": 28.0 # m3 liquor per 15 min
        },
        "HVAC_01": {
            "type": "HVAC System",
            "rated_power": 60.0,     # kW
            "nominal_power": 48.0,   # kW (humidification & chillers)
            "idle_power": 15.0,      # kW (fans only)
            "nominal_temp": 45.0,    # °C (compressor discharge)
            "nominal_vib": 1.6,      # mm/s RMS
            "nominal_rpm": 980.0,    # 6-pole fan/blower drive
            "unit_name": "m3_conditioned",
            "base_output_per_15m": 1200.0 # m3 conditioned air
        }
    }

    for m_id, spec in machines.items():
        cum_hours = 2400.0 + np.random.uniform(100, 800) # Initial machine runtime
        
        for i, ts in enumerate(timestamps):
            tariff, peak_type = get_tariff(ts)
            hour = ts.hour
            day_of_week = ts.dayofweek # 0=Monday, 6=Sunday
            
            # Realistic factory shift & load cycle:
            # Shift 1: 06:00 - 14:00 (Full load)
            # Shift 2: 14:00 - 22:00 (High load, peak tariff evening)
            # Shift 3: 22:00 - 06:00 (Night shift, baseline production)
            # Scheduled maintenance: Sunday morning 08:00 - 12:00
            
            is_maintenance = (day_of_week == 6 and 8 <= hour < 12)
            is_meal_break = (hour in [13, 21]) and (ts.minute < 30) # 30-min meal break
            
            if is_maintenance:
                status = "MAINTENANCE"
                load_factor = 0.0
                prod_target = 0.0
                maint_status = "IN_PROGRESS"
            elif is_meal_break:
                status = "IDLE_UNLOADED"
                load_factor = 0.15
                prod_target = spec["base_output_per_15m"] * 0.2
                maint_status = "GOOD"
            else:
                # Regular operation with minor shift load fluctuations
                status = "RUNNING_OPTIMAL"
                base_lf = 0.88 + 0.08 * np.sin(2 * np.pi * hour / 24)
                load_factor = np.clip(base_lf + np.random.normal(0, 0.03), 0.60, 1.0)
                prod_target = spec["base_output_per_15m"]
                maint_status = "GOOD"
                
            # Physics calculations
            if status == "MAINTENANCE":
                power_kw = 0.0
                rpm = 0.0
                temp_c = 28.0 + np.random.normal(0, 0.5) # Ambient temperature
                vib_mm_s = 0.05
                prod_units = 0.0
                pf = 1.0
            elif status == "IDLE_UNLOADED":
                power_kw = spec["idle_power"] + np.random.normal(0, 0.5)
                rpm = spec["nominal_rpm"] + np.random.normal(5, 3) # Unloaded runs slightly faster
                temp_c = spec["nominal_temp"] - 8.0 + np.random.normal(0, 0.8)
                vib_mm_s = spec["nominal_vib"] * 0.7 + np.random.normal(0, 0.05)
                prod_units = 0.0 # Idle produces zero output
                pf = 0.68 # Low power factor in unloaded induction machines
            else: # RUNNING_OPTIMAL
                power_kw = spec["nominal_power"] * load_factor + np.random.normal(0, 0.8)
                # RPM drops slightly under heavier mechanical torque load (motor slip)
                rpm = spec["nominal_rpm"] * (1.0 - 0.02 * (load_factor - 0.85)) + np.random.normal(0, 4)
                # Temperature tracks load and ambient diurnal heat
                ambient_delta = 5.0 * np.sin(2 * np.pi * (hour - 8) / 24) # Peak ambient at 14:00
                temp_c = spec["nominal_temp"] + (load_factor - 0.85) * 12.0 + ambient_delta + np.random.normal(0, 0.7)
                vib_mm_s = spec["nominal_vib"] * (0.9 + 0.2 * load_factor) + np.random.normal(0, 0.08)
                prod_units = max(0.0, prod_target * (load_factor / 0.88) + np.random.normal(0, 1.2))
                pf = 0.89 + np.random.normal(0, 0.01)

            # Three-phase electrical calculations:
            # V_line = 415V nominal, with +/- 2% Indian grid fluctuation
            voltage_v = 415.0 + 8.0 * np.sin(2 * np.pi * hour / 24) + np.random.normal(0, 2.5)
            if power_kw > 0.1:
                # I = (P * 1000) / (sqrt(3) * V * pf)
                current_a = (power_kw * 1000.0) / (np.sqrt(3) * voltage_v * pf)
            else:
                current_a = 0.0

            # Energy in 15-minute interval: E = P * (15/60) = P * 0.25 kWh
            energy_kwh = power_kw * 0.25
            if power_kw > 1.0:
                cum_hours += 0.25

            records.append({
                "Timestamp": ts,
                "Machine_ID": m_id,
                "Machine_Type": spec["type"],
                "Power_kW": round(float(power_kw), 3),
                "Energy_kWh": round(float(energy_kwh), 4),
                "Voltage_V": round(float(voltage_v), 1),
                "Current_A": round(float(current_a), 2),
                "Temperature_C": round(float(temp_c), 2),
                "Vibration_mm_s": round(float(max(0.01, vib_mm_s)), 3),
                "RPM": round(float(max(0.0, rpm)), 1),
                "Operating_Hours": round(float(cum_hours), 2),
                "Production_Units": round(float(prod_units), 2),
                "Production_Target": round(float(prod_target), 2),
                "Machine_Status": status,
                "Ground_Truth": 0,
                "Anomaly_Type": "NORMAL",
                "Tariff_Rs_per_kWh": tariff,
                "Peak_OffPeak": peak_type,
                "Maintenance_Status": maint_status
            })

    df = pd.DataFrame(records)

    # -------------------------------------------------------------
    # REALISTIC INDUSTRIAL ANOMALY INJECTION
    # Diverse classes distributed across machines and days
    # -------------------------------------------------------------
    
    # Machine 1 (MOTOR_01): Combined mechanical degradation (bearing wear / friction)
    # Day 9, 10:00 to 14:00 (16 intervals)
    mask_deg = (
        (df["Machine_ID"] == "MOTOR_01") &
        (df["Timestamp"] >= "2026-01-09 10:00:00") &
        (df["Timestamp"] <= "2026-01-09 14:00:00")
    )
    df.loc[mask_deg, "Ground_Truth"] = 1
    df.loc[mask_deg, "Anomaly_Type"] = "COMBINED_HEALTH_ANOMALY"
    df.loc[mask_deg, "Machine_Status"] = "RUNNING_DEGRADED"
    df.loc[mask_deg, "Power_kW"] *= 1.32  # 32% extra power due to mechanical drag
    df.loc[mask_deg, "Temperature_C"] += 18.5 # Bearing friction heating
    df.loc[mask_deg, "Vibration_mm_s"] += 3.8 # Elevated vibration (ISO 10816 danger zone)
    df.loc[mask_deg, "RPM"] -= 95.0 # Speed drop due to mechanical binding
    df.loc[mask_deg, "Maintenance_Status"] = "NEEDS_INSPECTION"

    # Machine 2 (COMPRESSOR_01): Idle energy waste (Unloader valve failure)
    # Machine runs fully unloaded overnight drawing high power without producing air
    # Day 5, 23:00 to Day 6 04:00 (20 intervals)
    mask_idle = (
        (df["Machine_ID"] == "COMPRESSOR_01") &
        (df["Timestamp"] >= "2026-01-05 23:00:00") &
        (df["Timestamp"] <= "2026-01-06 04:00:00")
    )
    df.loc[mask_idle, "Ground_Truth"] = 1
    df.loc[mask_idle, "Anomaly_Type"] = "IDLE_WASTE"
    df.loc[mask_idle, "Machine_Status"] = "IDLE_UNLOADED"
    df.loc[mask_idle, "Power_kW"] = 28.5 + np.random.normal(0, 1.0, mask_idle.sum()) # Wasteful 63% power draw
    df.loc[mask_idle, "Production_Units"] = 0.0 # Zero compressed air utilized

    # Machine 2 (COMPRESSOR_01): Vibration anomaly (Belt loose / coupling misalignment)
    # Day 11, 14:00 to 17:30 (14 intervals)
    mask_vib = (
        (df["Machine_ID"] == "COMPRESSOR_01") &
        (df["Timestamp"] >= "2026-01-11 14:00:00") &
        (df["Timestamp"] <= "2026-01-11 17:30:00")
    )
    df.loc[mask_vib, "Ground_Truth"] = 1
    df.loc[mask_vib, "Anomaly_Type"] = "VIBRATION_ANOMALY"
    df.loc[mask_vib, "Vibration_mm_s"] += 4.5 # Heavy vibration spike

    # Machine 3 (PUMP_01): Inefficient operation (Cavitation / Impeller blockage)
    # High power draw while pumping volume drops drastically
    # Day 8, 09:00 to 13:00 (16 intervals)
    mask_ineff = (
        (df["Machine_ID"] == "PUMP_01") &
        (df["Timestamp"] >= "2026-01-08 09:00:00") &
        (df["Timestamp"] <= "2026-01-08 13:00:00")
    )
    df.loc[mask_ineff, "Ground_Truth"] = 1
    df.loc[mask_ineff, "Anomaly_Type"] = "INEFFICIENT_OPERATION"
    df.loc[mask_ineff, "Power_kW"] *= 1.25
    df.loc[mask_ineff, "Production_Units"] *= 0.45 # Throughput collapsed by 55%
    df.loc[mask_ineff, "Vibration_mm_s"] += 2.2 # Fluid turbulence / cavitation vibration

    # Machine 4 (HVAC_01): Thermal anomaly (Condenser coil choking / refrigerant leak)
    # High temperature rise with excessive power consumption
    # Day 12, 12:00 to 18:00 (24 intervals)
    mask_temp = (
        (df["Machine_ID"] == "HVAC_01") &
        (df["Timestamp"] >= "2026-01-12 12:00:00") &
        (df["Timestamp"] <= "2026-01-12 18:00:00")
    )
    df.loc[mask_temp, "Ground_Truth"] = 1
    df.loc[mask_temp, "Anomaly_Type"] = "TEMPERATURE_ANOMALY"
    df.loc[mask_temp, "Power_kW"] *= 1.28
    df.loc[mask_temp, "Temperature_C"] += 24.0 # Severe thermal buildup

    # Sensor glitch / anomaly (Single-point measurement artifact)
    # 10 sporadic sensor glitches across various machines
    glitch_indices = np.random.choice(df[df["Ground_Truth"] == 0].index, size=10, replace=False)
    for idx in glitch_indices:
        sensor_choice = np.random.choice(["Power_kW", "Voltage_V", "Vibration_mm_s", "Temperature_C"])
        df.loc[idx, "Ground_Truth"] = 1
        df.loc[idx, "Anomaly_Type"] = "SENSOR_GLITCH"
        if sensor_choice == "Power_kW":
            df.loc[idx, "Power_kW"] = df.loc[idx, "Power_kW"] * 2.5
        elif sensor_choice == "Voltage_V":
            df.loc[idx, "Voltage_V"] = 210.0 # Unrealistic voltage drop spike
        elif sensor_choice == "Vibration_mm_s":
            df.loc[idx, "Vibration_mm_s"] = 14.5
        elif sensor_choice == "Temperature_C":
            df.loc[idx, "Temperature_C"] = 115.0

    # Re-synchronize derived electrical columns after anomaly modifications
    df["Energy_kWh"] = (df["Power_kW"] * 0.25).round(4)
    # Update Current_A for modified power
    active_mask = df["Power_kW"] > 0.1
    df.loc[active_mask, "Current_A"] = (
        (df.loc[active_mask, "Power_kW"] * 1000.0) / 
        (np.sqrt(3) * df.loc[active_mask, "Voltage_V"] * 0.88)
    ).round(2)

    # Sort deterministically by Timestamp and Machine_ID
    df = df.sort_values(by=["Timestamp", "Machine_ID"]).reset_index(drop=True)
    return df

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    print("Generating comprehensive industrial dataset for SME-EnergyIQ...")
    df = generate_textile_factory_dataset(days=14, freq="15min")
    
    csv_path = os.path.join("data", "factory_data.csv")
    df.to_csv(csv_path, index=False)
    
    print(f"Factory dataset created successfully at: {csv_path}")
    print(f"Total readings: {len(df):,}")
    print(f"Machines simulated: {df['Machine_ID'].nunique()} ({list(df['Machine_ID'].unique())})")
    print(f"Date range: {df['Timestamp'].min()} to {df['Timestamp'].max()}")
    print("\nAnomaly Breakdown:")
    print(df["Anomaly_Type"].value_counts())
    print("\nSample records:")
    print(df[["Timestamp", "Machine_ID", "Power_kW", "Energy_kWh", "Temperature_C", "Vibration_mm_s", "Anomaly_Type"]].head())