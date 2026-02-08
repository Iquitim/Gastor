from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd

class BaseStrategy(ABC):
    """
    Abstract Base Class for all trading strategies.
    Ensures consistent interface for both Backtest and Paper/Live Trading.
    """
    
    def __init__(self, params: Dict[str, Any]):
        self.params = params

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates indicators and generates buy/sell signals.
        
        Args:
            df: DataFrame with OHLCV data.
            
        Returns:
            DataFrame with added indicator columns and 'buy_signal'/'sell_signal' boolean columns.
        """
        pass

    def get_param(self, key: str, default: Any = None) -> Any:
        return self.params.get(key, default)
