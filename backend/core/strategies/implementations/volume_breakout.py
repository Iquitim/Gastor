import pandas as pd
from ..base import BaseStrategy
from core.indicators import calc_volume_ratio

class VolumeBreakout(BaseStrategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        lookback = int(self.get_param("lookback", 20))
        vol_mult = float(self.get_param("volume_mult", 2.0))
        price_break = float(self.get_param("price_break_pct", 1.0))
        
        # Volume Spike
        vol_ratio = calc_volume_ratio(df['volume'], lookback)
        vol_spike = vol_ratio > vol_mult
        
        # Price Jump: (Close / Open - 1) * 100 > pct
        price_jump = ((df['close'] / df['open'] - 1) * 100) > price_break
        
        df['buy_signal'] = vol_spike & price_jump
        
        # Exit: Break low of last N candles (simplified trailing)
        # Shift 1 to use previous N lows (breakdown support)
        low_n = df['low'].rolling(window=lookback).min()
        df['sell_signal'] = df['close'] < low_n.shift(1)
        
        return df
