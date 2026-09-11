# SME-EnergyIQ: Operational Assumptions & Limitations

---

## 1. Machinery Specifications & Baselines

| Asset ID | Machine Type | Rated Power (kW) | Nominal Load (kW) | Idle Power (kW) | Nominal Temp (°C) | Nominal Vib (mm/s RMS) | Nominal Speed (RPM) | Production Metric |
|---|---|---|---|---|---|---|---|---|
| **MOTOR_01** | Ring Spinning Motor | 55.0 | 45.0 | 12.0 | 62.0 | 1.8 | 1485 | kg yarn |
| **COMPRESSOR_01** | Screw Air Compressor | 45.0 | 38.0 | 16.0 | 75.0 | 2.2 | 2950 | $Nm^3$ air |
| **PUMP_01** | Dyeing Circulation Pump | 22.0 | 18.0 | 4.5 | 52.0 | 1.4 | 1450 | $m^3$ liquor |
| **HVAC_01** | Humidification Plant | 60.0 | 48.0 | 15.0 | 45.0 | 1.6 | 980 | $m^3$ conditioned air |

---

## 2. Indian Industrial Time-of-Day (ToD) Tariffs

Based on standard Indian State Electricity Distribution Company (DISCOM) High-Tension (HT-1) Industrial Tariff schedules (e.g., TANGEDCO, MSEDCL, BESCOM):

- **Normal Hours (06:00 to 18:00)**: ₹7.50 / kWh (Standard Base Energy Charge)
- **Evening Peak Hours (18:00 to 22:00)**: ₹10.00 / kWh (+33.3% Peak Surcharge)
- **Night Off-Peak Hours (22:00 to 06:00)**: ₹5.50 / kWh (-26.7% Incentive Rebate)

---

## 3. Grid Carbon Emission Factors & Environmental Equivalencies

> [!NOTE]
> **Simulation benchmark assumption**: 0.82 kg CO2e/kWh. This emission factor is used for synthetic benchmarking and demonstration. It is not an independently audited plant-specific electricity emission factor.

- **Emission Boundary (Scope 2 Only)**:
  - This prototype models **electricity-related Scope 2 emissions only**.
  - Does **not** model:
    - Scope 1 direct fuel combustion (boilers, diesel generators, furnace oil)
    - Refrigerant leakage or chemical process reaction emissions
    - Scope 3 supply chain, logistics, or upstream/downstream lifecycle emissions
- **Central Electricity Authority (CEA) Indicative Grid Benchmarks**:
  - National Grid Weighted Average Benchmark: **0.82 kg CO2e / kWh** (`DEFAULT_GRID_EMISSION_FACTOR`)
  - Regional State Grid Variations (for simulation scenario comparison):
    - Tamil Nadu (TANGEDCO): 0.79 kg CO2e / kWh
    - Maharashtra (MSEDCL): 0.85 kg CO2e / kWh
    - Gujarat (UGVCL): 0.81 kg CO2e / kWh
  - Green Open Access / Captive Solar Power Purchase Agreement (PPA): 0.35 kg CO2e / kWh (assumes 60% captive solar blend).
- **Environmental Equivalency Constants (Simulation Benchmarks)**:
  - `TREE_CO2_ABSORPTION_KG_PER_YEAR`: **21.77 kg CO2/year** (Standard urban tree annual carbon sequestration rate).
  - `CAR_CO2_KG_PER_KM`: **0.192 kg CO2/km** (Average passenger vehicle internal combustion tailpipe emission factor).
  - *Note: Equivalencies are visual reporting aids only and do not alter physical carbon accounting calculations.*

---

## 4. Engineering Assumptions & Limitations

1. **Synthetic Simulation**: Physical hardware (CT clamps, accelerometers, edge gateway) is simulated using deterministic mathematical physics with realistic sensor noise and thermal inertia.
2. **Shift Flexibility**: Ring spinning frames require continuous operation; therefore, spinning flexibility is constrained between 120 kg/h and 230 kg/h. Batch dyeing pumps and compressed air receivers possess high storage/process buffering capacity and can shift completely out of peak hours.
3. **Power Factor**: Assumed between 0.88 and 0.92 under optimal load, dropping to 0.65–0.72 during unloaded idle operation.
4. **Maintenance Schedules**: Sunday morning maintenance windows are modeled where machine availability is zero.

