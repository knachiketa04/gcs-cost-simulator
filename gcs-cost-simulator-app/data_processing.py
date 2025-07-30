# data_processing.py - Optimized data processing utilities
from typing import Dict, List, Tuple, Optional, Any, Union
import logging

logger = logging.getLogger(__name__)


class DataProcessor:
    """Optimized data processing and formatting utilities"""
    
    @staticmethod
    def format_cost_value(value: float, precision: int = 2, show_currency: bool = True) -> str:
        """Format cost values with proper currency display"""
        if value == 0:
            return "$0.00" if show_currency else "0.00"
        
        # Handle large numbers with K/M suffixes
        if abs(value) >= 1_000_000:
            formatted = f"{value/1_000_000:.1f}M"
        elif abs(value) >= 1_000:
            formatted = f"{value/1_000:.1f}K"
        else:
            formatted = f"{value:.{precision}f}"
        
        return f"${formatted}" if show_currency else formatted
    
    @staticmethod
    def format_storage_value(value: float, precision: int = 1, show_unit: bool = True) -> str:
        """Format storage values with appropriate units"""
        if value == 0:
            return "0 GB" if show_unit else "0"
        
        # Handle large storage amounts with TB/PB suffixes
        if abs(value) >= 1_000_000:  # PB
            formatted = f"{value/1_000_000:.{precision}f} PB"
        elif abs(value) >= 1_000:  # TB
            formatted = f"{value/1_000:.{precision}f} TB"
        else:  # GB
            formatted = f"{value:.{precision}f} GB"
        
        return formatted if show_unit else formatted.split()[0]
    
    @staticmethod
    def format_percentage(value: float, precision: int = 1) -> str:
        """Format percentage values"""
        if abs(value) < 0.01:
            return "0.0%"
        return f"{value:.{precision}f}%"
    
    @staticmethod
    def format_number(value: Union[int, float], precision: int = 0) -> str:
        """Format large numbers with K/M/B suffixes"""
        if value == 0:
            return "0"
        
        if abs(value) >= 1_000_000_000:
            return f"{value/1_000_000_000:.1f}B"
        elif abs(value) >= 1_000_000:
            return f"{value/1_000_000:.1f}M"
        elif abs(value) >= 1_000:
            return f"{value/1_000:.1f}K"
        else:
            return f"{value:.{precision}f}" if isinstance(value, float) else str(value)
    
    @staticmethod
    def calculate_percentage_change(old_value: float, new_value: float) -> float:
        """Calculate percentage change between two values"""
        if old_value == 0:
            return 100.0 if new_value > 0 else 0.0
        return ((new_value - old_value) / old_value) * 100
    
    @staticmethod
    def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
        """Safely divide two numbers, returning default if denominator is zero"""
        return numerator / denominator if denominator != 0 else default
    
    @staticmethod
    def calculate_growth_factor(initial_value: float, final_value: float, periods: int) -> float:
        """Calculate compound growth rate between two values over given periods"""
        if initial_value <= 0 or periods <= 0:
            return 0.0
        
        return ((final_value / initial_value) ** (1 / periods)) - 1


class DataValidator:
    """Data validation utilities with comprehensive error handling"""
    
    @staticmethod
    def validate_positive_number(value: Any, field_name: str = "value") -> Tuple[bool, str]:
        """Validate that a value is a positive number"""
        try:
            num_value = float(value)
            if num_value < 0:
                return False, f"{field_name} must be non-negative"
            return True, ""
        except (ValueError, TypeError):
            return False, f"{field_name} must be a valid number"
    
    @staticmethod
    def validate_range(value: Any, min_val: float, max_val: float,
                      field_name: str = "value") -> Tuple[bool, str]:
        """Validate that a value is within a specified range"""
        try:
            num_value = float(value)
            if num_value < min_val or num_value > max_val:
                return False, f"{field_name} must be between {min_val} and {max_val}"
            return True, ""
        except (ValueError, TypeError):
            return False, f"{field_name} must be a valid number"
    
    @staticmethod
    def validate_storage_distribution(distribution: Dict[str, float]) -> Tuple[bool, List[str]]:
        """Validate storage distribution across tiers"""
        errors = []
        required_tiers = ['standard', 'nearline', 'coldline', 'archive']
        
        # Check all required tiers are present
        for tier in required_tiers:
            if tier not in distribution:
                errors.append(f"Missing storage tier: {tier}")
        
        # Validate all values are non-negative
        for tier, amount in distribution.items():
            is_valid, error = DataValidator.validate_positive_number(amount, f"{tier} storage")
            if not is_valid:
                errors.append(error)
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_time_series_data(data: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Validate time series data structure"""
        errors = []
        
        if not data:
            errors.append("Time series data cannot be empty")
            return False, errors
        
        required_fields = ['month', 'total_cost', 'storage_cost']
        for i, record in enumerate(data):
            for field in required_fields:
                if field not in record:
                    errors.append(f"Missing field '{field}' in record {i+1}")
        
        return len(errors) == 0, errors


class DataAggregator:
    """Aggregate and summarize data for reporting"""
    
    @staticmethod
    def aggregate_monthly_costs(monthly_data: List[Dict[str, float]]) -> Dict[str, float]:
        """Aggregate monthly cost data into summary statistics"""
        if not monthly_data:
            return {'total': 0, 'average': 0, 'min': 0, 'max': 0}
        
        costs = [record.get('total_cost', 0) for record in monthly_data]
        
        return {
            'total': sum(costs),
            'average': sum(costs) / len(costs),
            'min': min(costs),
            'max': max(costs),
            'months': len(costs)
        }
    
    @staticmethod
    def calculate_tier_utilization(storage_data: List[Dict[str, float]]) -> Dict[str, Dict[str, float]]:
        """Calculate storage tier utilization statistics"""
        if not storage_data:
            return {}
        
        tiers = ['standard', 'nearline', 'coldline', 'archive']
        utilization = {}
        
        for tier in tiers:
            tier_amounts = [record.get(tier, 0) for record in storage_data]
            total_amounts = [record.get('total', sum(record.get(t, 0) for t in tiers)) 
                           for record in storage_data]
            
            # Calculate percentages
            percentages = [
                DataProcessor.safe_divide(amount, total, 0) * 100
                for amount, total in zip(tier_amounts, total_amounts)
            ]
            
            utilization[tier] = {
                'avg_gb': sum(tier_amounts) / len(tier_amounts),
                'avg_percentage': sum(percentages) / len(percentages),
                'max_gb': max(tier_amounts),
                'min_gb': min(tier_amounts)
            }
        
        return utilization
    
    @staticmethod
    def calculate_cost_trends(cost_data: List[Dict[str, float]]) -> Dict[str, Any]:
        """Calculate cost trends and growth patterns"""
        if len(cost_data) < 2:
            return {'trend': 'insufficient_data', 'growth_rate': 0}
        
        costs = [record.get('total_cost', 0) for record in cost_data]
        
        # Calculate linear trend
        first_half_avg = sum(costs[:len(costs)//2]) / (len(costs)//2)
        second_half_avg = sum(costs[len(costs)//2:]) / (len(costs) - len(costs)//2)
        
        trend_direction = 'increasing' if second_half_avg > first_half_avg else 'decreasing'
        growth_rate = DataProcessor.calculate_percentage_change(first_half_avg, second_half_avg)
        
        # Calculate volatility (standard deviation)
        avg_cost = sum(costs) / len(costs)
        variance = sum((cost - avg_cost) ** 2 for cost in costs) / len(costs)
        volatility = variance ** 0.5
        
        return {
            'trend': trend_direction,
            'growth_rate': growth_rate,
            'volatility': volatility,
            'stability': 'stable' if volatility < avg_cost * 0.1 else 'volatile'
        }


class DataExporter:
    """Export data in various formats for external analysis"""
    
    @staticmethod
    def prepare_csv_data(simulation_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prepare simulation results for CSV export"""
        csv_data = []
        
        # Extract monthly data
        if 'monthly_data' in simulation_results:
            for month_data in simulation_results['monthly_data']:
                csv_data.append({
                    'Month': month_data.get('month', 0),
                    'Total_Cost_USD': month_data.get('total_cost', 0),
                    'Storage_Cost_USD': month_data.get('storage_cost', 0),
                    'API_Cost_USD': month_data.get('api_cost', 0),
                    'Special_Cost_USD': month_data.get('special_cost', 0),
                    'Standard_GB': month_data.get('standard', 0),
                    'Nearline_GB': month_data.get('nearline', 0),
                    'Coldline_GB': month_data.get('coldline', 0),
                    'Archive_GB': month_data.get('archive', 0),
                    'Total_Storage_GB': month_data.get('total_storage', 0)
                })
        
        return csv_data
    
    @staticmethod
    def create_summary_report(autoclass_results: Dict[str, Any],
                            lifecycle_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive summary report"""
        autoclass_summary = DataAggregator.aggregate_monthly_costs(
            autoclass_results.get('monthly_data', [])
        )
        lifecycle_summary = DataAggregator.aggregate_monthly_costs(
            lifecycle_results.get('monthly_data', [])
        )
        
        cost_difference = autoclass_summary['total'] - lifecycle_summary['total']
        winner = 'Lifecycle' if cost_difference > 0 else 'Autoclass'
        savings_pct = abs(cost_difference) / max(autoclass_summary['total'], lifecycle_summary['total']) * 100
        
        return {
            'comparison': {
                'winner': winner,
                'cost_difference': abs(cost_difference),
                'savings_percentage': savings_pct,
                'autoclass_total': autoclass_summary['total'],
                'lifecycle_total': lifecycle_summary['total']
            },
            'autoclass_summary': autoclass_summary,
            'lifecycle_summary': lifecycle_summary,
            'generated_at': 'timestamp_placeholder'  # Would be replaced with actual timestamp
        }
