"""
SME-EnergyIQ: Master Orchestrator Pipeline
Executes end-to-end industrial intelligence loop:
MEASURE -> UNDERSTAND -> DETECT -> PREDICT -> OPTIMIZE -> VERIFY
"""

import sys
import os
import time

from utils import logger
import generate_data
import data_processing
import anomaly_detection
import machine_health
import energy_analysis
import optimization
import carbon_analysis

def run_full_pipeline(force_regenerate: bool = False):
    start_time = time.time()
    logger.info("=================================================================")
    logger.info("SME-EnergyIQ: INITIATING FULL INDUSTRIAL INTELLIGENCE PIPELINE")
    logger.info("Target: Indian Textile SME (Spinning & Weaving Mill)")
    logger.info("=================================================================")
    
    # 1. MEASURE: Ingest or Optionally Regenerate Sensor Data
    raw_path = os.path.join("data", "factory_data.csv")
    os.makedirs("data", exist_ok=True)
    if force_regenerate or not os.path.exists(raw_path):
        logger.info("Step 1/6: Generating synthetic multi-machine telemetry (force_regenerate=True or missing)...")
        df_raw = generate_data.generate_textile_factory_dataset(days=14, freq="15min")
        df_raw.to_csv(raw_path, index=False)
    else:
        logger.info("Step 1/6: Reusing existing factory telemetry from data/factory_data.csv (force_regenerate=False)...")
    
    # 2. UNDERSTAND: Data Quality Audit & Feature Engineering
    logger.info("Step 2/6: Auditing data quality and engineering ISO features...")
    data_processing.run_pipeline()
    
    # 3. DETECT: AI Anomaly Detection (Isolation Forest)
    logger.info("Step 3/6: Fitting AI Isolation Forest and triaging severities...")
    anomaly_detection.train_and_detect_anomalies()
    
    # 4. PREDICT & EXPLAIN: Machine Health & 4-Tier Explainable Alerts
    logger.info("Step 4/6: Computing ISO 10816 health scores and 4-tier explainable alerts...")
    machine_health.process_machine_health_and_alerts()
    
    # 5. MEASURE & BENCHMARK: Energy & SEC Analysis
    logger.info("Step 5/6: Calculating SEC, Time-of-Day tariffs, and idle energy waste...")
    energy_analysis.analyze_factory_energy()
    
    # 6. OPTIMIZE & SUSTAIN: PuLP MILP Production Scheduling & Carbon Accounting
    logger.info("Step 6/6: Solving PuLP MILP optimizer and computing CEA carbon footprint...")
    optimization.build_and_solve_optimizer()
    carbon_analysis.generate_sustainability_report()
    
    elapsed = time.time() - start_time
    logger.info("=================================================================")
    logger.info(f"SME-EnergyIQ: PIPELINE EXECUTED SUCCESSFULLY in {elapsed:.2f} seconds!")
    logger.info("All artifacts ready for Industrial Streamlit Dashboard.")
    logger.info("=================================================================")

if __name__ == "__main__":
    force_regen = "--force-regenerate" in sys.argv
    run_full_pipeline(force_regenerate=force_regen)

