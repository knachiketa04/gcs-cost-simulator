# chart_components.py - Chart generation components
import matplotlib.pyplot as plt
import streamlit as st
from typing import Tuple, Dict, Any
import pandas as pd
from utils import get_storage_unit_and_value, get_cost_unit_and_value


class ChartGenerator:
    """Centralized chart generation with consistent styling"""
    
    @staticmethod
    def setup_chart_styling() -> Dict[str, Any]:
        """Setup consistent chart styling configuration"""
        return {
            'linewidth': 2,
            'alpha': 0.7,
            'grid_alpha': 0.3,
            'figsize': (15, 12),
            'colors': {
                'autoclass': 'blue',
                'lifecycle': 'red',
                'standard': '#1f77b4',
                'nearline': '#ff7f0e',
                'coldline': '#2ca02c',
                'archive': '#d62728',
                'total': '#9467bd',
                'cost_difference': 'green'
            }
        }
    
    @staticmethod
    def create_data_distribution_chart(df: pd.DataFrame, title: str, 
                                     ax: plt.Axes, style: Dict[str, Any],
                                     storage_unit_factor: float = 1, 
                                     storage_label: str = "GB Stored"):
        """Create data distribution chart for storage classes"""
        storage_classes = ['Standard', 'Nearline', 'Coldline', 'Archive']
        
        for storage_class in storage_classes:
            chart_data = df[f"{storage_class} (GB)"] / storage_unit_factor
            ax.plot(df["Month"], chart_data,
                   label=storage_class,
                   linewidth=style['linewidth'],
                   color=style['colors'][storage_class.lower()])
        
        # Add total data line
        total_data = df["Total Data (GB)"] / storage_unit_factor
        ax.plot(df["Month"], total_data, 
               label="Total", 
               linestyle="--", 
               alpha=style['alpha'],
               color=style['colors']['total'])
        
        ax.set_ylabel(storage_label)
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=style['grid_alpha'])
    
    @staticmethod
    def create_cost_comparison_chart(autoclass_df: pd.DataFrame,
                                   lifecycle_df: pd.DataFrame,
                                   ax: plt.Axes, style: Dict[str, Any],
                                   cost_factor: float = 1,
                                   cost_label: str = "Cost ($)"):
        """Create cost comparison chart between strategies"""
        autoclass_costs = autoclass_df["Total Cost ($)"] / cost_factor
        lifecycle_costs = lifecycle_df["Total Cost ($)"] / cost_factor
        
        ax.plot(autoclass_df["Month"], autoclass_costs,
               label="🤖 Autoclass",
               linewidth=3,
               color=style['colors']['autoclass'])
        ax.plot(lifecycle_df["Month"], lifecycle_costs,
               label="📋 Lifecycle",
               linewidth=3,
               color=style['colors']['lifecycle'])
        
        ax.set_ylabel(cost_label)
        ax.set_title("💰 Total Cost Comparison")
        ax.legend()
        ax.grid(True, alpha=style['grid_alpha'])
    
    @staticmethod
    def create_cost_difference_chart(autoclass_df: pd.DataFrame,
                                   lifecycle_df: pd.DataFrame,
                                   ax: plt.Axes, style: Dict[str, Any],
                                   cost_factor: float = 1,
                                   cost_label: str = "Cost ($)"):
        """Create cost difference chart over time"""
        cost_difference = (autoclass_df["Total Cost ($)"] - lifecycle_df["Total Cost ($)"]) / cost_factor
        
        ax.plot(autoclass_df["Month"], cost_difference, 
               linewidth=2, 
               color=style['colors']['cost_difference'])
        ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        
        # Extract unit from cost_label for proper labeling
        unit_part = cost_label.split('(')[1] if '(' in cost_label else cost_label
        ax.set_ylabel(f"Cost Difference ({unit_part}")
        ax.set_xlabel("Month")
        ax.set_title("💸 Cost Difference (Autoclass - Lifecycle)")
        ax.grid(True, alpha=style['grid_alpha'])
        
        # Add contextual annotations
        final_difference = cost_difference.iloc[-1]
        if final_difference > 0:
            ax.text(0.7, 0.9, "Lifecycle\nSaves Money", 
                   transform=ax.transAxes,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen", alpha=0.7),
                   verticalalignment='top')
        else:
            ax.text(0.7, 0.1, "Autoclass\nSaves Money", 
                   transform=ax.transAxes,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.7),
                   verticalalignment='bottom')
    
    @staticmethod
    def create_cost_breakdown_chart(df: pd.DataFrame, title: str, 
                                  ax: plt.Axes, style: Dict[str, Any],
                                  strategy_type: str = "autoclass",
                                  cost_factor: float = 1,
                                  cost_label: str = "Cost ($)"):
        """Create cost breakdown chart for single strategy"""
        storage_costs = df["Storage Cost ($)"] / cost_factor
        api_costs = df["API Cost ($)"] / cost_factor
        
        ax.plot(df["Month"], storage_costs, 
               label="Storage", 
               linewidth=style['linewidth'])
        ax.plot(df["Month"], api_costs, 
               label="API", 
               linewidth=style['linewidth'])
        
        # Add strategy-specific cost line
        if strategy_type == "autoclass":
            special_costs = df["Autoclass Fee ($)"] / cost_factor
            special_label = "Autoclass Fee"
        else:
            special_costs = df["Retrieval Cost ($)"] / cost_factor
            special_label = "Retrieval Cost"
        
        ax.plot(df["Month"], special_costs, 
               label=special_label, 
               linewidth=style['linewidth'])
        
        # Add total cost line
        total_costs = df["Total Cost ($)"] / cost_factor
        ax.plot(df["Month"], total_costs, 
               label="Total", 
               linestyle="--", 
               alpha=style['alpha'])
        
        ax.set_ylabel(cost_label)
        ax.set_xlabel("Month")
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=style['grid_alpha'])
    
    @classmethod
    def create_comparison_dashboard(cls, autoclass_df: pd.DataFrame,
                                  lifecycle_df: pd.DataFrame):
        """Create complete comparison dashboard with 4 charts"""
        st.subheader("📈 Side-by-Side Visual Comparison")
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        style = cls.setup_chart_styling()
        
        # Determine appropriate units for charts
        max_autoclass_data = autoclass_df["Total Data (GB)"].max()
        max_lifecycle_data = lifecycle_df["Total Data (GB)"].max()
        max_data = max(max_autoclass_data, max_lifecycle_data)
        storage_unit_factor, storage_unit = get_storage_unit_and_value(max_data)
        
        storage_factor = 1024 if storage_unit == "TiB" else 1
        storage_label = "TiB Stored" if storage_unit == "TiB" else "GB Stored"
        
        # Data distribution charts
        cls.create_data_distribution_chart(
            autoclass_df, "🤖 Autoclass Data Distribution", ax1, style, 
            storage_factor, storage_label
        )
        cls.create_data_distribution_chart(
            lifecycle_df, "📋 Lifecycle Data Distribution", ax2, style,
            storage_factor, storage_label
        )
        
        # Determine cost units
        max_autoclass_cost = autoclass_df["Total Cost ($)"].max()
        max_lifecycle_cost = lifecycle_df["Total Cost ($)"].max()
        max_cost = max(max_autoclass_cost, max_lifecycle_cost)
        cost_unit_factor, cost_unit = get_cost_unit_and_value(max_cost)
        
        cost_factor = 1000000 if cost_unit == "M" else 1
        cost_label = "Cost ($M)" if cost_unit == "M" else "Cost ($)"
        
        # Cost comparison
        cls.create_cost_comparison_chart(
            autoclass_df, lifecycle_df, ax3, style, cost_factor, cost_label
        )
        
        # Cost difference over time
        cls.create_cost_difference_chart(
            autoclass_df, lifecycle_df, ax4, style, cost_factor, cost_label
        )
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)
    
    @classmethod
    def create_single_strategy_charts(cls, df: pd.DataFrame, analysis_mode: str):
        """Create charts for single strategy analysis"""
        strategy_name = "Autoclass" if analysis_mode == "🤖 Autoclass Only" else "Lifecycle"
        st.subheader(f"🪄 {strategy_name} Data Growth Over Time")
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
        style = cls.setup_chart_styling()
        
        # Determine appropriate storage unit for chart
        max_total_data = df["Total Data (GB)"].max()
        storage_unit_factor, storage_unit = get_storage_unit_and_value(max_total_data)
        
        storage_factor = 1024 if storage_unit == "TiB" else 1
        storage_label = "TiB Stored" if storage_unit == "TiB" else "GB Stored"
        
        # Data distribution chart
        cls.create_data_distribution_chart(
            df, "Data Distribution Across Storage Classes", ax1, style,
            storage_factor, storage_label
        )
        
        # Determine appropriate cost unit for chart
        max_total_cost = df["Total Cost ($)"].max()
        cost_unit_factor, cost_unit = get_cost_unit_and_value(max_total_cost)
        
        cost_factor = 1000000 if cost_unit == "M" else 1
        cost_label = "Cost ($M)" if cost_unit == "M" else "Cost ($)"
        
        # Cost breakdown chart
        cls.create_cost_breakdown_chart(
            df, "Monthly Cost Breakdown", ax2, style,
            "autoclass" if analysis_mode == "🤖 Autoclass Only" else "lifecycle",
            cost_factor, cost_label
        )
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)


class ChartUtilities:
    """Utility functions for chart-related operations"""
    
    @staticmethod
    def calculate_chart_units(data_values: list, cost_values: list = None) -> Dict[str, Any]:
        """Calculate appropriate units for chart display"""
        max_data = max(data_values) if data_values else 0
        storage_unit_factor, storage_unit = get_storage_unit_and_value(max_data)
        
        result = {
            'storage_factor': 1024 if storage_unit == "TiB" else 1,
            'storage_label': "TiB Stored" if storage_unit == "TiB" else "GB Stored"
        }
        
        if cost_values:
            max_cost = max(cost_values) if cost_values else 0
            cost_unit_factor, cost_unit = get_cost_unit_and_value(max_cost)
            result.update({
                'cost_factor': 1000000 if cost_unit == "M" else 1,
                'cost_label': "Cost ($M)" if cost_unit == "M" else "Cost ($)"
            })
        
        return result
    
    @staticmethod
    def prepare_chart_data(df: pd.DataFrame, unit_config: Dict[str, Any]) -> Dict[str, pd.Series]:
        """Prepare data for charting with appropriate unit scaling"""
        storage_factor = unit_config.get('storage_factor', 1)
        cost_factor = unit_config.get('cost_factor', 1)
        
        chart_data = {
            'standard': df["Standard (GB)"] / storage_factor,
            'nearline': df["Nearline (GB)"] / storage_factor,
            'coldline': df["Coldline (GB)"] / storage_factor,
            'archive': df["Archive (GB)"] / storage_factor,
            'total_data': df["Total Data (GB)"] / storage_factor,
            'storage_cost': df["Storage Cost ($)"] / cost_factor,
            'api_cost': df["API Cost ($)"] / cost_factor,
            'total_cost': df["Total Cost ($)"] / cost_factor
        }
        
        # Add strategy-specific costs if available
        if "Autoclass Fee ($)" in df.columns:
            chart_data['autoclass_fee'] = df["Autoclass Fee ($)"] / cost_factor
        if "Retrieval Cost ($)" in df.columns:
            chart_data['retrieval_cost'] = df["Retrieval Cost ($)"] / cost_factor
        
        return chart_data
