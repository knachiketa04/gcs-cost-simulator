# pricing_engine.py - Centralized pricing logic
from typing import Dict, Tuple, List
import logging

logger = logging.getLogger(__name__)


class GCSPricingEngine:
    """Centralized Google Cloud Storage pricing calculations"""
    
    # Storage pricing per GB per month (USD)
    STORAGE_PRICES = {
        'standard': 0.020,
        'nearline': 0.010,
        'coldline': 0.004,
        'archive': 0.0012
    }
    
    # API operation pricing (per 1000 operations)
    API_PRICES = {
        'class_a': 0.05,  # Write operations
        'class_b': 0.004  # Read operations
    }
    
    # Retrieval pricing per GB
    RETRIEVAL_PRICES = {
        'nearline': 0.01,
        'coldline': 0.02,
        'archive': 0.05
    }
    
    # Autoclass management fee per GB per month
    AUTOCLASS_FEE = 0.0025
    
    @classmethod
    def calculate_storage_cost(cls, storage_gb: Dict[str, float]) -> float:
        """Calculate monthly storage costs across all tiers"""
        total_cost = 0.0
        
        for tier, gb_amount in storage_gb.items():
            if tier in cls.STORAGE_PRICES and gb_amount > 0:
                cost = gb_amount * cls.STORAGE_PRICES[tier]
                total_cost += cost
                logger.debug(f"{tier.title()} storage: {gb_amount:.1f} GB × ${cls.STORAGE_PRICES[tier]:.4f} = ${cost:.2f}")
        
        return total_cost
    
    @classmethod
    def calculate_api_cost(cls, read_ops: int, write_ops: int = 0) -> float:
        """Calculate API operation costs"""
        # Convert operations to thousands for pricing calculation
        read_cost = (read_ops / 1000) * cls.API_PRICES['class_b']
        write_cost = (write_ops / 1000) * cls.API_PRICES['class_a']
        
        total_cost = read_cost + write_cost
        logger.debug(f"API costs: {read_ops} reads = ${read_cost:.4f}, {write_ops} writes = ${write_cost:.4f}")
        
        return total_cost
    
    @classmethod
    def calculate_retrieval_cost(cls, retrievals: Dict[str, float]) -> float:
        """Calculate data retrieval costs for lifecycle policies"""
        total_cost = 0.0
        
        for tier, gb_amount in retrievals.items():
            if tier in cls.RETRIEVAL_PRICES and gb_amount > 0:
                cost = gb_amount * cls.RETRIEVAL_PRICES[tier]
                total_cost += cost
                logger.debug(f"{tier.title()} retrieval: {gb_amount:.1f} GB × ${cls.RETRIEVAL_PRICES[tier]:.3f} = ${cost:.2f}")
        
        return total_cost
    
    @classmethod
    def calculate_autoclass_fee(cls, total_storage_gb: float) -> float:
        """Calculate Autoclass management fee"""
        fee = total_storage_gb * cls.AUTOCLASS_FEE
        logger.debug(f"Autoclass fee: {total_storage_gb:.1f} GB × ${cls.AUTOCLASS_FEE:.4f} = ${fee:.4f}")
        return fee
    
    @classmethod
    def get_tier_cost_per_gb(cls, tier: str) -> float:
        """Get cost per GB for a specific storage tier"""
        return cls.STORAGE_PRICES.get(tier, 0.0)
    
    @classmethod
    def get_retrieval_cost_per_gb(cls, tier: str) -> float:
        """Get retrieval cost per GB for a specific tier"""
        return cls.RETRIEVAL_PRICES.get(tier, 0.0)
    
    @classmethod
    def calculate_cost_breakdown(cls, storage_gb: Dict[str, float],
                               read_ops: int, retrievals: Dict[str, float] = None,
                               use_autoclass: bool = False) -> Dict[str, float]:
        """Calculate comprehensive cost breakdown"""
        storage_cost = cls.calculate_storage_cost(storage_gb)
        api_cost = cls.calculate_api_cost(read_ops)
        
        total_storage = sum(storage_gb.values())
        
        if use_autoclass:
            special_cost = cls.calculate_autoclass_fee(total_storage)
            special_label = 'autoclass_fee'
        else:
            retrieval_dict = retrievals or {}
            special_cost = cls.calculate_retrieval_cost(retrieval_dict)
            special_label = 'retrieval_cost'
        
        return {
            'storage_cost': storage_cost,
            'api_cost': api_cost,
            special_label: special_cost,
            'total_cost': storage_cost + api_cost + special_cost
        }


class PricingOptimizer:
    """Optimization logic for cost calculations"""
    
    @staticmethod
    def find_optimal_tier_distribution(total_gb: float, access_pattern: Dict[str, float],
                                     target_cost_reduction: float = 0.20) -> Dict[str, float]:
        """Find optimal distribution across storage tiers for cost reduction"""
        # Simple heuristic: distribute based on access frequency
        read_frequency = access_pattern.get('monthly_read_gb', 0) / total_gb if total_gb > 0 else 0
        
        if read_frequency > 0.1:  # High access - more in standard/nearline
            return {
                'standard': total_gb * 0.6,
                'nearline': total_gb * 0.3,
                'coldline': total_gb * 0.08,
                'archive': total_gb * 0.02
            }
        elif read_frequency > 0.05:  # Medium access
            return {
                'standard': total_gb * 0.3,
                'nearline': total_gb * 0.4,
                'coldline': total_gb * 0.2,
                'archive': total_gb * 0.1
            }
        else:  # Low access - more in coldline/archive
            return {
                'standard': total_gb * 0.1,
                'nearline': total_gb * 0.2,
                'coldline': total_gb * 0.3,
                'archive': total_gb * 0.4
            }
    
    @staticmethod
    def estimate_cost_impact(current_distribution: Dict[str, float],
                           optimized_distribution: Dict[str, float]) -> Dict[str, float]:
        """Estimate cost impact of changing storage distribution"""
        current_cost = GCSPricingEngine.calculate_storage_cost(current_distribution)
        optimized_cost = GCSPricingEngine.calculate_storage_cost(optimized_distribution)
        
        savings = current_cost - optimized_cost
        savings_percentage = (savings / current_cost * 100) if current_cost > 0 else 0
        
        return {
            'current_cost': current_cost,
            'optimized_cost': optimized_cost,
            'monthly_savings': savings,
            'savings_percentage': savings_percentage
        }
    
    @staticmethod
    def calculate_break_even_point(autoclass_cost: float, lifecycle_cost: float,
                                 monthly_difference: float) -> int:
        """Calculate break-even point in months between strategies"""
        if monthly_difference <= 0:
            return 0  # Already break-even or lifecycle always better
        
        initial_setup_difference = abs(autoclass_cost - lifecycle_cost)
        return int(initial_setup_difference / monthly_difference) + 1


class RegionalPricingEngine:
    """Handle region-specific pricing calculations"""
    
    # Regional multipliers for different cost components
    REGIONAL_MULTIPLIERS = {
        'us-central1': {'storage': 1.0, 'api': 1.0, 'network': 1.0},
        'us-east1': {'storage': 1.0, 'api': 1.0, 'network': 1.0},
        'us-west1': {'storage': 1.0, 'api': 1.0, 'network': 1.0},
        'europe-west1': {'storage': 1.0, 'api': 1.0, 'network': 1.2},
        'europe-west2': {'storage': 1.05, 'api': 1.05, 'network': 1.25},
        'asia-southeast1': {'storage': 1.0, 'api': 1.0, 'network': 1.15},
        'asia-northeast1': {'storage': 1.1, 'api': 1.1, 'network': 1.2},
        'australia-southeast1': {'storage': 1.1, 'api': 1.1, 'network': 1.3}
    }
    
    @classmethod
    def apply_regional_pricing(cls, base_costs: Dict[str, float], region: str) -> Dict[str, float]:
        """Apply regional pricing multipliers to base costs"""
        if region not in cls.REGIONAL_MULTIPLIERS:
            logger.warning(f"Unknown region {region}, using us-central1 pricing")
            region = 'us-central1'
        
        multipliers = cls.REGIONAL_MULTIPLIERS[region]
        
        return {
            'storage_cost': base_costs.get('storage_cost', 0) * multipliers['storage'],
            'api_cost': base_costs.get('api_cost', 0) * multipliers['api'],
            'retrieval_cost': base_costs.get('retrieval_cost', 0) * multipliers['network'],
            'autoclass_fee': base_costs.get('autoclass_fee', 0) * multipliers['storage'],
        }
    
    @classmethod
    def get_region_cost_comparison(cls, base_costs: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        """Compare costs across all supported regions"""
        regional_costs = {}
        
        for region in cls.REGIONAL_MULTIPLIERS.keys():
            regional_costs[region] = cls.apply_regional_pricing(base_costs, region)
            regional_costs[region]['total_cost'] = sum(regional_costs[region].values())
        
        return regional_costs


class CostProjector:
    """Project costs over time with growth and optimization factors"""
    
    @staticmethod
    def project_costs_with_growth(base_costs: Dict[str, float], months: int,
                                growth_rate: float = 0.0) -> List[Dict[str, float]]:
        """Project costs over time with data growth"""
        projections = []
        monthly_growth_factor = (1 + growth_rate / 100) ** (1/12)  # Convert annual to monthly
        
        for month in range(months):
            growth_multiplier = monthly_growth_factor ** month
            
            month_costs = {
                key: value * growth_multiplier 
                for key, value in base_costs.items()
            }
            month_costs['month'] = month + 1
            month_costs['growth_factor'] = growth_multiplier
            
            projections.append(month_costs)
        
        return projections
    
    @staticmethod
    def calculate_cumulative_costs(monthly_projections: List[Dict[str, float]]) -> Dict[str, float]:
        """Calculate cumulative costs from monthly projections"""
        cumulative = {}
        
        for projection in monthly_projections:
            for key, value in projection.items():
                if key not in ['month', 'growth_factor']:
                    cumulative[key] = cumulative.get(key, 0) + value
        
        return cumulative
