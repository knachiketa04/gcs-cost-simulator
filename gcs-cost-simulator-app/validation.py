# validation.py - Minimal critical validation for GCS configuration

def run_comprehensive_tco_validation(analysis_mode, config, terminal_storage_class, lifecycle_rules):
    """
    Run only critical validation checks that would break the simulation.
    Returns empty warnings list and only critical errors.
    """
    warnings = []  # No more warnings
    errors = []
    
    # Critical error: Object size threshold validation (breaks Autoclass simulation)
    if config.get("avg_object_size_large_kib", 512) < 128:
        errors.append(f"❌ **Configuration Error**: Large objects must be ≥128 KiB (currently {config['avg_object_size_large_kib']} KiB)")
    
    if config.get("avg_object_size_small_kib", 64) >= 128:
        errors.append(f"❌ **Configuration Error**: Small objects must be <128 KiB (currently {config['avg_object_size_small_kib']} KiB)")
    
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
