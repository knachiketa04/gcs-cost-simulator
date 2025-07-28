# simulation.py - Core simulation logic for both strategies

import pandas as pd
from utils import format_storage_value, format_cost_value, get_storage_unit_and_value, get_cost_unit_and_value


def get_storage_class_by_age(age_days, terminal_class):
    """
    Determine storage class based on age and terminal configuration for TCO analysis.
    
    Uses standard GCS Autoclass transition thresholds:
    - Standard -> Nearline: 30 days
    - Nearline -> Coldline: 90 days  
    - Coldline -> Archive: 365 days
    """
    if terminal_class == "nearline":
        # Nearline terminal: Standard -> Nearline (stop)
        if age_days >= 30:
            return "nearline"
        else:
            return "standard"
    else:
        # Archive terminal: Standard -> Nearline -> Coldline -> Archive
        if age_days >= 365:
            return "archive"
        elif age_days >= 90:
            return "coldline"
        elif age_days >= 30:
            return "nearline"
        else:
            return "standard"


def process_generation_lifecycle(gen, storage_classes, access_rates, pricing, month):
    """Process a single generation for lifecycle strategy with transition operation costs"""
    total_objects = gen["objects"]
    transition_cost = 0  # Track specific transition costs for lifecycle transitions
    
    # Check if transition occurred this month (age-based lifecycle transitions)
    current_class = get_storage_class_by_age(gen["age_days"], "archive")  # Lifecycle goes to archive
    previous_class = get_storage_class_by_age(gen["age_days"] - 30, "archive")  # Previous month's class
    
    if current_class != previous_class:
        # Lifecycle transition occurred - apply specific transition cost based on transition type
        if previous_class == "standard" and current_class == "nearline":
            transition_cost = gen["objects"] * pricing["lifecycle_transitions"]["standard_to_nearline"]
        elif previous_class == "nearline" and current_class == "coldline":
            transition_cost = gen["objects"] * pricing["lifecycle_transitions"]["nearline_to_coldline"]
        elif previous_class == "coldline" and current_class == "archive":
            transition_cost = gen["objects"] * pricing["lifecycle_transitions"]["coldline_to_archive"]
    
    # Calculate retrieval costs based on access patterns
    retrieval_costs = {"nearline": 0, "coldline": 0, "archive": 0}
    
    # Determine storage class based on age
    age_days = gen["age_days"]
    if age_days >= 365:
        storage_class = "archive"
        if access_rates["archive"] > 0:
            retrieval_costs["archive"] += gen["size"] * access_rates["archive"] * pricing["retrieval_costs"]["archive"]
    elif age_days >= 90:
        storage_class = "coldline"
        if access_rates["coldline"] > 0:
            retrieval_costs["coldline"] += gen["size"] * access_rates["coldline"] * pricing["retrieval_costs"]["coldline"]
    elif age_days >= 30:
        storage_class = "nearline"
        if access_rates["nearline"] > 0:
            retrieval_costs["nearline"] += gen["size"] * access_rates["nearline"] * pricing["retrieval_costs"]["nearline"]
    else:
        storage_class = "standard"
    
    # Add to storage class
    storage_classes[storage_class] += gen["size"]
    
    # Age the generation for next month
    gen["age_days"] += 30
    
    return total_objects, retrieval_costs, transition_cost


def process_generation_autoclass(gen, storage_classes, access_rates, terminal_storage_class, month, pricing):
    """Process a single generation for autoclass strategy with accurate re-promotion logic and operation charges"""
    original_size = gen["size"]
    remaining_size = gen["size"]
    original_objects = gen["objects"]
    remaining_objects = gen["objects"]
    total_eligible_objects = 0
    new_generations = []
    transition_operations = 0  # Track Class A operations for transitions
    
    storage_class = get_storage_class_by_age(gen["age_days"], terminal_storage_class)
    
    # Handle Standard tier data lifecycle (hot vs cold data behavior)
    if storage_class == "standard":
        # Every month, split Standard data into hot (stays) and cold (transitions)
        hot_data_portion = access_rates["standard"]  # Percentage that stays hot
        cold_data_portion = 1 - access_rates["standard"]  # Percentage that becomes cold
        
        hot_volume = original_size * hot_data_portion
        cold_volume = original_size * cold_data_portion
        hot_objects = original_objects * hot_data_portion
        cold_objects = original_objects * cold_data_portion
        
        # Hot data stays in Standard (reset age to keep it hot)
        if hot_volume > 0.001:
            new_generations.append({
                "size": hot_volume,
                "age_days": 0,  # Reset age for hot data - stays hot
                "objects": hot_objects,
                "created_month": month
            })
            storage_classes["standard"] += hot_volume
            total_eligible_objects += hot_objects
        
        # Cold data: if it's been in Standard for 30+ days, move to Nearline
        if gen["age_days"] >= 30:
            # Cold data that's ready to transition to Nearline
            if cold_volume > 0.001:
                storage_classes["nearline"] += cold_volume
                total_eligible_objects += cold_objects
        else:
            # Cold data that's still aging toward Nearline transition
            if cold_volume > 0.001:
                new_generations.append({
                    "size": cold_volume,
                    "age_days": gen["age_days"] + 30,  # Age it normally
                    "objects": cold_objects,
                    "created_month": gen["created_month"]
                })
                storage_classes["standard"] += cold_volume
                total_eligible_objects += cold_objects
                
        return total_eligible_objects, new_generations, transition_operations
    
    # Handle access and re-promotion for colder tiers (data moves freely in Autoclass)
    access_rate = access_rates.get(storage_class, 0)
    if access_rate > 0 and storage_class != "standard":
        accessed_volume = original_size * access_rate
        accessed_objects = original_objects * access_rate
        
        # Calculate transition operation charges based on source storage class
        # From docs: "When Autoclass transitions an object from Coldline storage or Archive storage to
        # Standard storage or Nearline storage, each transition incurs a Class A operation charge"
        if storage_class in ["coldline", "archive"] and accessed_volume > 0.001:
            transition_operations += accessed_objects  # Each object access = 1 Class A operation
        
        # Re-promote accessed data to standard (create new generation)
        if accessed_volume > 0.001:  # Only create if significant size
            new_generations.append({
                "size": accessed_volume,
                "age_days": 0,
                "objects": accessed_objects,
                "created_month": month
            })
            # Add re-promoted data to Standard storage class
            storage_classes["standard"] += accessed_volume
            # Count re-promoted objects in total eligible objects
            total_eligible_objects += accessed_objects
        
        # Update current generation (remove accessed portion)
        remaining_size -= accessed_volume
        remaining_objects -= accessed_objects
        gen["size"] = remaining_size
        gen["objects"] = remaining_objects

    # Add remaining data to appropriate storage class
    if remaining_size > 0.001:  # Only process significant sizes
        storage_classes[storage_class] += remaining_size
        total_eligible_objects += remaining_objects
        
        # Age the generation for next month
        gen["age_days"] += 30
        return total_eligible_objects, [gen] + new_generations, transition_operations
    
    return total_eligible_objects, new_generations, transition_operations


def optimize_generations(generations, max_generations=150):
    """Smart merging that preserves age accuracy while reducing generation count"""
    if len(generations) <= max_generations:
        return generations
        
    # Sort by size and keep largest generations intact
    generations.sort(key=lambda x: x["size"], reverse=True)
    large_generations = generations[:100]  # Keep 100 largest
    small_generations = generations[100:]   # Merge the rest
    
    # Group small generations by their natural storage tier based on age
    tier_groups = {
        "standard": [],    # age < 30 days
        "nearline": [],    # 30 <= age < 90 days  
        "coldline": [],    # 90 <= age < 365 days
        "archive": []      # age >= 365 days
    }
    
    for gen in small_generations:
        age = gen["age_days"]
        if age >= 365:
            tier_groups["archive"].append(gen)
        elif age >= 90:
            tier_groups["coldline"].append(gen)
        elif age >= 30:
            tier_groups["nearline"].append(gen)
        else:
            tier_groups["standard"].append(gen)
    
    # Merge within each tier, preserving age accuracy
    for tier, tier_gens in tier_groups.items():
        if tier_gens:
            merged_size = sum(g["size"] for g in tier_gens)
            merged_objects = sum(g["objects"] for g in tier_gens)
            # Preserve the maximum age within the tier (most conservative)
            max_age = max(g["age_days"] for g in tier_gens)
            # Use the earliest creation month for tracking
            earliest_month = min(g["created_month"] for g in tier_gens)
            
            if merged_size > 0:
                large_generations.append({
                    "size": merged_size,
                    "age_days": max_age,  # Preserve actual age, not forced!
                    "objects": merged_objects,
                    "created_month": earliest_month
                })
    
    return large_generations


def simulate_storage_strategy(params, strategy_config):
    """Unified simulation function for both strategies"""
    
    generations = []
    results = []
    cumulative_non_eligible_objects = 0
    cumulative_non_eligible_data = 0
    strategy_type = strategy_config["type"]  # "autoclass" or "lifecycle"
    
    for month in range(1, params["months"] + 1):
        # Calculate new data (unified logic)
        if month == 1:
            monthly_data = params["initial_data_gb"]
        else:
            if params["monthly_growth_rate"] > 0:
                previous_total_data = sum(gen["size"] for gen in generations) + cumulative_non_eligible_data
                monthly_data = previous_total_data * params["monthly_growth_rate"]
            else:
                monthly_data = 0
        
        eligible_data = monthly_data * params["percent_large_objects"]
        non_eligible_data = monthly_data * (1 - params["percent_large_objects"])
        
        eligible_objects = (eligible_data * 1024 * 1024) / params["avg_object_size_large_kib"]
        non_eligible_objects = (non_eligible_data * 1024 * 1024) / params["avg_object_size_small_kib"]

        cumulative_non_eligible_objects += non_eligible_objects
        cumulative_non_eligible_data += non_eligible_data

        # Add new generation for eligible data
        if eligible_data > 0:
            generations.append({
                "size": eligible_data, 
                "age_days": 0, 
                "objects": eligible_objects,
                "created_month": month
            })

        # Initialize storage classes
        storage_classes = {"standard": cumulative_non_eligible_data, "nearline": 0, "coldline": 0, "archive": 0}
        
        # Strategy-specific processing
        if strategy_type == "autoclass":
            total_eligible_objects = 0
            active_generations = []
            new_generations = []
            total_transition_operations = 0
            
            for gen in generations:
                if gen["size"] < 0.001:  # Skip tiny generations
                    continue
                    
                gen_objects, gen_new_gens, gen_transition_ops = process_generation_autoclass(
                    gen, storage_classes, params["access_rates"], 
                    strategy_config["terminal_storage_class"], month, params["pricing"]
                )
                total_eligible_objects += gen_objects
                total_transition_operations += gen_transition_ops
                
                # Separate active and new generations
                for new_gen in gen_new_gens:
                    if new_gen["age_days"] == 0:  # New generation from re-promotion
                        new_generations.append(new_gen)
                    else:  # Aged existing generation
                        active_generations.append(new_gen)
            
            generations = active_generations + new_generations
            total_objects = total_eligible_objects + cumulative_non_eligible_objects
            
            # Calculate costs with Autoclass-specific pricing
            storage_cost = sum(storage_classes[c] * params["pricing"][c]["storage"] for c in storage_classes)
            
            # API costs: Base operations + transition operations (Class A charges for coldline/archive→standard)
            base_api_cost = (params["reads"] * params["pricing"]["operations"]["class_b"]) + (params["writes"] * params["pricing"]["operations"]["class_a"])
            transition_api_cost = total_transition_operations * params["pricing"]["operations"]["class_a"]
            api_cost = base_api_cost + transition_api_cost
            
            autoclass_fee = (total_eligible_objects / 1000) * params["pricing"]["autoclass_fee_per_1000_objects_per_month"]
            special_cost = autoclass_fee
            special_label = "Autoclass Fee ($)"
            special_formatted = "Autoclass Fee (Formatted)"
            
        else:  # lifecycle
            total_objects = cumulative_non_eligible_objects
            total_retrieval_cost = 0
            total_transition_cost = 0
            storage_classes = {"standard": 0, "nearline": 0, "coldline": 0, "archive": 0}
            active_generations = []
            
            for gen in generations:
                if gen["size"] < 0.001:  # Skip tiny generations
                    continue
                    
                gen_objects, retrieval_costs, transition_cost = process_generation_lifecycle(
                    gen, storage_classes, params["access_rates"], params["pricing"], month
                )
                total_objects += gen_objects
                total_retrieval_cost += sum(retrieval_costs.values())
                total_transition_cost += transition_cost
                active_generations.append(gen)
            
            generations = active_generations
            
            # Calculate costs
            storage_cost = sum(storage_classes[c] * params["pricing"][c]["storage"] for c in storage_classes)
            
            # API costs: Base operations + lifecycle transition costs (direct $ costs, not per-operation)
            base_api_cost = (params["reads"] * params["pricing"]["operations"]["class_b"]) + (params["writes"] * params["pricing"]["operations"]["class_a"])
            api_cost = base_api_cost + total_transition_cost
            special_cost = total_retrieval_cost
            special_label = "Retrieval Cost ($)"
            special_formatted = "Retrieval Cost (Formatted)"
        
        # Optimize generations periodically
        if len(generations) > 150:
            generations = optimize_generations(generations)
        
        total_cost = storage_cost + api_cost + special_cost
        total_data = sum(storage_classes.values())

        # Build result row
        result = {
            "Month": f"Month {month}",
            # Raw values for calculations (always in GB and $)
            "Standard (GB)": round(storage_classes["standard"], 2),
            "Nearline (GB)": round(storage_classes["nearline"], 2),
            "Coldline (GB)": round(storage_classes["coldline"], 2),
            "Archive (GB)": round(storage_classes["archive"], 2),
            "Total Data (GB)": round(total_data, 2),
            special_label: round(special_cost, 2),
            "Storage Cost ($)": round(storage_cost, 2),
            "API Cost ($)": round(api_cost, 2),
            "Total Cost ($)": round(total_cost, 2),
            # Formatted values for display
            "Standard (Formatted)": format_storage_value(storage_classes["standard"]),
            "Nearline (Formatted)": format_storage_value(storage_classes["nearline"]),
            "Coldline (Formatted)": format_storage_value(storage_classes["coldline"]),
            "Archive (Formatted)": format_storage_value(storage_classes["archive"]),
            "Total Data (Formatted)": format_storage_value(total_data),
            special_formatted: format_cost_value(special_cost),
            "Storage Cost (Formatted)": format_cost_value(storage_cost),
            "API Cost (Formatted)": format_cost_value(api_cost),
            "Total Cost (Formatted)": format_cost_value(total_cost)
        }
        
        # Add strategy-specific fields
        if strategy_type == "autoclass":
            result["Total Eligible Objects"] = round(total_eligible_objects, 0)
            result["Total Non-Eligible Objects"] = round(cumulative_non_eligible_objects, 0)
        else:
            result["Total Objects"] = round(total_objects, 0)
        
        results.append(result)

    return pd.DataFrame(results)
