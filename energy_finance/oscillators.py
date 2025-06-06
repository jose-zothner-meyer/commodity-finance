# Custom Oscillators for Commodity Finance Analysis
# Based on "Trading Systems and Methods" by Perry J. Kaufman
# Enhanced with John Ehlers' Digital Signal Processing Oscillators
# Specialized oscillators for energy and commodity markets

import numpy as np
import pandas as pd
from typing import List, Tuple
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
    prices_arr = np.array(prices)
    kama = np.zeros_like(prices_arr)
    
    if len(prices) < period:
        return [np.nan] * len(prices)
    
    # Initialize first value
    kama[period-1] = prices_arr[period-1]
    
    # Calculate smoothing constants
    fastest_sc = 2.0 / (fast_sc + 1)
    slowest_sc = 2.0 / (slow_sc + 1)
    
    for i in range(period, len(prices_arr)):
        # Calculate change and volatility
        change = abs(prices_arr[i] - prices_arr[i-period])
        volatility = sum(abs(prices_arr[j] - prices_arr[j-1]) for j in range(i-period+1, i+1))
        
        # Calculate efficiency ratio
        er = change / volatility if volatility != 0 else 0
        
        # Calculate smoothing constant
        sc = (er * (fastest_sc - slowest_sc) + slowest_sc) ** 2
        
        # Calculate KAMA
        kama[i] = kama[i-1] + sc * (prices_arr[i] - kama[i-1])
    
    return kama.tolist()


def calculate_price_oscillator(prices: List[float], short_period: int = 12, long_period: int = 26) -> List[float]:
    """
    Price Oscillator (Percentage) - Chapter 5
    Enhanced version showing percentage difference between two moving averages
    """
    prices_arr = np.array(prices)
    short_ma = pd.Series(prices_arr).rolling(window=short_period).mean()
    long_ma = pd.Series(prices_arr).rolling(window=long_period).mean()
    
    # Calculate percentage oscillator
    oscillator = ((short_ma - long_ma) / long_ma * 100).fillna(0)
    return oscillator.tolist()


def calculate_commodity_channel_index_enhanced(high: List[float], low: List[float], close: List[float], 
                                             period: int = 20, factor: float = 0.015) -> List[float]:
    """
    Enhanced Commodity Channel Index - Chapter 5
    Kaufman's improved version with better sensitivity for commodity markets
    """
    high_arr = np.array(high)
    low_arr = np.array(low)
    close_arr = np.array(close)
    
    # Calculate typical price
    typical_price = (high_arr + low_arr + close_arr) / 3
    
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
    prices_arr = np.array(prices)
    momentum = []
    
    for i in range(len(prices_arr)):
        if i < period:
            momentum.append(0.0)
        else:
            mom_value = prices_arr[i] - prices_arr[i-period]
            momentum.append(mom_value)
    
    return clean_oscillator_values(momentum)


def calculate_rate_of_change_oscillator(prices: List[float], period: int = 12) -> List[float]:
    """
    Rate of Change Oscillator - Chapter 4
    Percentage-based momentum oscillator preferred for commodity analysis
    """
    prices_arr = np.array(prices)
    roc = []
    
    for i in range(len(prices_arr)):
        if i < period or prices_arr[i-period] == 0:
            roc.append(0.0)
        else:
            roc_value = ((prices_arr[i] - prices_arr[i-period]) / prices_arr[i-period]) * 100
            roc.append(roc_value)
    
    return clean_oscillator_values(roc)


def calculate_stochastic_momentum_index(high: List[float], low: List[float], close: List[float],
                                      period: int = 14, smooth_k: int = 3, smooth_d: int = 3) -> Tuple[List[float], List[float]]:
    """
    Stochastic Momentum Index - Chapter 5
    Kaufman's enhanced stochastic that works better in trending markets
    """
    high_arr = np.array(high)
    low_arr = np.array(low)
    close_arr = np.array(close)
    
    # Calculate the difference between close and midpoint of the range
    midpoint = (high_arr + low_arr) / 2
    diff = close_arr - midpoint
    
    # Calculate the range
    range_values = high_arr - low_arr
    
    # Calculate SMI
    smi_raw = []
    for i in range(len(close_arr)):
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
    high_arr = np.array(high)
    low_arr = np.array(low)
    close_arr = np.array(close)
    volume_arr = np.array(volume)
    
    # Calculate Money Flow Multiplier
    clv = []
    for i in range(len(close_arr)):
        if high_arr[i] - low_arr[i] != 0:
            clv_value = ((close_arr[i] - low_arr[i]) - (high_arr[i] - close_arr[i])) / (high_arr[i] - low_arr[i])
        else:
            clv_value = 0
        clv.append(clv_value)
    
    # Calculate Money Flow Volume
    mfv = np.array(clv) * volume_arr
    
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
    prices_arr = np.array(prices)
    efficiency_ratio = []
    
    for i in range(len(prices_arr)):
        if i < period:
            efficiency_ratio.append(0.0)
        else:
            # Calculate net change
            net_change = abs(prices_arr[i] - prices_arr[i-period])
            
            # Calculate total change (volatility)
            total_change = sum(abs(prices_arr[j] - prices_arr[j-1]) for j in range(i-period+1, i+1))
            
            # Calculate efficiency ratio
            if total_change != 0:
                er = net_change / total_change
            else:
                er = 0
            
            efficiency_ratio.append(er)
    
    return clean_oscillator_values(efficiency_ratio)


# ============================================================================
# JOHN EHLERS DIGITAL SIGNAL PROCESSING OSCILLATORS
# Based on "Cybernetic Analysis for Stocks and Futures" by John F. Ehlers
# ============================================================================

def calculate_ehlers_fisher_transform(prices: List[float], period: int = 10) -> List[float]:
    """
    Ehlers Fisher Transform - Converts prices to Gaussian normal distribution
    Excellent for identifying turning points in commodity markets
    Reference: "Cybernetic Analysis for Stocks and Futures"
    """
    prices_arr = np.array(prices, dtype=float)
    fisher = []
    value1 = []
    
    for i in range(len(prices_arr)):
        if i < period - 1:
            fisher.append(0.0)
            value1.append(0.0)
        else:
            # Calculate highest and lowest in period
            high_period = np.max(prices_arr[i-period+1:i+1])
            low_period = np.min(prices_arr[i-period+1:i+1])
            
            # Normalize price between -1 and 1
            if high_period != low_period:
                value = 2.0 * (prices_arr[i] - low_period) / (high_period - low_period) - 1.0
            else:
                value = 0.0
                
            # Limit value to prevent overflow
            value = max(-0.999, min(0.999, value))
            
            # Smooth with previous value
            if i == period - 1:
                value1_smooth = value
            else:
                value1_smooth = 0.66 * value + 0.34 * value1[-1]
            
            value1.append(value1_smooth)
            
            # Calculate Fisher Transform
            if value1_smooth != 0:
                fisher_value = 0.5 * np.log((1 + value1_smooth) / (1 - value1_smooth))
            else:
                fisher_value = 0.0
            
            # Smooth Fisher Transform
            if i == period - 1:
                fisher_smooth = fisher_value
            else:
                fisher_smooth = 0.5 * fisher_value + 0.5 * fisher[-1]
            
            fisher.append(fisher_smooth)
    
    return clean_oscillator_values(fisher)


def calculate_ehlers_stochastic_cg(high: List[float], low: List[float], close: List[float], period: int = 8) -> List[float]:
    """
    Ehlers Stochastic Center of Gravity Oscillator
    Uses center of gravity to smooth stochastic and reduce noise
    Reference: "Rocket Science for Traders"
    """
    high_arr = np.array(high, dtype=float)
    low_arr = np.array(low, dtype=float)
    close_arr = np.array(close, dtype=float)
    
    stoch_cg = []
    
    for i in range(len(close_arr)):
        if i < period - 1:
            stoch_cg.append(0.0)
        else:
            # Calculate stochastic for the period
            stoch_values = []
            for j in range(i - period + 1, i + 1):
                period_high = np.max(high_arr[max(0, j-period+1):j+1])
                period_low = np.min(low_arr[max(0, j-period+1):j+1])
                
                if period_high != period_low:
                    stoch = (close_arr[j] - period_low) / (period_high - period_low) * 100
                else:
                    stoch = 50.0
                
                stoch_values.append(stoch)
            
            # Calculate Center of Gravity
            numerator = sum((k + 1) * stoch_values[k] for k in range(len(stoch_values)))
            denominator = sum(stoch_values)
            
            if denominator != 0:
                cg = -numerator / denominator + (period + 1) / 2.0
                cg_normalized = (cg / period) * 100
            else:
                cg_normalized = 50.0
            
            stoch_cg.append(cg_normalized)
    
    return clean_oscillator_values(stoch_cg)


def calculate_ehlers_super_smoother(prices: List[float], period: int = 10) -> List[float]:
    """
    Ehlers Super Smoother - Two-pole Butterworth filter
    Removes high-frequency noise while preserving low-frequency trends
    Reference: "Cybernetic Analysis for Stocks and Futures"
    """
    prices_arr = np.array(prices, dtype=float)
    
    # Calculate filter coefficients
    a1 = np.exp(-1.414 * np.pi / period)
    b1 = 2 * a1 * np.cos(1.414 * np.pi / period)
    c2 = b1
    c3 = -a1 * a1
    c1 = 1 - c2 - c3
    
    filt = []
    
    for i in range(len(prices_arr)):
        if i < 2:
            filt.append(prices_arr[i])
        else:
            filt_value = c1 * (prices_arr[i] + prices_arr[i-1]) / 2 + c2 * filt[i-1] + c3 * filt[i-2]
            filt.append(filt_value)
    
    return clean_oscillator_values(filt)


def calculate_ehlers_cycle_period(prices: List[float]) -> List[float]:
    """
    Ehlers Autocorrelation Periodogram - Measures dominant cycle period
    Useful for determining the optimal period for other indicators
    Reference: "Cycle Analytics for Traders"
    """
    prices_arr = np.array(prices, dtype=float)
    
    # Apply Super Smoother first
    smooth_prices = calculate_ehlers_super_smoother(prices, 7)
    smooth_prices_arr = np.array(smooth_prices)
    
    periods = []
    
    for i in range(len(prices_arr)):
        if i < 7:
            periods.append(20.0)  # Default period
        else:
            # Calculate autocorrelations for different periods
            maxCorr = 0
            bestPeriod = 20
            
            for period in range(8, min(50, i)):
                if i >= period:
                    # Calculate correlation
                    correlation = 0
                    count = 0
                    
                    for j in range(period):
                        if i - j - period >= 0:
                            correlation += smooth_prices_arr[i - j] * smooth_prices_arr[i - j - period]
                            count += 1
                    
                    if count > 0:
                        correlation /= count
                        
                        if correlation > maxCorr:
                            maxCorr = correlation
                            bestPeriod = period
            
            periods.append(float(bestPeriod))
    
    return clean_oscillator_values(periods)


def calculate_ehlers_mama(prices: List[float], fast_limit: float = 0.5, slow_limit: float = 0.05) -> Tuple[List[float], List[float]]:
    """
    Ehlers MESA Adaptive Moving Average (MAMA) and Following Adaptive Moving Average (FAMA)
    Adapts to the current cycle period of the market
    Reference: "MESA and Trading Market Cycles"
    """
    prices_arr = np.array(prices, dtype=float)
    
    # Initialize arrays
    mama = [prices_arr[0]]
    fama = [prices_arr[0]]
    period = [20.0]
    smooth = [prices_arr[0]]
    detrender = [0.0]
    i1 = [0.0]
    q1 = [0.0]
    ji = [0.0]
    jq = [0.0]
    i2 = [0.0]
    q2 = [0.0]
    re = [0.0]
    im = [0.0]
    
    for i in range(1, len(prices_arr)):
        # Super Smoother
        if i < 4:
            smooth_val = prices_arr[i]
        else:
            smooth_val = (4 * prices_arr[i] + 3 * prices_arr[i-1] + 2 * prices_arr[i-2] + prices_arr[i-3]) / 10
        smooth.append(smooth_val)
        
        # Detrend
        if i < 6:
            detrender.append(0.0)
        else:
            detrender.append((0.0962 * smooth[i] + 0.5769 * smooth[i-2] - 0.5769 * smooth[i-4] - 0.0962 * smooth[i-6]) * (0.075 * period[i-1] + 0.54))
        
        # Compute InPhase and Quadrature components
        if i < 3:
            i1.append(0.0)
            q1.append(0.0)
        else:
            i1.append(detrender[i-3])
            if i < 6:
                q1.append(0.0)
            else:
                q1.append((0.0962 * detrender[i] + 0.5769 * detrender[i-2] - 0.5769 * detrender[i-4] - 0.0962 * detrender[i-6]) * (0.075 * period[i-1] + 0.54))
        
        # Advance the phase by 90 degrees
        if i < 6:
            ji.append(0.0)
            jq.append(0.0)
        else:
            ji.append((0.0962 * i1[i] + 0.5769 * i1[i-2] - 0.5769 * i1[i-4] - 0.0962 * i1[i-6]) * (0.075 * period[i-1] + 0.54))
            jq.append((0.0962 * q1[i] + 0.5769 * q1[i-2] - 0.5769 * q1[i-4] - 0.0962 * q1[i-6]) * (0.075 * period[i-1] + 0.54))
        
        # Phasor addition
        i2.append(i1[i] - q1[i])
        q2.append(q1[i] + i1[i])
        
        # Smooth the I and Q components
        i2[i] = 0.2 * i2[i] + 0.8 * i2[i-1] if i > 0 else i2[i]
        q2[i] = 0.2 * q2[i] + 0.8 * q2[i-1] if i > 0 else q2[i]
        
        # Homodyne discriminator
        re.append(i2[i] * i2[i-1] + q2[i] * q2[i-1] if i > 0 else 0.0)
        im.append(i2[i] * q2[i-1] - q2[i] * i2[i-1] if i > 0 else 0.0)
        
        # Smooth re and im
        re[i] = 0.2 * re[i] + 0.8 * re[i-1] if i > 0 else re[i]
        im[i] = 0.2 * im[i] + 0.8 * im[i-1] if i > 0 else im[i]
        
        # Calculate period
        if im[i] != 0 and re[i] != 0:
            new_period = 360 / (np.arctan(im[i] / re[i]) * 180 / np.pi)
        else:
            new_period = period[i-1] if i > 0 else 20.0
        
        # Constrain period
        new_period = max(6, min(50, new_period))
        period.append(0.2 * new_period + 0.8 * period[i-1] if i > 0 else new_period)
        
        # Calculate alpha
        alpha = fast_limit / period[i] if period[i] > 0 else fast_limit
        alpha = max(slow_limit, min(fast_limit, alpha))
        
        # Calculate MAMA and FAMA
        mama_val = alpha * prices_arr[i] + (1 - alpha) * mama[i-1] if i > 0 else prices_arr[i]
        fama_val = 0.5 * alpha * mama_val + (1 - 0.5 * alpha) * fama[i-1] if i > 0 else prices_arr[i]
        
        mama.append(mama_val)
        fama.append(fama_val)
    
    return clean_oscillator_values(mama), clean_oscillator_values(fama)


def calculate_ehlers_sinewave_indicator(prices: List[float]) -> Tuple[List[float], List[float]]:
    """
    Ehlers Sinewave Indicator - Identifies cycle mode vs trend mode
    Returns sine and leadsine components
    Reference: "Rocket Science for Traders"
    """
    prices_arr = np.array(prices, dtype=float)
    
    # Get MAMA values first
    mama_values, _ = calculate_ehlers_mama(prices)
    mama_arr = np.array(mama_values)
    
    sine = []
    leadsine = []
    
    # Initialize DCPeriod and other variables
    dcperiod = [20.0]
    
    for i in range(len(prices_arr)):
        if i < 5:
            sine.append(0.0)
            leadsine.append(0.0)
            if i > 0:
                dcperiod.append(dcperiod[-1])
        else:
            # Calculate dominant cycle period using autocorrelation
            maxCorr = 0
            dc_period = 20
            
            for period in range(8, min(50, i)):
                corr = 0
                count = 0
                for j in range(period):
                    if i - j - period >= 0:
                        corr += mama_arr[i-j] * mama_arr[i-j-period]
                        count += 1
                if count > 0:
                    corr /= count
                    if corr > maxCorr:
                        maxCorr = corr
                        dc_period = period
            
            dcperiod.append(0.25 * dc_period + 0.75 * dcperiod[-1])
            
            # Calculate sine wave
            sine_val = np.sin(2 * np.pi / dcperiod[i])
            leadsine_val = np.sin(2 * np.pi / dcperiod[i] + np.pi/4)  # Lead by 45 degrees
            
            sine.append(sine_val)
            leadsine.append(leadsine_val)
    
    return clean_oscillator_values(sine), clean_oscillator_values(leadsine)


def calculate_ehlers_hilbert_transform(prices: List[float]) -> List[float]:
    """
    Ehlers Hilbert Transform Discriminator - Measures instantaneous phase
    Excellent for cycle analysis and market timing
    Reference: "Cybernetic Analysis for Stocks and Futures"
    """
    prices_arr = np.array(prices, dtype=float)
    
    # Smooth the data first
    smooth = calculate_ehlers_super_smoother(prices, 7)
    smooth_arr = np.array(smooth)
    
    hilbert = []
    
    for i in range(len(prices_arr)):
        if i < 7:
            hilbert.append(0.0)
        else:
            # Calculate Hilbert Transform using 7-period
            ht_val = (smooth_arr[i-6] - smooth_arr[i-4] + 
                     0.5 * (smooth_arr[i-2] - smooth_arr[i]) + 
                     0.25 * (smooth_arr[i-5] - smooth_arr[i-1]) +
                     0.125 * (smooth_arr[i-3])) / 2.0
            
            hilbert.append(ht_val)
    
    return clean_oscillator_values(hilbert)