# utils.py - Utility functions for formatting and configuration

import streamlit as st
from config import DEFAULT_PRICING


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


def format_small_number(value):
    """Format small numbers appropriately"""
    if value < 0.000001:  # Less than 1 millionth
        return f"{value:.2e}"  # Scientific notation
    elif value < 0.001:   # Less than 1 thousandth
        return f"{value:.7f}".rstrip('0').rstrip('.')  # Remove trailing zeros
    else:
        return f"{value:.6f}".rstrip('0').rstrip('.')


def calculate_upload_operations(object_count: int, avg_object_size_kib: float) -> int:
    """
    Calculate the number of API operations for uploading objects to GCS.
    
    For large objects (>32 MiB), GCS uses multipart uploads which require
    multiple API operations: initiate + upload parts + complete.
    
    Args:
        object_count: Number of objects to upload
        avg_object_size_kib: Average object size in KiB
    
    Returns:
        Total number of Class A operations required
    """
    if object_count == 0:
        return 0
    
    # GCS multipart upload threshold: 32 MiB (32,768 KiB)
    multipart_threshold_kib = 32 * 1024
    
    if avg_object_size_kib <= multipart_threshold_kib:
        # Simple upload: 1 operation per object
        return object_count
    else:
        # Multipart upload calculation
        # Each part is typically 16 MiB for optimal performance
        part_size_kib = 16 * 1024  # 16 MiB in KiB
        
        # Operations per object: initiate (1) + parts (n) + complete (1)
        parts_per_object = max(1, int((avg_object_size_kib + part_size_kib - 1) // part_size_kib))
        operations_per_object = 1 + parts_per_object + 1  # initiate + parts + complete
        
        return object_count * operations_per_object


def get_nested_value(dictionary, key_path):
    """Get nested dictionary value using dot notation (e.g., 'operations.class_a')"""
    keys = key_path.split('.')
    value = dictionary
    for key in keys:
        value = value[key]
    return value


def render_config_section(section_config, current_pricing):
    """Dynamically render configuration sections based on schema"""
    config_values = {}
    
    for section_key, section_data in section_config["sections"].items():
        st.markdown(f"**{section_data['title']}**")
        
        for field_key, field_config in section_data["fields"].items():
            default_path = field_config["default"]
            default_value = get_nested_value(current_pricing, default_path)
            
            value = st.number_input(
                field_config["label"],
                min_value=0.0,
                value=default_value,
                step=field_config["step"],
                format=field_config["format"]
            )
            
            config_values[field_key] = value
    
    return config_values


def build_pricing_config(config_values):
    """Build pricing configuration from UI values with Autoclass-specific adjustments"""
    base_pricing = {
        "standard": {"storage": config_values["standard_storage_price"], "min_storage_days": 0},
        "nearline": {"storage": config_values["nearline_storage_price"], "min_storage_days": 30},
        "coldline": {"storage": config_values["coldline_storage_price"], "min_storage_days": 90},
        "archive": {"storage": config_values["archive_storage_price"], "min_storage_days": 365},
        "operations": {
            "class_a": config_values["class_a_price"],
            "class_b": config_values["class_b_price"]
        },
        "lifecycle_transitions": {
            "standard_to_nearline": config_values["std_to_nearline_price"],
            "nearline_to_coldline": config_values["nearline_to_coldline_price"],
            "coldline_to_archive": config_values["coldline_to_archive_price"]
        },
        "autoclass_fee_per_1000_objects_per_month": config_values["autoclass_fee_price"],
        "retrieval_costs": {
            "nearline": config_values["nearline_retrieval_price"],
            "coldline": config_values["coldline_retrieval_price"],
            "archive": config_values["archive_retrieval_price"]
        },
        "early_deletion_fees": {
            "nearline": config_values["nearline_storage_price"],
            "coldline": config_values["coldline_storage_price"],
            "archive": config_values["archive_storage_price"]
        }
    }
    
    # Add Autoclass-specific pricing adjustments
    base_pricing["autoclass_adjustments"] = {
        "no_retrieval_fees": True,  # Autoclass doesn't charge retrieval fees
        "no_early_deletion_fees": True,  # Autoclass doesn't charge early deletion fees
        "standard_rate_operations": True,  # All operations charged at Standard rate
        "transition_operation_charges": {
            "to_standard_from_nearline": False,  # No Class A charge
            "to_standard_from_coldline": True,   # Class A charge applies
            "to_standard_from_archive": True     # Class A charge applies
        }
    }
    
    return base_pricing


def render_sidebar_config(sidebar_config):
    """Render sidebar configuration sections"""
    config_values = {}
    
    for section_name, section_fields in sidebar_config.items():
        # Convert section_name to readable title
        section_title = section_name.replace('_', ' ').title()
        st.sidebar.header(section_title)
        
        for field_key, field_config in section_fields.items():
            field_type = field_config["type"]
            
            if field_type == "slider":
                value = st.sidebar.slider(
                    field_config["label"],
                    field_config["min"],
                    field_config["max"],
                    field_config["default"],
                    help=field_config.get("help")
                )
            elif field_type == "number_input":
                # Ensure type consistency between value and step
                default_value = field_config["default"]
                step_value = field_config.get("step", 1.0)
                min_value = field_config.get("min", 0.0)
                max_value = field_config.get("max")
                
                # Convert to consistent types based on whether step is integer or float
                if isinstance(step_value, int) or step_value == int(step_value):
                    # Use integer types
                    step_value = int(step_value)
                    default_value = int(default_value)
                    min_value = int(min_value) if min_value is not None else 0
                    max_value = int(max_value) if max_value is not None else None
                else:
                    # Use float types
                    step_value = float(step_value)
                    default_value = float(default_value)
                    min_value = float(min_value) if min_value is not None else 0.0
                    max_value = float(max_value) if max_value is not None else None
                
                value = st.sidebar.number_input(
                    field_config["label"],
                    min_value=min_value,
                    max_value=max_value,
                    value=default_value,
                    step=step_value,
                    help=field_config.get("help")
                )
            
            # Apply conversions
            if field_config.get("convert") == "percentage":
                value = value / 100
                
            config_values[field_key] = value
    
    return config_values


def create_display_dataframe(df, mode):
    """Create display dataframe with formatted columns based on mode"""
    if mode == "autoclass":
        display_columns = [
            "Month", "Standard (Formatted)", "Nearline (Formatted)", "Coldline (Formatted)", 
            "Archive (Formatted)", "Total Data (Formatted)", "Total Eligible Objects", 
            "Total Non-Eligible Objects", "Autoclass Fee (Formatted)", "Storage Cost (Formatted)", 
            "Upload API Cost (Formatted)", "User API Cost (Formatted)", "Transition API Cost (Formatted)",
            "API Cost (Formatted)", "Total Cost (Formatted)"
        ]
        column_names = [
            "Month", "Standard", "Nearline", "Coldline", "Archive", "Total Data", 
            "Eligible Objects", "Non-Eligible Objects", "Autoclass Fee", "Storage Cost", 
            "Upload API", "User API", "Transition API", "Total API", "Total Cost"
        ]
    elif mode == "lifecycle":
        display_columns = [
            "Month", "Standard (Formatted)", "Nearline (Formatted)", "Coldline (Formatted)", 
            "Archive (Formatted)", "Total Data (Formatted)", "Total Objects", 
            "Retrieval Cost (Formatted)", "Storage Cost (Formatted)", 
            "Upload API Cost (Formatted)", "User API Cost (Formatted)", "Transition API Cost (Formatted)",
            "API Cost (Formatted)", "Total Cost (Formatted)"
        ]
        column_names = [
            "Month", "Standard", "Nearline", "Coldline", "Archive", "Total Data", 
            "Total Objects", "Retrieval Cost", "Storage Cost", 
            "Upload API", "User API", "Transition API", "Total API", "Total Cost"
        ]
    else:  # comparison
        # Create comparison data
        autoclass_df, lifecycle_df = df
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
        return comparison_data
    
    display_df = df[display_columns].copy()
    display_df.columns = column_names
    return display_df


def display_pricing_summary(pricing):
    """Display current pricing summary in sidebar"""
    st.sidebar.markdown("**Current Pricing Summary:**")
    st.sidebar.markdown(f"- Standard: ${pricing['standard']['storage']:.4f}/GB/month")
    st.sidebar.markdown(f"- Nearline: ${pricing['nearline']['storage']:.4f}/GB/month")
    st.sidebar.markdown(f"- Coldline: ${pricing['coldline']['storage']:.4f}/GB/month") 
    st.sidebar.markdown(f"- Archive: ${pricing['archive']['storage']:.4f}/GB/month")
    st.sidebar.markdown(f"- Class A Ops: ${format_small_number(pricing['operations']['class_a'])}/op")
    st.sidebar.markdown(f"- Class B Ops: ${format_small_number(pricing['operations']['class_b'])}/op")
    st.sidebar.markdown(f"- Autoclass Fee: ${pricing['autoclass_fee_per_1000_objects_per_month']:.4f}/1K objects/month")
