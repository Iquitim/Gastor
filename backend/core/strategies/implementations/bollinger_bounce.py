import pandas as pd
from ..base import BaseStrategy
from core.indicators import calc_bollinger_bands

class BollingerBounce(BaseStrategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        period = int(self.get_param("bb_period", 20))
        std = float(self.get_param("bb_std", 2.0))
        
        upper, middle, lower = calc_bollinger_bands(df['close'], period, std)
        
        df['bb_upper'] = upper
        df['bb_lower'] = lower
        df['bb_middle'] = middle
        
        # Signal Generation
        # Buy when price touches lower band
        df['buy_signal'] = df['low'] <= lower
        # Sell when price touches upper band
        df['sell_signal'] = df['high'] >= upper
        
        return df
