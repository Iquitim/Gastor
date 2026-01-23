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
# INDICADORES ESTATÍSTICOS (CONSTRUTOR)
# =============================================================================

def calc_zscore(data: pd.Series, period: int = 20) -> pd.Series:
    """Z-Score - Mede quantos desvios padrão o preço está da média.
    
    Fórmula: (x - mean) / std
    Interpretação: |Z| > 2 indica desvio significativo
    """
    mean = data.rolling(window=period).mean()
    std = data.rolling(window=period).std()
    return (data - mean) / (std + 1e-10)


def calc_mad(data: pd.Series, period: int = 20) -> pd.Series:
    """MAD (Median Absolute Deviation) - Dispersão robusta a outliers.
    
    Fórmula: median(|x - median(x)|)
    Mais estável que desvio padrão para dados com outliers.
    """
    median = data.rolling(window=period).median()
    return (data - median).abs().rolling(window=period).median()


def calc_zscore_robust(data: pd.Series, period: int = 20) -> pd.Series:
    """Z-Score Robusto - Versão robusta usando mediana e MAD.
    
    Fórmula: (x - median) / (MAD * 1.4826)
    O fator 1.4826 normaliza o MAD para ser comparável ao desvio padrão.
    """
    median = data.rolling(window=period).median()
    mad = calc_mad(data, period)
    return (data - median) / (mad * 1.4826 + 1e-10)


def calc_bollinger_pctb(data: pd.Series, period: int = 20, std_dev: float = 2.0) -> pd.Series:
    """Bollinger %B - Posição percentual do preço dentro das bandas.
    
    Fórmula: (close - lower) / (upper - lower)
    Interpretação: 0 = banda inferior, 1 = banda superior, >1 ou <0 = fora das bandas
    """
    upper, middle, lower = calc_bollinger_bands(data, period, std_dev)
    return (data - lower) / (upper - lower + 1e-10)


def calc_roc(data: pd.Series, period: int = 12) -> pd.Series:
    """ROC (Rate of Change) - Variação percentual entre períodos.
    
    Fórmula: ((close / close_N) - 1) * 100
    Mede momentum como percentual de mudança.
    """
    return ((data / data.shift(period)) - 1) * 100


def calc_stochastic(close: pd.Series, high: pd.Series, low: pd.Series, 
                    period: int = 14, smooth_k: int = 3, smooth_d: int = 3) -> Tuple[pd.Series, pd.Series]:
    """Stochastic Oscillator - Posição do preço dentro do range.
    
    Fórmula: %K = (close - low_N) / (high_N - low_N) * 100
    
    Returns:
        Tuple: (%K suavizado, %D linha de sinal)
    Interpretação: >80 = sobrecomprado, <20 = sobrevendido
    """
    lowest_low = low.rolling(window=period).min()
    highest_high = high.rolling(window=period).max()
    
    stoch_k = ((close - lowest_low) / (highest_high - lowest_low + 1e-10)) * 100
    stoch_k = stoch_k.rolling(window=smooth_k).mean()  # Suavização
    stoch_d = stoch_k.rolling(window=smooth_d).mean()  # Linha de sinal
    
    return stoch_k, stoch_d


def calc_volume_ratio(volume: pd.Series, period: int = 20) -> pd.Series:
    """Volume Ratio - Volume atual relativo à média histórica.
    
    Fórmula: volume / SMA(volume, N)
    Interpretação: >1.5 = volume alto (confirmação), <0.5 = volume baixo (fraqueza)
    """
    avg_volume = volume.rolling(window=period).mean()
    return volume / (avg_volume + 1e-10)


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
