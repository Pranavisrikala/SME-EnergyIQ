"""
SME-EnergyIQ: Industrial AI Anomaly Detection Engine
Target Industry: Indian Textile Manufacturing SME

Core AI Technique:
- Context-Aware Multi-variate Isolation Forest (scikit-learn)
- Planned maintenance context filtering (avoids false breakdown alarms during service)
- Continuous Anomaly Scoring [0 - 100] via tree path length decision function
- Defensible Industrial Severity Triaging (NORMAL, MEDIUM, HIGH, CRITICAL)
- Voltage sensor data-quality classification distinct from mechanical machine failure
- Ground Truth Model Evaluation (Precision, Recall, F1) decoupled from operational alerting
"""

import os
import datetime
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)

from utils import (
    ISO_10816_THRESHOLDS,
    MACHINE_SPECS,
    SENSOR_BOUNDS,
    is_maintenance_state,
    is_voltage_out_of_bounds,
    logger,
    save_json
)

# Core clean telemetry features used by V2 AI model
FEATURE_COLUMNS = [
    "Power_kW",
    "Temperature_C",
    "Vibration_mm_s",
    "RPM",
    "Load_Ratio",
    "Temp_Elevation",
    "Excess_Idle_Power",
    "Vib_Elevation",
    "RPM_Drop"
]

def train_and_detect_anomalies(data_path="data/processed/factory_data_clean.csv"):
    if not os.path.exists(data_path):
        logger.warning(f"Processed data not found at {data_path}. Checking raw data...")
        data_path = "data/factory_data.csv"
        
    logger.info(f"Loading factory dataset from {data_path}...")
    df = pd.read_csv(data_path)
    
    # Ensure all required V2 features exist
    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            if col == "Load_Ratio":
                df[col] = (df["Power_kW"] / 50.0).clip(0, 1.5)
            elif col == "Temp_Elevation":
                df["Nominal_Temp"] = df["Machine_ID"].map(lambda m: MACHINE_SPECS.get(m, {}).get("nominal_temp", 50.0))
                df[col] = (df["Temperature_C"] - df["Nominal_Temp"]).round(2)
            elif col == "Excess_Idle_Power":
                df["Idle_Nom"] = df["Machine_ID"].map(lambda m: MACHINE_SPECS.get(m, {}).get("idle_power", 10.0))
                df[col] = np.where(
                    df.get("Production_Units", 1.0) <= 0.05,
                    np.maximum(0.0, df["Power_kW"] - df["Idle_Nom"] * 1.15).round(3),
                    0.0
                )
            elif col == "Vib_Elevation":
                df["Vib_Nom"] = df["Machine_ID"].map(lambda m: MACHINE_SPECS.get(m, {}).get("nominal_vib", 1.8))
                df[col] = np.maximum(0.0, df["Vibration_mm_s"] - df["Vib_Nom"]).round(3)
            elif col == "RPM_Drop":
                df["RPM_Nom"] = df["Machine_ID"].map(lambda m: MACHINE_SPECS.get(m, {}).get("nominal_rpm", 1450.0))
                df[col] = np.where(
                    df["Power_kW"] > 5.0,
                    np.maximum(0.0, df["RPM_Nom"] - df["RPM"]).round(1),
                    0.0
                )

    # -------------------------------------------------------------
    # 1. CONTEXT-AWARE MACHINE-SPECIFIC MODEL TRAINING
    # Train separate Isolation Forest per machine on operational records
    # -------------------------------------------------------------
    maint_mask = df["Machine_Status"].apply(is_maintenance_state)
    train_mask = ~maint_mask
    
    os.makedirs("models", exist_ok=True)
    models = {}
    contamination_rate = 0.025
    
    df["Anomaly_Score"] = 0.0
    df["Predicted_Anomaly"] = 0
    
    unique_machines = list(df["Machine_ID"].unique())
    logger.info(f"Fitting V2 machine-specific Isolation Forests across {len(unique_machines)} assets...")
    
    for m_id in unique_machines:
        m_train_mask = train_mask & (df["Machine_ID"] == m_id)
        X_m_train = df.loc[m_train_mask, FEATURE_COLUMNS].fillna(0)
        
        logger.info(f"Training model for {m_id} on {len(X_m_train)} operational records...")
        m_model = IsolationForest(
            n_estimators=150,
            contamination=contamination_rate,
            random_state=42,
            n_jobs=1
        )
        m_model.fit(X_m_train)
        models[m_id] = m_model
        
        # Save individual asset model artifact
        asset_model_path = os.path.join("models", f"anomaly_model_{m_id}.pkl")
        joblib.dump(m_model, asset_model_path)
        
        # Inference for this machine across all records
        m_all_mask = df["Machine_ID"] == m_id
        X_m_all = df.loc[m_all_mask, FEATURE_COLUMNS].fillna(0)
        raw_scores = m_model.decision_function(X_m_all)
        raw_preds = m_model.predict(X_m_all) # 1 = normal, -1 = anomaly
        
        # Normalize anomaly score to [0, 100]
        min_s, max_s = raw_scores.min(), raw_scores.max()
        if max_s > min_s:
            scores_100 = ((max_s - raw_scores) / (max_s - min_s) * 100.0).round(2)
        else:
            scores_100 = np.zeros_like(raw_scores)
            
        df.loc[m_all_mask, "Anomaly_Score"] = scores_100
        df.loc[m_all_mask, "Predicted_Anomaly"] = (raw_preds == -1).astype(int)

    # Save primary/ensemble model dictionary for backwards compatibility
    joblib.dump(models, os.path.join("models", "anomaly_model.pkl"))

    # Planned maintenance context rule: Zero alerts, zero anomaly score during service
    df.loc[maint_mask, "Predicted_Anomaly"] = 0
    df.loc[maint_mask, "Anomaly_Score"] = 0.0
    
    # -------------------------------------------------------------
    # 2. HYBRID INDUSTRIAL SEVERITY ASSIGNMENT
    # Fuses statistical anomaly score with deterministic ISO 10816 & physics rules
    # -------------------------------------------------------------
    def assign_severity(row):
        # Rule 1: Planned maintenance is expected downtime, NEVER an equipment failure alert
        if is_maintenance_state(row.get("Machine_Status")):
            return "NORMAL"
            
        score = row.get("Anomaly_Score", 0.0)
        pred = row.get("Predicted_Anomaly", 0)
        vib = row.get("Vibration_mm_s", 0.0)
        status = row.get("Machine_Status", "RUNNING")
        v_val = row.get("Voltage_V", 415.0)
        is_volt_glitch = is_voltage_out_of_bounds(v_val)
        excess_idle = row.get("Excess_Idle_Power", 0.0)
        temp_elev = row.get("Temp_Elevation", 0.0)
        prod = row.get("Production_Units", 1.0)
        power = row.get("Power_kW", 0.0)
        
        # Scheduled meal break: idle power is within normal bounds (excess_idle < 4.0 kW)
        is_normal_meal_break = (status == "IDLE_UNLOADED") and (excess_idle < 4.0)

        # CRITICAL: Imminent damage or severe mechanical/electrical failure
        # - ISO 10816 Zone D vibration (> 7.1 mm/s: Unacceptable, stop machine)
        # - Extreme multi-variate anomaly score (>= 85.0) under active load
        if vib > ISO_10816_THRESHOLDS["ZONE_C_UNSATISFACTORY"]:
            return "CRITICAL"
        elif score >= 85.0 and pred == 1 and not is_normal_meal_break:
            return "CRITICAL"
            
        # HIGH: Significant abnormal condition / equipment degradation
        # - ISO 10816 Zone C vibration (4.5 to 7.1 mm/s: restricted operation)
        # - Genuine idle energy waste: compressor unloader failure (Excess_Idle >= 5.0 kW with zero production)
        # - Sustained severe thermal elevation (> 20°C above nominal under load)
        # - Strong multi-variate outlier (>= 75.0) confirmed by model (excluding scheduled meal breaks)
        elif vib > ISO_10816_THRESHOLDS["ZONE_B_SATISFACTORY"]:
            return "HIGH"
        elif excess_idle >= 5.0 and (prod <= 0.05):
            return "HIGH"
        elif (temp_elev >= 20.0) and (power > 25.0):
            return "HIGH"
        elif score >= 75.0 and pred == 1 and not is_normal_meal_break:
            return "HIGH"
            
        # SENSOR DATA QUALITY: Grid voltage sag/surge outside 340-480V
        elif is_volt_glitch:
            return "MEDIUM"
            
        # MEDIUM: Mild abnormal behavior / early warning
        elif (score >= 60.0 or pred == 1) and not is_normal_meal_break:
            return "MEDIUM"
            
        # NORMAL: Operating within normal baseline bounds
        else:
            return "NORMAL"
            
    df["Severity"] = df.apply(assign_severity, axis=1)

    # -------------------------------------------------------------
    # 3. MODEL EVALUATION (Decoupled from Operational Alert Feed)
    # Ground truth is used strictly for model metrics, NOT for alert generation!
    # -------------------------------------------------------------
    has_ground_truth = "Ground_Truth" in df.columns
    eval_metrics = {}
    
    if has_ground_truth:
        y_true = df.loc[train_mask, "Ground_Truth"]
        y_pred = df.loc[train_mask, "Predicted_Anomaly"]
        
        cm = confusion_matrix(y_true, y_pred)
        tn, fp, fn, tp = cm.ravel()
        
        acc = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        spec = tn / (tn + fp) if (tn + fp) > 0 else 0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0
        
        # Category-level breakdown
        category_breakdown = {}
        if "Anomaly_Type" in df.columns:
            for cat in df.loc[train_mask, "Anomaly_Type"].unique():
                if cat != "NORMAL":
                    cat_mask = train_mask & (df["Anomaly_Type"] == cat)
                    cat_total = int(cat_mask.sum())
                    cat_det = int((df.loc[cat_mask, "Predicted_Anomaly"] == 1).sum())
                    cat_rate = round(cat_det / cat_total * 100.0, 2) if cat_total > 0 else 0.0
                    category_breakdown[cat] = {
                        "total": cat_total,
                        "detected": cat_det,
                        "missed": cat_total - cat_det,
                        "detection_rate_pct": cat_rate
                    }
        
        eval_metrics = {
            "confusion_matrix": cm.tolist(),
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
            "accuracy": round(float(acc), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1), 4),
            "specificity": round(float(spec), 4),
            "false_positive_rate": round(float(fpr), 4),
            "false_negative_rate": round(float(fnr), 4),
            "total_ground_truth_anomalies": int(y_true.sum()),
            "total_predicted_anomalies": int(y_pred.sum()),
            "category_breakdown": category_breakdown
        }
        
        print("\n" + "="*60)
        print("SME-EnergyIQ V2 AI ANOMALY DETECTION EVALUATION (MACHINE-SPECIFIC)")
        print("="*60)
        print(f"Confusion Matrix (Operational Records, N = {len(y_true)}):")
        print(f"  TN: {tn:5d}  |  FP: {fp:5d}")
        print(f"  FN: {fn:5d}  |  TP: {tp:5d}")
        print(f"\nAccuracy               : {acc:.2%}")
        print(f"Precision              : {prec:.2%}")
        print(f"Recall (Sensitivity)   : {rec:.2%}")
        print(f"F1-Score               : {f1:.2%}")
        print(f"Specificity (TNR)      : {spec:.2%}")
        print(f"False Positive Rate    : {fpr:.2%}")
        print(f"False Negative Rate    : {fnr:.2%}")
        
        print("\nDetection by Anomaly Category:")
        for cat, stats in category_breakdown.items():
            print(f"  {cat:25s}: Total={stats['total']:2d}, Detected={stats['detected']:2d}, "
                  f"Missed={stats['missed']:2d}, Rate={stats['detection_rate_pct']:5.1f}%")
        print("="*60)

    # Save Model Metadata
    metadata = {
        "version": "V2_MACHINE_SPECIFIC",
        "model_type": "IsolationForest",
        "n_estimators": 150,
        "contamination": contamination_rate,
        "features": FEATURE_COLUMNS,
        "trained_at": datetime.datetime.now().isoformat(),
        "assets_trained": unique_machines,
        "evaluation_metrics": eval_metrics
    }
    save_json(metadata, os.path.join("models", "model_metadata.json"))
    
    # Save Anomaly Results
    res_path = os.path.join("results", "anomaly_results.csv")
    df.to_csv(res_path, index=False)
    logger.info(f"V2 Anomaly detection results saved to {res_path}")
    
    return df, models, eval_metrics

if __name__ == "__main__":
    df_results, models, metrics = train_and_detect_anomalies()
    print("\nV2 Severity Distribution:")
    print(df_results["Severity"].value_counts())
    print(f"Maintenance records retained: {(df_results['Machine_Status'] == 'MAINTENANCE').sum()}")