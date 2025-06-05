# Custom Oscillators for Commodity Finance Analysis
# Based on "Trading Systems and Methods" by Perry J. Kaufman
# Specialized oscillators for energy and commodity markets

import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Optional
import warnings
warnings.filterwarnings('ignore')


def clean_oscillator_values(values: List[float]) -> List[float]:
    """
    Clean oscillator values by replacing NaN and infinite values with 0
    This ensures JSON serialization works properly
    """
    cleaned = []
    for val in values:
        if pd.isna(val) or np.isinf(val):
            cleaned.append(0.0)
        else:
            cleaned.append(float(val))
    return cleaned


def calculate_kaufman_adaptive_moving_average(prices: List[float], period: int = 10, fast_sc: float = 2.0, slow_sc: float = 30.0) -> List[float]:
    """
    Kaufman's Adaptive Moving Average (KAMA) - Chapter 3
    Adapts to market volatility by adjusting smoothing based on efficiency ratio
    """
    prices = np.array(prices)
    kama = np.zeros_like(prices)
    
    if len(prices) < period:
        return [np.nan] * len(prices)
    
    # Initialize first value
    kama[period-1] = prices[period-1]
    
    # Calculate smoothing constants
    fastest_sc = 2.0 / (fast_sc + 1)
    slowest_sc = 2.0 / (slow_sc + 1)
    
    for i in range(period, len(prices)):
        # Calculate change and volatility
        change = abs(prices[i] - prices[i-period])
        volatility = sum(abs(prices[j] - prices[j-1]) for j in range(i-period+1, i+1))
        
        # Calculate efficiency ratio
        er = change / volatility if volatility != 0 else 0
        
        # Calculate smoothing constant
        sc = (er * (fastest_sc - slowest_sc) + slowest_sc) ** 2
        
        # Calculate KAMA
        kama[i] = kama[i-1] + sc * (prices[i] - kama[i-1])
    
    return kama.tolist()


def calculate_price_oscillator(prices: List[float], short_period: int = 12, long_period: int = 26) -> List[float]:
    """
    Price Oscillator (Percentage) - Chapter 5
    Enhanced version showing percentage difference between two moving averages
    """
    prices = np.array(prices)
    short_ma = pd.Series(prices).rolling(window=short_period).mean()
    long_ma = pd.Series(prices).rolling(window=long_period).mean()
    
    # Calculate percentage oscillator
    oscillator = ((short_ma - long_ma) / long_ma * 100).fillna(0)
    return oscillator.tolist()


def calculate_commodity_channel_index_enhanced(high: List[float], low: List[float], close: List[float], 
                                             period: int = 20, factor: float = 0.015) -> List[float]:
    """
    Enhanced Commodity Channel Index - Chapter 5
    Kaufman's improved version with better sensitivity for commodity markets
    """
    high = np.array(high)
    low = np.array(low)
    close = np.array(close)
    
    # Calculate typical price
    typical_price = (high + low + close) / 3
    
    cci = []
    for i in range(len(typical_price)):
        if i < period - 1:
            cci.append(0.0)
        else:
            # Calculate moving average of typical price
            tp_slice = typical_price[i-period+1:i+1]
            tp_ma = np.mean(tp_slice)
            
            # Calculate mean deviation (Kaufman's preferred method)
            mean_deviation = np.mean(np.abs(tp_slice - tp_ma))
            
            # Calculate CCI
            if mean_deviation != 0:
                cci_value = (typical_price[i] - tp_ma) / (factor * mean_deviation)
            else:
                cci_value = 0
            
            cci.append(cci_value)
    
    return clean_oscillator_values(cci)


def calculate_momentum_oscillator(prices: List[float], period: int = 10) -> List[float]:
    """
    Momentum Oscillator - Chapter 4
    Simple but effective momentum calculation as described by Kaufman
    """
    prices = np.array(prices)
    momentum = []
    
    for i in range(len(prices)):
        if i < period:
            momentum.append(0.0)
        else:
            mom_value = prices[i] - prices[i-period]
            momentum.append(mom_value)
    
    return clean_oscillator_values(momentum)


def calculate_rate_of_change_oscillator(prices: List[float], period: int = 12) -> List[float]:
    """
    Rate of Change Oscillator - Chapter 4
    Percentage-based momentum oscillator preferred for commodity analysis
    """
    prices = np.array(prices)
    roc = []
    
    for i in range(len(prices)):
        if i < period or prices[i-period] == 0:
            roc.append(0.0)
        else:
            roc_value = ((prices[i] - prices[i-period]) / prices[i-period]) * 100
            roc.append(roc_value)
    
    return clean_oscillator_values(roc)


def calculate_stochastic_momentum_index(high: List[float], low: List[float], close: List[float],
                                      period: int = 14, smooth_k: int = 3, smooth_d: int = 3) -> Tuple[List[float], List[float]]:
    """
    Stochastic Momentum Index - Chapter 5
    Kaufman's enhanced stochastic that works better in trending markets
    """
    high = np.array(high)
    low = np.array(low)
    close = np.array(close)
    
    # Calculate the difference between close and midpoint of the range
    midpoint = (high + low) / 2
    diff = close - midpoint
    
    # Calculate the range
    range_values = high - low
    
    # Calculate SMI
    smi_raw = []
    for i in range(len(close)):
        if i < period - 1:
            smi_raw.append(np.nan)
        else:
            # Sum of differences and ranges over the period
            sum_diff = np.sum(diff[i-period+1:i+1])
            sum_range = np.sum(range_values[i-period+1:i+1])
            
            if sum_range != 0:
                smi_value = (sum_diff / (sum_range / 2)) * 100
            else:
                smi_value = 0
            
            smi_raw.append(smi_value)
    
    # Smooth the SMI
    smi_k = pd.Series(smi_raw).rolling(window=smooth_k).mean().fillna(0).tolist()
    smi_d = pd.Series(smi_k).rolling(window=smooth_d).mean().fillna(0).tolist()
    
    return smi_k, smi_d


def calculate_accumulation_distribution_oscillator(high: List[float], low: List[float], 
                                                  close: List[float], volume: List[float],
                                                  short_period: int = 3, long_period: int = 10) -> List[float]:
    """
    Accumulation/Distribution Oscillator - Chapter 7
    Volume-weighted oscillator particularly useful for commodity markets
    """
    high = np.array(high)
    low = np.array(low)
    close = np.array(close)
    volume = np.array(volume)
    
    # Calculate Money Flow Multiplier
    clv = []
    for i in range(len(close)):
        if high[i] - low[i] != 0:
            clv_value = ((close[i] - low[i]) - (high[i] - close[i])) / (high[i] - low[i])
        else:
            clv_value = 0
        clv.append(clv_value)
    
    # Calculate Money Flow Volume
    mfv = np.array(clv) * volume
    
    # Calculate Accumulation/Distribution Line
    ad_line = np.cumsum(mfv)
    
    # Calculate short and long moving averages
    ad_short = pd.Series(ad_line).rolling(window=short_period).mean()
    ad_long = pd.Series(ad_line).rolling(window=long_period).mean()
    
    # Calculate oscillator
    ad_oscillator = (ad_short - ad_long).fillna(0)
    
    return ad_oscillator.tolist()


def calculate_kaufman_efficiency_ratio(prices: List[float], period: int = 10) -> List[float]:
    """
    Efficiency Ratio - Chapter 3
    Measures market efficiency and trend strength
    """
    prices = np.array(prices)
    efficiency_ratio = []
    
    for i in range(len(prices)):
        if i < period:
            efficiency_ratio.append(0.0)
        else:
            # Calculate net change
            net_change = abs(prices[i] - prices[i-period])
            
            # Calculate total change (volatility)
            total_change = sum(abs(prices[j] - prices[j-1]) for j in range(i-period+1, i+1))
            
            # Calculate efficiency ratio
            if total_change != 0:
                er = net_change / total_change
            else:
                er = 0
            
            efficiency_ratio.append(er)
    
    return clean_oscillator_values(efficiency_ratio)