#!/usr/bin/env python3
"""
Test script to verify the 700 TiB fixed data scenario works correctly.
This tests that:
1. Month 1: All 700 TiB is in Standard storage
2. Month 2+: Data transitions between tiers but total remains 700 TiB
3. No new data is added when growth rate is 0%
"""

import sys
import os
sys.path.append('streamlit_app')

# Import the simulation function
from app import simulate_autoclass_with_objects

def test_700tb_scenario():
    print("Testing 700 TiB Fixed Data Scenario")
    print("=" * 50)
    
    # Test parameters - 700 TiB with 0% growth
    initial_data_gb = 700000  # 700 TiB = 700,000 GB
    monthly_growth_rate = 0.0  # 0% growth = fixed data
    avg_object_size_large_kib = 512
    avg_object_size_small_kib = 64
    percent_large_objects = 0.8  # 80% eligible for autoclass
    months = 12
    nearline_read_rate = 0.2  # 20% accessed monthly
    coldline_read_rate = 0.3  # 30% accessed monthly  
    archive_read_rate = 0.1   # 10% accessed monthly
    reads = 10000
    writes = 1000
    
    # Run simulation
    df = simulate_autoclass_with_objects(
        initial_data_gb=initial_data_gb,
        monthly_growth_rate=monthly_growth_rate,
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
    
    print(f"Initial Data: {initial_data_gb:,} GB (700 TiB)")
    print(f"Growth Rate: {monthly_growth_rate}%")
    print(f"Months: {months}")
    print()
    
    # Check key metrics for first few months
    for i in range(min(6, len(df))):
        row = df.iloc[i]
        total_data = row["Total Data (GB)"]
        standard = row["Standard (GB)"]
        nearline = row["Nearline (GB)"]
        coldline = row["Coldline (GB)"]
        archive = row["Archive (GB)"]
        
        print(f"Month {i+1}:")
        print(f"  Total Data: {total_data:,.1f} GB")
        print(f"  Standard: {standard:,.1f} GB ({standard/total_data*100:.1f}%)")
        print(f"  Nearline: {nearline:,.1f} GB ({nearline/total_data*100:.1f}%)")
        print(f"  Coldline: {coldline:,.1f} GB ({coldline/total_data*100:.1f}%)")
        print(f"  Archive: {archive:,.1f} GB ({archive/total_data*100:.1f}%)")
        print()
    
    # Verify total data remains constant
    total_data_values = df["Total Data (GB)"].tolist()
    expected_total = initial_data_gb
    
    print("Validation Results:")
    print("-" * 30)
    
    # Check if total data remains constant (within rounding tolerance)
    all_constant = all(abs(total - expected_total) < 1.0 for total in total_data_values)
    print(f"✓ Total data remains constant at {expected_total:,} GB: {all_constant}")
    
    # Check Month 1 starts with all data in Standard
    month1_standard = df.iloc[0]["Standard (GB)"]
    month1_total = df.iloc[0]["Total Data (GB)"]
    month1_all_standard = abs(month1_standard - month1_total) < 1.0
    print(f"✓ Month 1 has all data in Standard: {month1_all_standard}")
    
    # Check data transitions occur in later months
    final_month = df.iloc[-1]
    has_transitions = (final_month["Nearline (GB)"] > 0 or 
                      final_month["Coldline (GB)"] > 0 or 
                      final_month["Archive (GB)"] > 0)
    print(f"✓ Data transitions to colder tiers: {has_transitions}")
    
    # Show final distribution
    print(f"\nFinal Month Distribution:")
    print(f"  Standard: {final_month['Standard (GB)']:,.1f} GB")
    print(f"  Nearline: {final_month['Nearline (GB)']:,.1f} GB") 
    print(f"  Coldline: {final_month['Coldline (GB)']:,.1f} GB")
    print(f"  Archive: {final_month['Archive (GB)']:,.1f} GB")
    print(f"  Total: {final_month['Total Data (GB)']:,.1f} GB")
    
    return df

if __name__ == "__main__":
    test_700tb_scenario()
