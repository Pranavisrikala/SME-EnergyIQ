import os
import pandas as pd
import matplotlib.pyplot as plt

# Ensure results directory exists
os.makedirs("results", exist_ok=True)

# Load factory data
data = pd.read_csv("data/factory_data.csv")

# Convert Timestamp into datetime format
data["Timestamp"] = pd.to_datetime(data["Timestamp"])

# Plot multi-machine power consumption
plt.figure(figsize=(14, 6))

colors = {
    "MOTOR_01": "#1f77b4",
    "COMPRESSOR_01": "#ff7f0e",
    "PUMP_01": "#2ca02c",
    "HVAC_01": "#d62728"
}

for m_id, group in data.groupby("Machine_ID"):
    # Plot 3-day sample or full horizon with alpha
    plt.plot(
        group["Timestamp"],
        group["Power_kW"],
        label=f"{m_id} ({group['Machine_Type'].iloc[0]})",
        color=colors.get(m_id, None),
        alpha=0.85,
        linewidth=1.2
    )

plt.title("SME Textile Factory - Machine-Level Power Profiles (14-Day Operation)", fontsize=14, fontweight="bold")
plt.xlabel("Timestamp", fontsize=11)
plt.ylabel("Power Demand (kW)", fontsize=11)
plt.grid(True, linestyle="--", alpha=0.5)
plt.legend(loc="upper right", framealpha=0.9)
plt.xticks(rotation=30)
plt.tight_layout()

output_path = "results/power_consumption.png"
plt.savefig(output_path, dpi=150)
plt.close()
print(f"Graph saved successfully to {output_path}!")
