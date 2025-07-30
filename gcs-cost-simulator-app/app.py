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
from validation import run_comprehensive_tco_validation

# Import new modular components
from lifecycle_paths import LifecyclePathManager, LifecyclePath
from chart_components import ChartGenerator
from analysis_engine import AnalysisEngine
from data_processing import DataProcessor
from configuration_manager import ConfigurationManager
from pricing_engine import GCSPricingEngine, PricingOptimizer, RegionalPricingEngine, CostProjector


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
                index=1,  # Default to Nearline (matches GCS default)
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


def setup_access_pattern_config(terminal_storage_class):
    """Setup access pattern configuration with conditional logic based on terminal storage class"""
    st.sidebar.header("Monthly Access Rates")
    st.sidebar.markdown("*Access rates determine data lifecycle behavior*")
    
    # Standard access rate - always shown
    standard_access_rate = st.sidebar.slider(
        "Standard (% staying hot/month)", 0, 100, 40, 
        help="Percentage of Standard data that remains hot each month (rest becomes cold and transitions to Nearline after 30 days)"
    ) / 100

    # Initialize access rates with defaults
    nearline_read_rate = 0.20
    coldline_read_rate = 0.15  
    archive_read_rate = 0.15

    # Conditional UI logic: Hide controls when data won't reach those tiers
    if standard_access_rate == 1.0:
        st.sidebar.warning("🔒 **All data stays hot in Standard tier** - no cold tier transitions")
    else:
        nearline_read_rate = st.sidebar.slider("Nearline (% accessed/month)", 0, 100, 20, help="Percentage accessed monthly (moves back to Standard)") / 100
        
        # Only show coldline/archive controls if terminal storage class allows it
        if terminal_storage_class == "archive":
            if nearline_read_rate == 1.0:
                st.sidebar.warning("🔒 **All Nearline data re-promoted** - no deeper cold storage")
            else:
                coldline_read_rate = st.sidebar.slider("Coldline (% accessed/month)", 0, 100, 15, help="Percentage accessed monthly (moves back to Standard)") / 100
                
                if coldline_read_rate == 1.0:
                    st.sidebar.warning("🔒 **All Coldline data re-promoted** - no Archive storage")
                else:
                    archive_read_rate = st.sidebar.slider("Archive (% accessed/month)", 0, 100, 15, help="Percentage accessed monthly (moves back to Standard)") / 100

    # Visual feedback about tier blocking and terminal configuration
    if terminal_storage_class == "nearline":
        st.sidebar.info("💡 **Terminal Config**: Nearline Terminal - Data stops at Nearline tier")
        st.sidebar.caption("⚠️ Coldline and Archive tiers disabled by terminal configuration")
    elif standard_access_rate == 1.0:
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
    """Setup flexible lifecycle configuration with dropdown path selection"""
    lifecycle_rules = {"nearline_days": 30, "coldline_days": 90, "archive_days": 365}  # Default
    
    if analysis_mode in ["📋 Lifecycle Only", "⚖️ Side-by-Side Comparison"]:
        st.sidebar.header("📋 Flexible Lifecycle Rules")
        st.sidebar.markdown("*Choose your optimal transition path*")
        
        # Get available paths from the modular system
        path_options = LifecyclePathManager.get_grouped_options()
        
        # Path selection dropdown
        selected_path_name = st.sidebar.selectbox(
            "🛤️ Lifecycle Path",
            options=path_options,
            index=0,  # Default to first option (Full Linear Path)
            help="Choose your lifecycle transition strategy"
        )
        
        # Get selected path info using the modular system
        selected_path_id = LifecyclePathManager.get_path_by_name(selected_path_name)
        if selected_path_id:
            selected_path = LifecyclePathManager.get_path_info(selected_path_id)
            
            # Display path information
            st.sidebar.info(f"""
            **📋 {selected_path.name}**
            
            🛤️ **Path**: {selected_path.path}
            
            💡 **Description**: {selected_path.description}
            """)
            
            # Dynamic day inputs based on selected path
            st.sidebar.markdown("**⏰ Transition Timing**")
            
            # Create input fields based on path structure
            transition_days = []
            
            for i in range(len(selected_path.classes) - 1):
                from_class = selected_path.classes[i]
                to_class = selected_path.classes[i + 1]
                
                # Get default value
                default_value = selected_path.default_days[i] if i < len(selected_path.default_days) else 30
                
                # Create input field
                days = st.sidebar.number_input(
                    f"Days: {from_class} → {to_class}",
                    min_value=1,
                    max_value=3650,
                    value=default_value,
                    key=f"transition_{selected_path_id}_{i}",
                    help=f"Days after creation to transition from {from_class} to {to_class}"
                )
                
                transition_days.append(days)
            
            # Convert to lifecycle_rules format using modular system
            lifecycle_rules = LifecyclePathManager.convert_to_rules(selected_path_id, transition_days)
            
            # Show configuration status
            st.sidebar.success("✅ Lifecycle path configured")
            
            # Create timeline display
            timeline_text = ""
            current_day = 0
            for i, days in enumerate(transition_days):
                from_class = selected_path.classes[i]
                to_class = selected_path.classes[i + 1]
                if i == 0:
                    timeline_text += f"• Day 0-{days}: {from_class}\n"
                timeline_text += f"• Day {current_day + 1}+: {to_class}\n"
                current_day = days
            
            st.sidebar.markdown(f"**📅 Timeline:**\n{timeline_text}")
    
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
    
    # Summary metrics using modular formatting
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🤖 Autoclass Total Cost", DataProcessor.format_cost_value(autoclass_total_cost))
        autoclass_final_archive = autoclass_df["Archive (GB)"].iloc[-1]
        autoclass_final_total = autoclass_df["Total Data (GB)"].iloc[-1]
        autoclass_archive_pct = DataProcessor.safe_divide(autoclass_final_archive, autoclass_final_total, 0) * 100
        st.caption(f"Archive usage: {DataProcessor.format_percentage(autoclass_archive_pct)}")
    
    with col2:
        st.metric("📋 Lifecycle Total Cost", DataProcessor.format_cost_value(lifecycle_total_cost))
        lifecycle_final_archive = lifecycle_df["Archive (GB)"].iloc[-1] 
        lifecycle_final_total = lifecycle_df["Total Data (GB)"].iloc[-1]
        lifecycle_archive_pct = DataProcessor.safe_divide(lifecycle_final_archive, lifecycle_final_total, 0) * 100
        st.caption(f"Archive usage: {DataProcessor.format_percentage(lifecycle_archive_pct)}")
    
    with col3:
        if cost_difference > 0:
            st.metric("💰 Lifecycle Savings", DataProcessor.format_cost_value(cost_difference), f"{DataProcessor.format_percentage(savings_percentage)}")
        else:
            st.metric("💸 Autoclass Savings", DataProcessor.format_cost_value(abs(cost_difference)), f"{DataProcessor.format_percentage(savings_percentage)}")
    
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
    """Display detailed cost analysis for comparison using modular analysis engine"""
    st.markdown("**Cost Analysis & Insights**")
    
    # Use modular analysis engine for comprehensive comparison
    comparison_result = AnalysisEngine.compare_strategies(autoclass_df, lifecycle_df)
    
    # Cost breakdown comparison using analysis engine
    autoclass_cost_breakdown = comparison_result['autoclass_breakdown']
    lifecycle_cost_breakdown = comparison_result['lifecycle_breakdown']
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**🤖 Autoclass Breakdown**")
        st.write(f"Storage Cost: {DataProcessor.format_cost_value(autoclass_cost_breakdown['storage'])}")
        st.write(f"API Cost: {DataProcessor.format_cost_value(autoclass_cost_breakdown['api'])}")
        st.write(f"Management Fee: {DataProcessor.format_cost_value(autoclass_cost_breakdown['special'])}")
        st.write(f"**Total: {DataProcessor.format_cost_value(autoclass_cost_breakdown['total'])}**")
    
    with col2:
        st.markdown("**📋 Lifecycle Breakdown**")
        st.write(f"Storage Cost: {DataProcessor.format_cost_value(lifecycle_cost_breakdown['storage'])}")
        st.write(f"API Cost: {DataProcessor.format_cost_value(lifecycle_cost_breakdown['api'])}")
        st.write(f"Retrieval Cost: {DataProcessor.format_cost_value(lifecycle_cost_breakdown['special'])}")
        st.write(f"**Total: {DataProcessor.format_cost_value(lifecycle_cost_breakdown['total'])}**")
    
    # Enhanced insights using analysis engine
    st.markdown("**💡 Key Insights**")
    winner = comparison_result['winner']
    savings_pct = comparison_result['savings_percentage']
    cost_difference = comparison_result['cost_difference']
    
    if winner == "Lifecycle":
        st.success(f"""📋 **Lifecycle policy saves {DataProcessor.format_cost_value(cost_difference)} ({DataProcessor.format_percentage(savings_pct)})**
        
{comparison_result['recommendation']}""")
    else:
        st.success(f"""🤖 **Autoclass saves {DataProcessor.format_cost_value(cost_difference)} ({DataProcessor.format_percentage(savings_pct)})**
        
{comparison_result['recommendation']}""")
    
    # Generate strategic insights using analysis engine
    comparison_insights = AnalysisEngine.generate_comparison_insights(comparison_result)
    for insight in comparison_insights:
        st.write(f"• {insight}")


def display_single_strategy_results(df, analysis_mode, lifecycle_rules=None):
    """Enhanced display results for single strategy analysis with lifecycle path info"""
    strategy_name = "Autoclass" if analysis_mode == "🤖 Autoclass Only" else "Lifecycle"
    
    # Enhanced header with path information for lifecycle
    if analysis_mode == "📋 Lifecycle Only" and lifecycle_rules:
        path_name = lifecycle_rules.get("path_name", "Custom Path")
        path_description = lifecycle_rules.get("path_description", "")
        
        st.subheader(f"📊 {strategy_name} Monthly Breakdown")
        
        # Display selected path information
        st.info(f"""
        **🛤️ Selected Path**: {path_name}
        
        **💡 Strategy**: {path_description}
        
        **📅 Transition Timeline**: {create_lifecycle_timeline_display(lifecycle_rules)}
        """)
    else:
        st.subheader(f"📊 {strategy_name} Monthly Breakdown")

    # Create and display dataframe
    mode_key = "autoclass" if analysis_mode == "🤖 Autoclass Only" else "lifecycle"
    display_df = create_display_dataframe(df, mode_key)
    st.dataframe(display_df, use_container_width=True)

    # Enhanced summary with path-specific insights
    total_cost = df["Total Cost ($)"].sum()
    st.markdown(f"### 💰 Total {len(df)}-Month {strategy_name} Cost: **{format_cost_value(total_cost)}**")

    # Enhanced cost breakdown with lifecycle insights
    if analysis_mode == "📋 Lifecycle Only" and lifecycle_rules:
        display_lifecycle_insights(df, lifecycle_rules)
    else:
        display_standard_cost_breakdown(df, analysis_mode)


def create_lifecycle_timeline_display(lifecycle_rules):
    """Create a timeline display for the selected lifecycle path"""
    if not lifecycle_rules:
        return "Standard lifecycle progression"
    
    path_classes = lifecycle_rules.get("path_classes", ["Standard", "Archive"])
    transition_days = lifecycle_rules.get("transition_days", [365])
    
    timeline = ""
    for i, days in enumerate(transition_days):
        from_class = path_classes[i]
        to_class = path_classes[i + 1]
        
        if i == 0:
            timeline += f"Day 0-{days}: {from_class} → "
        timeline += f"Day {days}+: {to_class}"
        if i < len(transition_days) - 1:
            timeline += " → "
    
    return timeline


def display_lifecycle_insights(df, lifecycle_rules):
    """Display enhanced insights for lifecycle strategy with path-specific analysis"""
    st.subheader("💸 Lifecycle Strategy Analysis")
    
    # Basic cost breakdown
    total_cost = df["Total Cost ($)"].sum()
    total_storage = df["Storage Cost ($)"].sum()
    total_api = df["API Cost ($)"].sum()
    total_retrieval = df["Retrieval Cost ($)"].sum()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Storage Cost", format_cost_value(total_storage))
        st.metric("API Cost", format_cost_value(total_api))
    with col2:
        st.metric("Retrieval Cost", format_cost_value(total_retrieval))
    with col3:
        st.metric("**Total Cost**", f"**{format_cost_value(total_cost)}**")
    
    # Path-specific insights
    path_name = lifecycle_rules.get("path_name", "Custom Path")
    path_classes = lifecycle_rules.get("path_classes", ["Standard", "Archive"])
    
    st.subheader("🎯 Path-Specific Insights")
    
    # Calculate final distribution
    final_month = df.iloc[-1]
    storage_distribution = {
        "Standard": final_month["Standard (GB)"],
        "Nearline": final_month["Nearline (GB)"],
        "Coldline": final_month["Coldline (GB)"],
        "Archive": final_month["Archive (GB)"]
    }
    
    total_data = sum(storage_distribution.values())
    
    # Show distribution for classes in the path
    st.markdown("**📊 Final Storage Distribution:**")
    for storage_class in path_classes:
        if storage_class.lower() in ["standard", "nearline", "coldline", "archive"]:
            class_key = storage_class.title()
            if class_key in storage_distribution:
                amount = storage_distribution[class_key]
                percentage = (amount / total_data * 100) if total_data > 0 else 0
                st.metric(
                    f"{class_key} Storage",
                    f"{format_storage_value(amount)} ({percentage:.1f}%)"
                )
    
    # Path efficiency analysis
    st.subheader("⚡ Path Efficiency Analysis")
    
    # Calculate average cost per GB
    avg_cost_per_gb = total_cost / total_data if total_data > 0 else 0
    
    # Determine path efficiency based on final distribution
    archive_percentage = (storage_distribution["Archive"] / total_data * 100) if total_data > 0 else 0
    
    efficiency_rating = "🟢 Highly Efficient" if archive_percentage > 70 else \
                       "🟡 Moderately Efficient" if archive_percentage > 30 else \
                       "🔴 Conservative"
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Average Cost per GB", f"${avg_cost_per_gb:.4f}")
        st.metric("Archive Utilization", f"{archive_percentage:.1f}%")
    with col2:
        st.metric("Efficiency Rating", efficiency_rating)
        st.metric("Path Complexity", f"{len(path_classes)} storage tiers")
    
    # Recommendations based on path type
    display_path_recommendations(lifecycle_rules, storage_distribution, total_data)


def display_path_recommendations(lifecycle_rules, storage_distribution, total_data):
    """Display recommendations based on the selected lifecycle path"""
    st.subheader("💡 Optimization Recommendations")
    
    path_id = lifecycle_rules.get("path_id", "")
    
    recommendations = []
    
    # Analyze distribution and provide recommendations
    archive_percentage = (storage_distribution["Archive"] / total_data * 100) if total_data > 0 else 0
    standard_percentage = (storage_distribution["Standard"] / total_data * 100) if total_data > 0 else 0
    
    if "std_arc" in path_id:  # Direct Standard → Archive
        if standard_percentage > 50:
            recommendations.append("⚡ Consider reducing transition time to Archive for better cost optimization")
        else:
            recommendations.append("✅ Direct Archive transition is working efficiently")
    
    elif "std_cld" in path_id:  # Standard → Coldline paths
        coldline_percentage = (storage_distribution["Coldline"] / total_data * 100) if total_data > 0 else 0
        if coldline_percentage > 60:
            recommendations.append("✅ Coldline strategy is effectively reducing storage costs")
        if standard_percentage > 30:
            recommendations.append("⚡ Consider faster transition to Coldline for additional savings")
    
    elif "full_linear" in path_id:  # Full linear path
        if archive_percentage < 30:
            recommendations.append("⚡ Consider more aggressive transition timing for better cost optimization")
        else:
            recommendations.append("✅ Balanced progression through all storage tiers")
    
    # General recommendations
    if standard_percentage > 40:
        recommendations.append("💡 High Standard storage usage - consider faster transitions for cost savings")
    
    if archive_percentage > 80:
        recommendations.append("🎯 Excellent archive utilization - optimal for long-term storage")
    
    # Display recommendations
    if recommendations:
        for rec in recommendations:
            st.markdown(f"- {rec}")
    else:
        st.markdown("- ✅ Your current lifecycle path appears well-optimized for your data pattern")


def display_standard_cost_breakdown(df, analysis_mode):
    """Display standard cost breakdown for non-lifecycle strategies"""
    st.subheader("💸 Cost Breakdown Summary")
    total_cost = df["Total Cost ($)"].sum()
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


def setup_object_characteristics_config(analysis_mode):
    """Setup object characteristics configuration including size inputs"""
    st.sidebar.header("Object Characteristics")
    
    # First render the percentage slider
    percent_large_objects = st.sidebar.slider(
        "% of Data >128 KiB (Autoclass Eligible)", 
        0, 100, 90
    ) / 100.0
    
    # Add validation warning for Autoclass eligibility
    if analysis_mode in ["🤖 Autoclass Only", "⚖️ Side-by-Side Comparison"]:
        st.sidebar.warning("⚠️ **Autoclass Requirement**: Only objects ≥128 KiB are eligible for automatic transitions")
    
    # Default values
    avg_object_size_large_kib = 512
    avg_object_size_small_kib = 64
    
    # Show object size inputs based on the percentage
    if percent_large_objects > 0:  # Show large object size input if there's any eligible data
        max_object_size_kib = 5 * 1024 * 1024  # GCS maximum: 5 TiB in KiB
        avg_object_size_large_kib = st.sidebar.number_input(
            "Average Object Size for Data ≥128 KiB (KiB)", 
            min_value=128, 
            max_value=max_object_size_kib,
            value=512, 
            help="Autoclass-eligible objects must be at least 128 KiB. GCS maximum object size is 5 TiB."
        )

    if percent_large_objects < 1:  # Show small object size input if there's any non-eligible data
        avg_object_size_small_kib = st.sidebar.number_input(
            "Average Object Size for Data <128 KiB (KiB)", 
            min_value=1, max_value=127, value=64,
            help="Objects <128 KiB remain in Standard storage permanently in Autoclass"
        )
    
    return {
        "percent_large_objects": percent_large_objects,
        "avg_object_size_large_kib": avg_object_size_large_kib,
        "avg_object_size_small_kib": avg_object_size_small_kib
    }


def main():
    """Main application function"""
    # Setup UI configuration
    analysis_mode, terminal_storage_class = setup_ui_configuration()
    
    # Setup pricing configuration
    pricing = setup_pricing_configuration()
    
    # Setup sidebar configuration (excluding object_characteristics which we'll handle separately)
    sidebar_config_sections = {k: v for k, v in UI_CONFIG["sidebar"].items() if k != "object_characteristics"}
    sidebar_config = render_sidebar_config(sidebar_config_sections)
    
    # Setup object characteristics with integrated object size inputs
    object_config = setup_object_characteristics_config(analysis_mode)
    
    # Merge the configurations
    sidebar_config.update(object_config)
    
    # Setup access patterns
    access_rates = setup_access_pattern_config(terminal_storage_class)
    
    # Setup lifecycle configuration
    lifecycle_rules = setup_lifecycle_configuration(analysis_mode)
    
    # Build complete configuration
    config = {
        **sidebar_config,
        "pricing": pricing,
        "access_rates": access_rates
    }
    
    # Enhanced configuration validation using modular ConfigurationManager
    st.subheader("🔍 Enhanced Configuration Validation")
    
    # Validate simulation configuration
    sim_config = {
        'simulation_months': config['months'],
        'initial_data_gb': config['initial_data_gb'],
        'monthly_upload_gb': config.get('monthly_upload_gb', 100),  # Default if not present
        'data_growth_rate': config.get('monthly_growth_rate', 0) * 12  # Convert to annual
    }
    
    is_valid, validation_errors = ConfigurationManager.validate_simulation_config(sim_config)
    if not is_valid:
        for error in validation_errors:
            st.error(f"⚠️ Configuration Error: {error}")
        st.stop()
    
    # Validate access pattern if present
    if 'access_rates' in config:
        access_pattern = {
            'monthly_delete_gb': config.get('monthly_delete_gb', 0),
            'monthly_read_gb': config.get('monthly_read_gb', 50),
            'monthly_read_ops': config.get('monthly_read_ops', 1000)
        }
        
        is_access_valid, access_errors = ConfigurationManager.validate_access_pattern(access_pattern)
        if not is_access_valid:
            for error in access_errors:
                st.warning(f"⚠️ Access Pattern Warning: {error}")
    
    # Show configuration impact estimation
    impact_analysis = ConfigurationManager.estimate_configuration_impact(sim_config)
    if impact_analysis:
        with st.expander("💡 Configuration Impact Analysis", expanded=False):
            for category, impact in impact_analysis.items():
                st.info(f"**{category.title()}**: {impact}")
    
    # Show progress for longer simulations
    if config["months"] > 36:
        st.info(f"⏳ Running {config['months']}-month simulation... This may take a moment for longer periods.")

    # Run comprehensive TCO validation (original validation still included)
    st.subheader("🔍 TCO Configuration Validation")
    warnings, errors = run_comprehensive_tco_validation(analysis_mode, config, terminal_storage_class, lifecycle_rules)
    
    # Display validation results
    if errors:
        for error in errors:
            st.error(error)
        st.stop()  # Stop execution if there are critical errors
    
    if warnings:
        with st.expander("⚠️ Configuration Warnings", expanded=len(warnings) > 2):
            for warning in warnings:
                st.warning(warning)
    
    # Run simulations
    with st.spinner("Running simulation...") if config["months"] > 24 else st.empty():
        autoclass_df, lifecycle_df = run_simulations(analysis_mode, config, terminal_storage_class, lifecycle_rules)
    
    # Display results based on analysis mode
    if analysis_mode == "⚖️ Side-by-Side Comparison":
        display_comparison_results(autoclass_df, lifecycle_df)
        ChartGenerator.create_comparison_dashboard(autoclass_df, lifecycle_df)
        
        # Key insights for comparison mode handled in display_cost_analysis
        
    else:
        # Single strategy results
        df = autoclass_df if analysis_mode == "🤖 Autoclass Only" else lifecycle_df
        display_single_strategy_results(df, analysis_mode, lifecycle_rules if analysis_mode == "📋 Lifecycle Only" else None)
        ChartGenerator.create_single_strategy_charts(df, analysis_mode)
        
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
                    st.info("ℹ️ Autoclass management fees represent a significant portion of total costs")
                elif special_percentage < 5:
                    st.success("✅ Autoclass management fees are minimal - excellent choice for dynamic access patterns")
            else:  # Lifecycle Only
                if special_percentage > 20:
                    st.info("ℹ️ Retrieval costs represent a significant portion of total costs")
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
