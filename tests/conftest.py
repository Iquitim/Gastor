"""
Pytest Fixtures - Configurações compartilhadas para testes.

Fornece dados de teste e mocks para isolar testes do Streamlit.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import sys


# =============================================================================
# MOCK DO STREAMLIT
# =============================================================================

class MockSessionState(dict):
    """Mock do session_state que suporta get() como o Streamlit."""
    def get(self, key, default=None):
        return super().get(key, default)

@pytest.fixture(autouse=True)
def mock_streamlit():
    """
    Mock automático do Streamlit para todos os testes.
    Isso permite executar código que usa st.session_state sem Streamlit rodando.
    """
    mock_st = MagicMock()
    mock_st.session_state = MockSessionState({
        'sb_coin': 'SOL/USDT',
        'initial_balance': 10000.0,
        # NÃO inclui custom_exchange_fee e custom_slippage 
        # para que o código use os valores padrão
    })
    
    with patch.dict(sys.modules, {'streamlit': mock_st}):
        yield mock_st


# =============================================================================
# FIXTURES DE DADOS
# =============================================================================

@pytest.fixture
def sample_ohlcv_data():
    """
    Gera DataFrame com dados OHLCV sintéticos para testes.
    100 candles com tendência de alta seguida de queda.
    """
    np.random.seed(42)  # Reprodutibilidade
    
    n_candles = 100
    base_price = 100.0
    
    # Cria tendência: alta por 50 candles, queda por 50
    trend = np.concatenate([
        np.linspace(0, 20, 50),  # Alta
        np.linspace(20, 5, 50)   # Queda
    ])
    
    # Adiciona ruído
    noise = np.random.randn(n_candles) * 2
    close = base_price + trend + noise
    
    # Gera OHLC baseado no close
    high = close + np.abs(np.random.randn(n_candles)) * 1.5
    low = close - np.abs(np.random.randn(n_candles)) * 1.5
    open_price = close + np.random.randn(n_candles) * 0.5
    volume = np.random.randint(1000, 10000, n_candles).astype(float)
    
    # Cria índice de timestamps
    start_date = datetime(2025, 1, 1)
    timestamps = [start_date + timedelta(hours=i) for i in range(n_candles)]
    
    df = pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=pd.DatetimeIndex(timestamps))
    
    return df


@pytest.fixture
def sample_df_with_indicators(sample_ohlcv_data):
    """
    DataFrame com indicadores técnicos pré-calculados.
    """
    from src.core.indicators import calc_rsi, calc_ema, calc_sma, calc_atr, calc_bollinger_bands, calc_macd
    
    df = sample_ohlcv_data.copy()
    
    # Calcula indicadores
    df['rsi'] = calc_rsi(df['close'], 14)
    df['ema_9'] = calc_ema(df['close'], 9)
    df['ema_21'] = calc_ema(df['close'], 21)
    df['sma_20'] = calc_sma(df['close'], 20)
    df['atr'] = calc_atr(df['high'], df['low'], df['close'], 14)
    
    bb_upper, bb_middle, bb_lower = calc_bollinger_bands(df['close'], 20, 2.0)
    df['bb_upper'] = bb_upper
    df['bb_middle'] = bb_middle
    df['bb_lower'] = bb_lower
    
    macd_line, signal_line = calc_macd(df['close'])
    df['macd'] = macd_line
    df['macd_signal'] = signal_line
    
    return df


@pytest.fixture
def sample_trades():
    """
    Lista de trades de exemplo para testes de portfólio.
    """
    base_time = datetime(2025, 1, 1, 10, 0)
    
    return [
        {'action': 'BUY', 'price': 100.0, 'amount': 10.0, 'timestamp': base_time, 'coin': 'SOL/USDT'},
        {'action': 'SELL', 'price': 110.0, 'amount': 10.0, 'timestamp': base_time + timedelta(hours=5), 'coin': 'SOL/USDT'},
        {'action': 'BUY', 'price': 105.0, 'amount': 10.0, 'timestamp': base_time + timedelta(hours=10), 'coin': 'SOL/USDT'},
        {'action': 'SELL', 'price': 108.0, 'amount': 10.0, 'timestamp': base_time + timedelta(hours=15), 'coin': 'SOL/USDT'},
    ]


@pytest.fixture
def invalid_trades():
    """
    Lista de trades inválidos para testar sanitização.
    Inclui venda sem saldo e trades fora de ordem.
    """
    base_time = datetime(2025, 1, 1, 10, 0)
    
    return [
        # Venda sem compra prévia (inválida)
        {'action': 'SELL', 'price': 100.0, 'amount': 5.0, 'timestamp': base_time, 'coin': 'SOL/USDT'},
        # Compra válida
        {'action': 'BUY', 'price': 100.0, 'amount': 10.0, 'timestamp': base_time + timedelta(hours=1), 'coin': 'SOL/USDT'},
        # Venda maior que o saldo (deve ajustar ou remover)
        {'action': 'SELL', 'price': 110.0, 'amount': 15.0, 'timestamp': base_time + timedelta(hours=2), 'coin': 'SOL/USDT'},
    ]
