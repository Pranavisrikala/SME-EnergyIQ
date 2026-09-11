"""
SME-EnergyIQ: Energy & Specific Energy Consumption (SEC) Analytics Engine
Target Industry: Indian Textile Manufacturing SME

Formulas & Engineering Concepts:
1. Fundamental Energy Relationship: E(kWh) = P(kW) * t(h)
2. Specific Energy Consumption: SEC = Energy_Consumed (kWh) / Production_Output (Units)
   - Unit for Ring Spinning (MOTOR_01) : kWh / kg yarn
   - Unit for Compressor (COMPRESSOR_01) : kWh / Nm3 air
   - Unit for Dyeing Pump (PUMP_01)    : kWh / m3 liquor
   - Unit for Humidification (HVAC_01)  : kWh / 1000 m3 air
3. Time-of-Day Cost Breakdown: Peak vs Normal vs Off-Peak
4. Idle Energy Waste Quantification: Energy consumed during non-productive periods
"""

import os
import json
import pandas as pd
import numpy as np

from utils import logger, save_json

def analyze_factory_energy(input_path="results/factory_data_enriched.csv"):
    if not os.path.exists(input_path):
        input_path = "data/processed/factory_data_clean.csv"
        if not os.path.exists(input_path):
            input_path = "data/factory_data.csv"
            
    logger.info(f"Analyzing factory energy profiles from {input_path}...")
    df = pd.read_csv(input_path)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df["Date"] = df["Timestamp"].dt.date
    df["Hour"] = df["Timestamp"].dt.hour
    
    # 1. Factory Totals
    total_energy_kwh = float(df["Energy_kWh"].sum())
    total_cost_rs = float((df["Energy_kWh"] * df["Tariff_Rs_per_kWh"]).sum())
    avg_cost_per_kwh = round(total_cost_rs / max(total_energy_kwh, 1.0), 2)
    max_peak_power_kw = float(df.groupby("Timestamp")["Power_kW"].sum().max())
    avg_factory_power_kw = float(df.groupby("Timestamp")["Power_kW"].sum().mean())
    
    # 2. Breakdown by Machine
    machine_breakdown = {}
    for m_id, group in df.groupby("Machine_ID"):
        m_kwh = float(group["Energy_kWh"].sum())
        m_cost = float((group["Energy_kWh"] * group["Tariff_Rs_per_kWh"]).sum())
        m_prod = float(group["Production_Units"].sum())
        m_sec = round(m_kwh / max(m_prod, 0.1), 4)
        m_peak = float(group["Power_kW"].max())
        m_avg = float(group["Power_kW"].mean())
        
        machine_breakdown[m_id] = {
            "type": group["Machine_Type"].iloc[0],
            "total_energy_kwh": round(m_kwh, 2),
            "share_of_factory_pct": round((m_kwh / total_energy_kwh) * 100.0, 2),
            "total_cost_rs": round(m_cost, 2),
            "total_production": round(m_prod, 1),
            "sec_kwh_per_unit": m_sec,
            "peak_power_kw": round(m_peak, 2),
            "avg_power_kw": round(m_avg, 2)
        }
        
    # 3. Energy by Machine Operating State
    state_breakdown = {}
    for state, group in df.groupby("Machine_Status"):
        s_kwh = float(group["Energy_kWh"].sum())
        s_cost = float((group["Energy_kWh"] * group["Tariff_Rs_per_kWh"]).sum())
        state_breakdown[state] = {
            "total_kwh": round(s_kwh, 2),
            "share_pct": round((s_kwh / total_energy_kwh) * 100.0, 2),
            "cost_rs": round(s_cost, 2),
            "intervals_count": int(len(group))
        }
        
    # Idle waste quantification
    idle_kwh = state_breakdown.get("IDLE_UNLOADED", {}).get("total_kwh", 0.0)
    idle_cost = state_breakdown.get("IDLE_UNLOADED", {}).get("cost_rs", 0.0)
    
    # 4. Energy and Cost by Tariff Window (Time-of-Day)
    tariff_breakdown = {}
    for t_type, group in df.groupby("Peak_OffPeak"):
        t_kwh = float(group["Energy_kWh"].sum())
        t_cost = float((group["Energy_kWh"] * group["Tariff_Rs_per_kWh"]).sum())
        tariff_breakdown[t_type] = {
            "total_kwh": round(t_kwh, 2),
            "share_pct": round((t_kwh / total_energy_kwh) * 100.0, 2),
            "cost_rs": round(t_cost, 2),
            "cost_share_pct": round((t_cost / total_cost_rs) * 100.0, 2)
        }
        
    # 5. Daily Summary & SEC Profile
    daily_records = []
    for date, day_group in df.groupby("Date"):
        day_kwh = float(day_group["Energy_kWh"].sum())
        day_cost = float((day_group["Energy_kWh"] * day_group["Tariff_Rs_per_kWh"]).sum())
        # Spinning yarn is the core commercial throughput proxy
        yarn_prod = float(day_group[day_group["Machine_ID"] == "MOTOR_01"]["Production_Units"].sum())
        day_sec = round(day_kwh / max(yarn_prod, 1.0), 3)
        peak_kw = float(day_group.groupby("Timestamp")["Power_kW"].sum().max())
        
        daily_records.append({
            "Date": str(date),
            "Total_Energy_kWh": round(day_kwh, 2),
            "Total_Cost_Rs": round(day_cost, 2),
            "Yarn_Production_kg": round(yarn_prod, 1),
            "Factory_SEC_kWh_per_kg": day_sec,
            "Peak_Demand_kW": round(peak_kw, 2)
        })
    df_daily = pd.DataFrame(daily_records)
    
    # Factory baseline SEC (Total Factory kWh / Total Yarn kg)
    total_yarn = float(df[df["Machine_ID"] == "MOTOR_01"]["Production_Units"].sum())
    baseline_factory_sec = round(total_energy_kwh / max(total_yarn, 1.0), 3)

    summary = {
        "factory_overview": {
            "total_energy_kwh": round(total_energy_kwh, 2),
            "total_cost_rs": round(total_cost_rs, 2),
            "average_cost_per_kwh_rs": avg_cost_per_kwh,
            "peak_demand_kw": round(max_peak_power_kw, 2),
            "average_demand_kw": round(avg_factory_power_kw, 2),
            "baseline_factory_sec_kwh_per_kg": baseline_factory_sec,
            "total_yarn_production_kg": round(total_yarn, 1),
            "idle_energy_waste_kwh": round(idle_kwh, 2),
            "idle_energy_waste_cost_rs": round(idle_cost, 2)
        },
        "machine_breakdown": machine_breakdown,
        "operating_state_breakdown": state_breakdown,
        "tariff_window_breakdown": tariff_breakdown
    }

    # Save outputs
    os.makedirs("results", exist_ok=True)
    save_json(summary, "results/energy_summary.json")
    df_daily.to_csv("results/daily_sec_profile.csv", index=False)
    logger.info("Energy and SEC analytics completed and saved to results/")
    
    return summary, df_daily

if __name__ == "__main__":
    summary, df_daily = analyze_factory_energy()
    print("\n=== FACTORY ENERGY OVERVIEW ===")
    for k, v in summary["factory_overview"].items():
        print(f"  {k}: {v}")
        
    print("\n=== MACHINE ENERGY & SEC BREAKDOWN ===")
    for m_id, data in summary["machine_breakdown"].items():
        print(f"  {m_id} ({data['type']}):")
        print(f"    Energy: {data['total_energy_kwh']} kWh ({data['share_of_factory_pct']}%) | Cost: Rs. {data['total_cost_rs']}")
        print(f"    SEC: {data['sec_kwh_per_unit']} kWh/unit | Peak: {data['peak_power_kw']} kW")
        
    print("\n=== TARIFF TIME-OF-DAY BREAKDOWN ===")
    for t_zone, data in summary["tariff_window_breakdown"].items():
        print(f"  {t_zone}: {data['total_kwh']} kWh ({data['share_pct']}%) -> Rs. {data['cost_rs']} ({data['cost_share_pct']}% of bill)")
        
    print("\nDaily SEC Sample:")
    print(df_daily.head())
