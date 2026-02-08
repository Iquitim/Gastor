import pandas as pd
from ..base import BaseStrategy
from core.indicators import calc_macd, calc_rsi

class MACDRSICombo(BaseStrategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        rsi_confirm = int(self.get_param("rsi_confirm", 50))
        
        macd, signal = calc_macd(df['close'])
        rsi = calc_rsi(df['close'], 14)
        
        df['macd'] = macd
        df['macd_signal'] = signal
        df['rsi'] = rsi
        
        cross_up = (macd > signal) & (macd.shift(1) <= signal.shift(1))
        cross_down = (macd < signal) & (macd.shift(1) >= signal.shift(1))
        
        # Original Logic: Buy if MACD > Signal AND RSI > Confirm
        # This is a state condition + filter, not necessarily a crossover event, 
        # but BacktestEngine logic was:
        # buy_signal = (macd > signal) & (rsi > rsi_confirm)
        # sell_signal = cross_down
        
        df['buy_signal'] = (macd > signal) & (rsi > rsi_confirm)
        df['sell_signal'] = cross_down
        
        return df
