# ui_components.py - Reusable UI components for GCS Cost Simulator
from typing import Dict, Any, Optional, List
import streamlit as st
import pandas as pd
from utils import format_storage_value, format_cost_value


class UIComponent:
    """Base class for reusable UI components"""
    
    @staticmethod
    def render_metric_grid(metrics: Dict[str, Any], columns: int = 3):
        """Render metrics in responsive grid layout"""
        cols = st.columns(columns)
        for i, (label, value) in enumerate(metrics.items()):
            with cols[i % columns]:
                st.metric(label, value)
    
    @staticmethod
    def render_comparison_table(data: Dict, title: str):
        """Render comparison table with consistent styling"""
        st.subheader(title)
        comparison_df = pd.DataFrame(data)
        st.dataframe(comparison_df, use_container_width=True)
    
    @staticmethod
    def render_info_card(title: str, content: str, icon: str = "ℹ️"):
        """Render styled info card with consistent formatting"""
        st.info(f"""
        **{icon} {title}**
        
        {content}
        """)
    
    @staticmethod
    def render_analysis_mode_selector():
        """Render analysis mode selection UI component"""
        st.subheader("📊 Analysis Mode")
        analysis_mode = st.radio(
            "Choose analysis type:",
            ["🤖 Autoclass Only", "📋 Lifecycle Only", "⚖️ Side-by-Side Comparison"],
            index=2,  # Default to comparison
            horizontal=True
        )
        return analysis_mode
    
    @staticmethod
    def render_terminal_storage_selector(analysis_mode: str):
        """Render terminal storage class selector for Autoclass"""
        terminal_storage_class = "archive"  # Default
        
        if analysis_mode in ["🤖 Autoclass Only", "⚖️ Side-by-Side Comparison"]:
            st.subheader("🎛️ Autoclass Configuration")
            col1, col2 = st.columns(2)
            with col1:
                terminal_storage_class = st.selectbox(
                    "Terminal Storage Class",
                    ["nearline", "archive"],
                    index=1,  # Default to Archive
                    help="**Nearline**: Objects stop at Nearline storage (GCS default). **Archive**: Full progression through all storage tiers."
                )
            with col2:
                description = (
                    'Objects will transition: Standard → Nearline (stop)' 
                    if terminal_storage_class == 'nearline' 
                    else 'Objects will transition: Standard → Nearline → Coldline → Archive'
                )
                st.info(f"**Selected**: {terminal_storage_class.title()} Terminal\n\n{description}")
        
        return terminal_storage_class


class AnalysisComponents:
    """Components for analysis display and insights"""
    
    @staticmethod
    def render_cost_breakdown(costs: Dict[str, float], title: str):
        """Render cost breakdown with percentages and formatting"""
        st.markdown(f"**{title}**")
        total = sum(costs.values())
        
        breakdown_metrics = {}
        for component, amount in costs.items():
            percentage = (amount / total * 100) if total > 0 else 0
            breakdown_metrics[component] = f"{format_cost_value(amount)} ({percentage:.1f}%)"
        
        UIComponent.render_metric_grid(breakdown_metrics)
    
    @staticmethod
    def render_insights_panel(insights: List[str], recommendations: List[str]):
        """Render insights and recommendations in two-column layout"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**💡 Key Insights**")
            for insight in insights:
                st.markdown(f"• {insight}")
        
        with col2:
            st.markdown("**🎯 Recommendations**") 
            for rec in recommendations:
                st.markdown(f"• {rec}")
    
    @staticmethod
    def render_comparison_summary(autoclass_cost: float, lifecycle_cost: float):
        """Render side-by-side comparison summary metrics"""
        cost_difference = autoclass_cost - lifecycle_cost
        savings_percentage = (abs(cost_difference) / max(autoclass_cost, lifecycle_cost)) * 100
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🤖 Autoclass Total Cost", format_cost_value(autoclass_cost))
        
        with col2:
            st.metric("📋 Lifecycle Total Cost", format_cost_value(lifecycle_cost))
        
        with col3:
            if cost_difference > 0:
                st.metric("💰 Lifecycle Savings", format_cost_value(cost_difference), f"{savings_percentage:.1f}%")
            else:
                st.metric("💸 Autoclass Savings", format_cost_value(abs(cost_difference)), f"{savings_percentage:.1f}%")
    
    @staticmethod
    def render_storage_distribution_metrics(storage_dist: Dict[str, float], path_classes: List[str]):
        """Render storage distribution metrics for specific path classes"""
        st.markdown("**📊 Final Storage Distribution:**")
        
        total_data = sum(storage_dist.values())
        distribution_metrics = {}
        
        for storage_class in path_classes:
            class_key = storage_class.title()
            if class_key in storage_dist:
                amount = storage_dist[class_key]
                percentage = (amount / total_data * 100) if total_data > 0 else 0
                distribution_metrics[f"{class_key} Storage"] = f"{format_storage_value(amount)} ({percentage:.1f}%)"
        
        UIComponent.render_metric_grid(distribution_metrics, columns=2)
    
    @staticmethod
    def render_efficiency_analysis(avg_cost_per_gb: float, archive_percentage: float, 
                                 path_complexity: int):
        """Render path efficiency analysis metrics"""
        st.subheader("⚡ Path Efficiency Analysis")
        
        # Determine efficiency rating based on archive percentage
        if archive_percentage > 70:
            efficiency_rating = "🟢 Highly Efficient"
        elif archive_percentage > 30:
            efficiency_rating = "🟡 Moderately Efficient"  
        else:
            efficiency_rating = "🔴 Conservative"
        
        efficiency_metrics = {
            "Average Cost per GB": f"${avg_cost_per_gb:.4f}",
            "Archive Utilization": f"{archive_percentage:.1f}%",
            "Efficiency Rating": efficiency_rating,
            "Path Complexity": f"{path_complexity} storage tiers"
        }
        
        UIComponent.render_metric_grid(efficiency_metrics, columns=2)


class ValidationComponents:
    """Components for validation and error display"""
    
    @staticmethod
    def render_validation_results(warnings: List[str], errors: List[str]):
        """Render validation results with appropriate styling"""
        st.subheader("🔍 TCO Configuration Validation")
        
        # Display errors first (critical)
        if errors:
            for error in errors:
                st.error(error)
            st.stop()  # Stop execution if there are critical errors
        
        # Display warnings in expandable section
        if warnings:
            with st.expander("⚠️ Configuration Warnings", expanded=len(warnings) > 2):
                for warning in warnings:
                    st.warning(warning)
    
    @staticmethod
    def render_autoclass_requirement_warning(analysis_mode: str):
        """Render Autoclass eligibility warning"""
        if analysis_mode in ["🤖 Autoclass Only", "⚖️ Side-by-Side Comparison"]:
            st.sidebar.warning("⚠️ **Autoclass Requirement**: Only objects ≥128 KiB are eligible for automatic transitions")


class ProgressComponents:
    """Components for progress indication and loading states"""
    
    @staticmethod
    def render_simulation_progress(months: int):
        """Render progress indication for long simulations"""
        if months > 36:
            st.info(f"⏳ Running {months}-month simulation... This may take a moment for longer periods.")
        
        # Return appropriate context manager for spinner
        if months > 24:
            return st.spinner("Running simulation...")
        else:
            return st.empty()  # No-op context manager


class ExportComponents:
    """Components for export functionality"""
    
    @staticmethod
    def render_export_section(csv_buffer, csv_filename: str, pdf_generate_callback):
        """Render export options section"""
        st.subheader("📦 Export Reports")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 CSV Data Export**")
            st.download_button(
                label="📄 Download CSV",
                data=csv_buffer.getvalue(),
                file_name=csv_filename,
                mime="text/csv"
            )
        
        with col2:
            st.markdown("**📋 PDF Report**")
            if st.button("📑 Generate PDF Report", type="secondary"):
                with st.spinner("Generating comprehensive PDF report..."):
                    pdf_buffer = pdf_generate_callback()
                    
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=pdf_buffer.getvalue(),
                        file_name=csv_filename.replace('.csv', '.pdf'),
                        mime="application/pdf"
                    )
