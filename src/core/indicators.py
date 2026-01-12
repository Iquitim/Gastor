"""
Gastor Core - Módulo de Indicadores Técnicos

Contém todas as funções de cálculo de indicadores usadas pelas estratégias.
"""

import pandas as pd
import numpy as np
from typing import Tuple


# =============================================================================
# MÉDIAS MÓVEIS
# =============================================================================

def calc_ema(data: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average"""
    return data.ewm(span=period, adjust=False).mean()


def calc_sma(data: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average"""
    return data.rolling(window=period).mean()


def calc_median(data: pd.Series, period: int = 50) -> pd.Series:
    """Mediana Móvel - alternativa à média para reduzir impacto de outliers"""
    return data.rolling(window=period).median()


# =============================================================================
# OSCILADORES
# =============================================================================

def calc_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index"""
    delta = data.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-10)
    return 100 - (100 / (1 + rs))


def calc_macd(data: pd.Series) -> Tuple[pd.Series, pd.Series]:
    """MACD (Moving Average Convergence Divergence)
    
    Returns:
        Tuple: (macd_line, signal_line)
    """
    ema12 = calc_ema(data, 12)
    ema26 = calc_ema(data, 26)
    macd = ema12 - ema26
    signal = calc_ema(macd, 9)
    return macd, signal


# =============================================================================
# VOLATILIDADE
# =============================================================================

def calc_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average True Range - medida de volatilidade"""
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def calc_bollinger_bands(data: pd.Series, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Bollinger Bands
    
    Returns:
        Tuple: (upper_band, middle_band, lower_band)
    """
    middle = calc_sma(data, period)
    std = data.rolling(window=period).std()
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    return upper, middle, lower


# =============================================================================
# CANAIS E BREAKOUT
# =============================================================================

def calc_donchian(high: pd.Series, low: pd.Series, period: int = 20) -> Tuple[pd.Series, pd.Series]:
    """Donchian Channel
    
    Returns:
        Tuple: (upper, lower)
    """
    upper = high.rolling(window=period).max()
    lower = low.rolling(window=period).min()
    return upper, lower


# =============================================================================
# SINAIS DE ENTRADA (LONG)
# =============================================================================

def signal_ema_cross_long(close: pd.Series, fast: int = 9, slow: int = 21) -> pd.Series:
    """Sinal de entrada LONG: EMA rápida cruza acima da lenta"""
    ema_fast = calc_ema(close, fast)
    ema_slow = calc_ema(close, slow)
    cross_up = (ema_fast > ema_slow).astype(int).diff() == 1
    return cross_up


def signal_rsi_oversold(close: pd.Series, period: int = 14, level: int = 30) -> pd.Series:
    """Sinal de entrada LONG: RSI abaixo do nível (oversold)"""
    rsi = calc_rsi(close, period)
    return rsi < level


def signal_macd_cross_long(close: pd.Series) -> pd.Series:
    """Sinal de entrada LONG: MACD cruza acima da linha de sinal"""
    macd, signal = calc_macd(close)
    cross_up = (macd > signal).astype(int).diff() == 1
    return cross_up


def signal_breakout_long(close: pd.Series, high: pd.Series, low: pd.Series, period: int = 20) -> pd.Series:
    """Sinal de entrada LONG: Preço rompe topo do canal Donchian"""
    upper, _ = calc_donchian(high, low, period)
    return close > upper.shift(1)


def signal_median_cross_long(close: pd.Series, period: int = 50) -> pd.Series:
    """Sinal de entrada LONG: Preço cruza acima da mediana móvel"""
    median = calc_median(close, period)
    cross_up = (close > median).astype(int).diff() == 1
    return cross_up


# =============================================================================
# SINAIS DE ENTRADA (SHORT)
# =============================================================================

def signal_ema_cross_short(close: pd.Series, fast: int = 9, slow: int = 21) -> pd.Series:
    """Sinal de entrada SHORT: EMA rápida cruza abaixo da lenta"""
    ema_fast = calc_ema(close, fast)
    ema_slow = calc_ema(close, slow)
    cross_down = (ema_fast < ema_slow).astype(int).diff() == 1
    return cross_down


def signal_rsi_overbought(close: pd.Series, period: int = 14, level: int = 70) -> pd.Series:
    """Sinal de entrada SHORT: RSI acima do nível (overbought)"""
    rsi = calc_rsi(close, period)
    return rsi > level


def signal_macd_cross_short(close: pd.Series) -> pd.Series:
    """Sinal de entrada SHORT: MACD cruza abaixo da linha de sinal"""
    macd, signal = calc_macd(close)
    cross_down = (macd < signal).astype(int).diff() == 1
    return cross_down


def signal_breakdown_short(close: pd.Series, high: pd.Series, low: pd.Series, period: int = 20) -> pd.Series:
    """Sinal de entrada SHORT: Preço rompe fundo do canal Donchian"""
    _, lower = calc_donchian(high, low, period)
    return close < lower.shift(1)


def signal_median_cross_short(close: pd.Series, period: int = 50) -> pd.Series:
    """Sinal de entrada SHORT: Preço cruza abaixo da mediana móvel"""
    median = calc_median(close, period)
    cross_down = (close < median).astype(int).diff() == 1
    return cross_down
