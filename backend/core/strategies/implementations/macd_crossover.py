import pandas as pd
from ..base import BaseStrategy
from core.indicators import calc_macd

class MACDCrossover(BaseStrategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        # MACD parameters usually fixed in indicator calc, but can be extensible if calc_macd supports it
        # Current calc_macd in indicators.py uses 12, 26, 9 hardcoded or defaults?
        # Let's check indicators.py content if possible, but for now assume standard or no params
        # Wait, BacktestEngine implementation didn't take params for constants, just calls calc_macd(close)
        
        macd, signal = calc_macd(df['close'])
        
        df['macd'] = macd
        df['macd_signal'] = signal
        
        # Signal Generation
        df['buy_signal'] = df['macd'] > df['macd_signal']
        df['sell_signal'] = df['macd'] < df['macd_signal']
        
        return df
