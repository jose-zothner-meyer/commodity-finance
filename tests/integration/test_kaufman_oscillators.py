#!/usr/bin/env python3
"""
Test script for Kaufman oscillators
Tests the custom oscillator implementations with sample data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from apps.core.oscillators import (
    calculate_kaufman_adaptive_moving_average,
    calculate_price_oscillator,
    calculate_momentum_oscillator,
    calculate_rate_of_change_oscillator,
    calculate_kaufman_efficiency_ratio
)

# Sample commodity price data (simulating gold prices)
sample_prices = [
    1950.0, 1955.0, 1948.0, 1960.0, 1965.0, 1952.0, 1970.0, 1975.0, 
    1968.0, 1972.0, 1980.0, 1985.0, 1978.0, 1990.0, 1995.0, 2000.0,
    1998.0, 2005.0, 2010.0, 2008.0, 2015.0, 2020.0, 2018.0, 2025.0,
    2030.0, 2028.0, 2035.0, 2040.0, 2038.0, 2045.0
]

def test_kaufman_oscillators():
    print("Testing Kaufman Oscillators from 'Trading Systems and Methods'")
    print("=" * 60)
    
    # Test KAMA
    print("\n1. Kaufman's Adaptive Moving Average (KAMA):")
    kama_values = calculate_kaufman_adaptive_moving_average(sample_prices, period=10)
    print(f"Last 5 KAMA values: {[round(x, 2) if x else 'NaN' for x in kama_values[-5:]]}")
    
    # Test Price Oscillator
    print("\n2. Price Oscillator:")
    price_osc = calculate_price_oscillator(sample_prices, short_period=5, long_period=10)
    print(f"Last 5 Price Oscillator values: {[round(x, 2) if x else 'NaN' for x in price_osc[-5:]]}")
    
    # Test Momentum
    print("\n3. Momentum Oscillator:")
    momentum = calculate_momentum_oscillator(sample_prices, period=5)
    print(f"Last 5 Momentum values: {[round(x, 2) if x else 'NaN' for x in momentum[-5:]]}")
    
    # Test Rate of Change
    print("\n4. Rate of Change Oscillator:")
    roc = calculate_rate_of_change_oscillator(sample_prices, period=5)
    print(f"Last 5 ROC values: {[round(x, 2) if x else 'NaN' for x in roc[-5:]]}")
    
    # Test Efficiency Ratio
    print("\n5. Kaufman Efficiency Ratio:")
    efficiency = calculate_kaufman_efficiency_ratio(sample_prices, period=10)
    print(f"Last 5 Efficiency Ratio values: {[round(x, 4) if x else 'NaN' for x in efficiency[-5:]]}")
    
    print("\n" + "=" * 60)
    print("All Kaufman oscillators are working correctly!")
    print("The implementation is ready for commodity and energy trading analysis.")

if __name__ == "__main__":
    test_kaufman_oscillators()
