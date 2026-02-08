import pandas as pd
from ..base import BaseStrategy
from core.indicators import calc_ema

class GoldenCross(BaseStrategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        fast = int(self.get_param("fast", 9))
        slow = int(self.get_param("slow", 21))
        
        # Calculate Indicators
        df['ema_fast'] = calc_ema(df['close'], fast)
        df['ema_slow'] = calc_ema(df['close'], slow)
        
        # Generate Signals (State-based logic)
        df['buy_signal'] = df['ema_fast'] > df['ema_slow']
        df['sell_signal'] = df['ema_fast'] < df['ema_slow']
        
        return df
