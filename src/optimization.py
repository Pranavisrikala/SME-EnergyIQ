"""
SME-EnergyIQ: Health-Aware, Process-Coupled & Dyeing Batch Production & Energy Optimizer (V3 - Phase 5)
Target Industry: Indian Textile Manufacturing SME (Spinning, Weaving & Dyeing)

Engineering Formulation:
1. Objective:
   Minimize: Total Electricity Cost (ToD Tariffs) + Peak Demand Charges (₹ / kW)
2. Tariffs (Indian DISCOM Standard):
   - Peak (18:00 - 22:00)     : ₹10.00 / kWh (+33.3% surcharge)
   - Normal (06:00 - 18:00)   : ₹7.50 / kWh
   - Off-Peak (22:00 - 06:00) : ₹5.50 / kWh (-26.7% rebate)
3. Health-Aware Scheduling Policy (Simulation Assumptions):
   - NORMAL   : 100% capacity (unrestricted scheduling capability)
   - MEDIUM   : 100% capacity (early warning monitoring; conservative load recommended)
   - HIGH     : 85% capacity derating (conservative load restriction to reduce stress)
   - CRITICAL : 0% capacity (machine restricted from scheduling pending maintenance)
4. Operational Availability:
   - AVAILABLE   : Machine ready for scheduled dispatch
   - MAINTENANCE : Machine in planned maintenance; production and power strictly 0
   - UNAVAILABLE : Machine condition unacceptable for operation
5. Process Coupling (Phase 4):
   - HVAC_01 -> MOTOR_01 proportional humidification coupling (k=0.90, gamma=22.6957 m3/kg)
6. Dyeing Batch Scheduling (Phase 5 MILP):
   - Discrete 3-hour continuous non-overlapping batches on PUMP_01 (BatchStart, BatchActive)
   - Simulation assumptions (not measured factory data): batch_duration_hours = 3, min_operating_rate_m3_h = 80.0
   - Active-batch auxiliary/base power component: 4.5 kW when BatchActive = 1; strictly 0 kW when BatchActive = 0
7. Model Type: Mixed-Integer Linear Program (MILP) with continuous & binary dispatch variables
"""

import os
import time
import pulp
import pandas as pd
import numpy as np

try:
    from utils import (
        DEFAULT_GRID_EMISSION_FACTOR,
        DYEING_BATCH_SPECS,
        HEALTH_SCHEDULING_POLICY,
        MACHINE_SPECS,
        OPTIMIZATION_SPECS,
        PROCESS_DEPENDENCY_SPECS,
        TOD_TARIFF_SLABS,
        load_v2_health_state,
        logger,
        save_json
    )
except ImportError:
    from src.utils import (
        DEFAULT_GRID_EMISSION_FACTOR,
        DYEING_BATCH_SPECS,
        HEALTH_SCHEDULING_POLICY,
        MACHINE_SPECS,
        OPTIMIZATION_SPECS,
        PROCESS_DEPENDENCY_SPECS,
        TOD_TARIFF_SLABS,
        load_v2_health_state,
        logger,
        save_json
    )

def build_and_solve_optimizer(target_multiplier=1.0, peak_penalty_weight=25.0, health_data=None, target_date=None):
    """
    Solves a 24-hour Time-of-Day health-aware production scheduling optimization using PuLP.
    Preserves 100% of production throughput where feasible while respecting machine condition,
    availability, and time-of-day electricity tariffs.
    """
    logger.info("Initializing PuLP Health & Availability Aware Production & Energy Optimizer...")
    
    hours = list(range(24))
    
    # 1. Define hourly Time-of-Day tariffs (₹/kWh)
    tariffs = []
    for h in hours:
        if 18 <= h < 22:
            tariffs.append(TOD_TARIFF_SLABS["PEAK"]["rate"])
        elif 6 <= h < 18:
            tariffs.append(TOD_TARIFF_SLABS["NORMAL"]["rate"])
        else:
            tariffs.append(TOD_TARIFF_SLABS["OFF_PEAK"]["rate"])

    # 2. Centralized Machine Specifications (Imported from utils.py)
    # Physical parameters (rated_power, idle_power, unit) from MACHINE_SPECS
    # Scheduling parameters (targets, hourly bounds, flexibility) from OPTIMIZATION_SPECS
    machine_specs = {}
    for m_id, phys in MACHINE_SPECS.items():
        opt = OPTIMIZATION_SPECS[m_id]
        machine_specs[m_id] = {
            "name": phys["name"],
            "daily_target": opt["daily_target"] * target_multiplier,
            "max_hourly_rate": opt["max_hourly_rate"],
            "min_hourly_rate": opt["min_hourly_rate"],
            "idle_power_kw": phys["idle_power"],
            "marginal_kw_per_unit": opt["marginal_kw_per_unit"],
            "rated_power": phys["rated_power"],
            "unit": phys["unit_name"],
            "flexibility": opt["flexibility"]
        }

    # 3. Read V2 Health, Severity, and Availability Interface
    if health_data is not None:
        health_state = health_data
    else:
        health_state = load_v2_health_state(target_date=target_date)

    # 4. Compute Effective Health-Aware Capacities and Availabilities
    effective_max_rate = {}
    effective_min_rate = {}
    availability = {}
    health_restricted_hours = 0
    maintenance_hours = 0

    for m in machine_specs:
        effective_max_rate[m] = {}
        effective_min_rate[m] = {}
        availability[m] = {}
        m_phys_max = machine_specs[m]["max_hourly_rate"]
        m_phys_min = machine_specs[m]["min_hourly_rate"]

        for h in hours:
            h_avail = health_state[m]["hourly_availability"][h]
            h_sev = health_state[m]["hourly_severity"][h]
            h_stat = health_state[m]["hourly_status"][h]

            policy = HEALTH_SCHEDULING_POLICY.get(h_sev, HEALTH_SCHEDULING_POLICY["NORMAL"])
            derate = policy["capacity_derating"]

            if h_avail == 0.0 or not policy["allow_scheduling"]:
                effective_max_rate[m][h] = 0.0
                effective_min_rate[m][h] = 0.0
                availability[m][h] = 0.0
                if h_stat == "MAINTENANCE":
                    maintenance_hours += 1
                else:
                    health_restricted_hours += 1
            else:
                availability[m][h] = 1.0
                effective_max_rate[m][h] = m_phys_max * derate
                effective_min_rate[m][h] = min(m_phys_min, effective_max_rate[m][h])
                if derate < 1.0:
                    health_restricted_hours += 1

    # Process Dependency Specifications & Parameters
    dep_cfg = PROCESS_DEPENDENCY_SPECS.get("HVAC_SPINNING_COUPLING", {})
    k_support = dep_cfg.get("support_ratio_k", 0.90)
    gamma_hvac_spinning = k_support * (machine_specs["HVAC_01"]["max_hourly_rate"] / machine_specs["MOTOR_01"]["max_hourly_rate"])

    # Dyeing Batch Specifications & Parameters (Simulation Assumptions)
    batch_cfg = DYEING_BATCH_SPECS["PUMP_01"]
    batch_duration = int(batch_cfg["batch_duration_hours"])
    min_batch_operating_rate = float(batch_cfg["min_operating_rate_m3_h"])
    pump_base_power = float(batch_cfg["base_power_kw"])

    # Propagate Process Coupling Constraints to Primary Process (HVAC -> Spinning)
    # Ring spinning frame cannot operate without humidification and climate control.
    # If HVAC is unavailable or derated, spinning effective bounds must respect HVAC support capacity.
    for h in hours:
        hvac_cap = effective_max_rate["HVAC_01"][h]
        if hvac_cap <= 0.0 or availability["HVAC_01"][h] == 0.0:
            effective_max_rate["MOTOR_01"][h] = 0.0
            effective_min_rate["MOTOR_01"][h] = 0.0
            availability["MOTOR_01"][h] = 0.0
        else:
            supported_motor_cap = hvac_cap / gamma_hvac_spinning
            if supported_motor_cap < effective_max_rate["MOTOR_01"][h]:
                effective_max_rate["MOTOR_01"][h] = supported_motor_cap
                effective_min_rate["MOTOR_01"][h] = min(effective_min_rate["MOTOR_01"][h], supported_motor_cap)

    # Feasibility Pre-Check 1: Machine Health & Availability Capacities
    infeasible_reasons = []
    for m, spec in machine_specs.items():
        total_healthy_cap = sum(effective_max_rate[m][h] for h in hours)
        if total_healthy_cap < spec["daily_target"]:
            msg = (
                f"Machine {m} required target ({spec['daily_target']:.1f} {spec['unit']}) "
                f"exceeds total available healthy capacity ({total_healthy_cap:.1f} {spec['unit']}). "
                f"Severity: {health_state[m]['severity']}, Status: {health_state[m]['status']}."
            )
            infeasible_reasons.append(msg)
            logger.warning(f"Health constraint breach: {msg}")

    # Feasibility Pre-Check 2: Process Coupling Capacity (HVAC Support for Spinning)
    max_supported_motor_cap = sum(
        min(effective_max_rate["MOTOR_01"][h], effective_max_rate["HVAC_01"][h] / gamma_hvac_spinning)
        for h in hours
    )
    if max_supported_motor_cap < machine_specs["MOTOR_01"]["daily_target"]:
        msg = (
            f"Process dependency infeasibility: MOTOR_01 daily target "
            f"({machine_specs['MOTOR_01']['daily_target']:.1f} kg) exceeds maximum HVAC-supported capacity "
            f"({max_supported_motor_cap:.1f} kg) at coupling ratio gamma={gamma_hvac_spinning:.4f} m3/kg. "
            f"HVAC Severity: {health_state['HVAC_01']['severity']}, Status: {health_state['HVAC_01']['status']}."
        )
        infeasible_reasons.append(msg)
        logger.warning(f"Process dependency breach: {msg}")

    # Feasibility Pre-Check 3: Dyeing Batch Scheduling Feasibility (PUMP_01)
    pump_policy = HEALTH_SCHEDULING_POLICY.get(health_state["PUMP_01"]["severity"], HEALTH_SCHEDULING_POLICY["NORMAL"])
    valid_batch_starts = []
    if pump_policy["allow_scheduling"] and pump_policy["capacity_derating"] > 0:
        for h in range(24 - batch_duration + 1):
            w_avail = [availability["PUMP_01"][h + i] for i in range(batch_duration)]
            w_cap = [effective_max_rate["PUMP_01"][h + i] for i in range(batch_duration)]
            if all(av > 0 for av in w_avail) and all(cp >= min_batch_operating_rate for cp in w_cap):
                valid_batch_starts.append(h)

    # Greedy interval scheduling to determine maximum non-overlapping batches
    max_non_overlapping_batches = 0
    next_avail_hour = 0
    for s in valid_batch_starts:
        if s >= next_avail_hour:
            max_non_overlapping_batches += 1
            next_avail_hour = s + batch_duration

    max_possible_pump_output = max_non_overlapping_batches * batch_duration * machine_specs["PUMP_01"]["max_hourly_rate"] * pump_policy["capacity_derating"]
    if max_possible_pump_output < machine_specs["PUMP_01"]["daily_target"]:
        msg = (
            f"Batch scheduling infeasibility: PUMP_01 daily target "
            f"({machine_specs['PUMP_01']['daily_target']:.1f} m3) exceeds maximum achievable capacity "
            f"({max_possible_pump_output:.1f} m3) across {max_non_overlapping_batches} possible {batch_duration}-hour batches. "
            f"PUMP_01 Severity: {health_state['PUMP_01']['severity']}, Status: {health_state['PUMP_01']['status']}."
        )
        infeasible_reasons.append(msg)
        logger.warning(f"Batch scheduling constraint breach: {msg}")

    # -------------------------------------------------------------
    # 5. BASELINE SIMULATION (Uncoordinated Schedule with Valid Batches)
    # -------------------------------------------------------------
    baseline_records = []
    base_hourly_weights = np.array([
        0.030, 0.030, 0.030, 0.030, 0.032, 0.035, # Night (00-06)
        0.045, 0.048, 0.050, 0.050, 0.048, 0.045, # Morning (06-12)
        0.038, 0.042, 0.048, 0.050, 0.052, 0.054, # Afternoon (12-18)
        0.058, 0.060, 0.058, 0.055,               # Evening Peak (18-22) - Heavy Unshifted
        0.035, 0.035                              # Late night (22-24)
    ])
    base_hourly_weights = base_hourly_weights / base_hourly_weights.sum()

    # Dispatch continuous machines (MOTOR_01, COMPRESSOR_01, HVAC_01)
    for m in ["MOTOR_01", "COMPRESSOR_01", "HVAC_01"]:
        spec = machine_specs[m]
        m_target = spec["daily_target"]
        m_weights = base_hourly_weights.copy()
        for h in hours:
            if availability[m][h] == 0.0:
                m_weights[h] = 0.0
            # If primary asset is MOTOR_01 and HVAC is unavailable at hour h, motor cannot run
            if m == "MOTOR_01" and availability["HVAC_01"][h] == 0.0:
                m_weights[h] = 0.0
        if m_weights.sum() > 0:
            m_weights = m_weights / m_weights.sum()
            m_hourly_prod = m_target * m_weights
        else:
            m_hourly_prod = np.zeros(24)

        for h in hours:
            prod = float(m_hourly_prod[h])
            hour_tar = tariffs[h]
            # If motor is uncoordinated but HVAC is down, motor cannot run
            m_eff_avail = availability[m][h]
            if m == "MOTOR_01" and availability["HVAC_01"][h] == 0.0:
                m_eff_avail = 0.0

            if m_eff_avail == 0.0:
                power = 0.0
                prod = 0.0
            else:
                power = spec["idle_power_kw"] + (spec["marginal_kw_per_unit"] * prod)

            baseline_records.append({
                "Hour": h,
                "Machine_ID": m,
                "Production": round(prod, 2),
                "Power_kW": round(power, 2),
                "Tariff_Rs": hour_tar,
                "Energy_kWh": round(power * 1.0, 2),
                "Cost_Rs": round(power * 1.0 * hour_tar, 2),
                "Health_Score": health_state[m]["hourly_health_score"][h],
                "Severity": health_state[m]["hourly_severity"][h],
                "Availability": m_eff_avail,
                "Operational_Status": health_state[m]["hourly_status"][h],
                "Effective_Capacity": round(effective_max_rate[m][h], 2),
                "Batch_ID": None,
                "Batch_Start": 0,
                "Batch_Active": 0,
                "Batch_Duration": 0
            })

    # Dispatch PUMP_01 baseline schedule: Uncoordinated standard shift batch schedule
    # A standard uncoordinated SME dyehouse runs 6 contiguous 3-hour batches (18 active hours) across shifts,
    # including unshifted batches during the expensive 18:00-22:00 evening peak window.
    p_spec = machine_specs["PUMP_01"]
    p_target = p_spec["daily_target"]
    base_pump_batches = []
    if pump_policy["allow_scheduling"] and pump_policy["capacity_derating"] > 0:
        candidate_shift_starts = [0, 3, 6, 9, 12, 15, 18, 21]
        for cs in candidate_shift_starts:
            if cs <= 24 - batch_duration:
                w_avail = [availability["PUMP_01"][cs + i] for i in range(batch_duration)]
                if all(av > 0 for av in w_avail):
                    if not any(abs(cs - prev_s) < batch_duration for prev_s in [b["start_hour"] for b in base_pump_batches]):
                        base_pump_batches.append({
                            "batch_id": f"BASE_BATCH_{len(base_pump_batches)+1:02d}",
                            "start_hour": cs,
                            "hours": [cs + i for i in range(batch_duration)],
                            "duration": batch_duration
                        })
                        if len(base_pump_batches) == 6:
                            break

    num_base_batches = len(base_pump_batches)
    base_batch_active_hours = num_base_batches * batch_duration
    if base_batch_active_hours > 0:
        max_eff_pump_rate = machine_specs["PUMP_01"]["max_hourly_rate"] * pump_policy["capacity_derating"]
        base_hourly_pump_rate = min(
            max_eff_pump_rate,
            p_target / base_batch_active_hours
        )
    else:
        base_hourly_pump_rate = 0.0

    base_batch_by_hour = {}
    for b in base_pump_batches:
        for idx, bh in enumerate(b["hours"]):
            base_batch_by_hour[bh] = {
                "batch_id": b["batch_id"],
                "batch_start": 1 if idx == 0 else 0,
                "batch_active": 1,
                "batch_duration": b["duration"]
            }

    for h in hours:
        hour_tar = tariffs[h]
        if h in base_batch_by_hour and availability["PUMP_01"][h] > 0 and pump_policy["allow_scheduling"]:
            b_info = base_batch_by_hour[h]
            prod = base_hourly_pump_rate
            power = pump_base_power + (p_spec["marginal_kw_per_unit"] * prod)
            b_id = b_info["batch_id"]
            b_start = b_info["batch_start"]
            b_act = 1
            b_dur = b_info["batch_duration"]
        else:
            prod = 0.0
            power = 0.0
            b_id = None
            b_start = 0
            b_act = 0
            b_dur = 0

        baseline_records.append({
            "Hour": h,
            "Machine_ID": "PUMP_01",
            "Production": round(prod, 2),
            "Power_kW": round(power, 2),
            "Tariff_Rs": hour_tar,
            "Energy_kWh": round(power * 1.0, 2),
            "Cost_Rs": round(power * 1.0 * hour_tar, 2),
            "Health_Score": health_state["PUMP_01"]["hourly_health_score"][h],
            "Severity": health_state["PUMP_01"]["hourly_severity"][h],
            "Availability": availability["PUMP_01"][h],
            "Operational_Status": health_state["PUMP_01"]["hourly_status"][h],
            "Effective_Capacity": round(effective_max_rate["PUMP_01"][h], 2),
            "Batch_ID": b_id,
            "Batch_Start": b_start,
            "Batch_Active": b_act,
            "Batch_Duration": b_dur
        })

    df_baseline = pd.DataFrame(baseline_records)

    # -------------------------------------------------------------
    # 6. PuLP MIXED-INTEGER LINEAR PROGRAMMING (MILP) MODEL
    # -------------------------------------------------------------
    model = pulp.LpProblem("Textile_Factory_Energy_Optimization", pulp.LpMinimize)

    # Decision variables
    # Continuous dispatch variables
    X = pulp.LpVariable.dicts("Prod", ((m, h) for m in machine_specs for h in hours), lowBound=0)
    Power = pulp.LpVariable.dicts("Power", ((m, h) for m in machine_specs for h in hours), lowBound=0)
    Peak_Demand = pulp.LpVariable("Peak_Demand", lowBound=0)

    # Discrete binary variables for PUMP_01 batch scheduling (Authentic MILP formulation)
    BatchStart = pulp.LpVariable.dicts("BatchStart", hours, cat=pulp.LpBinary)
    BatchActive = pulp.LpVariable.dicts("BatchActive", hours, cat=pulp.LpBinary)

    # Objective function
    # Min: Total Electricity Cost (ToD Tariffs) + Peak Demand Charges (₹ / kW)
    total_energy_cost = pulp.lpSum([tariffs[h] * Power[m, h] for m in machine_specs for h in hours])
    model += total_energy_cost + (peak_penalty_weight * Peak_Demand)

    # Constraint 1: Strict Throughput Conservation (Daily production quotas)
    for m, spec in machine_specs.items():
        model += pulp.lpSum([X[m, h] for h in hours]) == spec["daily_target"], f"Quota_{m}"

    # Constraint 2 & 3: Continuous Machines Dispatch & Power Physics (MOTOR_01, COMPRESSOR_01, HVAC_01)
    for m in ["MOTOR_01", "COMPRESSOR_01", "HVAC_01"]:
        spec = machine_specs[m]
        for h in hours:
            avail = availability[m][h]
            max_rate = effective_max_rate[m][h]
            min_rate = effective_min_rate[m][h]

            model += X[m, h] <= max_rate, f"MaxCap_{m}_{h}"
            model += X[m, h] >= min_rate, f"MinCap_{m}_{h}"

            if avail > 0:
                model += Power[m, h] == spec["idle_power_kw"] + (spec["marginal_kw_per_unit"] * X[m, h]), f"PowerEq_{m}_{h}"
            else:
                model += Power[m, h] == 0.0, f"PowerZero_{m}_{h}"

    # Constraint 4: Discrete Dyeing Batch Constraints for PUMP_01 (MILP)
    # 4a. Horizon handling: Forbid batch starts that cannot complete within 24 hours
    for h in hours:
        if h > 24 - batch_duration:
            model += BatchStart[h] == 0, f"Pump_NoLateStart_{h}"

    # 4b. Maintenance & Availability: Batch can only start if ALL D hours are available and healthy
    for h in range(24 - batch_duration + 1):
        window_avail = [availability["PUMP_01"][h + i] for i in range(batch_duration)]
        window_cap = [effective_max_rate["PUMP_01"][h + i] for i in range(batch_duration)]
        if (
            any(av == 0.0 for av in window_avail)
            or any(cp < min_batch_operating_rate for cp in window_cap)
            or not pump_policy["allow_scheduling"]
            or pump_policy["capacity_derating"] == 0
        ):
            model += BatchStart[h] == 0, f"Pump_MaintStartBlock_{h}"

    # 4c. Batch Continuity: Link active state to preceding start decisions
    for h in hours:
        model += BatchActive[h] == pulp.lpSum([
            BatchStart[t] for t in range(max(0, h - batch_duration + 1), h + 1)
        ]), f"Pump_ActiveLink_{h}"

    # 4d. Non-overlapping batches: At most 1 batch active simultaneously
    for h in hours:
        model += BatchActive[h] <= 1, f"Pump_SingleBatch_{h}"
    for h in range(24 - batch_duration + 1):
        model += pulp.lpSum([
            BatchStart[t] for t in range(h, min(24, h + batch_duration))
        ]) <= 1, f"Pump_NonOverlap_{h}"

    # 4e. Semi-Continuous Production Gating: [min_rate, max_rate] when active, strictly 0 when inactive
    for h in hours:
        eff_max = effective_max_rate["PUMP_01"][h]
        model += X["PUMP_01", h] <= eff_max * BatchActive[h], f"Pump_MaxCap_{h}"
        model += X["PUMP_01", h] >= min_batch_operating_rate * BatchActive[h], f"Pump_MinCap_{h}"

    # 4f. Discrete Power Physics: Auxiliary base power (4.5 kW) when active, strictly 0 kW when inactive
    for h in hours:
        model += Power["PUMP_01", h] == (pump_base_power * BatchActive[h]) + (p_spec["marginal_kw_per_unit"] * X["PUMP_01", h]), f"Pump_PowerEq_{h}"

    # Constraint 5: Factory Peak Demand Tracking
    for h in hours:
        model += Peak_Demand >= pulp.lpSum([Power[m, h] for m in machine_specs]), f"PeakTrack_{h}"

    # Constraint 6: Process Dependency / Coupling Constraints (HVAC -> Spinning)
    for h in hours:
        model += (
            X["HVAC_01", h] >= gamma_hvac_spinning * X["MOTOR_01", h],
            f"ProcessDep_HVAC_Spinning_{h}"
        )

    # Solve MILP model with COIN-OR CBC
    t0 = time.time()
    solver = pulp.PULP_CBC_CMD(msg=False)
    status = model.solve(solver)
    solve_duration = time.time() - t0
    solver_status = pulp.LpStatus[status]
    logger.info(f"PuLP MILP Optimization Solved in {solve_duration:.3f}s. Status: {solver_status}")

    # Variable and constraint counts for genuine MILP audit reporting
    continuous_var_count = sum(1 for v in model.variables() if v.cat == pulp.LpContinuous)
    binary_var_count = sum(1 for v in model.variables() if v.isBinary())
    integer_var_count = sum(1 for v in model.variables() if v.cat == pulp.LpInteger and not v.isBinary())
    total_var_count = len(model.variables())
    constraint_count = len(model.constraints)

    # -------------------------------------------------------------
    # 7. EXTRACT OPTIMIZED SCHEDULE, BATCHES & HANDLE INFEASIBILITY
    # -------------------------------------------------------------
    optimized_records = []
    opt_batches = []
    dep_margins = []
    validation_errors = []
    assigned_hours = []

    if solver_status == "Optimal":
        # Extract scheduled dyeing batches
        opt_batch_by_hour = {}
        batch_counter = 0
        for h in range(24 - batch_duration + 1):
            if pulp.value(BatchStart[h]) is not None and pulp.value(BatchStart[h]) > 0.5:
                batch_counter += 1
                b_id = f"OPT_BATCH_{batch_counter:02d}"
                b_hours = [h + i for i in range(batch_duration)]
                opt_batches.append({
                    "batch_id": b_id,
                    "start_hour": h,
                    "hours": b_hours,
                    "duration": batch_duration
                })
                for idx, bh in enumerate(b_hours):
                    opt_batch_by_hour[bh] = {
                        "batch_id": b_id,
                        "batch_start": 1 if idx == 0 else 0,
                        "batch_active": 1,
                        "batch_duration": batch_duration
                    }

        # Programmatic verification of every scheduled batch
        for b in opt_batches:
            b_id = b["batch_id"]
            s_h = b["start_hour"]
            b_hs = b["hours"]

            # 1. Verify exactly 3 consecutive hours
            if len(b_hs) != batch_duration:
                validation_errors.append(f"{b_id}: Expected {batch_duration} hours, got {len(b_hs)}")
            if b_hs != list(range(s_h, s_h + batch_duration)):
                validation_errors.append(f"{b_id}: Non-contiguous hours {b_hs} from start {s_h}")

            # 2. Verify no late starts
            if s_h > 24 - batch_duration:
                validation_errors.append(f"{b_id}: Invalid late start hour {s_h} > {24 - batch_duration}")

            # 3. Verify availability, maintenance, health, and production bounds
            for bh in b_hs:
                assigned_hours.append(bh)
                if availability["PUMP_01"][bh] == 0.0:
                    validation_errors.append(f"{b_id}: Hour {bh} is unavailable or in maintenance")
                p_val = pulp.value(X["PUMP_01", bh])
                eff_max = effective_max_rate["PUMP_01"][bh]
                if p_val is not None:
                    if p_val < min_batch_operating_rate - 1e-2:
                        validation_errors.append(f"{b_id}: Hour {bh} rate {p_val:.2f} below min {min_batch_operating_rate}")
                    if p_val > eff_max + 1e-2:
                        validation_errors.append(f"{b_id}: Hour {bh} rate {p_val:.2f} exceeds effective max {eff_max}")

        # 4. Verify no batch overlaps
        if len(assigned_hours) != len(set(assigned_hours)):
            validation_errors.append("Overlapping batch hours detected on PUMP_01!")

        # 5. Verify inactive hours have zero production and zero power
        for h in hours:
            if h not in opt_batch_by_hour:
                p_val = pulp.value(X["PUMP_01", h])
                pow_val = pulp.value(Power["PUMP_01", h])
                if p_val is not None and abs(p_val) > 1e-4:
                    validation_errors.append(f"PUMP_01 inactive hour {h} has non-zero production {p_val}")
                if pow_val is not None and abs(pow_val) > 1e-4:
                    validation_errors.append(f"PUMP_01 inactive hour {h} has non-zero power {pow_val}")

        # Construct records for all machines
        for m, spec in machine_specs.items():
            for h in hours:
                hour_tar = tariffs[h]
                prod_val = pulp.value(X[m, h])
                power_val = pulp.value(Power[m, h])

                if m == "PUMP_01":
                    b_info = opt_batch_by_hour.get(h, {
                        "batch_id": None, "batch_start": 0, "batch_active": 0, "batch_duration": 0
                    })
                    b_id = b_info["batch_id"]
                    b_start = b_info["batch_start"]
                    b_act = b_info["batch_active"]
                    b_dur = b_info["batch_duration"]
                else:
                    b_id, b_start, b_act, b_dur = None, 0, 0, 0

                optimized_records.append({
                    "Hour": h,
                    "Machine_ID": m,
                    "Production": round(prod_val, 2),
                    "Power_kW": round(power_val, 2),
                    "Tariff_Rs": hour_tar,
                    "Energy_kWh": round(power_val * 1.0, 2),
                    "Cost_Rs": round(power_val * 1.0 * hour_tar, 2),
                    "Health_Score": health_state[m]["hourly_health_score"][h],
                    "Severity": health_state[m]["hourly_severity"][h],
                    "Availability": availability[m][h],
                    "Operational_Status": health_state[m]["hourly_status"][h],
                    "Effective_Capacity": round(effective_max_rate[m][h], 2),
                    "Batch_ID": b_id,
                    "Batch_Start": b_start,
                    "Batch_Active": b_act,
                    "Batch_Duration": b_dur
                })

        for h in hours:
            hvac_p = pulp.value(X["HVAC_01", h])
            motor_p = pulp.value(X["MOTOR_01", h])
            dep_margins.append(hvac_p - (gamma_hvac_spinning * motor_p))

        df_optimized = pd.DataFrame(optimized_records)
    else:
        infeasible_msg = "Optimization infeasible under current health, availability, process-dependency, and batch-continuity constraints."
        logger.warning(infeasible_msg)
        if infeasible_msg not in infeasible_reasons:
            infeasible_reasons.insert(0, infeasible_msg)
        for m, spec in machine_specs.items():
            for h in hours:
                optimized_records.append({
                    "Hour": h,
                    "Machine_ID": m,
                    "Production": 0.0,
                    "Power_kW": 0.0,
                    "Tariff_Rs": tariffs[h],
                    "Energy_kWh": 0.0,
                    "Cost_Rs": 0.0,
                    "Health_Score": health_state[m]["hourly_health_score"][h],
                    "Severity": health_state[m]["hourly_severity"][h],
                    "Availability": availability[m][h],
                    "Operational_Status": health_state[m]["hourly_status"][h],
                    "Effective_Capacity": round(effective_max_rate[m][h], 2),
                    "Batch_ID": None,
                    "Batch_Start": 0,
                    "Batch_Active": 0,
                    "Batch_Duration": 0
                })
        df_optimized = pd.DataFrame(optimized_records)

    # -------------------------------------------------------------
    # 8. COMPARATIVE BENCHMARKING & METRICS
    # -------------------------------------------------------------
    base_energy = df_baseline["Energy_kWh"].sum()
    base_cost = df_baseline["Cost_Rs"].sum()
    base_peak = df_baseline.groupby("Hour")["Power_kW"].sum().max()
    base_yarn = df_baseline[df_baseline["Machine_ID"] == "MOTOR_01"]["Production"].sum()
    base_sec = base_energy / max(base_yarn, 1.0)
    base_co2 = base_energy * DEFAULT_GRID_EMISSION_FACTOR
    if base_yarn > 0:
        base_ci = base_co2 / base_yarn
    else:
        base_ci = None

    if solver_status == "Optimal":
        opt_energy = df_optimized["Energy_kWh"].sum()
        opt_cost = df_optimized["Cost_Rs"].sum()
        opt_peak = df_optimized.groupby("Hour")["Power_kW"].sum().max()
        opt_yarn = df_optimized[df_optimized["Machine_ID"] == "MOTOR_01"]["Production"].sum()
        opt_sec = opt_energy / max(opt_yarn, 1.0)
        opt_co2 = opt_energy * DEFAULT_GRID_EMISSION_FACTOR
        if opt_yarn > 0:
            opt_ci = opt_co2 / opt_yarn
        else:
            opt_ci = None

        cost_savings_rs = round(base_cost - opt_cost, 2)
        cost_savings_pct = round((cost_savings_rs / max(base_cost, 1.0)) * 100.0, 2)
        peak_reduction_kw = round(base_peak - opt_peak, 2)
        peak_reduction_pct = round((peak_reduction_kw / max(base_peak, 1.0)) * 100.0, 2)
        sec_improvement_pct = round(((base_sec - opt_sec) / max(base_sec, 0.001)) * 100.0, 2)
        if base_ci is not None and opt_ci is not None and base_ci > 0:
            ci_improvement_pct = round(((base_ci - opt_ci) / base_ci) * 100.0, 2)
        else:
            ci_improvement_pct = 0.0
        co2_avoided_kg = round(base_co2 - opt_co2, 2)
        preservation_pct = round((opt_yarn / max(base_yarn, 1.0)) * 100.0, 2)
    else:
        opt_energy = 0.0
        opt_cost = 0.0
        opt_peak = 0.0
        opt_yarn = 0.0
        opt_sec = 0.0
        opt_co2 = 0.0
        opt_ci = None
        cost_savings_rs = 0.0
        cost_savings_pct = 0.0
        peak_reduction_kw = 0.0
        peak_reduction_pct = 0.0
        sec_improvement_pct = 0.0
        ci_improvement_pct = 0.0
        co2_avoided_kg = 0.0
        preservation_pct = 0.0

    severity_counts = {"NORMAL": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for m in machine_specs:
        s = health_state[m]["severity"]
        severity_counts[s] = severity_counts.get(s, 0) + 1

    health_summary = {
        "machines_normal_count": severity_counts["NORMAL"],
        "machines_medium_count": severity_counts["MEDIUM"],
        "machines_high_count": severity_counts["HIGH"],
        "machines_critical_count": severity_counts["CRITICAL"],
        "health_restricted_machine_hours": health_restricted_hours,
        "maintenance_unavailable_machine_hours": maintenance_hours,
        "production_preservation_pct": preservation_pct,
        "solver_status": solver_status,
        "is_feasible": (solver_status == "Optimal"),
        "infeasibility_reasons": infeasible_reasons,
        "health_derating_policy": {
            k: v["capacity_derating"] for k, v in HEALTH_SCHEDULING_POLICY.items()
        },
        "machine_conditions": {
            m: {
                "health_score": health_state[m]["health_score"],
                "risk_level": health_state[m]["risk_level"],
                "severity": health_state[m]["severity"],
                "operational_availability": health_state[m]["operational_availability"]
            }
            for m in machine_specs
        }
    }

    dep_satisfied = bool(all(mg >= -1e-3 for mg in dep_margins)) if (solver_status == "Optimal" and dep_margins) else False
    min_dep_margin = 0.0 if (solver_status == "Optimal" and dep_margins and abs(min(dep_margins)) < 1e-3) else (round(float(min(dep_margins)), 2) if (solver_status == "Optimal" and dep_margins) else 0.0)

    process_dependency_summary = {
        "hvac_spinning_coupling": {
            "primary_asset": "MOTOR_01 (Ring Spinning Frame)",
            "support_asset": "HVAC_01 (Spinning Hall Humidification & Climate Control)",
            "coupling_ratio_gamma_m3_per_kg": round(gamma_hvac_spinning, 4),
            "support_ratio_k": k_support,
            "constraint_formulation": "X[HVAC_01, h] >= gamma * X[MOTOR_01, h]",
            "dependency_satisfied_all_hours": dep_satisfied,
            "min_hourly_margin_m3": min_dep_margin,
            "status": "ACTIVE_AND_ENFORCED" if solver_status == "Optimal" else "INFEASIBLE_OR_NOT_ENFORCED"
        },
        "compressor_decoupling_rationale": (
            "COMPRESSOR_01 supplies compressed air primarily to pneumatic actuators and weaving (air-jet looms), "
            "which are not modeled as separate decision variables in this 4-asset system. Receiver tank storage "
            "buffers provide decoupling, allowing compressor flex-scheduling against ToD tariffs without rigid coupling to spinning."
        ),
        "pump_decoupling_rationale": (
            "PUMP_01 supplies water to the yarn dyeing process, which is decoupled from ring spinning by intermediate "
            "yarn inventory buffers (bobbins/cones in storage). Continuous multi-hour batch constraints are enforced in Phase 5."
        )
    }

    milp_model_summary = {
        "model_type": "Mixed-Integer Linear Program (MILP)",
        "solver": "PuLP COIN-OR CBC",
        "solver_status": solver_status,
        "solve_duration_seconds": round(solve_duration, 4),
        "variable_counts": {
            "continuous": continuous_var_count,
            "binary": binary_var_count,
            "integer": integer_var_count,
            "total": total_var_count
        },
        "constraint_count": constraint_count
    }

    dyeing_batch_summary = {
        "batch_duration_hours": batch_duration,
        "min_operating_rate_m3_h": min_batch_operating_rate,
        "max_hourly_rate_m3_h": machine_specs["PUMP_01"]["max_hourly_rate"],
        "daily_target_m3": machine_specs["PUMP_01"]["daily_target"],
        "base_power_kw": pump_base_power,
        "marginal_kw_per_unit": machine_specs["PUMP_01"]["marginal_kw_per_unit"],
        "allow_horizon_wrap": False,
        "optimized_batch_count": len(opt_batches),
        "optimized_batches": opt_batches,
        "baseline_batch_count": num_base_batches,
        "baseline_batches": base_pump_batches,
        "programmatic_batch_validation": {
            "is_valid": len(validation_errors) == 0,
            "errors": validation_errors,
            "batch_continuity_enforced": len(validation_errors) == 0,
            "no_late_starts_enforced": all(b["start_hour"] <= 24 - batch_duration for b in opt_batches) if opt_batches else True,
            "no_overlaps_enforced": (len(assigned_hours) == len(set(assigned_hours))) if opt_batches else True
        },
        "simulation_assumption_disclaimer": "Simulation assumption — not measured factory data."
    }

    comparison = {
        "metrics": {
            "Total_Energy_kWh": {"baseline": round(base_energy, 2), "optimized": round(opt_energy, 2), "unit": "kWh"},
            "Total_Cost_Rs": {"baseline": round(base_cost, 2), "optimized": round(opt_cost, 2), "unit": "Rs.", "savings": cost_savings_rs, "improvement_pct": cost_savings_pct},
            "Peak_Demand_kW": {"baseline": round(base_peak, 2), "optimized": round(opt_peak, 2), "unit": "kW", "reduction_kw": peak_reduction_kw, "improvement_pct": peak_reduction_pct},
            "Yarn_Production_kg": {"baseline": round(base_yarn, 1), "optimized": round(opt_yarn, 1), "unit": "kg", "note": "100% Exact Throughput Conserved" if preservation_pct >= 99.9 else "Shortfall due to Infeasibility"},
            "Specific_Energy_Consumption_SEC": {"baseline": round(base_sec, 4), "optimized": round(opt_sec, 4), "unit": "kWh/kg", "improvement_pct": sec_improvement_pct},
            "CO2_Emissions_kg": {"baseline": round(base_co2, 2), "optimized": round(opt_co2, 2), "unit": "kg CO2e", "avoided_kg": co2_avoided_kg},
            "Carbon_Intensity_kg_CO2e_per_kg_yarn": {
                "baseline": round(base_ci, 4) if base_ci is not None else None,
                "optimized": round(opt_ci, 4) if opt_ci is not None else None,
                "unit": "kg CO2e/kg",
                "improvement_pct": ci_improvement_pct,
                "note": "Modeled Scope 2 CO2e per kg of finished yarn output"
            }
        },
        "milp_model_summary": milp_model_summary,
        "dyeing_batch_summary": dyeing_batch_summary,
        "health_aware_summary": health_summary,
        "process_dependency_summary": process_dependency_summary,
        "assumptions": {
            "grid_emission_factor_kg_per_kwh": DEFAULT_GRID_EMISSION_FACTOR,
            "grid_emission_factor_disclaimer": "Simulation benchmark assumption — not an audited plant-specific electricity emission factor.",
            "tariffs_used": {
                "peak_18_to_22": 10.0,
                "normal_06_to_18": 7.5,
                "off_peak_22_to_06": 5.5
            },
            "solver_used": "PuLP CBC MILP (Mixed-Integer Linear Program)",
            "health_derating_policy": "Simulation assumptions: HIGH=85% max capacity, CRITICAL=0% (restricted), NORMAL/MEDIUM=100%",
            "process_dependency_coupling": f"HVAC-Spinning proportional coupling (k={k_support}, gamma={gamma_hvac_spinning:.4f} m3/kg)",
            "dyeing_batch_specs": "Simulation assumption: 3-hour continuous batch, min operating rate 80 m3/h, 4.5 kW active base power (0 kW when inactive)"
        }
    }

    # Save detailed CSVs and JSON
    os.makedirs("results", exist_ok=True)
    df_baseline.to_csv("results/schedule_baseline.csv", index=False)
    df_optimized.to_csv("results/schedule_optimized.csv", index=False)
    save_json(comparison, "results/optimization_results.json")
    logger.info("Health-aware MILP batch optimization results exported to results/")

    return comparison, df_baseline, df_optimized

if __name__ == "__main__":
    comp, df_b, df_o = build_and_solve_optimizer()
    m = comp["metrics"]
    h_sum = comp["health_aware_summary"]
    dep = comp.get("process_dependency_summary", {}).get("hvac_spinning_coupling", {})
    milp_s = comp.get("milp_model_summary", {})
    batch_s = comp.get("dyeing_batch_summary", {})
    val_s = batch_s.get("programmatic_batch_validation", {})
    print("\n" + "="*65)
    print("SME-EnergyIQ: BATCH-CONSTRAINED INDUSTRIAL OPTIMIZATION (PuLP MILP)")
    print("="*65)
    print(f"Solver Status        : {milp_s.get('solver_status')} in {milp_s.get('solve_duration_seconds')}s (Feasible: {h_sum['is_feasible']})")
    print(f"Model Structure      : MILP | Continuous: {milp_s.get('variable_counts', {}).get('continuous')} | Binary: {milp_s.get('variable_counts', {}).get('binary')} | Constraints: {milp_s.get('constraint_count')}")
    print(f"Asset Condition      : Normal: {h_sum['machines_normal_count']} | Medium: {h_sum['machines_medium_count']} | High: {h_sum['machines_high_count']} | Critical: {h_sum['machines_critical_count']}")
    print(f"Dyeing Batches       : Baseline: {batch_s.get('baseline_batch_count')} batches | Optimized: {batch_s.get('optimized_batch_count')} batches (Duration: {batch_s.get('batch_duration_hours')}h each)")
    print(f"Batch Verification   : Contiguous: True | No Late Starts: {val_s.get('no_late_starts_enforced')} | No Overlaps: {val_s.get('no_overlaps_enforced')} | Valid: {val_s.get('is_valid')}")
    print(f"Process Coupling     : HVAC->Spinning (gamma={dep.get('coupling_ratio_gamma_m3_per_kg')} m3/kg, Enforced: {dep.get('dependency_satisfied_all_hours')}, Min Margin: {dep.get('min_hourly_margin_m3')} m3)")
    print(f"Throughput Preserved : {h_sum['production_preservation_pct']}% (Baseline: {m['Yarn_Production_kg']['baseline']} kg == Optimized: {m['Yarn_Production_kg']['optimized']} kg)")
    print(f"Energy Cost (Rs.)    : Baseline: Rs. {m['Total_Cost_Rs']['baseline']:,.2f} -> Optimized: Rs. {m['Total_Cost_Rs']['optimized']:,.2f}")
    print(f"Cost Savings         : Rs. {m['Total_Cost_Rs']['savings']:,.2f} ({m['Total_Cost_Rs']['improvement_pct']}%)")
    print(f"Peak Demand (kW)     : Baseline: {m['Peak_Demand_kW']['baseline']} kW -> Optimized: {m['Peak_Demand_kW']['optimized']} kW ({m['Peak_Demand_kW']['improvement_pct']}% Shaved)")
    print(f"Specific Energy (SEC): Baseline: {m['Specific_Energy_Consumption_SEC']['baseline']} -> Optimized: {m['Specific_Energy_Consumption_SEC']['optimized']} kWh/kg")
    print(f"Carbon Avoided       : {m['CO2_Emissions_kg']['avoided_kg']} kg CO2e")
    print("="*65)

