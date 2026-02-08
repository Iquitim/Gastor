import pandas as pd
from ..base import BaseStrategy
from core.indicators import calc_stochastic

class StochasticRSI(BaseStrategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        period = int(self.get_param("stoch_period", 14))
        buy_level = int(self.get_param("stoch_buy", 20))
        sell_level = int(self.get_param("stoch_sell", 80))
        
        k, d = calc_stochastic(df['close'], df['high'], df['low'], period)
        df['stoch_k'] = k
        df['stoch_d'] = d
        
        df['buy_signal'] = k < buy_level
        df['sell_signal'] = k > sell_level
        
        return df
