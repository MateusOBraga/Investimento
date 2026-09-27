"""
indicators.py
Cálculo de indicadores técnicos usados na análise das ações.
Todas as funções recebem/retornam pandas.Series.
"""

import pandas as pd
import numpy as np


def sma(series: pd.Series, window: int) -> pd.Series:
    """Média Móvel Simples."""
    return series.rolling(window=window, min_periods=window).mean()


def ema(series: pd.Series, window: int) -> pd.Series:
    """Média Móvel Exponencial."""
    return series.ewm(span=window, adjust=False).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Índice de Força Relativa (RSI)."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi_value = 100 - (100 / (1 + rs))
    return rsi_value.fillna(50)  # neutro quando não há dados suficientes


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """MACD: retorna (linha_macd, linha_sinal, histograma)."""
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def bollinger_bands(series: pd.Series, window: int = 20, num_std: float = 2.0):
    """Bandas de Bollinger: retorna (banda_superior, media, banda_inferior)."""
    mid = sma(series, window)
    std = series.rolling(window=window, min_periods=window).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    return upper, mid, lower


def volume_trend(volume: pd.Series, window: int = 20) -> pd.Series:
    """Razão entre volume atual e a média móvel de volume (>1 = acima da média)."""
    avg_vol = sma(volume, window)
    return volume / avg_vol.replace(0, np.nan)
