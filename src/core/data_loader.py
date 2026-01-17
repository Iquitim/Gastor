"""
Data loading and configuration constants.
"""

import pandas as pd
import streamlit as st

from src.data_manager import DataManager
from src.core.indicators import calc_ema, calc_rsi, calc_bollinger_bands, calc_macd
from src.core.config import COINS, COMMISSION, SLIPPAGE, TOTAL_FEE  # Re-exporta do config
from src.core.data_fetchers import (
    fetch_coingecko_ohlc,
    fetch_cryptocompare_ohlcv,
    AVAILABLE_DATA_SOURCES,
)


def load_data(coin: str, days: int, data_source: str = "auto") -> pd.DataFrame:
    """
    Carrega dados da moeda da fonte especificada.
    
    Args:
        coin: Par de trading (ex: BTC/USDT)
        days: Número de dias de histórico
        data_source: Fonte de dados (auto, ccxt_binance, ccxt_binanceus, coingecko, cryptocompare)
    
    Retorna:
        visible_df: DataFrame com os N dias solicitados (para Trading/ML treino)
        
    Session State:
        oot_df: 30 dias extras para validação OOT do ML
        full_df: N dias completos para Laboratório de Estratégias (sem corte OOT)
        data_source_used: Fonte de dados que foi realmente utilizada
        data_source_error: Erro (se houver) da fonte primária
    """
    df = None
    source_used = None
    error_message = None
    
    # Reset session state
    st.session_state.using_simulated_data = False
    st.session_state.data_source_used = None
    st.session_state.data_source_error = None
    
    dm = DataManager()
    
    # Carrega N + 30 dias extras para ter OOT
    total_days = days + 30
    
    if data_source == "auto":
        # Tenta todas as fontes em ordem
        sources_order = ["ccxt_binance", "ccxt_binanceus", "coingecko", "cryptocompare"]
        
        for src in sources_order:
            df, error = _fetch_from_source(src, coin, total_days, dm)
            if df is not None and len(df) > 0:
                source_used = src
                break
            error_message = error
        
        if df is None or len(df) == 0:
            st.session_state.data_source_error = error_message or "Todas as fontes falharam"
            
    elif data_source in ["ccxt_binance", "ccxt_binanceus"]:
        exchange = "binance" if data_source == "ccxt_binance" else "binanceus"
        try:
            df = dm.get_ccxt_historical_data(coin, '1h', total_days, exchange)
            source_used = data_source
        except Exception as e:
            error_message = f"{type(e).__name__}: {e}"
            st.session_state.data_source_error = f"Erro com {data_source}: {error_message}"
            
    elif data_source == "coingecko":
        df = fetch_coingecko_ohlc(coin, total_days)
        if df is not None:
            source_used = "coingecko"
        else:
            st.session_state.data_source_error = "CoinGecko não retornou dados. Tente outra fonte."
            
    elif data_source == "cryptocompare":
        df = fetch_cryptocompare_ohlcv(coin, total_days)
        if df is not None:
            source_used = "cryptocompare"
        else:
            st.session_state.data_source_error = "CryptoCompare não retornou dados. Tente outra fonte."
    
    # Fallback para dados simulados se tudo falhar
    if df is None or len(df) == 0:
        print("[DataLoader] ⚠️ Usando dados simulados como último recurso")
        df = dm._generate_simulated_data(coin.replace("/", ""), total_days * 24)
        source_used = "simulated"
    
    # Registra fonte utilizada
    st.session_state.data_source_used = source_used
    
    # Adiciona Features para análise inicial
    df['ema9'] = calc_ema(df['close'], 9)
    df['ema21'] = calc_ema(df['close'], 21)
    df['ema50'] = calc_ema(df['close'], 50)
    df['rsi'] = calc_rsi(df['close'], 14)
    bb_upper, bb_mid, bb_lower = calc_bollinger_bands(df['close'], 20, 2)
    df['bb_upper'] = bb_upper
    df['bb_mid'] = bb_mid
    df['bb_lower'] = bb_lower
    
    # MACD
    macd_line, signal = calc_macd(df['close'])
    hist = macd_line - signal
    df['macd'] = macd_line
    df['macd_signal'] = signal
    df['macd_hist'] = hist
    
    # SEPARAÇÃO OOT (Out of Time)
    # Reserva os últimos 30 dias para validação "blind" do ML
    oot_hours = 30 * 24  # 30 dias em horas
    
    if len(df) > oot_hours:
        oot_df = df.iloc[-oot_hours:].copy()
        visible_df = df.iloc[:-oot_hours].copy()
        
        st.session_state.oot_df = oot_df
        
        # FULL DF para Laboratório de Estratégias (sem corte OOT)
        # Usa exatamente os N dias solicitados (N*24 horas)
        requested_hours = days * 24
        st.session_state.full_df = df.iloc[-requested_hours:].copy()
    else:
        # Fallback se tiver poucos dados
        visible_df = df.copy()
        st.session_state.oot_df = pd.DataFrame()
        st.session_state.full_df = df.copy()
        
    return visible_df


def _fetch_from_source(source: str, coin: str, days: int, dm: DataManager) -> tuple:
    """
    Tenta buscar dados de uma fonte específica.
    
    Returns:
        (DataFrame ou None, mensagem de erro ou None)
    """
    try:
        if source == "ccxt_binance":
            df = dm.get_ccxt_historical_data(coin, '1h', days, 'binance')
            return (df, None) if df is not None and len(df) > 0 else (None, "Binance não retornou dados")
            
        elif source == "ccxt_binanceus":
            df = dm.get_ccxt_historical_data(coin, '1h', days, 'binanceus')
            return (df, None) if df is not None and len(df) > 0 else (None, "BinanceUS não retornou dados")
            
        elif source == "coingecko":
            df = fetch_coingecko_ohlc(coin, days)
            return (df, None) if df is not None and len(df) > 0 else (None, "CoinGecko não retornou dados")
            
        elif source == "cryptocompare":
            df = fetch_cryptocompare_ohlcv(coin, days)
            return (df, None) if df is not None and len(df) > 0 else (None, "CryptoCompare não retornou dados")
            
    except Exception as e:
        return (None, f"{type(e).__name__}: {e}")
    
    return (None, f"Fonte desconhecida: {source}")
