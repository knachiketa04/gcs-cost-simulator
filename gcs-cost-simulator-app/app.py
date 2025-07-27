# app.py - Main Streamlit application (REFACTORED)

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from config import DEFAULT_PRICING, UI_CONFIG
from utils import (format_storage_value, format_cost_value, get_storage_unit_and_value, 
                  get_cost_unit_and_value, render_config_section, build_pricing_config,
                  render_sidebar_config, create_display_dataframe, display_pricing_summary)
from simulation import simulate_storage_strategy
from reports import generate_pdf_report, generate_csv_export


def setup_ui_configuration():
    """Setup main UI configuration with centralized logic"""
    st.title("GCS Storage Strategy Simulator")
    st.markdown("*Compare Autoclass vs Lifecycle Policies for optimal storage cost planning*")

    # Analysis Mode Selection
    st.subheader("📊 Analysis Mode")
    analysis_mode = st.radio(
        "Choose analysis type:",
        ["🤖 Autoclass Only", "📋 Lifecycle Only", "⚖️ Side-by-Side Comparison"],
        index=2,  # Default to comparison
        horizontal=True
    )

    # Autoclass Configuration
    terminal_storage_class = "archive"  # Default
    if analysis_mode in ["🤖 Autoclass Only", "⚖️ Side-by-Side Comparison"]:
        st.subheader("🎛️ Autoclass Configuration")
        col1, col2 = st.columns(2)
        with col1:
            terminal_storage_class = st.selectbox(
                "Terminal Storage Class",
                ["nearline", "archive"],
                index=0,  # Default to Nearline (matches GCS default)
                help="**Nearline**: Objects stop at Nearline storage (GCS default). **Archive**: Full progression through all storage tiers."
            )
        with col2:
            st.info(f"**Selected**: {terminal_storage_class.title()} Terminal\n\n"
                    f"{'Objects will transition: Standard → Nearline (stop)' if terminal_storage_class == 'nearline' else 'Objects will transition: Standard → Nearline → Coldline → Archive'}")

    return analysis_mode, terminal_storage_class


def setup_pricing_configuration():
    """Setup pricing configuration with data-driven UI"""
    st.sidebar.header("💰 Pricing Configuration")
    st.sidebar.markdown("*Default: Iowa (us-central1) Regional Autoclass*")

    with st.sidebar.expander("Customize Pricing", expanded=False):
        config_values = render_config_section(UI_CONFIG["pricing"], DEFAULT_PRICING)
    
    pricing = build_pricing_config(config_values)
    display_pricing_summary(pricing)
    return pricing


def setup_access_pattern_config():
    """Setup access pattern configuration with conditional logic"""
    st.sidebar.header("Monthly Access Rates")
    st.sidebar.markdown("*Access rates determine data lifecycle behavior*")
    
    # Standard access rate - always shown
    standard_access_rate = st.sidebar.slider(
        "Standard (% staying hot/month)", 0, 100, 30, 
        help="Percentage of Standard data that remains hot each month (rest becomes cold and transitions to Nearline after 30 days)"
    ) / 100

    # Initialize access rates with defaults
    nearline_read_rate = 0.20
    coldline_read_rate = 0.30  
    archive_read_rate = 0.10

    # Conditional UI logic: Hide controls when data won't reach those tiers
    if standard_access_rate == 1.0:
        st.sidebar.warning("🔒 **All data stays hot in Standard tier** - no cold tier transitions")
    else:
        nearline_read_rate = st.sidebar.slider("Nearline (% accessed/month)", 0, 100, 20, help="Percentage accessed monthly (moves back to Standard)") / 100
        
        if nearline_read_rate == 1.0:
            st.sidebar.warning("🔒 **All Nearline data re-promoted** - no deeper cold storage")
        else:
            coldline_read_rate = st.sidebar.slider("Coldline (% accessed/month)", 0, 100, 30, help="Percentage accessed monthly (moves back to Standard)") / 100
            
            if coldline_read_rate == 1.0:
                st.sidebar.warning("🔒 **All Coldline data re-promoted** - no Archive storage")
            else:
                archive_read_rate = st.sidebar.slider("Archive (% accessed/month)", 0, 100, 10, help="Percentage accessed monthly (moves back to Standard)") / 100

    # Visual feedback about tier blocking
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

    return {
        "standard": standard_access_rate,
        "nearline": nearline_read_rate,
        "coldline": coldline_read_rate,
        "archive": archive_read_rate
    }


def setup_lifecycle_configuration(analysis_mode):
    """Setup lifecycle configuration when needed"""
    lifecycle_rules = {"nearline_days": 30, "coldline_days": 90, "archive_days": 365}  # Default
    
    if analysis_mode in ["📋 Lifecycle Only", "⚖️ Side-by-Side Comparison"]:
        st.sidebar.header("📋 Lifecycle Rules")
        st.sidebar.markdown("*Configure custom transition rules*")
        
        lifecycle_rules["nearline_days"] = st.sidebar.number_input("Days to Nearline", min_value=1, max_value=365, value=30, help="Days after creation to move to Nearline")
        lifecycle_rules["coldline_days"] = st.sidebar.number_input("Days to Coldline", min_value=lifecycle_rules["nearline_days"], max_value=365, value=90, help="Days after creation to move to Coldline")
        lifecycle_rules["archive_days"] = st.sidebar.number_input("Days to Archive", min_value=lifecycle_rules["coldline_days"], max_value=3650, value=365, help="Days after creation to move to Archive")
        
        st.sidebar.info(f"""
        **Lifecycle Flow:**
        • Standard → Nearline: {lifecycle_rules["nearline_days"]} days
        • Nearline → Coldline: {lifecycle_rules["coldline_days"]} days  
        • Coldline → Archive: {lifecycle_rules["archive_days"]} days
        """)
    
    return lifecycle_rules


def run_simulations(analysis_mode, config, terminal_storage_class, lifecycle_rules):
    """Run simulations based on analysis mode"""
    autoclass_df = None
    lifecycle_df = None
    
    # Build simulation parameters
    params = {
        "initial_data_gb": config["initial_data_gb"],
        "monthly_growth_rate": config["monthly_growth_rate"],
        "avg_object_size_large_kib": config.get("avg_object_size_large_kib", 512),
        "avg_object_size_small_kib": config.get("avg_object_size_small_kib", 64),
        "percent_large_objects": config["percent_large_objects"],
        "months": config["months"],
        "access_rates": config["access_rates"],
        "reads": config["reads"],
        "writes": config["writes"],
        "pricing": config["pricing"]
    }
    
    if analysis_mode in ["🤖 Autoclass Only", "⚖️ Side-by-Side Comparison"]:
        autoclass_config = {
            "type": "autoclass",
            "terminal_storage_class": terminal_storage_class
        }
        autoclass_df = simulate_storage_strategy(params, autoclass_config)
    
    if analysis_mode in ["📋 Lifecycle Only", "⚖️ Side-by-Side Comparison"]:
        lifecycle_config = {
            "type": "lifecycle",
            "lifecycle_rules": lifecycle_rules
        }
        lifecycle_df = simulate_storage_strategy(params, lifecycle_config)
    
    return autoclass_df, lifecycle_df


def display_comparison_results(autoclass_df, lifecycle_df):
    """Display side-by-side comparison results"""
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
    comparison_data = create_display_dataframe((autoclass_df, lifecycle_df), "comparison")
    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, use_container_width=True)
    
    # Detailed breakdown tabs
    tab1, tab2, tab3 = st.tabs(["🤖 Autoclass Details", "📋 Lifecycle Details", "📈 Cost Analysis"])
    
    with tab1:
        st.markdown("**Autoclass Strategy Details**")
        autoclass_display_df = create_display_dataframe(autoclass_df, "autoclass")
        st.dataframe(autoclass_display_df, use_container_width=True)
    
    with tab2:
        st.markdown("**Lifecycle Policy Details**")
        lifecycle_display_df = create_display_dataframe(lifecycle_df, "lifecycle")
        st.dataframe(lifecycle_display_df, use_container_width=True)
    
    with tab3:
        display_cost_analysis(autoclass_df, lifecycle_df)


def display_cost_analysis(autoclass_df, lifecycle_df):
    """Display detailed cost analysis for comparison"""
    st.markdown("**Cost Analysis & Insights**")
    
    # Cost breakdown comparison
    autoclass_storage = autoclass_df["Storage Cost ($)"].sum()
    autoclass_api = autoclass_df["API Cost ($)"].sum()
    autoclass_fee = autoclass_df["Autoclass Fee ($)"].sum()
    autoclass_total_cost = autoclass_df["Total Cost ($)"].sum()
    
    lifecycle_storage = lifecycle_df["Storage Cost ($)"].sum()
    lifecycle_api = lifecycle_df["API Cost ($)"].sum()
    lifecycle_retrieval = lifecycle_df["Retrieval Cost ($)"].sum()
    lifecycle_total_cost = lifecycle_df["Total Cost ($)"].sum()
    
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
    cost_difference = autoclass_total_cost - lifecycle_total_cost
    savings_percentage = (abs(cost_difference) / max(autoclass_total_cost, lifecycle_total_cost)) * 100
    
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


def display_single_strategy_results(analysis_mode, df):
    """Display results for single strategy analysis"""
    strategy_name = "Autoclass" if analysis_mode == "🤖 Autoclass Only" else "Lifecycle"
    st.subheader(f"📊 {strategy_name} Monthly Breakdown")

    # Create and display dataframe
    mode_key = "autoclass" if analysis_mode == "🤖 Autoclass Only" else "lifecycle"
    display_df = create_display_dataframe(df, mode_key)
    st.dataframe(display_df, use_container_width=True)

    # Summary
    total_cost = df["Total Cost ($)"].sum()
    st.markdown(f"### 💰 Total {len(df)}-Month {strategy_name} Cost: **{format_cost_value(total_cost)}**")

    # Cost Breakdown Summary
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


def create_comparison_charts(autoclass_df, lifecycle_df):
    """Create side-by-side comparison charts"""
    st.subheader("📈 Side-by-Side Visual Comparison")
    
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


def create_single_strategy_charts(df, analysis_mode):
    """Create charts for single strategy analysis"""
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


def display_export_options(analysis_mode, autoclass_df=None, lifecycle_df=None, 
                         months=12, initial_data_gb=0, monthly_growth_rate=0, 
                         pricing=None, access_rates=None, lifecycle_rules=None):
    """Display export options for CSV and PDF"""
    st.subheader("📦 Export Reports")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📊 CSV Data Export**")
        csv_buffer, filename_suffix = generate_csv_export(analysis_mode, autoclass_df, lifecycle_df)
        
        st.download_button(
            label="📄 Download CSV",
            data=csv_buffer.getvalue(),
            file_name=f"gcs_{filename_suffix}_simulation_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
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
                    standard_access_rate=access_rates["standard"],
                    nearline_read_rate=access_rates["nearline"],
                    coldline_read_rate=access_rates["coldline"],
                    archive_read_rate=access_rates["archive"],
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


def main():
    """Main application function"""
    # Setup UI configuration
    analysis_mode, terminal_storage_class = setup_ui_configuration()
    
    # Setup pricing configuration
    pricing = setup_pricing_configuration()
    
    # Setup sidebar configuration
    sidebar_config = render_sidebar_config(UI_CONFIG["sidebar"])
    
    # Setup access patterns
    access_rates = setup_access_pattern_config()
    
    # Setup lifecycle configuration
    lifecycle_rules = setup_lifecycle_configuration(analysis_mode)
    
    # Handle object size configuration (conditional UI)
    avg_object_size_large_kib = 512  # Default value
    avg_object_size_small_kib = 64   # Default value

    if sidebar_config["percent_large_objects"] > 0:  # Show large object size input if there's any eligible data
        avg_object_size_large_kib = st.sidebar.number_input("Average Object Size for Data >128 KiB (KiB)", min_value=129, value=512)

    if sidebar_config["percent_large_objects"] < 1:  # Show small object size input if there's any non-eligible data
        avg_object_size_small_kib = st.sidebar.number_input("Average Object Size for Data ≤128 KiB (KiB)", min_value=1, max_value=128, value=64)
    
    # Build complete configuration
    config = {
        **sidebar_config,
        "avg_object_size_large_kib": avg_object_size_large_kib,
        "avg_object_size_small_kib": avg_object_size_small_kib,
        "pricing": pricing,
        "access_rates": access_rates
    }
    
    # Show progress for longer simulations
    if config["months"] > 36:
        st.info(f"⏳ Running {config['months']}-month simulation... This may take a moment for longer periods.")

    # Run simulations
    with st.spinner("Running simulation...") if config["months"] > 24 else st.empty():
        autoclass_df, lifecycle_df = run_simulations(analysis_mode, config, terminal_storage_class, lifecycle_rules)
    
    # Display results based on analysis mode
    if analysis_mode == "⚖️ Side-by-Side Comparison":
        display_comparison_results(autoclass_df, lifecycle_df)
        create_comparison_charts(autoclass_df, lifecycle_df)
        
        # Key insights for comparison mode handled in display_cost_analysis
        
    else:
        # Single strategy results
        df = autoclass_df if analysis_mode == "🤖 Autoclass Only" else lifecycle_df
        display_single_strategy_results(analysis_mode, df)
        create_single_strategy_charts(df, analysis_mode)
        
        # Key insights for single strategy
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
            avg_monthly_cost = total_cost / config["months"]
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
    
    # Display export options
    display_export_options(
        analysis_mode, autoclass_df, lifecycle_df, 
        config["months"], config["initial_data_gb"], config["monthly_growth_rate"],
        pricing, access_rates, lifecycle_rules
    )


if __name__ == "__main__":
    main()
