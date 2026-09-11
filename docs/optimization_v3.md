# SME-EnergyIQ: V3 Health-Aware & Process-Coupled Production & Energy Optimization

**Engine Version**: V3 - Phase 4 (Process-Coupled Optimization)  
**Target Industry**: Indian Textile Manufacturing SME (Ring Spinning, Weaving & Dyeing)  
**Hackathon**: Schneider Electric Yuva Yodha Energy Tech Hackathon 2026  

---

## 1. Problem Definition & Scope

In industrial textile manufacturing SMEs, production scheduling cannot treat machinery as isolated islands. Supporting utilities—specifically climate control, humidification, and compressed air—must operate in lockstep with primary production processes:

1. **Uncoordinated Peak Tariffs**: High electrical draw during Time-of-Day (ToD) peak windows (18:00 – 22:00 at ₹10.00/kWh).
2. **Contract Demand Violations**: Simultaneous machine start-ups tripping grid demand thresholds.
3. **Unrealistic Independent Dispatch**: Scheduling ring spinning frames at full production without sufficient humidification and cooling, causing excessive yarn breakage ("ends down") and thermal motor failure.
4. **Health-Blind Dispatch**: Overworking degraded assets with elevated ISO vibration or thermal stress during off-peak periods.

The V3 Process-Coupled Optimizer answers:
> *"Given daily production requirements, machine condition, supporting utility coupling, and Time-of-Day electricity tariffs, what production schedule minimizes energy cost and peak demand while operating as a realistic, coordinated factory system?"*

---

## 2. Technical Formulation

### 2.1 Model Classification
- **Model Type**: Linear Program (LP) with continuous dispatch variables ($X_{m,h} \ge 0$, $\text{Power}_{m,h} \ge 0$, $\text{Peak\_Demand} \ge 0$).
- **Solver**: PuLP with COIN-OR CBC Solver (`PULP_CBC_CMD`).
- **Linear Coupling**: Process dependencies are formulated strictly as linear inequalities, preserving LP convexity and sub-second solve times without requiring binary variables. (Binary variables are strictly reserved for Phase 5 continuous batch scheduling).

### 2.2 Decision Variables
For machines $m \in \{\text{MOTOR\_01}, \text{COMPRESSOR\_01}, \text{PUMP\_01}, \text{HVAC\_01}\}$ and dispatch hours $h \in \{0, \dots, 23\}$:
- $X_{m,h}$: Hourly production output (kg yarn, $\text{Nm}^3$ air, $\text{m}^3$ liquor, $\text{m}^3$ air). Total: **96 variables**.
- $\text{Power}_{m,h}$: Hourly electrical active power draw (kW). Total: **96 variables**.
- $\text{Peak\_Demand}$: Maximum coincident factory electrical demand across the 24-hour horizon (kW). Total: **1 variable**.
- **Total Variables**: **193 continuous variables**.

### 2.3 Objective Function
$$\min Z = \sum_{m \in \mathcal{M}} \sum_{h=0}^{23} \left( \text{Tariff}_h \times \text{Power}_{m,h} \times 1\text{ h} \right) + w_{\text{peak}} \times \text{Peak\_Demand}$$
Where:
- $\text{Tariff}_h$: Indian DISCOM HT-1 ToD energy charge (₹/kWh: Peak=₹10.00, Normal=₹7.50, Off-Peak=₹5.50).
- $w_{\text{peak}}$: Peak demand penalty weighting ($25.0\text{ ₹/kW}$, centralized modeling parameter).

### 2.4 Constraints
1. **Strict Production Throughput Quotas**:
   $$\sum_{h=0}^{23} X_{m,h} = \text{Target}_m \quad \forall m \in \mathcal{M}$$
2. **Health-Aware Capacity Limits**:
   $$X_{m,h} \le \text{EffectiveMaxRate}_{m,h} \quad \forall m, h$$
   $$X_{m,h} \ge \text{EffectiveMinRate}_{m,h} \quad \forall m, h$$
3. **Linear Power-Throughput Physics Model**:
   $$\text{Power}_{m,h} = \begin{cases} 
   \text{IdlePower}_m + \left(\alpha_m \times X_{m,h}\right), & \text{if } \text{Availability}_{m,h} > 0 \\
   0.0, & \text{if } \text{Availability}_{m,h} = 0 \text{ (Maintenance / Outage)}
   \end{cases}$$
4. **Coincident Peak Demand Tracking**:
   $$\text{Peak\_Demand} \ge \sum_{m \in \mathcal{M}} \text{Power}_{m,h} \quad \forall h \in \{0, \dots, 23\}$$
5. **Process Coupling Constraint (HVAC $\rightarrow$ Spinning Frame)**:
   $$\frac{X_{\text{HVAC}, h}}{\text{max\_rate}_{\text{HVAC}}} \ge k_{\text{support}} \times \frac{X_{\text{MOTOR}, h}}{\text{max\_rate}_{\text{MOTOR}}}$$
   $$\implies X_{\text{HVAC}, h} \ge \gamma \cdot X_{\text{MOTOR}, h} \quad \forall h \in \{0, \dots, 23\}$$
   Where:
   $$\gamma = k_{\text{support}} \times \frac{\text{max\_rate}_{\text{HVAC}}}{\text{max\_rate}_{\text{MOTOR}}} = 0.90 \times \frac{5800}{230} \approx 22.6957 \text{ m}^3\text{ air / kg yarn}$$

---

## 3. Process Coupling & Industrial Justification

### 3.1 Ring Spinning and HVAC Climate Coupling (`HVAC_01` $\rightarrow$ `MOTOR_01`)
- **Physical Rationale**: Textile ring spinning frames generate intense frictional and motor heat while drawing raw roving into fine yarn. Cotton fibers require strict relative humidity ($55\% - 65\%\text{ RH}$) and temperature control ($28^\circ\text{C} - 32^\circ\text{C}$) to maintain fiber flexibility, control static electricity, and prevent yarn breakage ("ends down"). Running spinning frames without adequate conditioned airflow causes immediate quality degradation and machine tripping.
- **Formulation**: Normalized utilization coupling ensures that whenever the spinning frame runs at load fraction $\lambda$, the HVAC plant must run at least at load fraction $k \cdot \lambda$ ($k=0.90$).
- **Coupling Propagation**:
  - If HVAC is unavailable ($X_{\text{HVAC}, h} = 0$), then $X_{\text{MOTOR}, h} = 0$.
  - If HVAC capacity is derated to $C_{\text{HVAC}}$, spinning capacity cannot exceed $C_{\text{HVAC}} / \gamma$.

### 3.2 Compressor Decoupling Rationale (`COMPRESSOR_01`)
- **Textile Context**: `COMPRESSOR_01` supplies compressed air primarily to pneumatic valves, loom insertion nozzles (air-jet weaving), and dust cleaning. Ring spinning (`MOTOR_01`) does not require continuous high-volume compressed air.
- **Storage Decoupling**: Compressed air networks incorporate receiver tanks (air buffer storage). This allows `COMPRESSOR_01` to be scheduled flexibly (e.g., pre-charging tanks during off-peak hours) without rigid hour-by-hour synchronization to yarn spinning. Weaving machines are not modeled as separate decision variables in this 4-asset setup, so fabricating an artificial coupling to spinning would be physically inaccurate.

### 3.3 Pump / Dyeing Decoupling Rationale (`PUMP_01`)
- **Textile Context**: `PUMP_01` circulates hot dye liquor through pressurized yarn dyeing vessels. Ring spinning produces raw yarn bobbins, which are held in intermediate storage (buffer inventory) before being loaded into dyeing vats.
- **Storage Decoupling**: Because buffer inventory absorbs timing differences between spinning and dyeing, continuous batch scheduling is handled independently of instantaneous spinning output. (Phase 5 addresses multi-hour continuous dyeing batch constraints).

---

## 4. Health & Availability Integration Interface

### 4.1 Interface Architecture
The optimizer interfaces with the frozen V2 condition monitoring system through `load_v2_health_state()` in `src/utils.py`:
- **Inputs**: Reads `results/machine_health_snapshot.json` or date-filtered records from `results/factory_data_enriched.csv`.
- **Integrity**: Purely read-only; does **not** alter V2 health scores or models.
- **Outputs Provided to Optimizer**:
  - `health_score`: Condition rating ($0 - 100$) grounded in ISO 10816 vibration severity.
  - `severity`: Triaged condition rating (`NORMAL`, `MEDIUM`, `HIGH`, `CRITICAL`).
  - `status`: Machine state (`RUNNING_OPTIMAL`, `IDLE_UNLOADED`, `MAINTENANCE`, `RUNNING_DEGRADED`).
  - `operational_availability`: Categorical state (`AVAILABLE`, `MAINTENANCE`, `UNAVAILABLE`).
  - `hourly_availability`: 24-hour binary vector ($1.0$ for operating, $0.0$ for planned service or critical stoppage).

### 4.2 Health-Aware Scheduling Policy (Simulation Assumptions)

| Severity Level | Operational Risk | Scheduling Policy | Capacity Derating | Simulation Assumption Note |
|---|---|---|---|---|
| **NORMAL** | LOW | Unrestricted normal scheduling capability | $1.00$ ($100\%$) | Nominal physical operation |
| **MEDIUM** | MEDIUM | Normal scheduling permitted with monitoring | $1.00$ ($100\%$) | Early warning stage; peak avoidance recommended |
| **HIGH** | HIGH | Conservative load restriction applied | $0.85$ ($85\%$) | **Simulation assumption**: Derating to 85% reduces thermal and mechanical stress on degraded bearings/unloaders |
| **CRITICAL** | CRITICAL | Machine restricted from normal production | $0.00$ ($0\%$) | **Simulation assumption**: Machine de-scheduled pending remedial maintenance (ISO Zone D vibration) |

*Important Clarification*: These derating percentages represent defensible simulation policy assumptions for decision support, not certified original equipment manufacturer (OEM) laboratory measurements.

---

## 5. Critical Machine Handling & Infeasibility Detection

When an asset is in `CRITICAL` condition, under extended maintenance, or when supporting utility capacity is insufficient:
1. **No Silent Relaxation**: Production targets are **never** silently relaxed to mask capacity shortfalls.
2. **Feasibility Pre-Checks**:
   - Machine capacity check: $\sum_{h=0}^{23} \text{EffectiveMaxRate}_{m,h} \ge \text{Target}_m \quad \forall m$
   - Utility support check: $\sum_{h=0}^{23} \min\left(\text{EffectiveMaxRate}_{\text{MOTOR}, h}, \frac{\text{EffectiveMaxRate}_{\text{HVAC}, h}}{\gamma}\right) \ge \text{Target}_{\text{MOTOR}}$
3. **Engine Reporting**:
   When healthy capacity or utility support is insufficient, the engine marks the solver status as `Infeasible` and reports:
   > *"Optimization infeasible under current health, availability, and process-dependency constraints."*
4. **Engineering Fallback**:
   The output JSON and CSV records transparently declare `production_preservation_pct = 0.0` and detail the exact shortfall rather than inventing fictitious production.

---

## 6. Systematic Phase 4 Validation Suite

| Test Case | Scenario Description | Solver Status | Coupling Enforced | Key Observed Behavior |
|---|---|---|---|---|
| **Test A** | Nominal Health & Availability | `Optimal` | **Yes** ($\text{Min Margin} \ge 0$) | 100% throughput preserved; full ToD shifting active. |
| **Test B** | HVAC Capacity Restriction (HIGH Severity, 85% capacity) | `Optimal` | **Yes** | HVAC capped at $4,930\text{ m}^3/\text{h}$; spinning automatically restricted to $\le 217.22\text{ kg/h}$. |
| **Test C** | Compressor Restriction (HIGH Severity, 85% capacity) | `Optimal` | **Yes** (Decoupled) | Compressor derated to $\le 935.0\text{ m}^3/\text{h}$; spinning preserves $4,500\text{ kg}$ target independently. |
| **Test D** | Required Utility Unavailable (HVAC CRITICAL / 0 capacity) | `Infeasible` | **Enforced** | Solver correctly reports infeasibility with exact required diagnostic message. |
| **Test E** | Combined Maintenance + Dependency (HVAC Maintenance Hours 8–11) | `Optimal` | **Yes** | Spinning frame automatically de-scheduled ($0\text{ kg/h}$) during HVAC maintenance; catches up in remaining 20 h ($4,500\text{ kg}$ total preserved). |

---

## 7. Canonical Benchmark Results (Default Operational State)

| Metric | Baseline Schedule | Optimized Schedule | Impact |
|---|---|---|---|
| **Total Daily Energy** | 3,220.76 kWh | 3,220.76 kWh | Preserved (100% Throughput Conserved) |
| **Total Daily Electricity Cost** | ₹23,995.80 | ₹22,778.45 | **▼ ₹1,217.35 / day (5.07% Savings)** |
| **Peak Grid Demand** | 165.51 kW | 142.87 kW | **▼ 22.64 kW (13.68% Shaved)** |
| **Yarn Production Throughput** | 4,500.0 kg | 4,500.0 kg | **100.0% Exact Conservation** |
| **Specific Energy Consumption (SEC)** | 0.7157 kWh/kg | 0.7157 kWh/kg | Maintained High Efficiency |
| **Process Coupling Ratio ($\gamma$)** | 22.6957 $\text{m}^3/\text{kg}$ | 22.6957 $\text{m}^3/\text{kg}$ | **Satisfied across all 24 hours** |
| **Solver Status** | — | `Optimal` | Solved via PuLP CBC LP |
| **Health Restricted Hours** | 0 machine-hours | 0 machine-hours | All 4 assets currently NORMAL |
| **Maintenance Unavailable Hours** | 0 machine-hours | 0 machine-hours | Standard non-maintenance day |

---

## 8. Phase 5 — Dyeing Batch Scheduling & MILP Formulation

### 8.1 Industrial Process Background & Motivation
In textile yarn manufacturing, wet-processing (dyeing) liquor circulation pumps (`PUMP_01`) operate on discrete multi-hour exhaustion or package dyeing recipes. A typical exhaust dyeing cycle encompasses:
1. Scouring & Pre-treatment (bath heat-up and liquor wetting)
2. Dyestuff migration & exhaustion
3. Fixation under steady chemical/thermal equilibrium
4. Drain, neutralization, rinsing, and softening

In previous continuous Linear Programming (LP) formulations (Phases 1–4), `PUMP_01` was treated as an unconstrained continuous variable. Consequently, the solver could produce unphysical dispatch schedules—e.g. running 1 hour at partial load, shutting down for 1 hour, resuming at full load, and repeatedly cycling. In a real dye-house, such short cycling causes batch ruin, uneven dye uptake (shade variation/streaking), and excessive pump motor inrush wear.

### 8.2 Simulation Assumptions & Centralization
All batch parameters are centralized in `src/utils.py` under `DYEING_BATCH_SPECS` and represent **simulation assumptions** for algorithmic benchmarking (not certified OEM measurements):
- **Batch Duration ($D$)**: $3\text{ continuous hours}$ (`batch_duration_hours = 3`).
- **Minimum Operating Rate**: $80.0\text{ m}^3/\text{h}$ (`min_operating_rate_m3_h = 80.0`). Below this minimum flow rate, liquor velocity in the dyeing vessel drops below turbulent threshold, causing uneven dye migration.
- **Maximum Operating Rate**: $180.0\text{ m}^3/\text{h}$ (`max_hourly_rate_m3_h = 180.0`).
- **Active Batch Base Power**: $4.5\text{ kW}$ (`base_power_kw = 4.5`). Represents auxiliary pump agitation, circulation valves, and baseline power when a batch is active.
- **Marginal Power**: $0.105\text{ kW per m}^3/\text{h}$ (`marginal_kw_per_unit = 0.105`).
- **Inactive Power**: Strictly $0.0\text{ kW}$. When $\text{BatchActive} = 0$, the pump is fully de-energized with zero idle leakage.
- **Daily Production Target**: $2,500.0\text{ m}^3$ (`daily_target_m3 = 2500.0`).
- **Horizon Wrap**: Disabled (`allow_horizon_wrap = False`). Batches do not wrap across midnight.

### 8.3 Mixed-Integer Linear Programming (MILP) Formulation
To model discrete batch behavior, 48 binary decision variables are added alongside 193 continuous variables:
- $\text{BatchStart}_h \in \{0, 1\} \quad \forall h \in \{0, \dots, 23\}$
- $\text{BatchActive}_h \in \{0, 1\} \quad \forall h \in \{0, \dots, 23\}$

#### 1. Batch Continuity Constraint
An active batch at hour $h$ must have originated from a start variable in the interval $[h - D + 1, h]$:
$$\text{BatchActive}_h = \sum_{\tau=\max(0, h-D+1)}^h \text{BatchStart}_\tau \quad \forall h \in \{0, \dots, 23\}$$

#### 2. Non-Overlapping Batches
No machine can execute more than one batch simultaneously:
$$\text{BatchActive}_h \le 1 \quad \forall h \in \{0, \dots, 23\}$$
$$\sum_{\tau=h}^{\min(23, h+D-1)} \text{BatchStart}_\tau \le 1 \quad \forall h \in \{0, \dots, 23\}$$

#### 3. Horizon Boundary Gating (No Wrap-Around)
Batches cannot start if they would extend beyond the 24-hour horizon:
$$\text{BatchStart}_h = 0 \quad \forall h \in \{22, 23\}$$

#### 4. Maintenance & Health Availability Gating
A candidate batch cannot start if any hour during its 3-hour duration intersects scheduled maintenance or a health restriction:
$$\text{BatchStart}_h = 0 \quad \text{if } \exists \tau \in [h, h+D-1] \text{ s.t. } \text{Availability}_{\text{PUMP}, \tau} = 0 \text{ or } \text{EffectiveMaxRate}_{\text{PUMP}, \tau} = 0$$

#### 5. Semi-Continuous Production Rate Gating
When a batch is active, the pump operates between its minimum process flow rate ($80.0\text{ m}^3/\text{h}$) and health-derated maximum capacity. When inactive, production is strictly zero:
$$80.0 \cdot \text{BatchActive}_h \le X_{\text{PUMP}, h} \le \text{EffectiveMaxRate}_{\text{PUMP}, h} \cdot \text{BatchActive}_h \quad \forall h$$

#### 6. Discrete Semi-Continuous Power Model
$$\text{Power}_{\text{PUMP}, h} = 4.5 \cdot \text{BatchActive}_h + 0.105 \cdot X_{\text{PUMP}, h} \quad \forall h$$

---

## 9. Systematic Phase 5 Validation Suite (Tests A – H)

| Test ID | Scenario Description | Expected Outcome | Solver Status | Verified Result |
|---|---|---|---|---|
| **Test A** | Normal Weekday Operation | Discrete 3h batches, 100% throughput preserved | `Optimal` | **PASSED** (5 valid 3h batches, 0 late starts, 0 overlaps) |
| **Test B** | Peak Tariff Shifting (18:00–22:00) | Flexible batches shifted out of peak window | `Optimal` | **PASSED** (0.0 kWh PUMP_01 energy during peak tariff) |
| **Test C** | PUMP_01 HIGH Health Derating (85% max) | Batch count expands from 5 to 6 to preserve target | `Optimal` | **PASSED** (6 valid 3h batches at $\le 153.0\text{ m}^3/\text{h}$, target $2,500\text{ m}^3$ met) |
| **Test D** | PUMP_01 CRITICAL Health Restriction | Zero dispatch permitted, graceful infeasibility | `Infeasible` | **PASSED** (Halted with exact required diagnostic message) |
| **Test E** | Sunday Scheduled Maintenance (Hours 8–11) | Maintenance window strictly respected | `Optimal` | **PASSED** (Zero active batches in hours 8, 9, 10, 11) |
| **Test F** | Maintenance Overlap Prevention | Starts at hours 6 and 7 rejected (would hit h=8) | `Optimal` | **PASSED** (Starts 6–11 strictly forbidden) |
| **Test G** | End-of-Horizon Boundary Gating | Starts at hours 22 and 23 rejected | `Optimal` | **PASSED** (`BatchStart[22] == 0`, `BatchStart[23] == 0`) |
| **Test H** | Infeasible Capacity / Production Scenario | Transparent infeasibility report, no silent quota cut | `Infeasible` | **PASSED** (Reports infeasible with full diagnostic trace) |

---

## 10. Canonical Phase 5 Benchmark Results

| Metric | Baseline Schedule | Optimized Schedule | Impact |
|---|---|---|---|
| **Total Daily Energy** | 3,193.71 kWh | 3,180.31 kWh | ▼ 13.40 kWh (-0.42%) |
| **Total Daily Electricity Cost** | ₹23,575.50 | ₹22,447.71 | **▼ ₹1,127.79 / day (4.78% Savings)** |
| **Peak Grid Demand** | 154.89 kW | 142.38 kW | **▼ 12.51 kW (8.08% Shaved)** |
| **Yarn Production (MOTOR_01)** | 4,500.0 kg | 4,500.0 kg | **100.0% Exact Conservation** |
| **Dyeing Liquor (PUMP_01)** | 2,500.0 $\text{m}^3$ | 2,500.0 $\text{m}^3$ | **100.0% Target Conserved** |
| **Dyeing Batch Structure** | 6 batches (18 h active) | 5 batches (15 h active) | **Higher utilization, 0 short cycles** |
| **Specific Energy Consumption (SEC)** | 0.7097 kWh/kg | 0.7067 kWh/kg | **▼ 0.003 kWh/kg (0.42% More Efficient)** |
| **Carbon Avoided** | — | 10.99 kg $\text{CO}_2\text{e}$ | Decarbonization via Peak Load Shifting |
| **Model Structure** | — | Mixed-Integer Linear Program | Continuous: 193, Binary: 48, Constraints: 412 |
| **Solver Solve Time** | — | ~1.4 - 1.7 seconds | PuLP COIN-OR CBC |
| **Process Coupling ($\text{HVAC} \to \text{Spinning}$)** | — | Enforced ($\gamma = 22.6957\text{ m}^3/\text{kg}$) | Minimum Hourly Margin: $0.0\text{ m}^3$ |

---

## 11. Project State & Freezing Summary

1. **V2 Context-Aware Anomaly Detection**: **FROZEN** (Accuracy=98.49%, Hybrid Accuracy=99.89%, Recall=94.29%, F1=97.06%).
2. **Phase 1**: Optimization Audit & Discovery — **COMPLETED & FROZEN**.
3. **Phase 2**: Machine Parameter Centralization (`src/utils.py`) — **COMPLETED & FROZEN**.
4. **Phase 3**: Health & Availability Aware Optimization — **COMPLETED & FROZEN**.
5. **Phase 4**: Process Dependency Constraints (`HVAC_01` $\to$ `MOTOR_01`) — **COMPLETED & FROZEN**.
6. **Phase 5**: Dyeing Batch Scheduling & MILP Formulation (`PUMP_01`) — **COMPLETED & VERIFIED**.

