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

# --- Default Pricing Constants (Iowa us-central1 Regional) ---
default_pricing = {
    "standard": {"storage": 0.020, "min_storage_days": 0},
    "nearline": {"storage": 0.010, "min_storage_days": 30},
    "coldline": {"storage": 0.004, "min_storage_days": 90},
    "archive": {"storage": 0.0012, "min_storage_days": 365},
    "operations": {
        "class_a": 0.05 / 10000,  # Per operation
        "class_b": 0.004 / 10000  # Per operation
    },
    "autoclass_fee_per_1000_objects_per_month": 0.0025,  # Per 1000 objects per month
    "retrieval_costs": {
        "nearline": 0.01,    # $ per GB retrieved
        "coldline": 0.02,    # $ per GB retrieved  
        "archive": 0.05      # $ per GB retrieved
    },
    "early_deletion_fees": {
        "nearline": 0.010,   # $ per GB if deleted before 30 days
        "coldline": 0.004,   # $ per GB if deleted before 90 days
        "archive": 0.0012    # $ per GB if deleted before 365 days
    }
}

# --- UI ---
st.title("GCS Storage Strategy Simulator")
st.markdown("*Compare Autoclass vs Lifecycle Policies for optimal storage cost planning*")

# --- Analysis Mode Selection ---
st.subheader("📊 Analysis Mode")
analysis_mode = st.radio(
    "Choose analysis type:",
    ["🤖 Autoclass Only", "📋 Lifecycle Only", "⚖️ Side-by-Side Comparison"],
    index=2,  # Default to comparison
    horizontal=True
)

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
    
    st.markdown("**Lifecycle-Specific Costs**")
    nearline_retrieval_price = st.number_input("Nearline Retrieval ($/GB)", min_value=0.0, value=default_pricing["retrieval_costs"]["nearline"], step=0.001, format="%.4f")
    coldline_retrieval_price = st.number_input("Coldline Retrieval ($/GB)", min_value=0.0, value=default_pricing["retrieval_costs"]["coldline"], step=0.001, format="%.4f")
    archive_retrieval_price = st.number_input("Archive Retrieval ($/GB)", min_value=0.0, value=default_pricing["retrieval_costs"]["archive"], step=0.001, format="%.4f")

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
    "autoclass_fee_per_1000_objects_per_month": autoclass_fee_price,
    "retrieval_costs": {
        "nearline": nearline_retrieval_price,
        "coldline": coldline_retrieval_price,
        "archive": archive_retrieval_price
    },
    "early_deletion_fees": {
        "nearline": nearline_storage_price,  # Use storage price as proxy
        "coldline": coldline_storage_price,
        "archive": archive_storage_price
    }
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

# --- Lifecycle Configuration (only show if lifecycle is included) ---
if analysis_mode in ["📋 Lifecycle Only", "⚖️ Side-by-Side Comparison"]:
    st.sidebar.header("📋 Lifecycle Rules")
    st.sidebar.markdown("*Configure custom transition rules*")
    
    lifecycle_rules = {}
    lifecycle_rules["nearline_days"] = st.sidebar.number_input("Days to Nearline", min_value=1, max_value=365, value=30, help="Days after creation to move to Nearline")
    lifecycle_rules["coldline_days"] = st.sidebar.number_input("Days to Coldline", min_value=lifecycle_rules["nearline_days"], max_value=365, value=90, help="Days after creation to move to Coldline")
    lifecycle_rules["archive_days"] = st.sidebar.number_input("Days to Archive", min_value=lifecycle_rules["coldline_days"], max_value=3650, value=365, help="Days after creation to move to Archive")
    
    st.sidebar.info(f"""
    **Lifecycle Flow:**
    • Standard → Nearline: {lifecycle_rules["nearline_days"]} days
    • Nearline → Coldline: {lifecycle_rules["coldline_days"]} days  
    • Coldline → Archive: {lifecycle_rules["archive_days"]} days
    """)
else:
    # Default lifecycle rules (not used but needed for function calls)
    lifecycle_rules = {"nearline_days": 30, "coldline_days": 90, "archive_days": 365}

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

# --- Lifecycle Policy Simulation Function ---
def simulate_lifecycle_policy(initial_data_gb, monthly_growth_rate, avg_object_size_large_kib, avg_object_size_small_kib, percent_large_objects, months,
                             standard_access_rate, nearline_read_rate, coldline_read_rate, archive_read_rate,
                             reads, writes, lifecycle_rules):
    """
    Simulate lifecycle policy with time-based transitions and retrieval costs
    Key differences from Autoclass:
    - Time-based transitions (not access-based)
    - No re-promotion to Standard
    - Retrieval costs when accessing cold data
    - No management fees
    """
    generations = []
    results = []
    cumulative_non_eligible_objects = 0
    cumulative_non_eligible_data = 0

    for month in range(1, months + 1):
        # Calculate new data (same as Autoclass)
        if month == 1:
            monthly_data = initial_data_gb
        else:
            if monthly_growth_rate > 0:
                previous_total_data = sum(gen["size"] for gen in generations) + cumulative_non_eligible_data
                monthly_data = previous_total_data * monthly_growth_rate
            else:
                monthly_data = 0
        
        eligible_data = monthly_data * percent_large_objects
        non_eligible_data = monthly_data * (1 - percent_large_objects)
        
        eligible_objects = (eligible_data * 1024 * 1024) / avg_object_size_large_kib
        non_eligible_objects = (non_eligible_data * 1024 * 1024) / avg_object_size_small_kib

        cumulative_non_eligible_objects += non_eligible_objects
        cumulative_non_eligible_data += non_eligible_data

        # Add new generation for eligible data
        if eligible_data > 0:
            generations.append({
                "size": eligible_data, 
                "age_days": 0, 
                "objects": eligible_objects,
                "created_month": month
            })

        # Initialize storage classes
        storage_classes = {"standard": cumulative_non_eligible_data, "nearline": 0, "coldline": 0, "archive": 0}
        total_objects = cumulative_non_eligible_objects
        retrieval_costs = {"nearline": 0, "coldline": 0, "archive": 0}

        # Process each generation - TIME-BASED transitions
        active_generations = []
        for gen in generations:
            if gen["size"] < 0.001:  # Skip tiny generations
                continue
                
            age_days = gen["age_days"]
            
            # Determine storage class based on AGE ONLY (not access patterns)
            if age_days >= lifecycle_rules["archive_days"]:
                storage_class = "archive"
            elif age_days >= lifecycle_rules["coldline_days"]:
                storage_class = "coldline"
            elif age_days >= lifecycle_rules["nearline_days"]:
                storage_class = "nearline"
            else:
                storage_class = "standard"
            
            # Add to storage class
            storage_classes[storage_class] += gen["size"]
            total_objects += gen["objects"]
            
            # Calculate retrieval costs based on access patterns
            if storage_class == "nearline" and nearline_read_rate > 0:
                retrieval_costs["nearline"] += gen["size"] * nearline_read_rate * pricing["retrieval_costs"]["nearline"]
            elif storage_class == "coldline" and coldline_read_rate > 0:
                retrieval_costs["coldline"] += gen["size"] * coldline_read_rate * pricing["retrieval_costs"]["coldline"]
            elif storage_class == "archive" and archive_read_rate > 0:
                retrieval_costs["archive"] += gen["size"] * archive_read_rate * pricing["retrieval_costs"]["archive"]
            
            # Age the generation for next month
            gen["age_days"] += 30
            active_generations.append(gen)

        generations = active_generations

        # Calculate costs - NO AUTOCLASS FEES, but WITH RETRIEVAL COSTS
        storage_cost = sum(storage_classes[c] * pricing[c]["storage"] for c in storage_classes)
        api_cost = (reads * pricing["operations"]["class_b"]) + (writes * pricing["operations"]["class_a"])
        total_retrieval_cost = sum(retrieval_costs.values())
        
        # NO autoclass management fee for lifecycle
        total_cost = storage_cost + api_cost + total_retrieval_cost

        # Calculate total data
        total_data = sum(storage_classes.values())
        
        results.append({
            "Month": f"Month {month}",
            # Raw values for calculations
            "Standard (GB)": round(storage_classes["standard"], 2),
            "Nearline (GB)": round(storage_classes["nearline"], 2),
            "Coldline (GB)": round(storage_classes["coldline"], 2),
            "Archive (GB)": round(storage_classes["archive"], 2),
            "Total Data (GB)": round(total_data, 2),
            "Total Objects": round(total_objects, 0),
            "Retrieval Cost ($)": round(total_retrieval_cost, 2),
            "Storage Cost ($)": round(storage_cost, 2),
            "API Cost ($)": round(api_cost, 2),
            "Total Cost ($)": round(total_cost, 2),
            # Formatted values for display
            "Standard (Formatted)": format_storage_value(storage_classes["standard"]),
            "Nearline (Formatted)": format_storage_value(storage_classes["nearline"]),
            "Coldline (Formatted)": format_storage_value(storage_classes["coldline"]),
            "Archive (Formatted)": format_storage_value(storage_classes["archive"]),
            "Total Data (Formatted)": format_storage_value(total_data),
            "Retrieval Cost (Formatted)": format_cost_value(total_retrieval_cost),
            "Storage Cost (Formatted)": format_cost_value(storage_cost),
            "API Cost (Formatted)": format_cost_value(api_cost),
            "Total Cost (Formatted)": format_cost_value(total_cost)
        })

    return pd.DataFrame(results)

# --- Run Simulation Based on Analysis Mode ---
if months > 36:
    st.info(f"⏳ Running {months}-month simulation... This may take a moment for longer periods.")

with st.spinner("Running simulation...") if months > 24 else st.empty():
    # Run simulations based on selected analysis mode
    autoclass_df = None
    lifecycle_df = None
    
    if analysis_mode in ["🤖 Autoclass Only", "⚖️ Side-by-Side Comparison"]:
        autoclass_df = simulate_autoclass_with_objects(
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
    
    if analysis_mode in ["📋 Lifecycle Only", "⚖️ Side-by-Side Comparison"]:
        lifecycle_df = simulate_lifecycle_policy(
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
            writes=writes,
            lifecycle_rules=lifecycle_rules
        )
    
    # Set primary dataframe for backward compatibility
    if analysis_mode == "🤖 Autoclass Only":
        df = autoclass_df
    elif analysis_mode == "📋 Lifecycle Only":
        df = lifecycle_df
    else:  # Side-by-Side Comparison
        df = autoclass_df  # Default for legacy sections

# --- Display Results Based on Analysis Mode ---
if analysis_mode == "⚖️ Side-by-Side Comparison":
    st.subheader("⚖️ Side-by-Side Comparison")
    
    # Create comparison summary
    autoclass_total_cost = autoclass_df["Total Cost ($)"].sum()
    lifecycle_total_cost = lifecycle_df["Total Cost ($)"].sum()
    cost_difference = autoclass_total_cost - lifecycle_total_cost
    savings_percentage = (abs(cost_difference) / max(autoclass_total_cost, lifecycle_total_cost)) * 100
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🤖 Autoclass Total Cost", format_cost_value(autoclass_total_cost))
        autoclass_final_archive = autoclass_df["Archive (GB)"].iloc[-1]
        autoclass_final_total = autoclass_df["Total Data (GB)"].iloc[-1]
        autoclass_archive_pct = (autoclass_final_archive/autoclass_final_total*100) if autoclass_final_total > 0 else 0
        st.caption(f"Archive usage: {autoclass_archive_pct:.1f}%")
    
    with col2:
        st.metric("📋 Lifecycle Total Cost", format_cost_value(lifecycle_total_cost))
        lifecycle_final_archive = lifecycle_df["Archive (GB)"].iloc[-1] 
        lifecycle_final_total = lifecycle_df["Total Data (GB)"].iloc[-1]
        lifecycle_archive_pct = (lifecycle_final_archive/lifecycle_final_total*100) if lifecycle_final_total > 0 else 0
        st.caption(f"Archive usage: {lifecycle_archive_pct:.1f}%")
    
    with col3:
        if cost_difference > 0:
            st.metric("💰 Lifecycle Savings", format_cost_value(cost_difference), f"{savings_percentage:.1f}%")
        else:
            st.metric("💸 Autoclass Savings", format_cost_value(abs(cost_difference)), f"{savings_percentage:.1f}%")
    
    # Side-by-side table comparison
    st.subheader("📊 Monthly Comparison")
    
    # Create combined dataframe for comparison
    comparison_data = []
    for i in range(len(autoclass_df)):
        comparison_data.append({
            "Month": autoclass_df.iloc[i]["Month"],
            "Autoclass Total Cost": autoclass_df.iloc[i]["Total Cost (Formatted)"],
            "Lifecycle Total Cost": lifecycle_df.iloc[i]["Total Cost (Formatted)"],
            "Autoclass Archive": autoclass_df.iloc[i]["Archive (Formatted)"],
            "Lifecycle Archive": lifecycle_df.iloc[i]["Archive (Formatted)"],
            "Cost Difference": format_cost_value(autoclass_df.iloc[i]["Total Cost ($)"] - lifecycle_df.iloc[i]["Total Cost ($)"])
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, use_container_width=True)
    
    # Detailed breakdown tabs
    tab1, tab2, tab3 = st.tabs(["🤖 Autoclass Details", "📋 Lifecycle Details", "📈 Cost Analysis"])
    
    with tab1:
        st.markdown("**Autoclass Strategy Details**")
        autoclass_display_df = autoclass_df[["Month", "Standard (Formatted)", "Nearline (Formatted)", "Coldline (Formatted)", 
                         "Archive (Formatted)", "Total Data (Formatted)", "Total Eligible Objects", 
                         "Total Non-Eligible Objects", "Autoclass Fee (Formatted)", "Storage Cost (Formatted)", 
                         "API Cost (Formatted)", "Total Cost (Formatted)"]].copy()
        autoclass_display_df.columns = ["Month", "Standard", "Nearline", "Coldline", "Archive", "Total Data", 
                         "Eligible Objects", "Non-Eligible Objects", "Autoclass Fee", "Storage Cost", 
                         "API Cost", "Total Cost"]
        st.dataframe(autoclass_display_df, use_container_width=True)
    
    with tab2:
        st.markdown("**Lifecycle Policy Details**")
        lifecycle_display_df = lifecycle_df[["Month", "Standard (Formatted)", "Nearline (Formatted)", "Coldline (Formatted)", 
                         "Archive (Formatted)", "Total Data (Formatted)", "Total Objects", 
                         "Retrieval Cost (Formatted)", "Storage Cost (Formatted)", 
                         "API Cost (Formatted)", "Total Cost (Formatted)"]].copy()
        lifecycle_display_df.columns = ["Month", "Standard", "Nearline", "Coldline", "Archive", "Total Data", 
                         "Total Objects", "Retrieval Cost", "Storage Cost", 
                         "API Cost", "Total Cost"]
        st.dataframe(lifecycle_display_df, use_container_width=True)
    
    with tab3:
        st.markdown("**Cost Analysis & Insights**")
        
        # Cost breakdown comparison
        autoclass_storage = autoclass_df["Storage Cost ($)"].sum()
        autoclass_api = autoclass_df["API Cost ($)"].sum()
        autoclass_fee = autoclass_df["Autoclass Fee ($)"].sum()
        
        lifecycle_storage = lifecycle_df["Storage Cost ($)"].sum()
        lifecycle_api = lifecycle_df["API Cost ($)"].sum()
        lifecycle_retrieval = lifecycle_df["Retrieval Cost ($)"].sum()
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**🤖 Autoclass Breakdown**")
            st.write(f"Storage Cost: {format_cost_value(autoclass_storage)}")
            st.write(f"API Cost: {format_cost_value(autoclass_api)}")
            st.write(f"Management Fee: {format_cost_value(autoclass_fee)}")
            st.write(f"**Total: {format_cost_value(autoclass_total_cost)}**")
        
        with col2:
            st.markdown("**📋 Lifecycle Breakdown**")
            st.write(f"Storage Cost: {format_cost_value(lifecycle_storage)}")
            st.write(f"API Cost: {format_cost_value(lifecycle_api)}")
            st.write(f"Retrieval Cost: {format_cost_value(lifecycle_retrieval)}")
            st.write(f"**Total: {format_cost_value(lifecycle_total_cost)}**")
        
        # Insights
        st.markdown("**💡 Key Insights**")
        if cost_difference > 0:
            st.success(f"📋 **Lifecycle policy saves {format_cost_value(cost_difference)} ({savings_percentage:.1f}%)**")
            st.info("Lifecycle policies are more cost-effective for this scenario due to no management fees and predictable time-based transitions.")
        else:
            st.success(f"🤖 **Autoclass saves {format_cost_value(abs(cost_difference))} ({savings_percentage:.1f}%)**")
            st.info("Autoclass is more cost-effective due to intelligent access pattern optimization and no retrieval costs.")
        
        # Additional insights
        retrieval_impact = (lifecycle_retrieval / lifecycle_total_cost * 100) if lifecycle_total_cost > 0 else 0
        management_impact = (autoclass_fee / autoclass_total_cost * 100) if autoclass_total_cost > 0 else 0
        
        st.write(f"• Lifecycle retrieval costs: {retrieval_impact:.1f}% of total cost")
        st.write(f"• Autoclass management fee: {management_impact:.1f}% of total cost")
        
        if retrieval_impact > management_impact:
            st.warning("High retrieval costs in lifecycle policy - consider Autoclass for frequent access patterns")
        elif management_impact > 10:
            st.warning("High Autoclass management fees - consider lifecycle policy for predictable access patterns")

else:
    # Single analysis mode display
    strategy_name = "Autoclass" if analysis_mode == "🤖 Autoclass Only" else "Lifecycle"
    st.subheader(f"📊 {strategy_name} Monthly Breakdown")

    # Create a display dataframe with formatted values
    if analysis_mode == "🤖 Autoclass Only":
        display_df = df[["Month", "Standard (Formatted)", "Nearline (Formatted)", "Coldline (Formatted)", 
                         "Archive (Formatted)", "Total Data (Formatted)", "Total Eligible Objects", 
                         "Total Non-Eligible Objects", "Autoclass Fee (Formatted)", "Storage Cost (Formatted)", 
                         "API Cost (Formatted)", "Total Cost (Formatted)"]].copy()
        display_df.columns = ["Month", "Standard", "Nearline", "Coldline", "Archive", "Total Data", 
                             "Eligible Objects", "Non-Eligible Objects", "Autoclass Fee", "Storage Cost", 
                             "API Cost", "Total Cost"]
    else:  # Lifecycle Only
        display_df = df[["Month", "Standard (Formatted)", "Nearline (Formatted)", "Coldline (Formatted)", 
                         "Archive (Formatted)", "Total Data (Formatted)", "Total Objects", 
                         "Retrieval Cost (Formatted)", "Storage Cost (Formatted)", 
                         "API Cost (Formatted)", "Total Cost (Formatted)"]].copy()
        display_df.columns = ["Month", "Standard", "Nearline", "Coldline", "Archive", "Total Data", 
                             "Total Objects", "Retrieval Cost", "Storage Cost", 
                             "API Cost", "Total Cost"]

    st.dataframe(display_df, use_container_width=True)

# --- Summary & Cost Analysis ---
if analysis_mode == "⚖️ Side-by-Side Comparison":
    # Already displayed above in comparison section
    pass
else:
    # Single strategy summary
    total_cost = df["Total Cost ($)"].sum()
    strategy_name = "Autoclass" if analysis_mode == "🤖 Autoclass Only" else "Lifecycle"
    st.markdown(f"### 💰 Total {months}-Month {strategy_name} Cost: **{format_cost_value(total_cost)}**")

    # --- Cost Breakdown Summary ---
    st.subheader("💸 Cost Breakdown Summary")
    total_storage = df["Storage Cost ($)"].sum()
    total_api = df["API Cost ($)"].sum()
    
    if analysis_mode == "🤖 Autoclass Only":
        total_autoclass_fee = df["Autoclass Fee ($)"].sum()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Storage Cost", format_cost_value(total_storage))
            st.metric("API Cost", format_cost_value(total_api))
        with col2:
            st.metric("Autoclass Fee", format_cost_value(total_autoclass_fee))
        with col3:
            st.metric("**Total Cost**", f"**{format_cost_value(total_cost)}**")
    else:  # Lifecycle Only
        total_retrieval = df["Retrieval Cost ($)"].sum()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Storage Cost", format_cost_value(total_storage))
            st.metric("API Cost", format_cost_value(total_api))
        with col2:
            st.metric("Retrieval Cost", format_cost_value(total_retrieval))
        with col3:
            st.metric("**Total Cost**", f"**{format_cost_value(total_cost)}**")

# --- Charts and Visualizations ---
if analysis_mode == "⚖️ Side-by-Side Comparison":
    st.subheader("📈 Side-by-Side Visual Comparison")
    
    # Create comparison charts
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # Determine units for charts
    max_autoclass_data = autoclass_df["Total Data (GB)"].max()
    max_lifecycle_data = lifecycle_df["Total Data (GB)"].max()
    max_data = max(max_autoclass_data, max_lifecycle_data)
    storage_unit_factor, storage_unit = get_storage_unit_and_value(max_data)
    
    # Convert data for charts
    if storage_unit == "TiB":
        autoclass_factor = 1024
        lifecycle_factor = 1024
        storage_label = "TiB Stored"
    else:
        autoclass_factor = 1
        lifecycle_factor = 1
        storage_label = "GB Stored"
    
    # Autoclass data distribution
    ax1.plot(autoclass_df["Month"], autoclass_df["Standard (GB)"] / autoclass_factor, label="Standard", linewidth=2)
    ax1.plot(autoclass_df["Month"], autoclass_df["Nearline (GB)"] / autoclass_factor, label="Nearline", linewidth=2)
    ax1.plot(autoclass_df["Month"], autoclass_df["Coldline (GB)"] / autoclass_factor, label="Coldline", linewidth=2)
    ax1.plot(autoclass_df["Month"], autoclass_df["Archive (GB)"] / autoclass_factor, label="Archive", linewidth=2)
    ax1.set_ylabel(storage_label)
    ax1.set_title("🤖 Autoclass Data Distribution")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Lifecycle data distribution
    ax2.plot(lifecycle_df["Month"], lifecycle_df["Standard (GB)"] / lifecycle_factor, label="Standard", linewidth=2)
    ax2.plot(lifecycle_df["Month"], lifecycle_df["Nearline (GB)"] / lifecycle_factor, label="Nearline", linewidth=2)
    ax2.plot(lifecycle_df["Month"], lifecycle_df["Coldline (GB)"] / lifecycle_factor, label="Coldline", linewidth=2)
    ax2.plot(lifecycle_df["Month"], lifecycle_df["Archive (GB)"] / lifecycle_factor, label="Archive", linewidth=2)
    ax2.set_ylabel(storage_label)
    ax2.set_title("📋 Lifecycle Data Distribution")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Cost comparison
    max_autoclass_cost = autoclass_df["Total Cost ($)"].max()
    max_lifecycle_cost = lifecycle_df["Total Cost ($)"].max()
    max_cost = max(max_autoclass_cost, max_lifecycle_cost)
    cost_unit_factor, cost_unit = get_cost_unit_and_value(max_cost)
    
    cost_factor = 1000000 if cost_unit == "M" else 1
    cost_label = "Cost ($M)" if cost_unit == "M" else "Cost ($)"
    
    ax3.plot(autoclass_df["Month"], autoclass_df["Total Cost ($)"] / cost_factor, label="🤖 Autoclass", linewidth=3, color='blue')
    ax3.plot(lifecycle_df["Month"], lifecycle_df["Total Cost ($)"] / cost_factor, label="📋 Lifecycle", linewidth=3, color='red')
    ax3.set_ylabel(cost_label)
    ax3.set_title("💰 Total Cost Comparison")
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Cost difference over time
    cost_difference = autoclass_df["Total Cost ($)"] - lifecycle_df["Total Cost ($)"]
    ax4.plot(autoclass_df["Month"], cost_difference / cost_factor, linewidth=2, color='green')
    ax4.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    ax4.set_ylabel(f"Cost Difference ({cost_label.split('(')[1]}")
    ax4.set_xlabel("Month")
    ax4.set_title("💸 Cost Difference (Autoclass - Lifecycle)")
    ax4.grid(True, alpha=0.3)
    
    # Add annotation for positive/negative regions
    if cost_difference.iloc[-1] > 0:
        ax4.text(0.7, 0.9, "Lifecycle\nSaves Money", transform=ax4.transAxes, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen", alpha=0.7),
                verticalalignment='top')
    else:
        ax4.text(0.7, 0.1, "Autoclass\nSaves Money", transform=ax4.transAxes,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.7),
                verticalalignment='bottom')
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)
    
else:
    # Single strategy charts
    strategy_name = "Autoclass" if analysis_mode == "🤖 Autoclass Only" else "Lifecycle"
    st.subheader(f"🪄 {strategy_name} Data Growth Over Time")
    
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
        if analysis_mode == "🤖 Autoclass Only":
            chart_cost_special = df["Autoclass Fee ($)"] / 1000000
            special_label = "Autoclass Fee"
        else:
            chart_cost_special = df["Retrieval Cost ($)"] / 1000000
            special_label = "Retrieval Cost"
        chart_cost_total = df["Total Cost ($)"] / 1000000
        cost_label = "Cost ($M)"
    else:
        chart_cost_storage = df["Storage Cost ($)"]
        if analysis_mode == "🤖 Autoclass Only":
            chart_cost_special = df["Autoclass Fee ($)"]
            special_label = "Autoclass Fee"
        else:
            chart_cost_special = df["Retrieval Cost ($)"]
            special_label = "Retrieval Cost"
        chart_cost_total = df["Total Cost ($)"]
        cost_label = "Cost ($)"
    
    # Cost breakdown chart
    ax2.plot(df["Month"], chart_cost_storage, label="Storage", linewidth=2)
    ax2.plot(df["Month"], chart_cost_special, label=special_label, linewidth=2)
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
if analysis_mode != "⚖️ Side-by-Side Comparison":
    st.subheader("🔍 Key Insights")
    col1, col2 = st.columns(2)

    with col1:
        final_total_data = df['Total Data (GB)'].iloc[-1]
        final_archive_data = df['Archive (GB)'].iloc[-1]
        archive_percentage = (final_archive_data/final_total_data*100) if final_total_data > 0 else 0
        
        strategy_name = "Autoclass" if analysis_mode == "🤖 Autoclass Only" else "Lifecycle"
        
        st.info(f"""
        **{strategy_name} Data Lifecycle:**
        - Final month total data: {format_storage_value(final_total_data)}
        - Archive tier at end: {format_storage_value(final_archive_data)} ({archive_percentage:.1f}%)
        - Data distribution optimization achieved
        """)

    with col2:
        total_cost = df["Total Cost ($)"].sum()
        avg_monthly_cost = total_cost / months
        storage_percentage = (df["Storage Cost ($)"].sum() / total_cost * 100) if total_cost > 0 else 0
        
        if analysis_mode == "🤖 Autoclass Only":
            special_cost = df["Autoclass Fee ($)"].sum()
            special_percentage = (special_cost/total_cost*100) if total_cost > 0 else 0
            special_label = f"Autoclass fee: {format_cost_value(special_cost)} ({special_percentage:.1f}%)"
        else:
            special_cost = df["Retrieval Cost ($)"].sum()
            special_percentage = (special_cost/total_cost*100) if total_cost > 0 else 0
            special_label = f"Retrieval costs: {format_cost_value(special_cost)} ({special_percentage:.1f}%)"
        
        st.info(f"""
        **Cost Analysis:**
        - Average monthly cost: {format_cost_value(avg_monthly_cost)}
        - Storage costs: {storage_percentage:.1f}% of total
        - {special_label}
        """)
        
        # Strategy-specific insights
        if analysis_mode == "🤖 Autoclass Only":
            if special_percentage > 15:
                st.warning("⚠️ High Autoclass management fees - consider lifecycle policy for cost-sensitive scenarios")
            elif special_percentage < 5:
                st.success("✅ Autoclass management fees are minimal - excellent choice for dynamic access patterns")
        else:  # Lifecycle Only
            if special_percentage > 20:
                st.warning("⚠️ High retrieval costs - consider Autoclass for frequent access patterns")
            elif special_percentage < 5:
                st.success("✅ Low retrieval costs - lifecycle policy optimal for predictable access patterns")

# --- PDF Report Generation Function ---
def generate_pdf_report(analysis_mode, autoclass_df=None, lifecycle_df=None, months=12, 
                       initial_data_gb=0, monthly_growth_rate=0, pricing=None, 
                       standard_access_rate=0, nearline_read_rate=0, coldline_read_rate=0, 
                       archive_read_rate=0, lifecycle_rules=None):
    """Generate a comprehensive PDF report of the simulation based on analysis mode"""
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
    if analysis_mode == "⚖️ Side-by-Side Comparison":
        title = "GCS Storage Strategy Comparison Report"
        subtitle = "Autoclass vs Lifecycle Policy Analysis"
    elif analysis_mode == "🤖 Autoclass Only":
        title = "GCS Autoclass Cost Analysis Report"
        subtitle = "Intelligent Storage Optimization Analysis"
    else:  # Lifecycle Only
        title = "GCS Lifecycle Policy Cost Analysis Report"
        subtitle = "Time-Based Storage Transition Analysis"
    
    story.append(Paragraph(title, title_style))
    story.append(Paragraph(subtitle, styles['Normal']))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Executive Summary
    story.append(Paragraph("Executive Summary", heading_style))
    
    if analysis_mode == "⚖️ Side-by-Side Comparison":
        autoclass_total_cost = autoclass_df["Total Cost ($)"].sum()
        lifecycle_total_cost = lifecycle_df["Total Cost ($)"].sum()
        cost_difference = autoclass_total_cost - lifecycle_total_cost
        savings_percentage = (abs(cost_difference) / max(autoclass_total_cost, lifecycle_total_cost)) * 100
        
        winner = "Lifecycle Policy" if cost_difference > 0 else "Autoclass"
        savings_amount = abs(cost_difference)
        
        final_autoclass_data = autoclass_df['Total Data (GB)'].iloc[-1]
        final_lifecycle_data = lifecycle_df['Total Data (GB)'].iloc[-1]
        
        summary_text = f"""
        <b>Analysis Period:</b> {months} months<br/>
        <b>Initial Data:</b> {format_storage_value(initial_data_gb)}<br/>
        <b>Monthly Growth Rate:</b> {monthly_growth_rate*100:.1f}%<br/>
        <b>Final Data Volume:</b> {format_storage_value(final_autoclass_data)}<br/>
        <br/>
        <b>Cost Comparison Results:</b><br/>
        • Autoclass Total Cost: {format_cost_value(autoclass_total_cost)}<br/>
        • Lifecycle Total Cost: {format_cost_value(lifecycle_total_cost)}<br/>
        • <b>Winner: {winner}</b> (saves {format_cost_value(savings_amount)} / {savings_percentage:.1f}%)<br/>
        <br/>
        <b>Access Pattern Summary:</b><br/>
        • Standard Hot Data: {standard_access_rate*100:.1f}% stays hot<br/>
        • Nearline Access: {nearline_read_rate*100:.1f}%/month<br/>
        • Coldline Access: {coldline_read_rate*100:.1f}%/month<br/>
        • Archive Access: {archive_read_rate*100:.1f}%/month
        """
        
        if lifecycle_rules:
            summary_text += f"""<br/>
            <b>Lifecycle Configuration:</b><br/>
            • Nearline Transition: {lifecycle_rules['nearline_days']} days<br/>
            • Coldline Transition: {lifecycle_rules['coldline_days']} days<br/>
            • Archive Transition: {lifecycle_rules['archive_days']} days
            """
            
    else:
        # Single strategy analysis
        df = autoclass_df if analysis_mode == "🤖 Autoclass Only" else lifecycle_df
        total_cost = df["Total Cost ($)"].sum()
        avg_monthly_cost = total_cost / months if months > 0 else 0
        final_data_gb = df['Total Data (GB)'].iloc[-1]
        final_archive_gb = df['Archive (GB)'].iloc[-1]
        archive_percentage = (final_archive_gb/final_data_gb*100) if final_data_gb > 0 else 0
        
        strategy_name = "Autoclass" if analysis_mode == "🤖 Autoclass Only" else "Lifecycle Policy"
        
        summary_text = f"""
        <b>Analysis Period:</b> {months} months<br/>
        <b>Strategy:</b> {strategy_name}<br/>
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
        
        if analysis_mode == "📋 Lifecycle Only" and lifecycle_rules:
            summary_text += f"""<br/>
            <b>Lifecycle Configuration:</b><br/>
            • Nearline Transition: {lifecycle_rules['nearline_days']} days<br/>
            • Coldline Transition: {lifecycle_rules['coldline_days']} days<br/>
            • Archive Transition: {lifecycle_rules['archive_days']} days
            """
    
    story.append(Paragraph(summary_text, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Cost Breakdown
    story.append(Paragraph("Cost Breakdown Analysis", heading_style))
    
    if analysis_mode == "⚖️ Side-by-Side Comparison":
        autoclass_storage = autoclass_df["Storage Cost ($)"].sum()
        autoclass_api = autoclass_df["API Cost ($)"].sum()
        autoclass_fee = autoclass_df["Autoclass Fee ($)"].sum()
        
        lifecycle_storage = lifecycle_df["Storage Cost ($)"].sum()
        lifecycle_api = lifecycle_df["API Cost ($)"].sum()
        lifecycle_retrieval = lifecycle_df["Retrieval Cost ($)"].sum()
        
        cost_data = [
            ['Strategy', 'Storage Cost', 'API Cost', 'Special Cost', 'Total Cost'],
            ['Autoclass', format_cost_value(autoclass_storage), format_cost_value(autoclass_api), 
             f'{format_cost_value(autoclass_fee)} (Mgmt)', format_cost_value(autoclass_total_cost)],
            ['Lifecycle', format_cost_value(lifecycle_storage), format_cost_value(lifecycle_api), 
             f'{format_cost_value(lifecycle_retrieval)} (Retr)', format_cost_value(lifecycle_total_cost)],
            ['Difference', format_cost_value(autoclass_storage - lifecycle_storage), 
             format_cost_value(autoclass_api - lifecycle_api), 
             format_cost_value(autoclass_fee - lifecycle_retrieval), 
             format_cost_value(cost_difference)]
        ]
    else:
        # Single strategy breakdown
        df = autoclass_df if analysis_mode == "🤖 Autoclass Only" else lifecycle_df
        total_storage = df["Storage Cost ($)"].sum()
        total_api = df["API Cost ($)"].sum()
        total_cost = df["Total Cost ($)"].sum()
        
        if analysis_mode == "🤖 Autoclass Only":
            special_cost = df["Autoclass Fee ($)"].sum()
            special_label = "Autoclass Fee"
        else:
            special_cost = df["Retrieval Cost ($)"].sum()
            special_label = "Retrieval Cost"
        
        storage_pct = (total_storage / total_cost * 100) if total_cost > 0 else 0
        api_pct = (total_api / total_cost * 100) if total_cost > 0 else 0
        special_pct = (special_cost / total_cost * 100) if total_cost > 0 else 0
        
        cost_data = [
            ['Cost Component', 'Amount', 'Percentage'],
            ['Storage Costs', format_cost_value(total_storage), f'{storage_pct:.1f}%'],
            ['API Operations', format_cost_value(total_api), f'{api_pct:.1f}%'],
            [special_label, format_cost_value(special_cost), f'{special_pct:.1f}%'],
            ['Total', format_cost_value(total_cost), '100.0%']
        ]
    
    cost_table = Table(cost_data)
    cost_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(cost_table)
    story.append(PageBreak())
    
    # Monthly Data Tables
    if analysis_mode == "⚖️ Side-by-Side Comparison":
        story.append(Paragraph("Detailed Monthly Comparison", heading_style))
        
        # Create comparison table
        max_data = max(autoclass_df['Total Data (GB)'].max(), lifecycle_df['Total Data (GB)'].max())
        data_unit = "TiB" if max_data >= 1024 else "GB"
        data_factor = 1024 if data_unit == "TiB" else 1
        
        display_months = min(12, len(autoclass_df))
        
        table_data = [['Month', f'Autoclass Cost', f'Lifecycle Cost', 'Cost Difference', f'Archive Data ({data_unit})']]
        
        for i in range(display_months):
            auto_row = autoclass_df.iloc[i]
            life_row = lifecycle_df.iloc[i]
            cost_diff = auto_row['Total Cost ($)'] - life_row['Total Cost ($)']
            archive_data = auto_row['Archive (GB)'] / data_factor
            
            table_data.append([
                auto_row['Month'],
                format_cost_value(auto_row['Total Cost ($)']),
                format_cost_value(life_row['Total Cost ($)']),
                format_cost_value(cost_diff),
                f"{archive_data:,.2f}"
            ])
        
        if len(autoclass_df) > 12:
            table_data.append(['...', '...', '...', '...', '...'])
            # Add final month
            auto_final = autoclass_df.iloc[-1]
            life_final = lifecycle_df.iloc[-1]
            final_cost_diff = auto_final['Total Cost ($)'] - life_final['Total Cost ($)']
            final_archive = auto_final['Archive (GB)'] / data_factor
            
            table_data.append([
                auto_final['Month'],
                format_cost_value(auto_final['Total Cost ($)']),
                format_cost_value(life_final['Total Cost ($)']),
                format_cost_value(final_cost_diff),
                f"{final_archive:,.2f}"
            ])
    else:
        # Single strategy table
        story.append(Paragraph("Detailed Monthly Breakdown", heading_style))
        df = autoclass_df if analysis_mode == "🤖 Autoclass Only" else lifecycle_df
        
        max_data = df['Total Data (GB)'].max()
        data_unit = "TiB" if max_data >= 1024 else "GB"
        data_factor = 1024 if data_unit == "TiB" else 1
        
        display_months = min(12, len(df))
        
        if analysis_mode == "🤖 Autoclass Only":
            table_data = [['Month', f'Total Data ({data_unit})', 'Storage Cost', 'Autoclass Fee', 'Total Cost']]
            for i in range(display_months):
                row = df.iloc[i]
                table_data.append([
                    row['Month'],
                    f"{row['Total Data (GB)']/data_factor:,.2f}",
                    format_cost_value(row['Storage Cost ($)']),
                    format_cost_value(row['Autoclass Fee ($)']),
                    format_cost_value(row['Total Cost ($)'])
                ])
        else:
            table_data = [['Month', f'Total Data ({data_unit})', 'Storage Cost', 'Retrieval Cost', 'Total Cost']]
            for i in range(display_months):
                row = df.iloc[i]
                table_data.append([
                    row['Month'],
                    f"{row['Total Data (GB)']/data_factor:,.2f}",
                    format_cost_value(row['Storage Cost ($)']),
                    format_cost_value(row['Retrieval Cost ($)']),
                    format_cost_value(row['Total Cost ($)'])
                ])
        
        if len(df) > 12:
            table_data.append(['...', '...', '...', '...', '...'])
            # Add final month
            final_row = df.iloc[-1]
            if analysis_mode == "🤖 Autoclass Only":
                table_data.append([
                    final_row['Month'],
                    f"{final_row['Total Data (GB)']/data_factor:,.2f}",
                    format_cost_value(final_row['Storage Cost ($)']),
                    format_cost_value(final_row['Autoclass Fee ($)']),
                    format_cost_value(final_row['Total Cost ($)'])
                ])
            else:
                table_data.append([
                    final_row['Month'],
                    f"{final_row['Total Data (GB)']/data_factor:,.2f}",
                    format_cost_value(final_row['Storage Cost ($)']),
                    format_cost_value(final_row['Retrieval Cost ($)']),
                    format_cost_value(final_row['Total Cost ($)'])
                ])
    
    # Create and add table
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
    
    # Key Insights and Recommendations
    story.append(Paragraph("Key Insights and Recommendations", heading_style))
    
    if analysis_mode == "⚖️ Side-by-Side Comparison":
        winner_strategy = "Lifecycle Policy" if cost_difference > 0 else "Autoclass"
        insights_text = f"""
        <b>Strategy Comparison Results:</b><br/>
        • <b>Recommended Strategy: {winner_strategy}</b><br/>
        • Cost savings: {format_cost_value(abs(cost_difference))} ({savings_percentage:.1f}%)<br/>
        • Both strategies achieve similar archive utilization<br/>
        <br/>
        <b>Decision Factors:</b><br/>
        • {"Lifecycle saves money due to no management fees and predictable transitions" if cost_difference > 0 else "Autoclass saves money through intelligent optimization and no retrieval costs"}<br/>
        • {"Consider lifecycle for predictable, time-based access patterns" if cost_difference > 0 else "Consider Autoclass for dynamic, unpredictable access patterns"}<br/>
        • {"Lifecycle requires manual rule configuration but offers more control" if cost_difference > 0 else "Autoclass provides automatic optimization with minimal configuration"}
        """
    else:
        strategy_name = "Autoclass" if analysis_mode == "🤖 Autoclass Only" else "Lifecycle Policy"
        df = autoclass_df if analysis_mode == "🤖 Autoclass Only" else lifecycle_df
        
        storage_percentage = (df["Storage Cost ($)"].sum() / df["Total Cost ($)"].sum() * 100)
        
        if analysis_mode == "🤖 Autoclass Only":
            mgmt_percentage = (df["Autoclass Fee ($)"].sum() / df["Total Cost ($)"].sum() * 100)
            insights_text = f"""
            <b>{strategy_name} Analysis Results:</b><br/>
            • Storage costs represent {storage_percentage:.1f}% of total expenses<br/>
            • Autoclass management fee: {mgmt_percentage:.1f}% of total cost<br/>
            • {"Management fees are reasonable for the automation benefits" if mgmt_percentage < 15 else "Consider lifecycle policy to reduce management costs"}<br/>
            <br/>
            <b>Autoclass Benefits:</b><br/>
            • Automatic tier transitions based on access patterns<br/>
            • No retrieval costs for accessing cold data<br/>
            • Minimal configuration required<br/>
            • Intelligent optimization adapts to changing patterns
            """
        else:
            retrieval_percentage = (df["Retrieval Cost ($)"].sum() / df["Total Cost ($)"].sum() * 100)
            insights_text = f"""
            <b>{strategy_name} Analysis Results:</b><br/>
            • Storage costs represent {storage_percentage:.1f}% of total expenses<br/>
            • Retrieval costs: {retrieval_percentage:.1f}% of total cost<br/>
            • {"Retrieval costs are manageable for this access pattern" if retrieval_percentage < 20 else "High retrieval costs - consider Autoclass for frequent access"}<br/>
            <br/>
            <b>Lifecycle Policy Benefits:</b><br/>
            • No management fees (cost-effective for large datasets)<br/>
            • Predictable, time-based transitions<br/>
            • Full control over transition timing<br/>
            • Optimal for well-understood data lifecycle patterns
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
    
    if analysis_mode == "⚖️ Side-by-Side Comparison":
        # Export both datasets
        csv_buffer = BytesIO()
        
        # Create combined CSV with both strategies
        combined_data = []
        for i in range(len(autoclass_df)):
            combined_data.append({
                "Month": autoclass_df.iloc[i]["Month"],
                "Autoclass_Standard_GB": autoclass_df.iloc[i]["Standard (GB)"],
                "Autoclass_Nearline_GB": autoclass_df.iloc[i]["Nearline (GB)"],
                "Autoclass_Coldline_GB": autoclass_df.iloc[i]["Coldline (GB)"],
                "Autoclass_Archive_GB": autoclass_df.iloc[i]["Archive (GB)"],
                "Autoclass_Total_Cost": autoclass_df.iloc[i]["Total Cost ($)"],
                "Autoclass_Storage_Cost": autoclass_df.iloc[i]["Storage Cost ($)"],
                "Autoclass_Management_Fee": autoclass_df.iloc[i]["Autoclass Fee ($)"],
                "Lifecycle_Standard_GB": lifecycle_df.iloc[i]["Standard (GB)"],
                "Lifecycle_Nearline_GB": lifecycle_df.iloc[i]["Nearline (GB)"],
                "Lifecycle_Coldline_GB": lifecycle_df.iloc[i]["Coldline (GB)"],
                "Lifecycle_Archive_GB": lifecycle_df.iloc[i]["Archive (GB)"],
                "Lifecycle_Total_Cost": lifecycle_df.iloc[i]["Total Cost ($)"],
                "Lifecycle_Storage_Cost": lifecycle_df.iloc[i]["Storage Cost ($)"],
                "Lifecycle_Retrieval_Cost": lifecycle_df.iloc[i]["Retrieval Cost ($)"],
                "Cost_Difference": autoclass_df.iloc[i]["Total Cost ($)"] - lifecycle_df.iloc[i]["Total Cost ($)"]
            })
        
        combined_df = pd.DataFrame(combined_data)
        combined_df.to_csv(csv_buffer, index=False)
        
        st.download_button(
            label="📄 Download Comparison CSV",
            data=csv_buffer.getvalue(),
            file_name=f"gcs_strategy_comparison_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
    else:
        # Single strategy export
        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, index=False)
        strategy_name = "autoclass" if analysis_mode == "🤖 Autoclass Only" else "lifecycle"
        
        st.download_button(
            label="📄 Download CSV",
            data=csv_buffer.getvalue(),
            file_name=f"gcs_{strategy_name}_simulation_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )

with col2:
    st.markdown("**📋 PDF Report**")
    if st.button("📑 Generate PDF Report", type="secondary"):
        with st.spinner("Generating comprehensive PDF report..."):
            pdf_buffer = generate_pdf_report(
                analysis_mode=analysis_mode,
                autoclass_df=autoclass_df,
                lifecycle_df=lifecycle_df,
                months=months,
                initial_data_gb=initial_data_gb,
                monthly_growth_rate=monthly_growth_rate,
                pricing=pricing,
                standard_access_rate=standard_access_rate,
                nearline_read_rate=nearline_read_rate,
                coldline_read_rate=coldline_read_rate,
                archive_read_rate=archive_read_rate,
                lifecycle_rules=lifecycle_rules
            )
            
            # Generate appropriate filename
            if analysis_mode == "⚖️ Side-by-Side Comparison":
                filename = f"gcs_strategy_comparison_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            elif analysis_mode == "🤖 Autoclass Only":
                filename = f"gcs_autoclass_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            else:
                filename = f"gcs_lifecycle_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_buffer.getvalue(),
                file_name=filename,
                mime="application/pdf"
            )
