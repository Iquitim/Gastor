import pandas as pd
from ..base import BaseStrategy
from core.indicators import calc_donchian

class DonchianBreakout(BaseStrategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        period = int(self.get_param("period", 20))
        upper, lower = calc_donchian(df['high'], df['low'], period)
        
        df['donchian_upper'] = upper
        df['donchian_lower'] = lower
        
        # Breakout: Close current > Upper previous
        # We use shift(1) to avoid look-ahead bias if using current close against current period's high
        # But calc_donchian typically includes current candle in calculation if passed current series.
        # Standard implementation: Breakout of N-period high (excluding current).
        
        df['buy_signal'] = df['close'] > upper.shift(1)
        df['sell_signal'] = df['close'] < lower.shift(1)
        
        return df
