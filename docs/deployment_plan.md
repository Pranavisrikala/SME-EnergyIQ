# SME-EnergyIQ: SME Deployment & Business Model Document

---

## 1. The SME Context in Indian Manufacturing

Small and Medium Enterprises (SMEs) in India's textile belts (Surat, Tirupur, Coimbatore, Bhilwara, Ludhiana) operate on razor-thin net margins (3%–8%). Electricity represents **15% to 30% of total operating expenditure**, making energy optimization the single largest controllable cost lever.

However, existing enterprise Energy Management Systems (EMS) fail in Indian SMEs because:
1. They require exorbitant upfront capital investments (> ₹15–25 Lakhs).
2. They demand replacement of functional legacy machinery.
3. They produce complex analytics without clear, actionable engineering instructions.

---

## 2. Low-Cost Non-Invasive Retrofit Kit (< ₹18,000 / machine)

SME-EnergyIQ is engineered as a **plug-and-play retrofit** compatible with any 3-phase motor, compressor, or pump without plant downtime:

| Component | Function | Model / Spec | Est. Cost (INR) |
|---|---|---|---|
| **Digital Multi-function Meter** | RS-485 Modbus RTU Energy Meter | Schneider EasyLogic PM2120 | ₹5,500 |
| **Split-Core CT Clamps (Set of 3)** | Non-invasive current sensing without cutting power lines | 100A/5A Class 1.0 | ₹1,400 |
| **Vibration Transducer** | 4-20mA loop-powered accelerometer (0-25 mm/s RMS) | Industrial IEPE stud/magnetic mount | ₹3,800 |
| **Surface Temperature Probe** | PT100 RTD magnetic surface patch | 2-wire Class A | ₹1,200 |
| **Edge Gateway IPC** | Modbus-to-MQTT edge poller & buffer | Industrial ARM quad-core / Pi Gateway | ₹6,000 |
| **Total Hardware Investment** | Complete condition + energy monitoring per machine | | **₹17,900 / machine** |

---

## 3. Five-Phase Gradual Rollout Roadmap

```
Month 1: Phase 1 ──> Month 2: Phase 2 ──> Month 3: Phase 3 ──> Month 4-6: Phase 4 ──> Ongoing: Phase 5
 Sub-metering &        Baseline SEC &       Machine Health &        PuLP Production         ESG & Carbon
 Energy Monitoring     Anomaly Engine       ISO 10816 Diagnostics   Load Shifting           Accounting
```

1. **Phase 1: Sub-metering & Waste Elimination (Month 1)**
   - Retrofit smart meters on 4 primary motor control centers (MCC).
   - Track idle energy waste during lunch breaks and shift changeovers.
   - **Immediate ROI**: Eliminating 15-20 kW idle waste saves ~₹15,000/month.
2. **Phase 2: Anomaly Detection & Baselining (Month 2)**
   - Train Isolation Forest on plant baseline data.
   - Establish baseline Specific Energy Consumption (SEC) per yarn count.
3. **Phase 3: Machine Health & Vibration Triaging (Month 3)**
   - Mount vibration transducers and PT100 probes.
   - Activate the 4-Tier Explainable Alert Feed.
4. **Phase 4: PuLP Production Schedule Optimization (Month 4–6)**
   - Integrate daily production targets with Indian DISCOM ToD tariffs.
   - Automatically shift flexible air compressor charging and batch dyeing to night off-peak hours (₹5.50/kWh).
5. **Phase 5: ESG & Carbon Accounting (Ongoing)**
   - Automated Scope 2 indirect emissions tracking for supply chain sustainability audits.

---

## 4. Return on Investment (ROI) & Payback Period

- **Initial Outlay (4 Machines + Gateway)**: ₹75,000
- **Daily Electricity Cost**: ₹23,500
- **Daily Verified Savings from PuLP Load Shifting (5.27%)**: ₹1,241 / day
- **Monthly Savings (26 working days)**: ₹32,266 / month
- **Annual Savings**: **₹3,87,000 / year**
- **Payback Period**: **2.3 Months!**

