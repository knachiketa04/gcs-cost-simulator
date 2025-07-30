# validation.py - Minimal critical validation for GCS configuration

def validate_tco_configuration(config: dict) -> list:
    """Validate Total Cost of Ownership configuration for critical errors"""
    errors = []
    
    # Critical validation: Autoclass requires objects ≥128 KiB
    if config.get("avg_object_size_large_kib", 512) < 128:
        errors.append(f"❌ **Configuration Error**: Large objects must be ≥128 KiB (currently {config['avg_object_size_large_kib']} KiB)")
    
    # Critical validation: GCS maximum object size is 5 TiB (5,242,880 KiB)
    max_object_size_kib = 5 * 1024 * 1024  # 5 TiB in KiB
    if config.get("avg_object_size_large_kib", 512) > max_object_size_kib:
        errors.append(f"❌ **Configuration Error**: Objects cannot exceed 5 TiB ({max_object_size_kib:,} KiB). Currently: {config['avg_object_size_large_kib']:,} KiB")
    
    if config.get("avg_object_size_small_kib", 64) >= 128:
        errors.append(f"❌ **Configuration Error**: Small objects must be <128 KiB (currently {config['avg_object_size_small_kib']} KiB)")
    
    # Critical validation: Small objects cannot exceed 127 KiB
    if config.get("avg_object_size_small_kib", 64) > 127:
        errors.append(f"❌ **Configuration Error**: Small objects must be <128 KiB (currently {config['avg_object_size_small_kib']} KiB)")
    
    return errors


def run_comprehensive_tco_validation(analysis_mode, config, terminal_storage_class, lifecycle_rules):
    """
    Run only critical validation checks that would break the simulation.
    Returns empty warnings list and only critical errors.
    """
    warnings = []  # No more warnings
    errors = []
    
    # Critical error: Object size threshold validation (breaks Autoclass simulation)
    object_errors = validate_tco_configuration(config)
    errors.extend(object_errors)
    
    # Critical error: Pricing hierarchy validation (breaks cost calculations)
    pricing = config["pricing"]
    storage_prices = [
        ("Standard", pricing["standard"]["storage"]),
        ("Nearline", pricing["nearline"]["storage"]),
        ("Coldline", pricing["coldline"]["storage"]),
        ("Archive", pricing["archive"]["storage"])
    ]
    
    for i in range(len(storage_prices) - 1):
        current_name, current_price = storage_prices[i]
        next_name, next_price = storage_prices[i + 1]
        
        if current_price <= next_price:
            errors.append(f"❌ **TCO Error**: {current_name} (${current_price:.4f}) must cost more than {next_name} (${next_price:.4f})")
    
    return warnings, errors
