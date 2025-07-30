# configuration_manager.py - Configuration management and validation
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class StoragePattern:
    """Data class for storage access patterns"""
    name: str
    display_name: str
    upload_gb: float
    delete_gb: float
    read_gb: float
    read_ops: int
    description: str
    use_case: str


@dataclass
class TimeConfiguration:
    """Time-based configuration parameters"""
    simulation_months: int
    start_date: str
    data_growth_rate: float
    seasonal_variation: bool = False
    peak_months: List[int] = None
    
    def __post_init__(self):
        if self.peak_months is None:
            self.peak_months = [6, 7, 8, 11, 12]  # Summer and holiday seasons


class ConfigurationManager:
    """Manages all configuration aspects of the simulation"""
    
    # Predefined storage patterns for common use cases
    STORAGE_PATTERNS = {
        'backup': StoragePattern(
            name='backup',
            display_name='Backup & Archive',
            upload_gb=1000,
            delete_gb=50,
            read_gb=10,
            read_ops=100,
            description='Long-term backup storage with minimal access',
            use_case='Database backups, compliance archives'
        ),
        'analytics': StoragePattern(
            name='analytics',
            display_name='Analytics Data',
            upload_gb=500,
            delete_gb=100,
            read_gb=200,
            read_ops=1000,
            description='Data for analytics with periodic access',
            use_case='Log files, event data, ML training sets'
        ),
        'media': StoragePattern(
            name='media',
            display_name='Media Storage',
            upload_gb=2000,
            delete_gb=200,
            read_gb=500,
            read_ops=5000,
            description='Media files with moderate access patterns',
            use_case='Images, videos, audio files'
        ),
        'documents': StoragePattern(
            name='documents',
            display_name='Document Archive',
            upload_gb=100,
            delete_gb=10,
            read_gb=50,
            read_ops=500,
            description='Document storage with occasional retrieval',
            use_case='PDFs, reports, historical documents'
        ),
        'development': StoragePattern(
            name='development',
            display_name='Development Data',
            upload_gb=300,
            delete_gb=150,
            read_gb=400,
            read_ops=2000,
            description='Development artifacts with frequent access',
            use_case='Build artifacts, test data, repositories'
        )
    }
    
    @classmethod
    def get_storage_pattern(cls, pattern_name: str) -> Optional[StoragePattern]:
        """Get predefined storage pattern by name"""
        return cls.STORAGE_PATTERNS.get(pattern_name)
    
    @classmethod
    def get_all_patterns(cls) -> Dict[str, StoragePattern]:
        """Get all available storage patterns"""
        return cls.STORAGE_PATTERNS.copy()
    
    @classmethod
    def get_pattern_names(cls) -> List[str]:
        """Get list of available pattern names for UI selection"""
        return list(cls.STORAGE_PATTERNS.keys())
    
    @staticmethod
    def validate_simulation_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate simulation configuration parameters"""
        errors = []
        
        # Required fields
        required_fields = ['simulation_months', 'initial_data_gb', 'monthly_upload_gb']
        for field in required_fields:
            if field not in config or config[field] is None:
                errors.append(f"Missing required field: {field}")
        
        # Validate numeric ranges
        if 'simulation_months' in config:
            months = config['simulation_months']
            if not isinstance(months, (int, float)) or months < 1 or months > 120:
                errors.append("Simulation months must be between 1 and 120")
        
        if 'initial_data_gb' in config:
            initial_data = config['initial_data_gb']
            if not isinstance(initial_data, (int, float)) or initial_data < 0:
                errors.append("Initial data must be a non-negative number")
        
        if 'monthly_upload_gb' in config:
            upload = config['monthly_upload_gb']
            if not isinstance(upload, (int, float)) or upload < 0:
                errors.append("Monthly upload must be a non-negative number")
        
        # Validate optional fields
        if 'data_growth_rate' in config:
            growth_rate = config['data_growth_rate']
            if not isinstance(growth_rate, (int, float)) or growth_rate < -100 or growth_rate > 1000:
                errors.append("Data growth rate must be between -100% and 1000%")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_lifecycle_config(rules: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate lifecycle policy configuration"""
        errors = []
        
        if not rules:
            errors.append("Lifecycle rules cannot be empty")
            return False, errors
        
        # Validate transition rules
        required_transitions = ['standard_to_nearline', 'nearline_to_coldline', 'coldline_to_archive']
        for transition in required_transitions:
            if transition not in rules:
                errors.append(f"Missing transition rule: {transition}")
                continue
            
            days = rules[transition]
            if not isinstance(days, (int, float)) or days < 0 or days > 3650:  # Max 10 years
                errors.append(f"{transition} must be between 0 and 3650 days")
        
        # Validate logical order of transitions
        if all(t in rules for t in required_transitions):
            std_to_near = rules['standard_to_nearline']
            near_to_cold = rules['nearline_to_coldline']
            cold_to_arch = rules['coldline_to_archive']
            
            if std_to_near >= near_to_cold:
                errors.append("Standard to Nearline days must be less than Nearline to Coldline days")
            if near_to_cold >= cold_to_arch:
                errors.append("Nearline to Coldline days must be less than Coldline to Archive days")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_access_pattern(pattern: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate access pattern configuration"""
        errors = []
        
        required_fields = ['monthly_delete_gb', 'monthly_read_gb', 'monthly_read_ops']
        for field in required_fields:
            if field not in pattern:
                errors.append(f"Missing access pattern field: {field}")
                continue
            
            value = pattern[field]
            if not isinstance(value, (int, float)) or value < 0:
                errors.append(f"{field} must be a non-negative number")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def create_time_config(months: int, growth_rate: float = 0.0,
                          seasonal: bool = False) -> TimeConfiguration:
        """Create time configuration with validation"""
        if months < 1 or months > 120:
            raise ValueError("Simulation months must be between 1 and 120")
        
        if growth_rate < -100 or growth_rate > 1000:
            raise ValueError("Growth rate must be between -100% and 1000%")
        
        return TimeConfiguration(
            simulation_months=months,
            start_date="2024-01-01",  # Default start date
            data_growth_rate=growth_rate,
            seasonal_variation=seasonal
        )
    
    @staticmethod
    def apply_seasonal_variation(base_value: float, month: int,
                               seasonal_config: TimeConfiguration) -> float:
        """Apply seasonal variation to a base value"""
        if not seasonal_config.seasonal_variation:
            return base_value
        
        # Apply 20% increase during peak months
        if month in seasonal_config.peak_months:
            return base_value * 1.2
        else:
            return base_value * 0.9  # 10% decrease during off-peak
    
    @staticmethod
    def estimate_configuration_impact(config: Dict[str, Any]) -> Dict[str, str]:
        """Estimate the impact of configuration choices"""
        impacts = {}
        
        # Analyze data growth impact
        if 'data_growth_rate' in config:
            growth_rate = config['data_growth_rate']
            if growth_rate > 10:
                impacts['growth'] = "High growth rate will significantly increase storage costs over time"
            elif growth_rate > 5:
                impacts['growth'] = "Moderate growth rate will gradually increase costs"
            else:
                impacts['growth'] = "Low growth rate - costs will remain relatively stable"
        
        # Analyze access pattern impact
        if 'monthly_read_gb' in config and 'monthly_upload_gb' in config:
            read_gb = config['monthly_read_gb']
            upload_gb = config['monthly_upload_gb']
            
            if read_gb > upload_gb * 0.5:
                impacts['access'] = "High read activity - Autoclass may be more cost-effective"
            elif read_gb < upload_gb * 0.1:
                impacts['access'] = "Low read activity - Lifecycle policies likely more cost-effective"
            else:
                impacts['access'] = "Moderate read activity - both strategies may be viable"
        
        # Analyze simulation duration impact
        if 'simulation_months' in config:
            months = config['simulation_months']
            if months >= 36:
                impacts['duration'] = "Long simulation period - will show full impact of tier transitions"
            elif months >= 12:
                impacts['duration'] = "Medium simulation period - will show most tier benefits"
            else:
                impacts['duration'] = "Short simulation period - may not show full lifecycle benefits"
        
        return impacts


class RegionManager:
    """Manage GCS region-specific configurations"""
    
    # Region-specific pricing adjustments (multipliers relative to us-central1)
    REGION_MULTIPLIERS = {
        'us-central1': {'storage': 1.0, 'api': 1.0, 'network': 1.0},
        'us-east1': {'storage': 1.0, 'api': 1.0, 'network': 1.0},
        'us-west1': {'storage': 1.0, 'api': 1.0, 'network': 1.0},
        'europe-west1': {'storage': 1.0, 'api': 1.0, 'network': 1.2},
        'asia-southeast1': {'storage': 1.0, 'api': 1.0, 'network': 1.15},
        'australia-southeast1': {'storage': 1.1, 'api': 1.1, 'network': 1.3}
    }
    
    @classmethod
    def get_region_multiplier(cls, region: str, cost_type: str = 'storage') -> float:
        """Get region-specific cost multiplier"""
        if region not in cls.REGION_MULTIPLIERS:
            logger.warning(f"Unknown region {region}, using us-central1 pricing")
            region = 'us-central1'
        
        return cls.REGION_MULTIPLIERS[region].get(cost_type, 1.0)
    
    @classmethod
    def get_available_regions(cls) -> List[str]:
        """Get list of supported regions"""
        return list(cls.REGION_MULTIPLIERS.keys())
    
    @staticmethod
    def validate_region(region: str) -> bool:
        """Validate if region is supported"""
        return region in RegionManager.REGION_MULTIPLIERS
