import pandas as pd
from ..base import BaseStrategy
from core.indicators import calc_rsi

class RSIReversal(BaseStrategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        rsi_period = int(self.get_param("rsi_period", 14))
        rsi_buy = float(self.get_param("rsi_buy", 30))
        rsi_sell = float(self.get_param("rsi_sell", 70))
        
        # Calculate Indicator
        df['rsi'] = calc_rsi(df['close'], rsi_period)
        
        # Generate Signals
        # Note: In BacktestEngine, logic was direct comparison.
        # We store them as boolean Series in the DataFrame to be used by the Engine.
        df['buy_signal'] = df['rsi'] < rsi_buy
        df['sell_signal'] = df['rsi'] > rsi_sell
        
        return df
