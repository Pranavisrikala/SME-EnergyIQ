# SME-EnergyIQ: Engineering Methodology Document

---

## 1. AI Anomaly Detection Methodology

### 1.1 Unsupervised Isolation Forest
In industrial textile plants, machine failures are rare events. Supervised classification suffers from extreme class imbalance (less than 1% failure data) and cannot detect novel failure modes. Therefore, SME-EnergyIQ utilizes an **Isolation Forest** (Liu et al., 2008), an unsupervised tree-based ensemble.

- **Mechanism**: Random partitioning recursively splits feature space. Anomalies are isolated closer to the root of trees (shorter average path lengths $h(x)$).
- **Features Used**:
  $$\vec{x} = \left[ P, T, \text{Vib}, \text{RPM}, \text{Units}, \text{Load\_Ratio}, \text{SEC\_Proxy}, \Delta T_{\text{rolling}}, \frac{\text{Vib}}{P} \right]$$
- **Continuous Anomaly Scoring**: Rather than a crude binary flag, the raw `decision_function(x)` is min-max scaled into a continuous $0 - 100$ Anomaly Score:
  $$\text{Score} = \left( \frac{s_{\max} - s(x)}{s_{\max} - s_{\min}} \right) \times 100$$
- **Severity Triaging**:
  - `CRITICAL`: Anomaly Score $\ge 85$ OR $\text{Vibration} > 7.1\text{ mm/s}$ (ISO Zone D).
  - `HIGH`: Anomaly Score $\ge 75$ OR $\text{Vibration} > 4.5\text{ mm/s}$ (ISO Zone C).
  - `MEDIUM`: Anomaly Score $\ge 60$.
  - `NORMAL`: Anomaly Score $< 60$.

---

## 2. Machine Health & Condition Monitoring (ISO 10816-3)

Rather than making unrealistic claims such as *"Machine will fail in exactly 8 days"*, the system implements industrial condition monitoring grounded in **ISO 10816-3 (Mechanical Vibration - Evaluation of machine vibration on non-rotating parts)** for Class II/III industrial machinery (15 kW – 75 kW):

| ISO 10816 Zone | Vibration Velocity (RMS) | Condition Assessment | Health Penalty |
|---|---|---|---|
| **Zone A (Good)** | $\le 2.3\text{ mm/s}$ | Newly commissioned, optimal running | 0 pts |
| **Zone B (Satisfactory)** | $2.3 - 4.5\text{ mm/s}$ | Long-term unrestricted operation | $4 \times (\text{Vib} - 2.3)$ pts |
| **Zone C (Unsatisfactory)** | $4.5 - 7.1\text{ mm/s}$ | Restricted operation; remedial action needed | $22 + 8 \times (\text{Vib} - 4.5)$ pts |
| **Zone D (Unacceptable)** | $> 7.1\text{ mm/s}$ | Imminent mechanical damage danger | $45 + 3 \times (\text{Vib} - 7.1)$ pts |

The composite **Health Score** ($0 - 100$) integrates:
$$\text{Health Score} = 100 - \text{Vibration Penalty} - \text{Thermal Headroom Penalty} - \text{Idle Waste Penalty} - \text{AI Anomaly Penalty}$$

---

## 3. Four-Tier Explainable Alert Framework

Industrial factory managers and electricians reject black-box notifications. SME-EnergyIQ structures all critical notifications into four transparent tiers:

1. **OBSERVED DATA**: Exact telemetry deviations from baseline with engineering units and percentage changes.
2. **MODEL INFERENCE**: Isolation forest anomaly score, assigned severity, and operational status.
3. **ENGINEERING HYPOTHESIS**: Physical mechanical/electrical failure mode (e.g., bearing race wear, unloader valve leak, pump impeller cavitation, filter blockage).
4. **RECOMMENDED ACTION**: Concrete, low-cost maintenance instructions for factory technicians.

---

## 4. Production & Energy Optimization (PuLP MILP)

### Mathematical Formulation
Let $m \in \mathcal{M}$ represent machines and $h \in \{0, \dots, 23\}$ represent hourly dispatch intervals.

$$\min \sum_{h=0}^{23} C_h \sum_{m \in \mathcal{M}} P_{m,h} + w_{\text{peak}} \cdot D_{\text{peak}}$$

**Subject to:**
1. **Throughput Conservation (100% Demand Satisfaction)**:
   $$\sum_{h=0}^{23} X_{m,h} = \text{Target}_m \quad \forall m \in \mathcal{M}$$
2. **Machine Capacity Bounds**:
   $$\text{MinRate}_m \cdot A_{m,h} \le X_{m,h} \le \text{MaxRate}_m \cdot A_{m,h}$$
3. **Power-Throughput Physics**:
   $$P_{m,h} = \text{IdlePower}_m + \alpha_m \cdot X_{m,h}$$
4. **Contract Demand Peak Tracking**:
   $$D_{\text{peak}} \ge \sum_{m \in \mathcal{M}} P_{m,h} \quad \forall h$$

Where $C_h$ is the Time-of-Day tariff, $A_{m,h} \in \{0, 1\}$ is availability (accounting for maintenance windows), and $w_{\text{peak}}$ is the peak demand penalty weight.

---

## 5. Specific Energy Consumption (SEC) & Carbon Accounting

- **Specific Energy Consumption**:
  $$\text{SEC} = \frac{\text{Total Energy Consumed (kWh)}}{\text{Total Production Throughput (kg yarn)}}$$
- **Carbon Accounting**:
  $$\text{CO}_2\text{e (kg)} = \text{Energy (kWh)} \times \text{Emission Factor (kg CO}_2\text{e/kWh)}$$
  Default emission factor is set to **0.82 kg CO2e/kWh** based on the Central Electricity Authority (CEA) Baseline Database for the Indian Power Sector (v19).

