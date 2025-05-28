import numpy as np
from typing import List, Tuple

def calculate_rsi(prices: List[float], period: int = 14) -> List[float]:
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum()/period
    down = -seed[seed < 0].sum()/period
    rs = up/down if down != 0 else 0
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100./(1.+rs)
    for i in range(period, len(prices)):
        delta = deltas[i-1]
        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta
        up = (up*(period-1) + upval)/period
        down = (down*(period-1) + downval)/period
        rs = up/down if down != 0 else 0
        rsi[i] = 100. - 100./(1.+rs)
    return rsi.tolist()

def calculate_macd(prices: List[float], fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Tuple[List[float], List[float], List[float]]:
    prices = np.array(prices)
    exp1 = pd.Series(prices).ewm(span=fast_period, adjust=False).mean()
    exp2 = pd.Series(prices).ewm(span=slow_period, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=signal_period, adjust=False).mean()
    histogram = macd - signal
    return macd.tolist(), signal.tolist(), histogram.tolist()

def calculate_stochastic(prices: List[float], high_prices: List[float], low_prices: List[float], period: int = 14) -> List[float]:
    prices = np.array(prices)
    high_prices = np.array(high_prices)
    low_prices = np.array(low_prices)
    k = []
    for i in range(len(prices)):
        if i < period - 1:
            k.append(np.nan)
        else:
            lowest_low = np.min(low_prices[i-period+1:i+1])
            highest_high = np.max(high_prices[i-period+1:i+1])
            k.append(100 * ((prices[i] - lowest_low) / (highest_high - lowest_low) if highest_high != lowest_low else 0))
    return k

def calculate_cci(prices: List[float], high_prices: List[float], low_prices: List[float], period: int = 20) -> List[float]:
    prices = np.array(prices)
    high_prices = np.array(high_prices)
    low_prices = np.array(low_prices)
    tp = (high_prices + low_prices + prices) / 3
    cci = []
    for i in range(len(prices)):
        if i < period - 1:
            cci.append(np.nan)
        else:
            tp_slice = tp[i-period+1:i+1]
            tp_ma = np.mean(tp_slice)
            tp_std = np.std(tp_slice)
            cci.append((tp[i] - tp_ma) / (0.015 * tp_std) if tp_std != 0 else 0)
    return cci

def calculate_williams_r(prices: List[float], high_prices: List[float], low_prices: List[float], period: int = 14) -> List[float]:
    prices = np.array(prices)
    high_prices = np.array(high_prices)
    low_prices = np.array(low_prices)
    wr = []
    for i in range(len(prices)):
        if i < period - 1:
            wr.append(np.nan)
        else:
            highest_high = np.max(high_prices[i-period+1:i+1])
            lowest_low = np.min(low_prices[i-period+1:i+1])
            wr.append(-100 * ((highest_high - prices[i]) / (highest_high - lowest_low) if highest_high != lowest_low else 0))
    return wr 