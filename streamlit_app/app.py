
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# --- Pricing Constants ---
pricing = {
    "standard": {"storage": 0.020, "retrieval": 0.0},
    "nearline": {"storage": 0.010, "retrieval": 0.01},
    "coldline": {"storage": 0.004, "retrieval": 0.02},
    "archive": {"storage": 0.0012, "retrieval": 0.05},
    "operations": {
        "class_a": 0.05 / 10000,
        "class_b": 0.004 / 10000
    },
    "autoclass_fee_per_object": 0.0025
}

# --- UI ---
st.title("GCS Autoclass Simulator with Object Tracking and Management Fees")

st.sidebar.header("Write Pattern")
monthly_write = st.sidebar.number_input("Monthly New Data Written (GB)", min_value=1, value=200)
months = 12

st.sidebar.header("Object Characteristics")
avg_object_size_kib = st.sidebar.number_input("Average Object Size (KiB)", min_value=1, value=256)
percent_large_objects = st.sidebar.slider("% of Data >128 KiB (Autoclass Eligible)", 0, 100, 80) / 100

st.sidebar.header("Monthly Access Rates")
nearline_read_rate = st.sidebar.slider("Nearline (% accessed/month)", 0, 100, 20) / 100
coldline_read_rate = st.sidebar.slider("Coldline (% accessed/month)", 0, 100, 30) / 100
archive_read_rate = st.sidebar.slider("Archive (% accessed/month)", 0, 100, 10) / 100

st.sidebar.header("API Operations (per month)")
reads = st.sidebar.number_input("Class B (Reads)", min_value=0, value=10000)
writes = st.sidebar.number_input("Class A (Writes)", min_value=0, value=1000)

# --- Helper Function ---
def simulate_autoclass_with_objects(monthly_write, avg_object_size_kib, percent_large_objects, months,
                                    nearline_read_rate, coldline_read_rate, archive_read_rate,
                                    reads, writes):
    generations = []
    results = []

    for month in range(1, months + 1):
        total_objects = (monthly_write * 1024 * 1024) / avg_object_size_kib
        eligible_objects = total_objects * percent_large_objects
        eligible_data = monthly_write * percent_large_objects
        non_eligible_data = monthly_write * (1 - percent_large_objects)

        generations.append({"size": eligible_data, "age": 0})
        autoclass_fee = eligible_objects * pricing["autoclass_fee_per_object"]

        storage_classes = {"standard": non_eligible_data, "nearline": 0, "coldline": 0, "archive": 0}
        retrieval_cost = 0

        for gen in generations:
            gen["age"] += 1
            accessed = False

            if gen["age"] >= 12:
                storage_class = "archive"
                if archive_read_rate > 0:
                    accessed_volume = gen["size"] * archive_read_rate
                    retrieval_cost += accessed_volume * pricing[storage_class]["retrieval"]
                    gen["age"] = 0
                    storage_classes["standard"] += accessed_volume
                    gen["size"] -= accessed_volume
                    accessed = True
            elif gen["age"] >= 3:
                storage_class = "coldline"
                if coldline_read_rate > 0:
                    accessed_volume = gen["size"] * coldline_read_rate
                    retrieval_cost += accessed_volume * pricing[storage_class]["retrieval"]
                    gen["age"] = 0
                    storage_classes["standard"] += accessed_volume
                    gen["size"] -= accessed_volume
                    accessed = True
            elif gen["age"] >= 1:
                storage_class = "nearline"
                if nearline_read_rate > 0:
                    accessed_volume = gen["size"] * nearline_read_rate
                    retrieval_cost += accessed_volume * pricing[storage_class]["retrieval"]
                    gen["age"] = 0
                    storage_classes["standard"] += accessed_volume
                    gen["size"] -= accessed_volume
                    accessed = True
            else:
                storage_class = "standard"

            if not accessed or storage_class == "standard":
                storage_classes[storage_class] += gen["size"]

        storage_cost = sum(storage_classes[c] * pricing[c]["storage"] for c in storage_classes)
        api_cost = (reads * pricing["operations"]["class_b"]) + (writes * pricing["operations"]["class_a"])
        total = storage_cost + retrieval_cost + api_cost + autoclass_fee

        results.append({
            "Month": f"Month {month}",
            "Standard (GB)": round(storage_classes["standard"], 2),
            "Nearline (GB)": round(storage_classes["nearline"], 2),
            "Coldline (GB)": round(storage_classes["coldline"], 2),
            "Archive (GB)": round(storage_classes["archive"], 2),
            "Autoclass Fee ($)": round(autoclass_fee, 2),
            "Storage Cost ($)": round(storage_cost, 2),
            "Retrieval Cost ($)": round(retrieval_cost, 2),
            "API Cost ($)": round(api_cost, 2),
            "Total Cost ($)": round(total, 2)
        })

    return pd.DataFrame(results)

# --- Run Simulation ---
df = simulate_autoclass_with_objects(
    monthly_write=monthly_write,
    avg_object_size_kib=avg_object_size_kib,
    percent_large_objects=percent_large_objects,
    months=months,
    nearline_read_rate=nearline_read_rate,
    coldline_read_rate=coldline_read_rate,
    archive_read_rate=archive_read_rate,
    reads=reads,
    writes=writes
)

# --- Display Table ---
st.subheader("📊 Monthly Breakdown")
st.dataframe(df)

# --- Summary & Cost ---
total_cost = df["Total Cost ($)"].sum()
st.markdown(f"### 💰 Total 12-Month Cost: **${total_cost:.2f}**")

# --- Static Chart: Tier Growth ---
st.subheader("🪄 Tier-wise Data Growth Over Time")
fig, ax = plt.subplots()
ax.plot(df["Month"], df["Standard (GB)"], label="Standard")
ax.plot(df["Month"], df["Nearline (GB)"], label="Nearline")
ax.plot(df["Month"], df["Coldline (GB)"], label="Coldline")
ax.plot(df["Month"], df["Archive (GB)"], label="Archive")
ax.set_ylabel("GB Stored")
ax.set_title("Data Distribution Across Storage Classes")
ax.legend()
st.pyplot(fig)

# --- Export to CSV ---
st.subheader("📦 Export CSV")
csv_buffer = BytesIO()
df.to_csv(csv_buffer, index=False)
st.download_button(
    label="Download CSV",
    data=csv_buffer.getvalue(),
    file_name="autoclass_simulation_enhanced.csv",
    mime="text/csv"
)
