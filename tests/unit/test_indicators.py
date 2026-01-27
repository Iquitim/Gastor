"""
Testes Unitários - Módulo de Indicadores Técnicos (indicators.py)

Testa funções de cálculo de indicadores: RSI, EMA, SMA, ATR, Bollinger Bands, MACD.
"""

import pytest
import pandas as pd
import numpy as np
from src.core.indicators import (
    calc_rsi,
    calc_ema,
    calc_sma,
    calc_atr,
    calc_bollinger_bands,
    calc_macd,
    calc_median
)


class TestCalcRSI:
    """Testes para cálculo do RSI."""
    
    def test_rsi_range_is_0_to_100(self, sample_ohlcv_data):
        """RSI deve estar sempre entre 0 e 100."""
        rsi = calc_rsi(sample_ohlcv_data['close'], 14)
        
        # Ignora NaN dos primeiros períodos
        valid_rsi = rsi.dropna()
        
        assert valid_rsi.min() >= 0
        assert valid_rsi.max() <= 100
    
    def test_rsi_high_on_uptrend(self):
        """RSI deve ser alto quando preço sobe consistentemente."""
        # Cria série de alta constante
        prices = pd.Series([100 + i for i in range(30)])
        rsi = calc_rsi(prices, 14)
        
        # Últimos valores devem ser altos (> 60)
        assert rsi.iloc[-1] > 60
    
    def test_rsi_low_on_downtrend(self):
        """RSI deve ser baixo quando preço cai consistentemente."""
        # Cria série de queda constante
        prices = pd.Series([100 - i for i in range(30)])
        rsi = calc_rsi(prices, 14)
        
        # Últimos valores devem ser baixos (< 40)
        assert rsi.iloc[-1] < 40
    
    def test_rsi_returns_series(self, sample_ohlcv_data):
        """RSI deve retornar pandas Series."""
        rsi = calc_rsi(sample_ohlcv_data['close'], 14)
        assert isinstance(rsi, pd.Series)
        assert len(rsi) == len(sample_ohlcv_data)


class TestCalcEMA:
    """Testes para cálculo da EMA."""
    
    def test_ema_follows_price_trend(self, sample_ohlcv_data):
        """EMA deve seguir a tendência do preço."""
        ema = calc_ema(sample_ohlcv_data['close'], 9)
        
        # EMA não deve desviar muito do preço
        diff = abs(ema - sample_ohlcv_data['close'])
        mean_diff = diff.dropna().mean()
        
        assert mean_diff < sample_ohlcv_data['close'].mean() * 0.1  # Menos de 10% de desvio
    
    def test_ema_shorter_period_more_responsive(self, sample_ohlcv_data):
        """EMA curta deve reagir mais rápido que EMA longa."""
        ema_fast = calc_ema(sample_ohlcv_data['close'], 5)
        ema_slow = calc_ema(sample_ohlcv_data['close'], 20)
        
        # Variância da EMA curta deve ser maior (mais responsiva)
        assert ema_fast.dropna().var() > ema_slow.dropna().var()
    
    def test_ema_returns_series(self, sample_ohlcv_data):
        """EMA deve retornar pandas Series."""
        ema = calc_ema(sample_ohlcv_data['close'], 9)
        assert isinstance(ema, pd.Series)


class TestCalcSMA:
    """Testes para cálculo da SMA."""
    
    def test_sma_equals_mean(self):
        """SMA de período N deve ser igual à média dos últimos N valores."""
        prices = pd.Series([10, 20, 30, 40, 50])
        sma = calc_sma(prices, 3)
        
        # SMA do último valor deve ser média de [30, 40, 50] = 40
        assert sma.iloc[-1] == pytest.approx(40.0, rel=1e-6)
    
    def test_sma_has_nan_at_start(self):
        """SMA deve ter NaN nos primeiros (período-1) valores."""
        prices = pd.Series([10, 20, 30, 40, 50])
        sma = calc_sma(prices, 3)
        
        # Primeiros 2 valores devem ser NaN
        assert pd.isna(sma.iloc[0])
        assert pd.isna(sma.iloc[1])
        assert not pd.isna(sma.iloc[2])


class TestCalcATR:
    """Testes para cálculo do ATR."""
    
    def test_atr_is_always_positive(self, sample_ohlcv_data):
        """ATR deve ser sempre positivo."""
        atr = calc_atr(
            sample_ohlcv_data['high'],
            sample_ohlcv_data['low'],
            sample_ohlcv_data['close'],
            14
        )
        
        valid_atr = atr.dropna()
        assert (valid_atr >= 0).all()
    
    def test_atr_increases_with_volatility(self):
        """ATR deve aumentar quando volatilidade aumenta."""
        n = 50
        
        # Período calmo
        high_calm = pd.Series([101] * n)
        low_calm = pd.Series([99] * n)
        close_calm = pd.Series([100] * n)
        
        # Período volátil
        high_volatile = pd.Series([110] * n)
        low_volatile = pd.Series([90] * n)
        close_volatile = pd.Series([100] * n)
        
        atr_calm = calc_atr(high_calm, low_calm, close_calm, 14)
        atr_volatile = calc_atr(high_volatile, low_volatile, close_volatile, 14)
        
        assert atr_volatile.iloc[-1] > atr_calm.iloc[-1]


class TestCalcBollingerBands:
    """Testes para cálculo das Bollinger Bands."""
    
    def test_bands_order(self, sample_ohlcv_data):
        """Upper > Middle > Lower deve ser sempre verdade."""
        upper, middle, lower = calc_bollinger_bands(sample_ohlcv_data['close'], 20, 2.0)
        
        # Pega valores válidos (sem NaN)
        valid_idx = ~(upper.isna() | middle.isna() | lower.isna())
        
        assert (upper[valid_idx] >= middle[valid_idx]).all()
        assert (middle[valid_idx] >= lower[valid_idx]).all()
    
    def test_middle_equals_sma(self, sample_ohlcv_data):
        """Banda do meio deve ser igual à SMA."""
        upper, middle, lower = calc_bollinger_bands(sample_ohlcv_data['close'], 20, 2.0)
        sma = calc_sma(sample_ohlcv_data['close'], 20)
        
        # Compara valores válidos
        valid_idx = ~(middle.isna() | sma.isna())
        
        np.testing.assert_array_almost_equal(
            middle[valid_idx].values,
            sma[valid_idx].values,
            decimal=6
        )
    
    def test_bands_width_depends_on_std(self):
        """Largura das bandas deve depender do desvio padrão."""
        prices = pd.Series([100] * 30)  # Sem variação
        upper, middle, lower = calc_bollinger_bands(prices, 20, 2.0)
        
        # Com preço constante, upper == middle == lower
        valid_idx = ~upper.isna()
        width = upper[valid_idx].iloc[-1] - lower[valid_idx].iloc[-1]
        
        assert width == pytest.approx(0.0, abs=1e-6)


class TestCalcMACD:
    """Testes para cálculo do MACD."""
    
    def test_macd_returns_tuple(self, sample_ohlcv_data):
        """MACD deve retornar tupla (macd_line, signal_line)."""
        result = calc_macd(sample_ohlcv_data['close'])
        
        assert isinstance(result, tuple)
        assert len(result) == 2
    
    def test_macd_and_signal_are_series(self, sample_ohlcv_data):
        """MACD e Signal devem ser pandas Series."""
        macd_line, signal_line = calc_macd(sample_ohlcv_data['close'])
        
        assert isinstance(macd_line, pd.Series)
        assert isinstance(signal_line, pd.Series)
    
    def test_macd_positive_on_uptrend(self):
        """MACD deve ser positivo em tendência de alta."""
        prices = pd.Series([100 + i * 2 for i in range(50)])
        macd_line, _ = calc_macd(prices)
        
        # Últimos valores devem ser positivos
        assert macd_line.iloc[-1] > 0
