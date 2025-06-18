import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime

# --- Utility Functions for Unit Formatting ---
def format_storage_value(gb_value):
    """Format storage value with appropriate units (GB or TiB)"""
    if gb_value >= 1024:  # 1 TiB = 1024 GB
        tib_value = gb_value / 1024
        if tib_value >= 1000:
            return f"{tib_value:,.1f} TiB"
        else:
            return f"{tib_value:.2f} TiB"
    else:
        return f"{gb_value:.2f} GB"

def format_cost_value(cost):
    """Format cost value with appropriate units ($ or $M)"""
    if cost >= 1000000:  # 1 million or more
        million_value = cost / 1000000
        return f"${million_value:.2f}M"
    else:
        return f"${cost:,.2f}"

def get_storage_unit_and_value(gb_value):
    """Get storage unit and converted value for display"""
    if gb_value >= 1024:  # Use TiB for large values
        return gb_value / 1024, "TiB"
    else:
        return gb_value, "GB"

def get_cost_unit_and_value(cost):
    """Get cost unit and converted value for display"""
    if cost >= 1000000:  # Use millions for large costs
        return cost / 1000000, "M"
    else:
        return cost, ""

# --- Default Pricing Constants (Iowa us-central1 Regional Autoclass) ---
default_pricing = {
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
st.title("GCS Autoclass Cost Simulator")

# --- Pricing Configuration Section ---
st.sidebar.header("💰 Pricing Configuration")
st.sidebar.markdown("*Default: Iowa (us-central1) Regional Autoclass*")

with st.sidebar.expander("Customize Pricing", expanded=False):
    st.markdown("**Storage Costs ($ per GB per month)**")
    standard_storage_price = st.number_input("Standard Storage", min_value=0.0, value=default_pricing["standard"]["storage"], step=0.001, format="%.4f")
    nearline_storage_price = st.number_input("Nearline Storage", min_value=0.0, value=default_pricing["nearline"]["storage"], step=0.001, format="%.4f")
    coldline_storage_price = st.number_input("Coldline Storage", min_value=0.0, value=default_pricing["coldline"]["storage"], step=0.001, format="%.4f")
    archive_storage_price = st.number_input("Archive Storage", min_value=0.0, value=default_pricing["archive"]["storage"], step=0.001, format="%.4f")
    
    st.markdown("**API Operations ($ per operation)**")
    class_a_price = st.number_input("Class A Operations (Writes)", min_value=0.0, value=default_pricing["operations"]["class_a"], step=0.000001, format="%.7f")
    class_b_price = st.number_input("Class B Operations (Reads)", min_value=0.0, value=default_pricing["operations"]["class_b"], step=0.000001, format="%.7f")
    
    st.markdown("**Autoclass Management Fee**")
    autoclass_fee_price = st.number_input("Per 1000 Objects per Month ($)", min_value=0.0, value=default_pricing["autoclass_fee_per_1000_objects_per_month"], step=0.0001, format="%.4f")

# Build current pricing configuration
pricing = {
    "standard": {"storage": standard_storage_price, "min_storage_days": 0},
    "nearline": {"storage": nearline_storage_price, "min_storage_days": 30},
    "coldline": {"storage": coldline_storage_price, "min_storage_days": 90},
    "archive": {"storage": archive_storage_price, "min_storage_days": 365},
    "operations": {
        "class_a": class_a_price,
        "class_b": class_b_price
    },
    "autoclass_fee_per_1000_objects_per_month": autoclass_fee_price
}

# Display current pricing summary
def format_small_number(value):
    """Format small numbers appropriately"""
    if value < 0.000001:  # Less than 1 millionth
        return f"{value:.2e}"  # Scientific notation
    elif value < 0.001:   # Less than 1 thousandth
        return f"{value:.7f}".rstrip('0').rstrip('.')  # Remove trailing zeros
    else:
        return f"{value:.4f}"

st.sidebar.markdown("**Current Pricing Summary:**")
st.sidebar.markdown(f"- Standard: ${pricing['standard']['storage']:.4f}/GB/month")
st.sidebar.markdown(f"- Nearline: ${pricing['nearline']['storage']:.4f}/GB/month")
st.sidebar.markdown(f"- Coldline: ${pricing['coldline']['storage']:.4f}/GB/month") 
st.sidebar.markdown(f"- Archive: ${pricing['archive']['storage']:.4f}/GB/month")
st.sidebar.markdown(f"- Class A Ops: ${format_small_number(pricing['operations']['class_a'])}/op")
st.sidebar.markdown(f"- Class B Ops: ${format_small_number(pricing['operations']['class_b'])}/op")
st.sidebar.markdown(f"- Autoclass Fee: ${pricing['autoclass_fee_per_1000_objects_per_month']:.4f}/1K objects/month")

st.sidebar.header("Analysis Period")
months = st.sidebar.slider("Total Analysis Period (Months)", 12, 60, 12)

st.sidebar.header("Data Growth Pattern")
initial_data_gb = st.sidebar.number_input("Initial Data Upload (GB)", min_value=0, value=10240, help="Amount of data uploaded in Month 1")
monthly_growth_rate = st.sidebar.number_input("Monthly Growth Rate (%)", min_value=0.0, max_value=50.0, value=0.0, step=0.1, help="Percentage increase in data each month (0% = no new data)") / 100

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
st.sidebar.markdown("*Access rates determine data lifecycle behavior*")

# Standard access rate - always shown
standard_access_rate = st.sidebar.slider("Standard (% staying hot/month)", 0, 100, 30, help="Percentage of Standard data that remains hot each month (rest becomes cold and transitions to Nearline after 30 days)") / 100

# Initialize access rates with defaults
nearline_read_rate = 0.20   # 20% default
coldline_read_rate = 0.30   # 30% default  
archive_read_rate = 0.10    # 10% default

# Conditional UI logic: Hide controls when data won't reach those tiers
if standard_access_rate == 1.0:
    # 100% Standard access means no data will transition to colder tiers
    st.sidebar.warning("🔒 **All data stays hot in Standard tier** - no cold tier transitions")
    # Set locked values
    nearline_read_rate = 0.20   # These won't be used but maintain consistency
    coldline_read_rate = 0.30
    archive_read_rate = 0.10
else:
    # Show Nearline control when data can transition from Standard
    nearline_read_rate = st.sidebar.slider("Nearline (% accessed/month)", 0, 100, 20, help="Percentage accessed monthly (moves back to Standard)") / 100
    
    if nearline_read_rate == 1.0:
        # 100% Nearline access means no data will reach Coldline/Archive
        st.sidebar.warning("🔒 **All Nearline data re-promoted** - no deeper cold storage")
        # Set locked values
        coldline_read_rate = 0.30
        archive_read_rate = 0.10
    else:
        # Show Coldline control when data can transition from Nearline
        coldline_read_rate = st.sidebar.slider("Coldline (% accessed/month)", 0, 100, 30, help="Percentage accessed monthly (moves back to Standard)") / 100
        
        if coldline_read_rate == 1.0:
            # 100% Coldline access means no data will reach Archive
            st.sidebar.warning("🔒 **All Coldline data re-promoted** - no Archive storage")
            # Set locked value
            archive_read_rate = 0.10
        else:
            # Show Archive control when data can transition from Coldline
            archive_read_rate = st.sidebar.slider("Archive (% accessed/month)", 0, 100, 10, help="Percentage accessed monthly (moves back to Standard)") / 100

# Add visual feedback about tier blocking
if standard_access_rate == 1.0:
    st.sidebar.success("💡 **Data Flow**: All data stays in Standard tier (highest cost, immediate access)")
    st.sidebar.caption("⚠️ Nearline, Coldline, and Archive tiers effectively disabled")
elif nearline_read_rate == 1.0:
    st.sidebar.success("💡 **Data Flow**: Standard ↔ Nearline (re-promotion cycle)")  
    st.sidebar.caption("⚠️ Coldline and Archive tiers effectively disabled")
elif coldline_read_rate == 1.0:
    st.sidebar.success("💡 **Data Flow**: Standard ↔ Nearline ↔ Coldline (re-promotion cycle)")
    st.sidebar.caption("⚠️ Archive tier effectively disabled")
else:
    st.sidebar.info("💡 **Data Flow**: Full tier progression enabled (Standard → Nearline → Coldline → Archive)")
    st.sidebar.caption("✅ All storage tiers available for cost optimization")

st.sidebar.header("API Operations (per month)")
reads = st.sidebar.number_input("Class B (Reads)", min_value=0, value=10000)
writes = st.sidebar.number_input("Class A (Writes)", min_value=0, value=1000)

# --- Helper Function ---
def simulate_autoclass_with_objects(initial_data_gb, monthly_growth_rate, avg_object_size_large_kib, avg_object_size_small_kib, percent_large_objects, months,
                                    standard_access_rate, nearline_read_rate, coldline_read_rate, archive_read_rate,
                                    reads, writes):
    generations = []
    results = []
    cumulative_non_eligible_objects = 0  # Track cumulative non-eligible objects
    cumulative_non_eligible_data = 0     # Track cumulative non-eligible data

    for month in range(1, months + 1):
        # Calculate new objects and data for this month based on growth pattern
        if month == 1:
            # Initial data upload in month 1
            monthly_data = initial_data_gb
        else:
            # Growth model: data grows by percentage each month
            if monthly_growth_rate > 0:
                # Calculate incremental growth based on previous month's total
                previous_total_data = sum(gen["size"] for gen in generations) + cumulative_non_eligible_data
                monthly_data = previous_total_data * monthly_growth_rate
            else:
                # No new data if growth rate is 0%
                monthly_data = 0
        
        eligible_data = monthly_data * percent_large_objects
        non_eligible_data = monthly_data * (1 - percent_large_objects)
        
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

        # PERFORMANCE OPTIMIZATION: Process generations in batches and filter early
        active_generations = []
        
        for gen in generations:
            # Skip tiny generations to reduce processing
            if gen["size"] < 0.001:  # Less than 1 MB
                continue
                
            original_size = gen["size"]
            remaining_size = gen["size"]
            original_objects = gen["objects"]
            remaining_objects = gen["objects"]
            
            # Determine current storage class based on age in days and access patterns
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
                # For Standard tier, we need to model hot vs cold data behavior
                # standard_access_rate determines what stays hot, rest becomes cold and transitions faster
                access_rate = 0  # Standard doesn't have retrieval costs, but we track access patterns

            # Handle Standard tier data lifecycle (hot vs cold data behavior)
            if storage_class == "standard":
                # Every month, split Standard data into hot (stays) and cold (transitions)
                hot_data_portion = standard_access_rate  # Percentage that stays hot
                cold_data_portion = 1 - standard_access_rate  # Percentage that becomes cold
                
                hot_volume = original_size * hot_data_portion
                cold_volume = original_size * cold_data_portion
                hot_objects = original_objects * hot_data_portion
                cold_objects = original_objects * cold_data_portion
                
                # Hot data stays in Standard (reset age to keep it hot)
                if hot_volume > 0.001:
                    new_generations.append({
                        "size": hot_volume,
                        "age_days": 0,  # Reset age for hot data - stays hot
                        "objects": hot_objects,
                        "created_month": month
                    })
                    storage_classes["standard"] += hot_volume
                    total_eligible_objects += hot_objects
                
                # Cold data: if it's been in Standard for 30+ days, move to Nearline
                # If less than 30 days, age it normally but mark as cold
                if gen["age_days"] >= 30:
                    # Cold data that's ready to transition to Nearline
                    if cold_volume > 0.001:
                        storage_classes["nearline"] += cold_volume
                        total_eligible_objects += cold_objects
                else:
                    # Cold data that's still aging toward Nearline transition
                    if cold_volume > 0.001:
                        new_generations.append({
                            "size": cold_volume,
                            "age_days": gen["age_days"] + 30,  # Age it normally
                            "objects": cold_objects,
                            "created_month": gen["created_month"]
                        })
                        storage_classes["standard"] += cold_volume
                        total_eligible_objects += cold_objects
                
                # This generation has been processed, continue to next
                continue
            
            # Handle access and re-promotion for colder tiers (data moves freely in Autoclass)
            if access_rate > 0 and storage_class != "standard":
                accessed_volume = original_size * access_rate
                accessed_objects = original_objects * access_rate
                
                # Re-promote accessed data to standard (create new generation)
                if accessed_volume > 0.001:  # Only create if significant size
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
            if remaining_size > 0.001:  # Only process significant sizes
                storage_classes[storage_class] += remaining_size
                total_eligible_objects += remaining_objects
                
                # Age the generation for next month
                gen["age_days"] += 30
                active_generations.append(gen)

        # PERFORMANCE OPTIMIZATION: Replace generations list with only active ones
        generations = active_generations + new_generations
        
        # PERFORMANCE OPTIMIZATION: Smart merging that preserves age accuracy
        if len(generations) > 150:  # Increased threshold for better accuracy
            # Sort by size and keep largest generations intact
            generations.sort(key=lambda x: x["size"], reverse=True)
            large_generations = generations[:100]  # Keep 100 largest
            small_generations = generations[100:]   # Merge the rest
            
            # Group small generations by their natural storage tier based on age
            tier_groups = {
                "standard": [],    # age < 30 days
                "nearline": [],    # 30 <= age < 90 days  
                "coldline": [],    # 90 <= age < 365 days
                "archive": []      # age >= 365 days
            }
            
            for gen in small_generations:
                age = gen["age_days"]
                if age >= 365:
                    tier_groups["archive"].append(gen)
                elif age >= 90:
                    tier_groups["coldline"].append(gen)
                elif age >= 30:
                    tier_groups["nearline"].append(gen)
                else:
                    tier_groups["standard"].append(gen)
            
            # Merge within each tier, preserving age accuracy
            for tier, tier_gens in tier_groups.items():
                if tier_gens:
                    merged_size = sum(g["size"] for g in tier_gens)
                    merged_objects = sum(g["objects"] for g in tier_gens)
                    # Preserve the maximum age within the tier (most conservative)
                    max_age = max(g["age_days"] for g in tier_gens)
                    # Use the earliest creation month for tracking
                    earliest_month = min(g["created_month"] for g in tier_gens)
                    
                    if merged_size > 0:
                        large_generations.append({
                            "size": merged_size,
                            "age_days": max_age,  # Preserve actual age, not forced!
                            "objects": merged_objects,
                            "created_month": earliest_month
                        })
            
            generations = large_generations

        # Calculate costs
        storage_cost = sum(storage_classes[c] * pricing[c]["storage"] for c in storage_classes)
        api_cost = (reads * pricing["operations"]["class_b"]) + (writes * pricing["operations"]["class_a"])
        autoclass_fee = (total_eligible_objects / 1000) * pricing["autoclass_fee_per_1000_objects_per_month"]
        total_cost = storage_cost + api_cost + autoclass_fee

        # Calculate total data across all classes
        total_data = sum(storage_classes.values())

        # Determine appropriate units for display
        storage_unit_value, storage_unit = get_storage_unit_and_value(total_data)
        
        results.append({
            "Month": f"Month {month}",
            # Raw values for calculations (always in GB and $)
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
            # Formatted values for display
            "Standard (Formatted)": format_storage_value(storage_classes["standard"]),
            "Nearline (Formatted)": format_storage_value(storage_classes["nearline"]),
            "Coldline (Formatted)": format_storage_value(storage_classes["coldline"]),
            "Archive (Formatted)": format_storage_value(storage_classes["archive"]),
            "Total Data (Formatted)": format_storage_value(total_data),
            "Autoclass Fee (Formatted)": format_cost_value(autoclass_fee),
            "Storage Cost (Formatted)": format_cost_value(storage_cost),
            "API Cost (Formatted)": format_cost_value(api_cost),
            "Total Cost (Formatted)": format_cost_value(total_cost)
        })

    return pd.DataFrame(results)

# --- Run Simulation ---
if months > 36:
    st.info(f"⏳ Running {months}-month simulation... This may take a moment for longer periods.")

with st.spinner("Running simulation...") if months > 24 else st.empty():
    df = simulate_autoclass_with_objects(
        initial_data_gb=initial_data_gb,
        monthly_growth_rate=monthly_growth_rate,
        avg_object_size_large_kib=avg_object_size_large_kib,
        avg_object_size_small_kib=avg_object_size_small_kib,
        percent_large_objects=percent_large_objects,
        months=months,
        standard_access_rate=standard_access_rate,
        nearline_read_rate=nearline_read_rate,
        coldline_read_rate=coldline_read_rate,
        archive_read_rate=archive_read_rate,
        reads=reads,
        writes=writes
    )

# --- Display Table ---
st.subheader("📊 Monthly Breakdown")

# Create a display dataframe with formatted values
display_df = df[["Month", "Standard (Formatted)", "Nearline (Formatted)", "Coldline (Formatted)", 
                 "Archive (Formatted)", "Total Data (Formatted)", "Total Eligible Objects", 
                 "Total Non-Eligible Objects", "Autoclass Fee (Formatted)", "Storage Cost (Formatted)", 
                 "API Cost (Formatted)", "Total Cost (Formatted)"]].copy()

# Rename columns for better display
display_df.columns = ["Month", "Standard", "Nearline", "Coldline", "Archive", "Total Data", 
                     "Eligible Objects", "Non-Eligible Objects", "Autoclass Fee", "Storage Cost", 
                     "API Cost", "Total Cost"]

st.dataframe(display_df)

# --- Summary & Cost ---
total_cost = df["Total Cost ($)"].sum()
st.markdown(f"### 💰 Total {months}-Month Cost: **{format_cost_value(total_cost)}**")

# --- Cost Breakdown Summary ---
st.subheader("💸 Cost Breakdown Summary")
total_storage = df["Storage Cost ($)"].sum()
total_api = df["API Cost ($)"].sum()
total_autoclass_fee = df["Autoclass Fee ($)"].sum()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Storage Cost", format_cost_value(total_storage))
    st.metric("API Cost", format_cost_value(total_api))
with col2:
    st.metric("Autoclass Fee", format_cost_value(total_autoclass_fee))
with col3:
    st.metric("**Total Cost**", f"**{format_cost_value(total_cost)}**")

# --- Static Chart: Tier Growth ---
st.subheader("🪄 Tier-wise Data Growth Over Time")
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

# Determine appropriate storage unit for chart
max_total_data = df["Total Data (GB)"].max()
storage_unit_factor, storage_unit = get_storage_unit_and_value(max_total_data)

# Convert data for chart display
if storage_unit == "TiB":
    chart_data_standard = df["Standard (GB)"] / 1024
    chart_data_nearline = df["Nearline (GB)"] / 1024
    chart_data_coldline = df["Coldline (GB)"] / 1024
    chart_data_archive = df["Archive (GB)"] / 1024
    chart_data_total = df["Total Data (GB)"] / 1024
    storage_label = "TiB Stored"
else:
    chart_data_standard = df["Standard (GB)"]
    chart_data_nearline = df["Nearline (GB)"]
    chart_data_coldline = df["Coldline (GB)"]
    chart_data_archive = df["Archive (GB)"]
    chart_data_total = df["Total Data (GB)"]
    storage_label = "GB Stored"

# Data distribution chart
ax1.plot(df["Month"], chart_data_standard, label="Standard", linewidth=2)
ax1.plot(df["Month"], chart_data_nearline, label="Nearline", linewidth=2)
ax1.plot(df["Month"], chart_data_coldline, label="Coldline", linewidth=2)
ax1.plot(df["Month"], chart_data_archive, label="Archive", linewidth=2)
ax1.plot(df["Month"], chart_data_total, label="Total", linestyle="--", alpha=0.7)
ax1.set_ylabel(storage_label)
ax1.set_title("Data Distribution Across Storage Classes")
ax1.legend()
ax1.grid(True, alpha=0.3)

# Determine appropriate cost unit for chart
max_total_cost = df["Total Cost ($)"].max()
cost_unit_factor, cost_unit = get_cost_unit_and_value(max_total_cost)

# Convert cost data for chart display
if cost_unit == "M":
    chart_cost_storage = df["Storage Cost ($)"] / 1000000
    chart_cost_autoclass = df["Autoclass Fee ($)"] / 1000000
    chart_cost_total = df["Total Cost ($)"] / 1000000
    cost_label = "Cost ($M)"
else:
    chart_cost_storage = df["Storage Cost ($)"]
    chart_cost_autoclass = df["Autoclass Fee ($)"]
    chart_cost_total = df["Total Cost ($)"]
    cost_label = "Cost ($)"

# Cost breakdown chart
ax2.plot(df["Month"], chart_cost_storage, label="Storage", linewidth=2)
ax2.plot(df["Month"], chart_cost_autoclass, label="Autoclass Fee", linewidth=2)
ax2.plot(df["Month"], chart_cost_total, label="Total", linestyle="--", alpha=0.7)
ax2.set_ylabel(cost_label)
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
    final_total_data = df['Total Data (GB)'].iloc[-1]
    final_archive_data = df['Archive (GB)'].iloc[-1]
    archive_percentage = (final_archive_data/final_total_data*100) if final_total_data > 0 else 0
    
    st.info(f"""
    **Data Lifecycle:**
    - Final month total data: {format_storage_value(final_total_data)}
    - Archive tier at end: {format_storage_value(final_archive_data)} ({archive_percentage:.1f}%)
    - Data distribution optimization achieved
    """)

with col2:
    avg_monthly_cost = total_cost / months
    storage_percentage = (total_storage / total_cost * 100) if total_cost > 0 else 0
    autoclass_percentage = (total_autoclass_fee/total_cost*100) if total_cost > 0 else 0
    
    st.info(f"""
    **Cost Analysis:**
    - Average monthly cost: {format_cost_value(avg_monthly_cost)}
    - Storage costs: {storage_percentage:.1f}% of total
    - Autoclass fee: {format_cost_value(total_autoclass_fee)} ({autoclass_percentage:.1f}%)
    """)

# --- PDF Report Generation Function ---
def generate_pdf_report(df, total_cost, total_storage, total_api, total_autoclass_fee, months, 
                       initial_data_gb, monthly_growth_rate, pricing, standard_access_rate, 
                       nearline_read_rate, coldline_read_rate, archive_read_rate):
    """Generate a comprehensive PDF report of the simulation"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.darkblue,
        alignment=1,  # Center alignment
        spaceAfter=30
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.darkblue,
        spaceBefore=20,
        spaceAfter=10
    )
    
    # Title and Header
    story.append(Paragraph("GCS Autoclass Cost Analysis Report", title_style))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Executive Summary
    story.append(Paragraph("Executive Summary", heading_style))
    avg_monthly_cost = total_cost / months if months > 0 else 0
    storage_percentage = (total_storage / total_cost * 100) if total_cost > 0 else 0
    
    # Format values for PDF
    final_data_gb = df['Total Data (GB)'].iloc[-1]
    final_archive_gb = df['Archive (GB)'].iloc[-1]
    archive_percentage = (final_archive_gb/final_data_gb*100) if final_data_gb > 0 else 0
    
    summary_text = f"""
    <b>Analysis Period:</b> {months} months<br/>
    <b>Initial Data:</b> {format_storage_value(initial_data_gb)}<br/>
    <b>Monthly Growth Rate:</b> {monthly_growth_rate*100:.1f}%<br/>
    <b>Total Cost:</b> {format_cost_value(total_cost)}<br/>
    <b>Average Monthly Cost:</b> {format_cost_value(avg_monthly_cost)}<br/>
    <b>Final Data Volume:</b> {format_storage_value(final_data_gb)}<br/>
    <b>Archive Tier Usage:</b> {archive_percentage:.1f}%<br/>
    <br/>
    <b>Access Pattern Summary:</b><br/>
    • Standard Hot Data: {standard_access_rate*100:.1f}% stays hot<br/>
    • Nearline Access: {nearline_read_rate*100:.1f}%/month<br/>
    • Coldline Access: {coldline_read_rate*100:.1f}%/month<br/>
    • Archive Access: {archive_read_rate*100:.1f}%/month
    """
    story.append(Paragraph(summary_text, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Cost Breakdown
    story.append(Paragraph("Cost Breakdown", heading_style))
    cost_data = [
        ['Cost Component', 'Amount', 'Percentage'],
        ['Storage Costs', format_cost_value(total_storage), f'{storage_percentage:.1f}%'],
        ['API Operations', format_cost_value(total_api), f'{total_api/total_cost*100:.1f}%'],
        ['Autoclass Management Fee', format_cost_value(total_autoclass_fee), f'{total_autoclass_fee/total_cost*100:.1f}%'],
        ['Total', format_cost_value(total_cost), '100.0%']
    ]
    
    cost_table = Table(cost_data)
    cost_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(cost_table)
    story.append(Spacer(1, 20))
    
    # Access Pattern Configuration
    story.append(Paragraph("Access Pattern Configuration", heading_style))
    
    # Determine which tiers are effectively disabled
    disabled_tiers = []
    if standard_access_rate == 1.0:
        disabled_tiers = ["Nearline", "Coldline", "Archive"]
        data_flow = "All data stays in Standard tier (100% hot)"
    elif nearline_read_rate == 1.0:
        disabled_tiers = ["Coldline", "Archive"]
        data_flow = "Standard ↔ Nearline re-promotion cycle"
    elif coldline_read_rate == 1.0:
        disabled_tiers = ["Archive"]
        data_flow = "Standard ↔ Nearline ↔ Coldline re-promotion cycle"
    else:
        data_flow = "Full tier progression enabled"
    
    access_pattern_text = f"""
    <b>Monthly Access Rates:</b><br/>
    • Standard (Hot Data): {standard_access_rate*100:.1f}% stays hot/month<br/>
    • Nearline Access: {nearline_read_rate*100:.1f}% accessed/month<br/>
    • Coldline Access: {coldline_read_rate*100:.1f}% accessed/month<br/>
    • Archive Access: {archive_read_rate*100:.1f}% accessed/month<br/>
    <br/>
    <b>Data Flow Pattern:</b> {data_flow}<br/>
    """
    
    if disabled_tiers:
        access_pattern_text += f"<b>Effectively Disabled Tiers:</b> {', '.join(disabled_tiers)}<br/>"
    
    access_pattern_text += f"""<br/>
    <b>Impact Analysis:</b><br/>
    • Cold data transition: {(1-standard_access_rate)*100:.1f}% of Standard data becomes cold monthly<br/>
    • Re-promotion behavior: {"High re-promotion rates increase Standard tier usage" if any([nearline_read_rate >= 0.5, coldline_read_rate >= 0.5, archive_read_rate >= 0.5]) else "Low re-promotion rates optimize for cold storage savings"}
    """
    
    story.append(Paragraph(access_pattern_text, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Pricing Configuration
    story.append(Paragraph("Pricing Configuration", heading_style))
    pricing_text = f"""
    <b>Storage Pricing (per GB/month):</b><br/>
    • Standard: ${pricing['standard']['storage']:.4f}<br/>
    • Nearline: ${pricing['nearline']['storage']:.4f}<br/>
    • Coldline: ${pricing['coldline']['storage']:.4f}<br/>
    • Archive: ${pricing['archive']['storage']:.4f}<br/>
    <br/>
    <b>API Operations:</b><br/>
    • Class A (Writes): ${pricing['operations']['class_a']:.6f} per operation<br/>
    • Class B (Reads): ${pricing['operations']['class_b']:.6f} per operation<br/>
    <br/>
    <b>Autoclass Management Fee:</b> ${pricing['autoclass_fee_per_1000_objects_per_month']:.4f} per 1000 objects/month
    """
    story.append(Paragraph(pricing_text, styles['Normal']))
    story.append(PageBreak())
    
    # Monthly Data Table
    story.append(Paragraph("Detailed Monthly Breakdown", heading_style))
    
    # Determine appropriate units for the table
    max_data = df['Total Data (GB)'].max()
    max_cost = df['Total Cost ($)'].max()
    data_unit = "TiB" if max_data >= 1024 else "GB"
    cost_unit = "$M" if max_cost >= 1000000 else "$"
    
    # Prepare data for table (first 24 months or all if less)
    display_months = min(24, len(df))
    
    if data_unit == "TiB":
        table_data = [['Month', 'Standard (TiB)', 'Nearline (TiB)', 'Coldline (TiB)', 'Archive (TiB)', f'Total Cost ({cost_unit})']]
        
        for i in range(display_months):
            row = df.iloc[i]
            cost_value = row['Total Cost ($)'] / 1000000 if cost_unit == "$M" else row['Total Cost ($)']
            table_data.append([
                row['Month'],
                f"{row['Standard (GB)']/1024:,.2f}",
                f"{row['Nearline (GB)']/1024:,.2f}",
                f"{row['Coldline (GB)']/1024:,.2f}",
                f"{row['Archive (GB)']/1024:,.2f}",
                f"{cost_value:,.2f}"
            ])
        
        if len(df) > 24:
            table_data.append(['...', '...', '...', '...', '...', '...'])
            # Add last month
            last_row = df.iloc[-1]
            last_cost_value = last_row['Total Cost ($)'] / 1000000 if cost_unit == "$M" else last_row['Total Cost ($)']
            table_data.append([
                last_row['Month'],
                f"{last_row['Standard (GB)']/1024:,.2f}",
                f"{last_row['Nearline (GB)']/1024:,.2f}",
                f"{last_row['Coldline (GB)']/1024:,.2f}",
                f"{last_row['Archive (GB)']/1024:,.2f}",
                f"{last_cost_value:,.2f}"
            ])
    else:
        table_data = [['Month', 'Standard (GB)', 'Nearline (GB)', 'Coldline (GB)', 'Archive (GB)', f'Total Cost ({cost_unit})']]
        
        for i in range(display_months):
            row = df.iloc[i]
            cost_value = row['Total Cost ($)'] / 1000000 if cost_unit == "$M" else row['Total Cost ($)']
            table_data.append([
                row['Month'],
                f"{row['Standard (GB)']:,.1f}",
                f"{row['Nearline (GB)']:,.1f}",
                f"{row['Coldline (GB)']:,.1f}",
                f"{row['Archive (GB)']:,.1f}",
                f"{cost_value:,.2f}"
            ])
        
        if len(df) > 24:
            table_data.append(['...', '...', '...', '...', '...', '...'])
            # Add last month
            last_row = df.iloc[-1]
            last_cost_value = last_row['Total Cost ($)'] / 1000000 if cost_unit == "$M" else last_row['Total Cost ($)']
            table_data.append([
                last_row['Month'],
                f"{last_row['Standard (GB)']:,.1f}",
                f"{last_row['Nearline (GB)']:,.1f}",
                f"{last_row['Coldline (GB)']:,.1f}",
                f"{last_row['Archive (GB)']:,.1f}",
                f"{last_cost_value:,.2f}"
            ])
    
    # Create table
    data_table = Table(table_data)
    data_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(data_table)
    story.append(Spacer(1, 20))
    
    # Key Insights
    story.append(Paragraph("Key Insights", heading_style))
    
    final_data_gb = df['Total Data (GB)'].iloc[-1]
    final_archive_gb = df['Archive (GB)'].iloc[-1]
    archive_percentage = (final_archive_gb/final_data_gb*100) if final_data_gb > 0 else 0
    
    insights_text = f"""
    <b>Data Lifecycle Analysis:</b><br/>
    • Total data grew from {format_storage_value(initial_data_gb)} to {format_storage_value(final_data_gb)}<br/>
    • {archive_percentage:.1f}% of data reached Archive tier by end of simulation<br/>
    • Cost efficiency improved as data aged to colder storage tiers<br/>
    <br/>
    <b>Cost Optimization:</b><br/>
    • Storage costs represent {storage_percentage:.1f}% of total expenses<br/>
    • Autoclass management fee: {format_cost_value(total_autoclass_fee)} ({total_autoclass_fee/total_cost*100:.1f}% of total)<br/>
    • {"Autoclass provides cost optimization through automatic tier transitions" if storage_percentage > 70 else "Consider optimizing access patterns to maximize Autoclass benefits"}
    """
    story.append(Paragraph(insights_text, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

# --- Export Options ---
st.subheader("📦 Export Reports")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**📊 CSV Data Export**")
    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="📄 Download CSV",
        data=csv_buffer.getvalue(),
        file_name=f"autoclass_simulation_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )

with col2:
    st.markdown("**📋 PDF Report**")
    if st.button("📑 Generate PDF Report", type="secondary"):
        with st.spinner("Generating PDF report..."):
            pdf_buffer = generate_pdf_report(
                df=df,
                total_cost=total_cost,
                total_storage=total_storage,
                total_api=total_api,
                total_autoclass_fee=total_autoclass_fee,
                months=months,
                initial_data_gb=initial_data_gb,
                monthly_growth_rate=monthly_growth_rate,
                pricing=pricing,
                standard_access_rate=standard_access_rate,
                nearline_read_rate=nearline_read_rate,
                coldline_read_rate=coldline_read_rate,
                archive_read_rate=archive_read_rate
            )
            
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_buffer.getvalue(),
                file_name=f"gcs_autoclass_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf"
            )
