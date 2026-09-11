"""
SME-EnergyIQ: Phase 5 Comprehensive Audit Suite & Regression Tests
Validates Tests A through H, Programmatic Batch Continuity, Maintenance Gating,
Phase 3 & 4 Regression, and V2 Anomaly Detection Regression.
"""

import os
import sys
import copy
import pandas as pd
import numpy as np
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score

# Ensure src is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from utils import (
    DYEING_BATCH_SPECS,
    HEALTH_SCHEDULING_POLICY,
    MACHINE_SPECS,
    OPTIMIZATION_SPECS,
    PROCESS_DEPENDENCY_SPECS,
    load_v2_health_state,
    logger
)
from optimization import build_and_solve_optimizer


def get_mock_health_state(overrides=None):
    """Generates standard health state with optional machine-specific overrides."""
    base = load_v2_health_state()
    state = copy.deepcopy(base)
    if overrides:
        for m_id, vals in overrides.items():
            for k, v in vals.items():
                state[m_id][k] = v
    return state


def programmatic_batch_verifier(df_opt, health_state, batch_duration=3, min_rate=80.0):
    """
    Programmatically verifies EVERY scheduled batch on PUMP_01:
    - identify start hour
    - identify all active hours
    - verify exactly 3 consecutive active hours
    - verify no gaps
    - verify no overlap
    - verify availability
    - verify maintenance
    - verify health restriction
    - verify production bounds
    """
    p_df = df_opt[df_opt["Machine_ID"] == "PUMP_01"].sort_values("Hour").reset_index(drop=True)
    assigned_hours = []
    batches_found = []
    errors = []

    # Identify batches from Batch_Start flag
    start_hours = p_df[p_df["Batch_Start"] == 1]["Hour"].tolist()
    
    for s_h in start_hours:
        b_info = p_df[p_df["Hour"] == s_h].iloc[0]
        b_id = b_info["Batch_ID"]
        
        # Expected window
        expected_window = list(range(s_h, s_h + batch_duration))
        batches_found.append({"batch_id": b_id, "start_hour": s_h, "hours": expected_window})
        
        # 1. Verify horizon boundary gating
        if s_h > 24 - batch_duration:
            errors.append(f"{b_id}: Invalid late start hour {s_h} > {24 - batch_duration}")

        # 2. Check active hours in schedule
        for h in expected_window:
            if h >= 24:
                errors.append(f"{b_id}: Batch spills beyond 24h horizon at hour {h}")
                continue
            row = p_df[p_df["Hour"] == h].iloc[0]
            assigned_hours.append(h)

            # Active flag
            if row["Batch_Active"] != 1:
                errors.append(f"{b_id}: Hour {h} has Batch_Active != 1 (got {row['Batch_Active']})")

            # Availability & Maintenance
            if health_state["PUMP_01"]["hourly_availability"][h] == 0.0:
                errors.append(f"{b_id}: Hour {h} scheduled during maintenance or unavailability")
            if health_state["PUMP_01"]["hourly_status"][h] == "MAINTENANCE":
                errors.append(f"{b_id}: Hour {h} scheduled during MAINTENANCE status")

            # Health restriction & Production bounds
            eff_cap = row["Effective_Capacity"]
            prod = row["Production"]
            if prod < min_rate - 1e-2:
                errors.append(f"{b_id}: Hour {h} production {prod:.2f} < min {min_rate}")
            if prod > eff_cap + 1e-2:
                errors.append(f"{b_id}: Hour {h} production {prod:.2f} > effective max {eff_cap}")

    # 3. Check for consecutive hours without gaps
    for b in batches_found:
        hs = b["hours"]
        if len(hs) != batch_duration:
            errors.append(f"{b['batch_id']}: Window length {len(hs)} != {batch_duration}")
        if hs != list(range(hs[0], hs[0] + batch_duration)):
            errors.append(f"{b['batch_id']}: Gaps detected in batch hours {hs}")

    # 4. Check for overlaps
    if len(assigned_hours) != len(set(assigned_hours)):
        errors.append("Overlapping batch hours detected on PUMP_01")

    # 5. Check inactive hours
    inactive_hours = [h for h in range(24) if h not in assigned_hours]
    for ih in inactive_hours:
        row = p_df[p_df["Hour"] == ih].iloc[0]
        if row["Batch_Active"] != 0:
            errors.append(f"Hour {ih} inactive but Batch_Active == {row['Batch_Active']}")
        if abs(row["Production"]) > 1e-3:
            errors.append(f"Hour {ih} inactive but Production == {row['Production']}")
        if abs(row["Power_kW"]) > 1e-3:
            errors.append(f"Hour {ih} inactive but Power_kW == {row['Power_kW']}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "batch_count": len(batches_found),
        "batches": batches_found,
        "active_hours": sorted(assigned_hours),
        "inactive_hours": inactive_hours
    }


def run_test_a():
    """TEST A: Normal operation."""
    print("\n--- Running TEST A: Normal Operation ---")
    h_state = get_mock_health_state()
    comp, df_b, df_o = build_and_solve_optimizer(health_data=h_state)
    val = programmatic_batch_verifier(df_o, h_state)
    
    assert comp["health_aware_summary"]["solver_status"] == "Optimal", "Test A failed solver status"
    assert val["valid"], f"Test A validation errors: {val['errors']}"
    assert val["batch_count"] == 5, f"Test A expected 5 batches, got {val['batch_count']}"
    assert comp["health_aware_summary"]["production_preservation_pct"] == 100.0, "Test A throughput not 100%"
    print(f"TEST A PASSED: {val['batch_count']} batches, {len(val['active_hours'])}h active, valid={val['valid']}")
    return comp, val


def run_test_b():
    """TEST B: Peak tariff shifting (18:00 - 22:00)."""
    print("\n--- Running TEST B: Peak Tariff Shifting ---")
    h_state = get_mock_health_state()
    comp, df_b, df_o = build_and_solve_optimizer(health_data=h_state)
    p_df = df_o[df_o["Machine_ID"] == "PUMP_01"]
    peak_p = p_df[p_df["Hour"].isin([18, 19, 20, 21])]
    
    peak_power = peak_p["Power_kW"].sum()
    peak_prod = peak_p["Production"].sum()
    peak_active = peak_p["Batch_Active"].sum()
    
    assert comp["health_aware_summary"]["solver_status"] == "Optimal"
    assert peak_power == 0.0, f"Test B failed: PUMP_01 power during peak is {peak_power} kW"
    assert peak_prod == 0.0, f"Test B failed: PUMP_01 production during peak is {peak_prod} m3"
    assert peak_active == 0, f"Test B failed: PUMP_01 active during peak: {peak_active}"
    print(f"TEST B PASSED: Peak tariff hours (18-22) PUMP_01 Power={peak_power} kW, Active={peak_active}")
    return comp


def run_test_c():
    """TEST C: PUMP_01 HIGH health (85% derating)."""
    print("\n--- Running TEST C: PUMP_01 HIGH Health (85% derating) ---")
    h_state = get_mock_health_state({
        "PUMP_01": {
            "severity": "HIGH",
            "health_score": 55,
            "risk_level": "HIGH",
            "hourly_severity": ["HIGH"] * 24,
            "hourly_health_score": [55] * 24
        }
    })
    comp, df_b, df_o = build_and_solve_optimizer(health_data=h_state)
    val = programmatic_batch_verifier(df_o, h_state)
    
    p_df = df_o[df_o["Machine_ID"] == "PUMP_01"]
    active_rows = p_df[p_df["Batch_Active"] == 1]
    
    assert comp["health_aware_summary"]["solver_status"] == "Optimal"
    assert val["valid"], f"Test C validation errors: {val['errors']}"
    assert val["batch_count"] == 6, f"Test C expected 6 batches (18h) for derated pump, got {val['batch_count']}"
    assert all(active_rows["Production"] <= 153.0 + 1e-2), "Test C exceeded 85% capacity (153 m3/h)"
    assert abs(p_df["Production"].sum() - 2500.0) < 1.0, f"Test C target not met: {p_df['Production'].sum()}"
    print(f"TEST C PASSED: Batch count expanded to {val['batch_count']} batches, max active rate={active_rows['Production'].max():.2f} <= 153.0 m3/h, Target 2500m3 met")
    return comp, val


def run_test_d():
    """TEST D: PUMP_01 CRITICAL."""
    print("\n--- Running TEST D: PUMP_01 CRITICAL ---")
    h_state = get_mock_health_state({
        "PUMP_01": {
            "severity": "CRITICAL",
            "health_score": 25,
            "risk_level": "CRITICAL",
            "operational_availability": "UNAVAILABLE",
            "hourly_severity": ["CRITICAL"] * 24,
            "hourly_availability": [0.0] * 24,
            "hourly_health_score": [25] * 24
        }
    })
    comp, df_b, df_o = build_and_solve_optimizer(health_data=h_state)
    
    assert comp["health_aware_summary"]["solver_status"] == "Infeasible", f"Test D expected Infeasible, got {comp['health_aware_summary']['solver_status']}"
    assert not comp["health_aware_summary"]["is_feasible"], "Test D should not be feasible"
    assert len(comp["health_aware_summary"]["infeasibility_reasons"]) > 0, "Test D missing infeasibility reasons"
    p_df = df_o[df_o["Machine_ID"] == "PUMP_01"]
    assert p_df["Production"].sum() == 0.0, "Test D produced during CRITICAL"
    print(f"TEST D PASSED: Status=Infeasible, Reasons={comp['health_aware_summary']['infeasibility_reasons'][0]}")
    return comp


def run_test_e():
    """TEST E: PUMP_01 maintenance (hours 8..11)."""
    print("\n--- Running TEST E: PUMP_01 Maintenance (Hours 8-11) ---")
    avail = [1.0] * 24
    stats = ["RUNNING_OPTIMAL"] * 24
    for h in [8, 9, 10, 11]:
        avail[h] = 0.0
        stats[h] = "MAINTENANCE"
        
    h_state = get_mock_health_state({
        "PUMP_01": {
            "status": "MAINTENANCE",
            "operational_availability": "MAINTENANCE",
            "hourly_availability": avail,
            "hourly_status": stats
        }
    })
    comp, df_b, df_o = build_and_solve_optimizer(health_data=h_state)
    val = programmatic_batch_verifier(df_o, h_state)
    
    p_df = df_o[df_o["Machine_ID"] == "PUMP_01"]
    maint_rows = p_df[p_df["Hour"].isin([8, 9, 10, 11])]
    
    assert comp["health_aware_summary"]["solver_status"] == "Optimal"
    assert val["valid"], f"Test E validation errors: {val['errors']}"
    assert maint_rows["Batch_Active"].sum() == 0, "Test E active during maintenance"
    assert maint_rows["Power_kW"].sum() == 0.0, "Test E drew power during maintenance"
    assert maint_rows["Production"].sum() == 0.0, "Test E produced during maintenance"
    assert abs(p_df["Production"].sum() - 2500.0) < 1.0, f"Test E target not met: {p_df['Production'].sum()}"
    print(f"TEST E PASSED: Maintenance hours 8-11 strictly 0 kW / 0 m3, Total batches={val['batch_count']}, Target 2500m3 met")
    return comp, val


def run_test_f():
    """TEST F: Maintenance occurring inside candidate 3-hour batch."""
    print("\n--- Running TEST F: Maintenance Inside Candidate 3-Hour Batch ---")
    avail = [1.0] * 24
    stats = ["RUNNING_OPTIMAL"] * 24
    for h in [8, 9, 10, 11]:
        avail[h] = 0.0
        stats[h] = "MAINTENANCE"
        
    h_state = get_mock_health_state({
        "PUMP_01": {
            "status": "MAINTENANCE",
            "operational_availability": "MAINTENANCE",
            "hourly_availability": avail,
            "hourly_status": stats
        }
    })
    comp, df_b, df_o = build_and_solve_optimizer(health_data=h_state)
    val = programmatic_batch_verifier(df_o, h_state)
    
    p_df = df_o[df_o["Machine_ID"] == "PUMP_01"]
    
    # Hours 6 and 7 would overlap with hour 8 if started
    start_6 = p_df[p_df["Hour"] == 6]["Batch_Start"].iloc[0]
    start_7 = p_df[p_df["Hour"] == 7]["Batch_Start"].iloc[0]
    
    assert start_6 == 0, f"Test F failed: BatchStart[6] is {start_6} (would run 6, 7, 8; 8 is maintenance)"
    assert start_7 == 0, f"Test F failed: BatchStart[7] is {start_7} (would run 7, 8, 9; 8-9 are maintenance)"
    for mh in [8, 9, 10, 11]:
        s_val = p_df[p_df["Hour"] == mh]["Batch_Start"].iloc[0]
        assert s_val == 0, f"Test F failed: BatchStart[{mh}] is {s_val}"
        
    print(f"TEST F PASSED: BatchStart[6]={start_6}, BatchStart[7]={start_7}, BatchStart[8-11]=0 strictly enforced")
    return comp


def run_test_g():
    """TEST G: End-of-horizon batch starts."""
    print("\n--- Running TEST G: End-of-Horizon Batch Starts ---")
    h_state = get_mock_health_state()
    comp, df_b, df_o = build_and_solve_optimizer(health_data=h_state)
    p_df = df_o[df_o["Machine_ID"] == "PUMP_01"]
    
    start_22 = p_df[p_df["Hour"] == 22]["Batch_Start"].iloc[0]
    start_23 = p_df[p_df["Hour"] == 23]["Batch_Start"].iloc[0]
    
    assert start_22 == 0, f"Test G failed: BatchStart[22] is {start_22}"
    assert start_23 == 0, f"Test G failed: BatchStart[23] is {start_23}"
    print(f"TEST G PASSED: BatchStart[22]={start_22}, BatchStart[23]={start_23} (boundary gating active)")
    return comp


def run_test_h():
    """TEST H: Artificial infeasible capacity scenario."""
    print("\n--- Running TEST H: Artificial Infeasible Capacity Scenario ---")
    h_state = get_mock_health_state()
    # Request 2.0x target multiplier (PUMP_01 target = 5,000 m3; max 24h capacity = 4,320 m3)
    comp, df_b, df_o = build_and_solve_optimizer(target_multiplier=2.0, health_data=h_state)
    
    assert comp["health_aware_summary"]["solver_status"] == "Infeasible", f"Test H expected Infeasible, got {comp['health_aware_summary']['solver_status']}"
    assert not comp["health_aware_summary"]["is_feasible"]
    assert len(comp["health_aware_summary"]["infeasibility_reasons"]) > 0
    print(f"TEST H PASSED: Status=Infeasible, Reasons={comp['health_aware_summary']['infeasibility_reasons'][0]}")
    return comp


def run_v2_regression():
    """V2 Anomaly Detection Regression Verification."""
    print("\n--- Running V2 Regression Verification ---")
    res_path = "results/anomaly_results.csv"
    if not os.path.exists(res_path):
        raise FileNotFoundError(f"{res_path} not found")
        
    df = pd.read_csv(res_path)
    train_mask = df["Machine_Status"] != "MAINTENANCE"
    y_true = df.loc[train_mask, "Ground_Truth"]
    
    # 1. AI-only evaluation
    y_pred_ai = df.loc[train_mask, "Predicted_Anomaly"]
    cm_ai = confusion_matrix(y_true, y_pred_ai)
    tn_ai, fp_ai, fn_ai, tp_ai = cm_ai.ravel()
    acc_ai = accuracy_score(y_true, y_pred_ai)
    prec_ai = precision_score(y_true, y_pred_ai)
    rec_ai = recall_score(y_true, y_pred_ai)
    f1_ai = f1_score(y_true, y_pred_ai)
    
    print("AI-only Confusion Matrix:")
    print(f"  TP={tp_ai}, FP={fp_ai}, FN={fn_ai}, TN={tn_ai}")
    print(f"  Accuracy={acc_ai:.2%}, Precision={prec_ai:.2%}, Recall={rec_ai:.2%}, F1={f1_ai:.2%}")
    
    assert tp_ai == 79, f"AI-only TP expected 79, got {tp_ai}"
    assert fp_ai == 53, f"AI-only FP expected 53, got {fp_ai}"
    assert fn_ai == 26, f"AI-only FN expected 26, got {fn_ai}"
    assert tn_ai == 5090, f"AI-only TN expected 5090, got {tn_ai}"
    assert round(acc_ai, 4) == 0.9849, f"AI-only Acc expected 0.9849, got {acc_ai}"
    assert round(prec_ai, 4) == 0.5985, f"AI-only Prec expected 0.5985, got {prec_ai}"
    assert round(rec_ai, 4) == 0.7524, f"AI-only Rec expected 0.7524, got {rec_ai}"
    assert round(f1_ai, 4) == 0.6667, f"AI-only F1 expected 0.6667, got {f1_ai}"
    
    # 2. Hybrid evaluation (Severity in ['HIGH', 'CRITICAL'])
    y_pred_hybrid = df.loc[train_mask, "Severity"].isin(["HIGH", "CRITICAL"]).astype(int)
    cm_hy = confusion_matrix(y_true, y_pred_hybrid)
    tn_hy, fp_hy, fn_hy, tp_hy = cm_hy.ravel()
    acc_hy = accuracy_score(y_true, y_pred_hybrid)
    prec_hy = precision_score(y_true, y_pred_hybrid)
    rec_hy = recall_score(y_true, y_pred_hybrid)
    f1_hy = f1_score(y_true, y_pred_hybrid)
    
    print("\nHybrid Confusion Matrix:")
    print(f"  TP={tp_hy}, FP={fp_hy}, FN={fn_hy}, TN={tn_hy}")
    print(f"  Accuracy={acc_hy:.2%}, Precision={prec_hy:.2%}, Recall={rec_hy:.2%}, F1={f1_hy:.2%}")
    
    assert tp_hy == 99, f"Hybrid TP expected 99, got {tp_hy}"
    assert fp_hy == 0, f"Hybrid FP expected 0, got {fp_hy}"
    assert fn_hy == 6, f"Hybrid FN expected 6, got {fn_hy}"
    assert tn_hy == 5143, f"Hybrid TN expected 5143, got {tn_hy}"
    assert round(acc_hy, 4) == 0.9989, f"Hybrid Acc expected 0.9989, got {acc_hy}"
    assert round(prec_hy, 4) == 1.0000, f"Hybrid Prec expected 1.0000, got {prec_hy}"
    assert round(rec_hy, 4) == 0.9429, f"Hybrid Rec expected 0.9429, got {rec_hy}"
    assert round(f1_hy, 4) == 0.9706, f"Hybrid F1 expected 0.9706, got {f1_hy}"
    
    print("V2 REGRESSION PASSED: AI-only and Hybrid metrics exactly match specifications.")


def run_phase3_regression():
    """Phase 3 Health & Maintenance Regression Verification."""
    print("\n--- Running Phase 3 Regression Verification ---")
    # 1. HIGH Derating on COMPRESSOR_01
    h_state = get_mock_health_state({
        "COMPRESSOR_01": {
            "severity": "HIGH",
            "health_score": 58,
            "risk_level": "HIGH",
            "hourly_severity": ["HIGH"] * 24,
            "hourly_health_score": [58] * 24
        }
    })
    comp, df_b, df_o = build_and_solve_optimizer(health_data=h_state)
    c_df = df_o[df_o["Machine_ID"] == "COMPRESSOR_01"]
    max_c_cap = 1100.0 * 0.85
    assert comp["health_aware_summary"]["solver_status"] == "Optimal"
    assert c_df["Production"].max() <= max_c_cap + 1e-2, f"COMPRESSOR_01 exceeded 85% capacity {max_c_cap}"
    assert abs(c_df["Production"].sum() - 19200.0) < 1.0
    print(f"Phase 3 HIGH Derating Passed: COMPRESSOR_01 capped at {c_df['Production'].max():.2f} <= {max_c_cap:.2f} Nm3/h")

    # 2. CRITICAL on MOTOR_01
    h_state_crit = get_mock_health_state({
        "MOTOR_01": {
            "severity": "CRITICAL",
            "health_score": 20,
            "risk_level": "CRITICAL",
            "operational_availability": "UNAVAILABLE",
            "hourly_severity": ["CRITICAL"] * 24,
            "hourly_availability": [0.0] * 24,
            "hourly_health_score": [20] * 24
        }
    })
    comp_crit, _, _ = build_and_solve_optimizer(health_data=h_state_crit)
    assert comp_crit["health_aware_summary"]["solver_status"] == "Infeasible"
    print("Phase 3 CRITICAL Handling Passed: MOTOR_01 CRITICAL halts with Infeasible status")


def run_phase4_regression():
    """Phase 4 Process Coupling Regression Verification."""
    print("\n--- Running Phase 4 Regression Verification ---")
    # 1. Coupling enforcement under nominal conditions
    h_state = get_mock_health_state()
    comp, df_b, df_o = build_and_solve_optimizer(health_data=h_state)
    dep_sum = comp["process_dependency_summary"]["hvac_spinning_coupling"]
    gamma = dep_sum["coupling_ratio_gamma_m3_per_kg"]
    
    hvac_df = df_o[df_o["Machine_ID"] == "HVAC_01"].sort_values("Hour").reset_index(drop=True)
    motor_df = df_o[df_o["Machine_ID"] == "MOTOR_01"].sort_values("Hour").reset_index(drop=True)
    
    for h in range(24):
        hvac_p = hvac_df.loc[h, "Production"]
        motor_p = motor_df.loc[h, "Production"]
        req_hvac = gamma * motor_p
        assert hvac_p >= req_hvac - 0.05, f"Hour {h}: HVAC {hvac_p} < gamma * MOTOR {req_hvac}"
        
    assert dep_sum["dependency_satisfied_all_hours"] == True
    print(f"Phase 4 Coupling Ratio Passed: X[HVAC] >= {gamma:.4f} * X[MOTOR] satisfied across all 24 hours (Min margin: {dep_sum['min_hourly_margin_m3']} m3)")

    # 2. HVAC Unavailability disables dependent spinning
    avail_hvac = [1.0] * 24
    stats_hvac = ["RUNNING_OPTIMAL"] * 24
    for h in [8, 9, 10, 11]:
        avail_hvac[h] = 0.0
        stats_hvac[h] = "MAINTENANCE"
    h_state_maint = get_mock_health_state({
        "HVAC_01": {
            "status": "MAINTENANCE",
            "operational_availability": "MAINTENANCE",
            "hourly_availability": avail_hvac,
            "hourly_status": stats_hvac
        }
    })
    comp_m, _, df_o_m = build_and_solve_optimizer(health_data=h_state_maint)
    motor_m = df_o_m[df_o_m["Machine_ID"] == "MOTOR_01"]
    motor_down_prod = motor_m[motor_m["Hour"].isin([8, 9, 10, 11])]["Production"].sum()
    assert motor_down_prod == 0.0, f"Spinning operated during HVAC maintenance! Prod: {motor_down_prod}"
    print(f"Phase 4 Dependent Shutdown Passed: Spinning production during HVAC maintenance = {motor_down_prod} kg")


if __name__ == "__main__":
    print("=" * 70)
    print("STARTING PHASE 5 AUDIT VERIFICATION SUITE")
    print("=" * 70)
    
    run_test_a()
    run_test_b()
    run_test_c()
    run_test_d()
    run_test_e()
    run_test_f()
    run_test_g()
    run_test_h()
    
    run_v2_regression()
    run_phase3_regression()
    run_phase4_regression()
    
    print("\n" + "=" * 70)
    print("ALL TESTS (A - H) AND REGRESSIONS (V2, PHASE 3, PHASE 4) COMPLETED SUCCESSFULLY!")
    print("=" * 70)

