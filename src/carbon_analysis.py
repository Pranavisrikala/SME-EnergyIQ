"""
SME-EnergyIQ: Carbon Accounting & Industrial Sustainability Engine
Target Industry: Indian Textile Manufacturing SME

Core Methodology:
1. Carbon Emission Formula:
   CO2e (kg) = Energy_Consumption (kWh) * Emission_Factor (kg CO2e / kWh)
2. Indian Grid Reference:
   Central Electricity Authority (CEA) Baseline Database for Indian Power Sector (v19)
   Default Indian National Grid Weighted Average: 0.82 kg CO2e / kWh
3. Configurable Parameter:
   Users can adjust for state DISCOM grids (e.g. TANGEDCO, MSEDCL, UGVCL)
   or renewable captive solar/wind PPAs (Power Purchase Agreements).
4. Outputs:
   - Factory total CO2e (kg & metric tonnes)
   - Baseline vs Optimized avoided emissions
   - Carbon Intensity per kg of textile production
"""

import os
import pandas as pd
import numpy as np

from utils import (
    CAR_CO2_KG_PER_KM,
    DEFAULT_GRID_EMISSION_FACTOR,
    TREE_CO2_ABSORPTION_KG_PER_YEAR,
    logger,
    save_json
)

DISCOM_GRID_FACTORS = {
    "National_Grid_CEA_Avg": DEFAULT_GRID_EMISSION_FACTOR,
    "Tamil_Nadu_TANGEDCO": 0.79,
    "Maharashtra_MSEDCL": 0.85,
    "Gujarat_UGVCL": 0.81,
    "Green_PPA_Solar_Blend": 0.35 # 60% Solar + 40% Grid
}

def calculate_carbon_footprint(
    energy_kwh,
    emission_factor=DEFAULT_GRID_EMISSION_FACTOR
):
    """
    Computes greenhouse gas emissions with explicit factor citation.
    """
    co2_kg = energy_kwh * emission_factor
    co2_tonnes = co2_kg / 1000.0
    return round(co2_kg, 2), round(co2_tonnes, 3)

def generate_sustainability_report(
    emission_factor=DEFAULT_GRID_EMISSION_FACTOR,
    data_path="results/factory_data_enriched.csv"
):
    if not os.path.exists(data_path):
        data_path = "data/processed/factory_data_clean.csv"
        
    logger.info(f"Generating carbon sustainability report with grid factor: {emission_factor} kg CO2e/kWh...")
    df = pd.read_csv(data_path)
    
    total_factory_kwh = float(df["Energy_kWh"].sum())
    total_co2_kg, total_co2_tonnes = calculate_carbon_footprint(total_factory_kwh, emission_factor)
    
    # Machine breakdown
    machine_carbon = {}
    for m_id, grp in df.groupby("Machine_ID"):
        m_kwh = float(grp["Energy_kWh"].sum())
        m_co2_kg, m_co2_t = calculate_carbon_footprint(m_kwh, emission_factor)
        machine_carbon[m_id] = {
            "type": grp["Machine_Type"].iloc[0],
            "energy_kwh": round(m_kwh, 2),
            "co2_emissions_kg": m_co2_kg,
            "co2_emissions_tonnes": m_co2_t,
            "carbon_share_pct": round((m_kwh / total_factory_kwh) * 100.0, 2)
        }
        
    # Production throughput and carbon intensity
    yarn_df = df[df["Machine_ID"] == "MOTOR_01"]
    total_yarn_kg = float(yarn_df["Production_Units"].sum())
    if total_yarn_kg > 0:
        yarn_carbon_intensity = round(total_co2_kg / total_yarn_kg, 3) # kg CO2e per kg yarn
    else:
        yarn_carbon_intensity = None
    
    # Load optimization results if available
    opt_file = "results/optimization_results.json"
    opt_carbon_impact = {}
    if os.path.exists(opt_file):
        import json
        with open(opt_file, "r") as f:
            opt_data = json.load(f)
            base_kwh = float(opt_data["metrics"]["Total_Energy_kWh"]["baseline"])
            opt_kwh = float(opt_data["metrics"]["Total_Energy_kWh"]["optimized"])
            base_emissions = round(base_kwh * emission_factor, 2)
            opt_emissions = round(opt_kwh * emission_factor, 2)
            avoided_emissions_daily = round((base_kwh - opt_kwh) * emission_factor, 2)
            annual_potential_avoided = round(avoided_emissions_daily * 300.0 / 1000.0, 2) # 300 working days, tonnes
            base_yarn = float(opt_data["metrics"]["Yarn_Production_kg"]["baseline"])
            opt_yarn = float(opt_data["metrics"]["Yarn_Production_kg"]["optimized"])
            if base_yarn > 0:
                base_ci = round(base_emissions / base_yarn, 4)
            else:
                base_ci = None
            if opt_yarn > 0:
                opt_ci = round(opt_emissions / opt_yarn, 4)
            else:
                opt_ci = None
            opt_carbon_impact = {
                "baseline_emissions_kg_per_day": base_emissions,
                "optimized_emissions_kg_per_day": opt_emissions,
                "avoided_emissions_daily_kg": avoided_emissions_daily,
                "annual_potential_avoided_tonnes": annual_potential_avoided,
                "baseline_carbon_intensity_kg_per_kg": base_ci,
                "optimized_carbon_intensity_kg_per_kg": opt_ci,
                "emission_factor_kg_co2e_per_kwh": emission_factor,
                "disclaimer": "Model-estimated Scope 2 carbon impact from synthetic 24-hour optimization schedule (300 working days/year projection)."
            }
            
    # Environmental Equivalencies (EPA & BEE methodology)
    # Display-only interpretation metrics; do not alter emissions or energy calculations
    equivalent_trees_planted = round(total_co2_kg / TREE_CO2_ABSORPTION_KG_PER_YEAR, 1)
    equivalent_car_km = round(total_co2_kg / CAR_CO2_KG_PER_KM, 1)

    report = {
        "metadata": {
            "emission_factor_used_kg_per_kwh": emission_factor,
            "emission_factor_source": "Central Electricity Authority (CEA) Baseline Database v19 (Govt. of India reference assumption)",
            "disclaimer": (
                "Simulation benchmark assumption: 0.82 kg CO2e/kWh. "
                "This emission factor is used for synthetic benchmarking and demonstration. "
                "It is not an independently audited plant-specific electricity emission factor."
            )
        },
        "factory_footprint_14_days": {
            "total_energy_consumed_kwh": round(total_factory_kwh, 2),
            "total_co2_emissions_kg": total_co2_kg,
            "total_co2_emissions_tonnes": total_co2_tonnes,
            "total_yarn_kg": round(total_yarn_kg, 2),
            "carbon_intensity_kg_co2_per_kg_yarn": yarn_carbon_intensity
        },
        "optimization_carbon_impact": opt_carbon_impact,
        "machine_carbon_breakdown": machine_carbon,
        "equivalencies": {
            "tree_seedlings_grown_10_years": equivalent_trees_planted,
            "passenger_car_km_equivalent": equivalent_car_km
        },
        "grid_sensitivity_analysis": {
            k: {
                "factor": v,
                "total_co2_tonnes": calculate_carbon_footprint(total_factory_kwh, v)[1]
            }
            for k, v in DISCOM_GRID_FACTORS.items()
        }
    }
    
    os.makedirs("results", exist_ok=True)
    save_json(report, "results/carbon_sustainability_report.json")
    logger.info("Carbon and sustainability report saved to results/carbon_sustainability_report.json")
    return report

if __name__ == "__main__":
    rep = generate_sustainability_report()
    meta = rep["metadata"]
    fp = rep["factory_footprint_14_days"]
    print("\n" + "="*60)
    print("SME-EnergyIQ: CARBON & SUSTAINABILITY ASSESSMENT")
    print("="*60)
    print(f"Emission factor used : {meta['emission_factor_used_kg_per_kwh']} kg CO2e/kWh")
    print(f"Source               : {meta['emission_factor_source']}")
    print(f"Note                 : {meta['disclaimer']}")
    print("-"*60)
    print(f"14-Day Energy Total  : {fp['total_energy_consumed_kwh']:,} kWh")
    print(f"Total CO2 Emissions  : {fp['total_co2_emissions_kg']:,} kg ({fp['total_co2_emissions_tonnes']} Tonnes CO2e)")
    print(f"Yarn Carbon Intensity: {fp['carbon_intensity_kg_co2_per_kg_yarn']} kg CO2e / kg yarn")
    print(f"Equivalent Impact    : Equal to {rep['equivalencies']['tree_seedlings_grown_10_years']:,} mature trees absorption")
    print("="*60)

