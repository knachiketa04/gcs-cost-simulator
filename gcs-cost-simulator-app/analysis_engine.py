# analysis_engine.py - Business logic for analysis
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
from utils import format_cost_value, format_storage_value


class AnalysisEngine:
    """Core analysis logic separated from UI"""
    
    @staticmethod
    def calculate_cost_metrics(df: pd.DataFrame) -> Dict[str, float]:
        """Calculate standard cost metrics for a strategy"""
        return {
            'total_cost': df["Total Cost ($)"].sum(),
            'storage_cost': df["Storage Cost ($)"].sum(),
            'api_cost': df["API Cost ($)"].sum(),
            'avg_monthly_cost': df["Total Cost ($)"].sum() / len(df) if len(df) > 0 else 0
        }
    
    @staticmethod
    def calculate_storage_distribution(df: pd.DataFrame) -> Dict[str, float]:
        """Calculate final storage distribution across tiers"""
        if df.empty:
            return {'standard': 0, 'nearline': 0, 'coldline': 0, 'archive': 0, 'total': 0}
        
        final_month = df.iloc[-1]
        return {
            'standard': final_month["Standard (GB)"],
            'nearline': final_month["Nearline (GB)"],
            'coldline': final_month["Coldline (GB)"],
            'archive': final_month["Archive (GB)"],
            'total': final_month["Total Data (GB)"]
        }
    
    @staticmethod
    def calculate_cost_percentages(df: pd.DataFrame, strategy_type: str) -> Dict[str, float]:
        """Calculate cost component percentages"""
        total_cost = df["Total Cost ($)"].sum()
        if total_cost == 0:
            return {'storage': 0, 'api': 0, 'special': 0}
        
        storage_pct = (df["Storage Cost ($)"].sum() / total_cost * 100)
        api_pct = (df["API Cost ($)"].sum() / total_cost * 100)
        
        if strategy_type == "autoclass":
            special_cost = df["Autoclass Fee ($)"].sum()
        else:
            special_cost = df["Retrieval Cost ($)"].sum()
        
        special_pct = (special_cost / total_cost * 100)
        
        return {
            'storage': storage_pct,
            'api': api_pct,
            'special': special_pct,
            'special_cost': special_cost
        }
    
    @staticmethod
    def generate_strategy_insights(df: pd.DataFrame, strategy_type: str,
                                 lifecycle_rules: Optional[Dict] = None) -> List[str]:
        """Generate insights for single strategy analysis"""
        insights = []
        
        cost_metrics = AnalysisEngine.calculate_cost_metrics(df)
        storage_dist = AnalysisEngine.calculate_storage_distribution(df)
        cost_percentages = AnalysisEngine.calculate_cost_percentages(df, strategy_type)
        
        # Calculate archive utilization
        archive_pct = (storage_dist['archive'] / storage_dist['total'] * 100) if storage_dist['total'] > 0 else 0
        
        if strategy_type == "autoclass":
            insights.extend([
                f"Archive utilization: {archive_pct:.1f}%",
                f"Management fee impact: {cost_percentages['special']:.1f}% of total cost",
                "Intelligent access-based optimization active" if archive_pct > 50 else "Conservative optimization pattern"
            ])
            
            # Add management fee insights
            if cost_percentages['special'] > 15:
                insights.append("⚠️ Autoclass management fees represent significant portion of costs")
            elif cost_percentages['special'] < 5:
                insights.append("✅ Autoclass management fees are minimal - excellent for dynamic patterns")
                
        else:  # lifecycle
            path_name = lifecycle_rules.get('path_name', 'Custom') if lifecycle_rules else 'Custom'
            insights.extend([
                f"Archive utilization: {archive_pct:.1f}%",
                f"Retrieval cost impact: {cost_percentages['special']:.1f}% of total cost",
                f"Path efficiency: {path_name} strategy"
            ])
            
            # Add retrieval cost insights
            if cost_percentages['special'] > 20:
                insights.append("⚠️ Retrieval costs represent significant portion of total costs")
            elif cost_percentages['special'] < 5:
                insights.append("✅ Low retrieval costs - lifecycle policy optimal for predictable patterns")
        
        return insights
    
    @staticmethod
    def generate_strategy_recommendations(df: pd.DataFrame, strategy_type: str,
                                        lifecycle_rules: Optional[Dict] = None) -> List[str]:
        """Generate recommendations for strategy optimization"""
        recommendations = []
        
        storage_dist = AnalysisEngine.calculate_storage_distribution(df)
        cost_percentages = AnalysisEngine.calculate_cost_percentages(df, strategy_type)
        
        archive_pct = (storage_dist['archive'] / storage_dist['total'] * 100) if storage_dist['total'] > 0 else 0
        standard_pct = (storage_dist['standard'] / storage_dist['total'] * 100) if storage_dist['total'] > 0 else 0
        
        if strategy_type == "autoclass":
            if archive_pct < 30:
                recommendations.append("💡 Consider more aggressive access patterns to increase archive utilization")
            if cost_percentages['special'] > 20:
                recommendations.append("⚡ High management fees - consider lifecycle policies for predictable data")
        else:
            if lifecycle_rules:
                # Use path-specific recommendations from lifecycle_paths module
                from lifecycle_paths import LifecyclePathManager
                path_recommendations = LifecyclePathManager.generate_path_recommendations(
                    lifecycle_rules, 
                    {'Standard': storage_dist['standard'], 'Nearline': storage_dist['nearline'],
                     'Coldline': storage_dist['coldline'], 'Archive': storage_dist['archive']},
                    storage_dist['total']
                )
                recommendations.extend(path_recommendations)
            
            if cost_percentages['special'] > 25:
                recommendations.append("💡 High retrieval costs - consider Autoclass for frequent access patterns")
        
        # General recommendations
        if standard_pct > 60:
            recommendations.append("⚡ High Standard storage usage - consider faster transition policies")
        
        if not recommendations:
            recommendations.append("✅ Current strategy appears well-optimized for your data pattern")
        
        return recommendations
    
    @staticmethod
    def compare_strategies(autoclass_df: pd.DataFrame,
                          lifecycle_df: pd.DataFrame) -> Dict[str, Any]:
        """Compare two strategies and return comprehensive analysis"""
        autoclass_cost = autoclass_df["Total Cost ($)"].sum()
        lifecycle_cost = lifecycle_df["Total Cost ($)"].sum()
        cost_difference = autoclass_cost - lifecycle_cost
        savings_percentage = (abs(cost_difference) / max(autoclass_cost, lifecycle_cost)) * 100
        
        winner = "Lifecycle" if cost_difference > 0 else "Autoclass"
        
        # Detailed cost breakdowns
        autoclass_breakdown = {
            'storage': autoclass_df["Storage Cost ($)"].sum(),
            'api': autoclass_df["API Cost ($)"].sum(),
            'special': autoclass_df["Autoclass Fee ($)"].sum(),
            'total': autoclass_cost
        }
        
        lifecycle_breakdown = {
            'storage': lifecycle_df["Storage Cost ($)"].sum(),
            'api': lifecycle_df["API Cost ($)"].sum(),
            'special': lifecycle_df["Retrieval Cost ($)"].sum(),
            'total': lifecycle_cost
        }
        
        return {
            'winner': winner,
            'cost_difference': abs(cost_difference),
            'savings_percentage': savings_percentage,
            'autoclass_cost': autoclass_cost,
            'lifecycle_cost': lifecycle_cost,
            'autoclass_breakdown': autoclass_breakdown,
            'lifecycle_breakdown': lifecycle_breakdown,
            'recommendation': AnalysisEngine._generate_recommendation(cost_difference, savings_percentage)
        }
    
    @staticmethod
    def _generate_recommendation(cost_diff: float, savings_pct: float) -> str:
        """Generate recommendation based on cost analysis"""
        if abs(cost_diff) < 1000:  # Less than $1000 difference
            return "Costs are similar - choose based on operational preferences"
        elif cost_diff > 0:
            return f"Lifecycle policy recommended - saves {savings_pct:.1f}% through elimination of management fees"
        else:
            return f"Autoclass recommended - saves {savings_pct:.1f}% through intelligent optimization"
    
    @staticmethod
    def generate_comparison_insights(comparison_result: Dict[str, Any]) -> List[str]:
        """Generate insights for strategy comparison"""
        insights = []
        
        winner = comparison_result['winner']
        savings_pct = comparison_result['savings_percentage']
        autoclass_breakdown = comparison_result['autoclass_breakdown']
        lifecycle_breakdown = comparison_result['lifecycle_breakdown']
        
        insights.append(f"**{winner} is more cost-effective** (saves {savings_pct:.1f}%)")
        
        # Management fee vs retrieval cost comparison
        mgmt_fee_pct = (autoclass_breakdown['special'] / autoclass_breakdown['total'] * 100)
        retrieval_pct = (lifecycle_breakdown['special'] / lifecycle_breakdown['total'] * 100)
        
        insights.extend([
            f"Autoclass management fee: {mgmt_fee_pct:.1f}% of total cost",
            f"Lifecycle retrieval costs: {retrieval_pct:.1f}% of total cost"
        ])
        
        # Strategic insights
        if winner == "Lifecycle":
            insights.append("Lifecycle policies are more cost-effective due to no management fees and predictable transitions")
        else:
            insights.append("Autoclass is more cost-effective through intelligent optimization and no retrieval costs")
        
        return insights


class PerformanceAnalyzer:
    """Analyze performance characteristics of strategies"""
    
    @staticmethod
    def analyze_growth_efficiency(df: pd.DataFrame) -> Dict[str, float]:
        """Analyze how efficiently strategy handles data growth"""
        if len(df) < 2:
            return {'efficiency_score': 0, 'cost_per_gb_trend': 0}
        
        # Calculate cost per GB over time
        cost_per_gb = df["Total Cost ($)"] / df["Total Data (GB)"]
        cost_per_gb = cost_per_gb.replace([float('inf'), -float('inf')], 0).fillna(0)
        
        # Calculate trend (negative is good - decreasing cost per GB)
        first_half = cost_per_gb[:len(cost_per_gb)//2].mean()
        second_half = cost_per_gb[len(cost_per_gb)//2:].mean()
        trend = second_half - first_half
        
        # Efficiency score (lower cost per GB = higher efficiency)
        avg_cost_per_gb = cost_per_gb.mean()
        efficiency_score = max(0, min(100, (0.01 - avg_cost_per_gb) * 10000))  # Normalize to 0-100
        
        return {
            'efficiency_score': efficiency_score,
            'cost_per_gb_trend': trend,
            'avg_cost_per_gb': avg_cost_per_gb
        }
    
    @staticmethod
    def analyze_tier_optimization(df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze storage tier optimization effectiveness"""
        if df.empty:
            return {'optimization_score': 0, 'tier_distribution': {}}
        
        final_dist = AnalysisEngine.calculate_storage_distribution(df)
        total_data = final_dist['total']
        
        if total_data == 0:
            return {'optimization_score': 0, 'tier_distribution': final_dist}
        
        # Calculate optimization score based on archive utilization
        archive_pct = (final_dist['archive'] / total_data * 100)
        coldline_pct = (final_dist['coldline'] / total_data * 100)
        nearline_pct = (final_dist['nearline'] / total_data * 100)
        
        # Weight archive highest, then coldline, then nearline
        optimization_score = (archive_pct * 1.0 + coldline_pct * 0.7 + nearline_pct * 0.4)
        optimization_score = min(100, optimization_score)  # Cap at 100
        
        return {
            'optimization_score': optimization_score,
            'tier_distribution': final_dist,
            'archive_utilization': archive_pct
        }
