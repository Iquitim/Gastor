from typing import Dict, Type, Any
from .base import BaseStrategy
from .implementations.rsi_reversal import RSIReversal
from .implementations.golden_cross import GoldenCross
from .implementations.macd_crossover import MACDCrossover
from .implementations.bollinger_bounce import BollingerBounce
from .implementations.trend_following import TrendFollowing
from .implementations.stochastic_rsi import StochasticRSI
from .implementations.donchian_breakout import DonchianBreakout
from .implementations.ema_rsi_combo import EMARSICombo
from .implementations.macd_rsi_combo import MACDRSICombo
from .implementations.volume_breakout import VolumeBreakout
from .implementations.custom import Custom

STRATEGY_MAP: Dict[str, Type[BaseStrategy]] = {
    "rsi_reversal": RSIReversal,
    "golden_cross": GoldenCross,
    "macd_crossover": MACDCrossover,
    "bollinger_bounce": BollingerBounce,
    "trend_following": TrendFollowing,
    "stochastic_rsi": StochasticRSI,
    "donchian_breakout": DonchianBreakout,
    "ema_rsi_combo": EMARSICombo,
    "macd_rsi_combo": MACDRSICombo,
    "volume_breakout": VolumeBreakout,
    "custom": Custom,
    "custom_strategy": Custom, # Alias often used by frontend
    # Add other strategies here as they are implemented
}

def get_strategy_class(slug: str) -> Type[BaseStrategy]:
    return STRATEGY_MAP.get(slug)
