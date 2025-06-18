
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# --- Pricing Constants (Regional Autoclass) ---
pricing = {
    "standard": {"storage": 0.020, "min_storage_days": 0},
    "nearline": {"storage": 0.010, "min_storage_days": 30},
    "coldline": {"storage": 0.004, "min_storage_days": 90},
    "archive": {"storage": 0.0012, "min_storage_days": 365},
    "operations": {
        "class_a": 0.05 / 10000,  # Per operation
        "class_b": 0.004 / 10000  # Per operation
    },
    "autoclass_fee_per_1000_objects_per_month": 0.0025  # Per 1000 objects per month
}

# --- UI ---
st.title("GCS Autoclass Simulator with Object Tracking and Management Fees")

st.sidebar.header("Analysis Period")
months = st.sidebar.slider("Total Analysis Period (Months)", 12, 60, 12)

st.sidebar.header("Write Pattern")
monthly_write = st.sidebar.number_input("Monthly New Data Written (GB)", min_value=1, value=200)

st.sidebar.header("Object Characteristics")
percent_large_objects = st.sidebar.slider("% of Data >128 KiB (Autoclass Eligible)", 0, 100, 80) / 100

# Conditionally show object size inputs based on percentage
avg_object_size_large_kib = 512  # Default value
avg_object_size_small_kib = 64   # Default value

if percent_large_objects > 0:  # Show large object size input if there's any eligible data
    avg_object_size_large_kib = st.sidebar.number_input("Average Object Size for Data >128 KiB (KiB)", min_value=129, value=512)

if percent_large_objects < 1:  # Show small object size input if there's any non-eligible data
    avg_object_size_small_kib = st.sidebar.number_input("Average Object Size for Data ≤128 KiB (KiB)", min_value=1, max_value=128, value=64)

st.sidebar.header("Monthly Access Rates")
nearline_read_rate = st.sidebar.slider("Nearline (% accessed/month)", 0, 100, 20) / 100
coldline_read_rate = st.sidebar.slider("Coldline (% accessed/month)", 0, 100, 30) / 100
archive_read_rate = st.sidebar.slider("Archive (% accessed/month)", 0, 100, 10) / 100

st.sidebar.header("API Operations (per month)")
reads = st.sidebar.number_input("Class B (Reads)", min_value=0, value=10000)
writes = st.sidebar.number_input("Class A (Writes)", min_value=0, value=1000)

# --- Helper Function ---
def simulate_autoclass_with_objects(monthly_write, avg_object_size_large_kib, avg_object_size_small_kib, percent_large_objects, months,
                                    nearline_read_rate, coldline_read_rate, archive_read_rate,
                                    reads, writes):
    generations = []
    results = []
    cumulative_non_eligible_objects = 0  # Track cumulative non-eligible objects
    cumulative_non_eligible_data = 0     # Track cumulative non-eligible data

    for month in range(1, months + 1):
        # Calculate new objects and data for this month
        eligible_data = monthly_write * percent_large_objects
        non_eligible_data = monthly_write * (1 - percent_large_objects)
        
        # Calculate object counts separately for each category
        eligible_objects = (eligible_data * 1024 * 1024) / avg_object_size_large_kib  # Convert GB to KiB, then divide by object size
        non_eligible_objects = (non_eligible_data * 1024 * 1024) / avg_object_size_small_kib

        # Add to cumulative non-eligible totals
        cumulative_non_eligible_objects += non_eligible_objects
        cumulative_non_eligible_data += non_eligible_data

        # Add new generation for this month's data
        if eligible_data > 0:
            generations.append({
                "size": eligible_data, 
                "age_days": 0, 
                "objects": eligible_objects,
                "created_month": month
            })

        # Initialize storage classes with non-eligible data (always stays in Standard)
        storage_classes = {"standard": cumulative_non_eligible_data, "nearline": 0, "coldline": 0, "archive": 0}
        total_eligible_objects = 0
        total_non_eligible_objects = cumulative_non_eligible_objects  # Use cumulative count
        new_generations = []

        # Process each generation
        for gen in generations[:]:  # Use slice to avoid modification during iteration
            original_size = gen["size"]
            remaining_size = gen["size"]
            original_objects = gen["objects"]
            remaining_objects = gen["objects"]
            
            # Determine current storage class based on age in days
            if gen["age_days"] >= 365:
                storage_class = "archive"
                access_rate = archive_read_rate
            elif gen["age_days"] >= 90:
                storage_class = "coldline"
                access_rate = coldline_read_rate
            elif gen["age_days"] >= 30:
                storage_class = "nearline"
                access_rate = nearline_read_rate
            else:
                storage_class = "standard"
                access_rate = 0  # Standard tier - no access rate needed

            # Handle access and re-promotion (NO RETRIEVAL COSTS in Autoclass)
            if access_rate > 0 and storage_class != "standard":
                accessed_volume = original_size * access_rate
                accessed_objects = original_objects * access_rate
                
                # Re-promote accessed data to standard (create new generation)
                # NO retrieval cost in Autoclass - data moves freely back to Standard
                if accessed_volume > 0:
                    new_generations.append({
                        "size": accessed_volume,
                        "age_days": 0,
                        "objects": accessed_objects,
                        "created_month": month
                    })
                    # Add re-promoted data to Standard storage class
                    storage_classes["standard"] += accessed_volume
                    # Count re-promoted objects in total eligible objects
                    total_eligible_objects += accessed_objects
                
                # Update current generation (remove accessed portion)
                remaining_size -= accessed_volume
                remaining_objects -= accessed_objects
                gen["size"] = remaining_size
                gen["objects"] = remaining_objects

            # Add remaining data to appropriate storage class
            if remaining_size > 0:
                storage_classes[storage_class] += remaining_size
                total_eligible_objects += remaining_objects
            
            # Age the generation for next month (do this AFTER processing)
            gen["age_days"] += 30

        # Add new generations from re-promoted data
        generations.extend(new_generations)
        
        # Remove empty generations
        generations = [gen for gen in generations if gen["size"] > 0]

        # Calculate costs
        storage_cost = sum(storage_classes[c] * pricing[c]["storage"] for c in storage_classes)
        api_cost = (reads * pricing["operations"]["class_b"]) + (writes * pricing["operations"]["class_a"])
        autoclass_fee = (total_eligible_objects / 1000) * pricing["autoclass_fee_per_1000_objects_per_month"]
        total_cost = storage_cost + api_cost + autoclass_fee

        # Calculate total data across all classes
        total_data = sum(storage_classes.values())

        results.append({
            "Month": f"Month {month}",
            "Standard (GB)": round(storage_classes["standard"], 2),
            "Nearline (GB)": round(storage_classes["nearline"], 2),
            "Coldline (GB)": round(storage_classes["coldline"], 2),
            "Archive (GB)": round(storage_classes["archive"], 2),
            "Total Data (GB)": round(total_data, 2),
            "Total Eligible Objects": round(total_eligible_objects, 0),
            "Total Non-Eligible Objects": round(total_non_eligible_objects, 0),
            "Autoclass Fee ($)": round(autoclass_fee, 2),
            "Storage Cost ($)": round(storage_cost, 2),
            "API Cost ($)": round(api_cost, 2),
            "Total Cost ($)": round(total_cost, 2),
            "Active Generations": len(generations)
        })

    return pd.DataFrame(results)

# --- Run Simulation ---
df = simulate_autoclass_with_objects(
    monthly_write=monthly_write,
    avg_object_size_large_kib=avg_object_size_large_kib,
    avg_object_size_small_kib=avg_object_size_small_kib,
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
st.markdown(f"### 💰 Total {months}-Month Cost: **${total_cost:.2f}**")

# --- Cost Breakdown Summary ---
st.subheader("💸 Cost Breakdown Summary")
total_storage = df["Storage Cost ($)"].sum()
total_api = df["API Cost ($)"].sum()
total_autoclass_fee = df["Autoclass Fee ($)"].sum()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Storage Cost", f"${total_storage:.2f}")
    st.metric("API Cost", f"${total_api:.2f}")
with col2:
    st.metric("Autoclass Fee", f"${total_autoclass_fee:.2f}")
with col3:
    st.metric("**Total Cost**", f"**${total_cost:.2f}**")

# --- Static Chart: Tier Growth ---
st.subheader("🪄 Tier-wise Data Growth Over Time")
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

# Data distribution chart
ax1.plot(df["Month"], df["Standard (GB)"], label="Standard", linewidth=2)
ax1.plot(df["Month"], df["Nearline (GB)"], label="Nearline", linewidth=2)
ax1.plot(df["Month"], df["Coldline (GB)"], label="Coldline", linewidth=2)
ax1.plot(df["Month"], df["Archive (GB)"], label="Archive", linewidth=2)
ax1.plot(df["Month"], df["Total Data (GB)"], label="Total", linestyle="--", alpha=0.7)
ax1.set_ylabel("GB Stored")
ax1.set_title("Data Distribution Across Storage Classes")
ax1.legend()
ax1.grid(True, alpha=0.3)

# Cost breakdown chart
ax2.plot(df["Month"], df["Storage Cost ($)"], label="Storage", linewidth=2)
ax2.plot(df["Month"], df["Autoclass Fee ($)"], label="Autoclass Fee", linewidth=2)
ax2.plot(df["Month"], df["Total Cost ($)"], label="Total", linestyle="--", alpha=0.7)
ax2.set_ylabel("Cost ($)")
ax2.set_xlabel("Month")
ax2.set_title("Monthly Cost Breakdown")
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.xticks(rotation=45)
plt.tight_layout()
st.pyplot(fig)

# --- Key Insights ---
st.subheader("🔍 Key Insights")
col1, col2 = st.columns(2)

with col1:
    st.info(f"""
    **Data Lifecycle:**
    - Final month total data: {df['Total Data (GB)'].iloc[-1]:.1f} GB
    - Archive tier at end: {df['Archive (GB)'].iloc[-1]:.1f} GB ({df['Archive (GB)'].iloc[-1]/df['Total Data (GB)'].iloc[-1]*100:.1f}%)
    - Active generations: {df['Active Generations'].iloc[-1]}
    """)

with col2:
    avg_monthly_cost = total_cost / months
    storage_percentage = (total_storage / total_cost * 100) if total_cost > 0 else 0
    st.info(f"""
    **Cost Analysis:**
    - Average monthly cost: ${avg_monthly_cost:.2f}
    - Storage costs: {storage_percentage:.1f}% of total
    - Autoclass fee: ${total_autoclass_fee:.2f} ({total_autoclass_fee/total_cost*100:.1f}%)
    """)

# --- Comparison with Manual Lifecycle ---
st.subheader("⚖️ Autoclass vs Manual Lifecycle Comparison")
st.info("""
**Autoclass Benefits:**
- Automatic transitions based on access patterns (30, 90, 365 days)
- Instant re-promotion to Standard on access with NO retrieval costs
- No need to manage lifecycle policies manually
- Management fee: $0.0025 per 1000 objects per month for eligible objects

**Manual Lifecycle:**
- Fixed transition schedules regardless of access
- No automatic re-promotion
- Retrieval costs apply when accessing data in colder tiers
- No management fee
- Requires careful planning of access patterns
""")

# --- Data Validation ---
if total_autoclass_fee > total_storage:
    st.warning("⚠️ Autoclass management fees exceed storage costs. Consider if Autoclass is cost-effective for your use case.")

if df["Archive (GB)"].iloc[-1] < df["Total Data (GB)"].iloc[-1] * 0.1:
    st.info("💡 Most data is staying in higher tiers. Consider reviewing access patterns or object sizes.")

# --- Export to CSV ---
st.subheader("📦 Export CSV")
csv_buffer = BytesIO()
df.to_csv(csv_buffer, index=False)
st.download_button(
    label="Download CSV",
    data=csv_buffer.getvalue(),
    file_name="autoclass_simulation.csv",
    mime="text/csv"
)
