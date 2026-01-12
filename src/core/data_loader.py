"""
Data loading and configuration constants.
"""

import pandas as pd
import streamlit as st

from src.data_manager import DataManager
from src.core.indicators import calc_ema, calc_rsi, calc_bollinger_bands, calc_macd
from src.core.config import COINS, COMMISSION, SLIPPAGE, TOTAL_FEE  # Re-exporta do config


def load_data(coin: str, days: int) -> pd.DataFrame:
    """
    Carrega dados da moeda.
    
    Retorna:
        visible_df: DataFrame com os N dias solicitados (para Trading/ML treino)
        
    Session State:
        oot_df: 30 dias extras para validação OOT do ML
        full_df: N dias completos para Laboratório de Estratégias (sem corte OOT)
    """
    dm = DataManager()
    # Carrega N + 30 dias extras para ter OOT
    df = dm.get_ccxt_historical_data(coin, '1h', days + 30, 'binance')
    
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
