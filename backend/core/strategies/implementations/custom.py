import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from ..base import BaseStrategy
from core.indicators import (
    calc_rsi, calc_ema, calc_bollinger_bands,
    calc_stochastic, calc_donchian, calc_volume_ratio
)

class Custom(BaseStrategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        params = self.params
        
        # Parse Rules
        rules = params.get("rules", None)
        if not rules and "params" in params:
             inner = params["params"]
             if isinstance(inner, dict) and "rules" in inner:
                 rules = inner["rules"]
             elif isinstance(inner, dict) and "buy" in inner:
                 rules = inner
        
        if not rules:
             if "buy" in params:
                 rules = params

        if not rules or not isinstance(rules, dict):
            df['buy_signal'] = False
            df['sell_signal'] = False
            return df

        # Execute Rule Engine
        df['buy_signal'] = self._evaluate_rules_vectorized(df, rules.get("buy", []), rules.get("buyLogic", "OR"))
        df['sell_signal'] = self._evaluate_rules_vectorized(df, rules.get("sell", []), rules.get("sellLogic", "OR"))
        
        return df

    def _evaluate_rules_vectorized(self, df: pd.DataFrame, groups: List[Dict], group_logic: str) -> pd.Series:
        if not groups:
            return pd.Series([False] * len(df), index=df.index)

        final_signal = None 

        for group in groups:
            group_signal = None
            rules = group.get("rules", [])
            rule_logic = group.get("logic", "AND")

            for rule in rules:
                s_rule = self._evaluate_single_rule(df, rule)
                if group_signal is None:
                    group_signal = s_rule
                else:
                    if rule_logic == "AND":
                        group_signal = group_signal & s_rule
                    else:
                        group_signal = group_signal | s_rule
            
            if group_signal is not None:
                if final_signal is None:
                    final_signal = group_signal
                else:
                    if group_logic == "AND":
                        final_signal = final_signal & group_signal
                    else:
                        final_signal = final_signal | group_signal

        if final_signal is None:
             return pd.Series([False] * len(df), index=df.index)

        return final_signal.fillna(False)

    def _evaluate_single_rule(self, df: pd.DataFrame, rule: Dict) -> pd.Series:
        ind_name = rule.get("indicator", "close")
        period = int(rule.get("period", 0))
        lhs = self._get_indicator_series(df, ind_name, period)
        
        val_type = rule.get("valueType", "constant")
        if val_type == "constant":
            rhs = float(rule.get("value", 0))
        else:
             rhs_name = str(rule.get("value", "close"))
             rhs_period = int(rule.get("valuePeriod", 0))
             rhs = self._get_indicator_series(df, rhs_name, rhs_period)

        op = rule.get("operator", "<")
        
        # Comparar
        res = pd.Series([False] * len(df), index=df.index)
        
        if op == "<": res = lhs < rhs
        elif op == ">": res = lhs > rhs
        elif op == "<=": res = lhs <= rhs
        elif op == ">=": res = lhs >= rhs
        elif op == "==": res = lhs == rhs
        elif op == "cross_up":
            if isinstance(rhs, (int, float)):
                 res = (lhs > rhs) & (lhs.shift(1) <= rhs)
            else:
                 res = (lhs > rhs) & (lhs.shift(1) <= rhs.shift(1))
        elif op == "cross_down":
             if isinstance(rhs, (int, float)):
                 res = (lhs < rhs) & (lhs.shift(1) >= rhs)
             else:
                 res = (lhs < rhs) & (lhs.shift(1) >= rhs.shift(1))

        return res.fillna(False)

    def _get_indicator_series(self, df: pd.DataFrame, name: str, period: int) -> pd.Series:
        if name == "close": return df['close']
        if name == "volume": return df['volume']
        
        key = f"{name}_{period}"
        if key in df.columns:
            return df[key]

        # Cálculos dinâmicos
        params = df['close']
        
        series = None
        if name == "rsi":
            series = calc_rsi(params, period)
        elif name == "ema":
             series = calc_ema(params, period)
        elif name == "sma":
             series = params.rolling(window=period).mean()
        elif name == "avg_volume":
             series = df['volume'].rolling(window=period).mean()
        elif name == "median":
             series = params.rolling(window=period).median()
        elif name == "mad":
             # Rolling MAD
             roll_median = params.rolling(window=period).median()
             abs_dev = (params - roll_median).abs()
             series = abs_dev.rolling(window=period).median()
        elif name == "zscore_robust":
             # Robust Z-Score
             roll_median = params.rolling(window=period).median()
             abs_dev = (params - roll_median).abs()
             roll_mad = abs_dev.rolling(window=period).median()
             roll_mad = roll_mad.replace(0, 0.0001)
             k = 1.4826
             series = (params - roll_median) / (roll_mad * k)
        elif name == "bb_upper":
             std = 2.0
             u, m, l = calc_bollinger_bands(params, period, std)
             # Cache related components if possible, but simplest is just return requested
             # Side effect caching in DF
             df[f"bb_upper_{period}"] = u
             df[f"bb_lower_{period}"] = l
             return u
        elif name == "bb_lower":
             if f"bb_lower_{period}" in df.columns: return df[f"bb_lower_{period}"]
             std = 2.0
             u, m, l = calc_bollinger_bands(params, period, std)
             df[f"bb_upper_{period}"] = u
             df[f"bb_lower_{period}"] = l
             return l
        
        if series is not None:
             df[key] = series
             return series
        
        return df['close'] # Fallback
