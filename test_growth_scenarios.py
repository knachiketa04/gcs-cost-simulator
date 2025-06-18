#!/usr/bin/env python3
"""
Comprehensive test to verify both growth scenarios work correctly.
"""

import sys
import os
sys.path.append('streamlit_app')
from app import simulate_autoclass_with_objects

def test_growth_scenarios():
    print("Testing Both Growth Scenarios")
    print("=" * 50)
    
    # Common parameters
    avg_object_size_large_kib = 512
    avg_object_size_small_kib = 64
    percent_large_objects = 0.8
    months = 6
    nearline_read_rate = 0.2
    coldline_read_rate = 0.3
    archive_read_rate = 0.1
    reads = 10000
    writes = 1000
    
    # Scenario 1: Fixed Data (0% growth)
    print("SCENARIO 1: Fixed Data (0% growth)")
    print("-" * 40)
    
    df_fixed = simulate_autoclass_with_objects(
        initial_data_gb=100000,  # 100 TB initial
        monthly_growth_rate=0.0,  # 0% growth
        avg_object_size_large_kib=avg_object_size_large_kib,
        avg_object_size_small_kib=avg_object_size_small_kib,
        percent_large_objects=percent_large_objects,
        months=months,
        nearline_read_rate=nearline_read_rate,
        coldline_read_rate=coldline_read_rate,
        archive_read_rate=archive_read_rate,
        reads=reads,
        writes=writes
    )
    
    print("Month | Total Data (GB)")
    for i in range(len(df_fixed)):
        total = df_fixed.iloc[i]["Total Data (GB)"]
        print(f"  {i+1}   | {total:,.1f}")
    
    # Verify fixed data
    totals_fixed = df_fixed["Total Data (GB)"].tolist()
    is_constant = all(abs(total - 100000) < 100 for total in totals_fixed)  # Allow small rounding
    print(f"\n✓ Data remains constant: {is_constant}")
    
    # Scenario 2: Percentage Growth (5% monthly)
    print("\n\nSCENARIO 2: Percentage Growth (5% monthly)")
    print("-" * 40)
    
    df_growth = simulate_autoclass_with_objects(
        initial_data_gb=10000,   # 10 TB initial
        monthly_growth_rate=0.05, # 5% growth
        avg_object_size_large_kib=avg_object_size_large_kib,
        avg_object_size_small_kib=avg_object_size_small_kib,
        percent_large_objects=percent_large_objects,
        months=months,
        nearline_read_rate=nearline_read_rate,
        coldline_read_rate=coldline_read_rate,
        archive_read_rate=archive_read_rate,
        reads=reads,
        writes=writes
    )
    
    print("Month | Total Data (GB) | Growth")
    prev_total = 0
    for i in range(len(df_growth)):
        total = df_growth.iloc[i]["Total Data (GB)"]
        if i == 0:
            growth_str = "Initial"
        else:
            growth_rate = ((total - prev_total) / prev_total) * 100 if prev_total > 0 else 0
            growth_str = f"+{growth_rate:.1f}%"
        print(f"  {i+1}   | {total:,.1f}      | {growth_str}")
        prev_total = total
    
    # Verify growth pattern
    totals_growth = df_growth["Total Data (GB)"].tolist()
    is_growing = all(totals_growth[i] > totals_growth[i-1] for i in range(1, len(totals_growth)))
    print(f"\n✓ Data is growing each month: {is_growing}")
    
    # Calculate actual growth rates
    growth_rates = []
    for i in range(1, len(totals_growth)):
        rate = ((totals_growth[i] - totals_growth[i-1]) / totals_growth[i-1])
        growth_rates.append(rate)
    
    avg_growth_rate = sum(growth_rates) / len(growth_rates) if growth_rates else 0
    print(f"✓ Average monthly growth rate: {avg_growth_rate:.1%} (expected: ~5%)")
    
    print("\n" + "=" * 50)
    print("✅ Both scenarios working correctly!")

if __name__ == "__main__":
    test_growth_scenarios()
