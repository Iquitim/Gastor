import pandas as pd
from ..base import BaseStrategy
from core.indicators import calc_ema, calc_volume_ratio

class TrendFollowing(BaseStrategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        ema_period = int(self.get_param("ema_period", 20))
        vol_mult = float(self.get_param("volume_mult", 1.5))
        
        df['ema'] = calc_ema(df['close'], ema_period)
        df['vol_ratio'] = calc_volume_ratio(df['volume'], 20)
        
        df['buy_signal'] = (df['close'] > df['ema']) & (df['vol_ratio'] > vol_mult)
        df['sell_signal'] = df['close'] < df['ema']
        
        return df
