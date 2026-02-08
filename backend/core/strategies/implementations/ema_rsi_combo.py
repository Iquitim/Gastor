import pandas as pd
from ..base import BaseStrategy
from core.indicators import calc_ema, calc_rsi

class EMARSICombo(BaseStrategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        fast = int(self.get_param("fast_ema", 9))
        slow = int(self.get_param("slow_ema", 21))
        rsi_min = int(self.get_param("rsi_filter", 50))
        
        ema_fast = calc_ema(df['close'], fast)
        ema_slow = calc_ema(df['close'], slow)
        rsi = calc_rsi(df['close'], 14)
        
        df['ema_fast'] = ema_fast
        df['ema_slow'] = ema_slow
        df['rsi'] = rsi
        
        cross_up = (ema_fast > ema_slow) & (ema_fast.shift(1) <= ema_slow.shift(1))
        cross_down = (ema_fast < ema_slow) & (ema_fast.shift(1) >= ema_slow.shift(1))
        
        df['buy_signal'] = (ema_fast > ema_slow) & (rsi > rsi_min)
        df['sell_signal'] = cross_down
        
        return df
