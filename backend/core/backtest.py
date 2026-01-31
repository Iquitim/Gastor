"""
Backtest Engine Module
======================

Motor de execução de backtests vectorizados.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from core.indicators import (
    calc_rsi, calc_ema, calc_macd, calc_bollinger_bands,
    signal_rsi_oversold, signal_rsi_overbought,
    signal_ema_cross_long, signal_ema_cross_short,
    signal_macd_cross_long, signal_macd_cross_short,
    signal_macd_cross_long, signal_macd_cross_short,
    signal_breakout_long, signal_breakdown_short,
    calc_stochastic, calc_donchian, calc_volume_ratio
)


class BacktestEngine:
    def __init__(self, data: List[Dict[str, Any]], initial_balance: float = 10000.0, fee_rate: float = 0.0, use_compound: bool = True):
        self.df = pd.DataFrame(data)
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.fee_rate = fee_rate
        self.use_compound = use_compound
        print(f"DEBUG: BacktestEngine initialized. use_compound={self.use_compound} (Type: {type(self.use_compound)})")
        self.trades: List[Dict[str, Any]] = []
        
        # Garantir ordenação por timestamp
        if not self.df.empty:
            # Converter UNIX timestamp (seconds) para datetime
            if 'time' in self.df.columns:
                self.df['timestamp'] = pd.to_datetime(self.df['time'], unit='s')
            else:
                self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
                
            self.df = self.df.sort_values('timestamp').reset_index(drop=True)
            # Converter colunas para float
            cols = ['open', 'high', 'low', 'close', 'volume']
            self.df[cols] = self.df[cols].astype(float)

    def run(self, strategy_slug: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa a estratégia especificada.
        """
        if self.df.empty:
            return {"error": "Sem dados para backtest"}

        # Calcular sinais baseado na estratégia
        if strategy_slug == "rsi_reversal":
            self._strategy_rsi_reversal(params)
        elif strategy_slug == "golden_cross":
            self._strategy_golden_cross(params)
        elif strategy_slug == "macd_crossover":
            self._strategy_macd_crossover(params)
        elif strategy_slug == "bollinger_bounce":
            self._strategy_bollinger_bounce(params)
        elif strategy_slug == "custom":
            self._strategy_custom(params)
        elif strategy_slug == "trend_following":
            self._strategy_trend_following(params)
        elif strategy_slug == "stochastic_rsi":
            self._strategy_stochastic_rsi(params)
        elif strategy_slug == "donchian_breakout":
            self._strategy_donchian_breakout(params)
        elif strategy_slug == "ema_rsi_combo":
            self._strategy_ema_rsi_combo(params)
        elif strategy_slug == "macd_rsi_combo":
            self._strategy_macd_rsi_combo(params)
        elif strategy_slug == "volume_breakout":
            self._strategy_volume_breakout(params)
        elif strategy_slug == "custom_strategy":
             # Placeholder do frontend para Builder, tratar como custom vazio ou erro amigável
             # Se vier com regras injetadas (o que deveria), roda como custom
             if "rules" in params or "buy" in params:
                 self._strategy_custom(params)
             else:
                 return {"error": "Configure essa estratégia no Construtor"}
        else:
            return {"error": f"Estratégia '{strategy_slug}' não implementada"}

        # Simular trades
        metrics = self._calculate_metrics()
        
        return {
            "slug": strategy_slug,
            "params": params,
            "trades": self.trades,
            "metrics": metrics
        }

    def _strategy_rsi_reversal(self, params: Dict[str, Any]):
        """
        Estratégia RSI Reversal:
        - Compra: RSI < rsi_buy (Oversold)
        - Venda: RSI > rsi_sell (Overbought)
        """
        rsi_period = int(params.get("rsi_period", 14))
        rsi_buy = float(params.get("rsi_buy", 30))
        rsi_sell = float(params.get("rsi_sell", 70))
        
        self.df['rsi'] = calc_rsi(self.df['close'], rsi_period)
        
        self._simulate_trades(
            buy_signal=self.df['rsi'] < rsi_buy,
            sell_signal=self.df['rsi'] > rsi_sell
        )

    def _strategy_golden_cross(self, params: Dict[str, Any]):
        """
        Estratégia Golden Cross:
        - Compra: EMA rápida cruza ACIMA da lenta
        - Venda: EMA rápida cruza ABAIXO da lenta
        """
        fast = int(params.get("fast", 9))
        slow = int(params.get("slow", 21))
        
        self.df['ema_fast'] = calc_ema(self.df['close'], fast)
        self.df['ema_slow'] = calc_ema(self.df['close'], slow)
        
        buy_signal = (self.df['ema_fast'] > self.df['ema_slow']) & (self.df['ema_fast'].shift(1) <= self.df['ema_slow'].shift(1))
        sell_signal = (self.df['ema_fast'] < self.df['ema_slow']) & (self.df['ema_fast'].shift(1) >= self.df['ema_slow'].shift(1))
        
        self._simulate_trades(buy_signal, sell_signal)

    def _strategy_macd_crossover(self, params: Dict[str, Any]):
        """
        Estratégia MACD:
        - Compra: MACD cruza acima do Signal
        - Venda: MACD cruza abaixo do Signal
        """
        macd, signal = calc_macd(self.df['close'])
        
        buy_signal = (macd > signal) & (macd.shift(1) <= signal.shift(1))
        sell_signal = (macd < signal) & (macd.shift(1) >= signal.shift(1))
        
        self._simulate_trades(buy_signal, sell_signal)
        
    def _strategy_bollinger_bounce(self, params: Dict[str, Any]):
        """
        Estratégia Bollinger Bounce:
        - Compra: Preço toca banda inferior
        - Venda: Preço toca banda superior
        """
        period = int(params.get("bb_period", 20))
        std = float(params.get("bb_std", 2.0))
        
        upper, middle, lower = calc_bollinger_bands(self.df['close'], period, std)
        
        buy_signal = self.df['low'] <= lower
        sell_signal = self.df['high'] >= upper
        
        self._simulate_trades(buy_signal, sell_signal)

    def _strategy_trend_following(self, params: Dict[str, Any]):
        """
        Trend Following:
        - Compra: Preço > EMA AND Volume > AvgVolume * Mult
        - Venda: Preço < EMA
        """
        ema_period = int(params.get("ema_period", 20))
        vol_mult = float(params.get("volume_mult", 1.5))
        
        self.df['ema'] = calc_ema(self.df['close'], ema_period)
        self.df['vol_ratio'] = calc_volume_ratio(self.df['volume'], 20)
        
        buy_signal = (self.df['close'] > self.df['ema']) & (self.df['vol_ratio'] > vol_mult)
        sell_signal = self.df['close'] < self.df['ema']
        
        self._simulate_trades(buy_signal, sell_signal)

    def _strategy_stochastic_rsi(self, params: Dict[str, Any]):
        """
        Stochastic RSI:
        - Compra: Stoch K < buy_level (Oversold)
        - Venda: Stoch K > sell_level (Overbought)
        """
        period = int(params.get("stoch_period", 14))
        buy_level = int(params.get("stoch_buy", 20))
        sell_level = int(params.get("stoch_sell", 80))
        
        k, d = calc_stochastic(self.df['close'], self.df['high'], self.df['low'], period)
        
        buy_signal = k < buy_level
        sell_signal = k > sell_level
        
        self._simulate_trades(buy_signal, sell_signal)

    def _strategy_donchian_breakout(self, params: Dict[str, Any]):
        """
        Donchian Breakout:
        - Compra: Rompe Topo do Canal
        - Venda: Rompe Fundo do Canal
        """
        period = int(params.get("period", 20))
        upper, lower = calc_donchian(self.df['high'], self.df['low'], period)
        
        # Breakout: Close atual > Upper anterior
        buy_signal = self.df['close'] > upper.shift(1)
        sell_signal = self.df['close'] < lower.shift(1)
        
        self._simulate_trades(buy_signal, sell_signal)

    def _strategy_ema_rsi_combo(self, params: Dict[str, Any]):
        """
        EMA + RSI Combo:
        - Compra: Cross EMA Fast > Slow AND RSI > Filter (Momentum)
        - Venda: Cross EMA Fast < Slow
        """
        fast = int(params.get("fast_ema", 9))
        slow = int(params.get("slow_ema", 21))
        rsi_min = int(params.get("rsi_filter", 50))
        
        ema_fast = calc_ema(self.df['close'], fast)
        ema_slow = calc_ema(self.df['close'], slow)
        rsi = calc_rsi(self.df['close'], 14)
        
        cross_up = (ema_fast > ema_slow) & (ema_fast.shift(1) <= ema_slow.shift(1))
        cross_down = (ema_fast < ema_slow) & (ema_fast.shift(1) >= ema_slow.shift(1))
        
        buy_signal = cross_up & (rsi > rsi_min)
        sell_signal = cross_down
        
        self._simulate_trades(buy_signal, sell_signal)

    def _strategy_macd_rsi_combo(self, params: Dict[str, Any]):
        """
        MACD + RSI Combo:
        - Compra: MACD Cross Up AND RSI > Confirm
        - Venda: MACD Cross Down
        """
        rsi_confirm = int(params.get("rsi_confirm", 50))
        # macd_threshold unused in simple logic, but can be added
        
        macd, signal = calc_macd(self.df['close'])
        rsi = calc_rsi(self.df['close'], 14)
        
        cross_up = (macd > signal) & (macd.shift(1) <= signal.shift(1))
        cross_down = (macd < signal) & (macd.shift(1) >= signal.shift(1))
        
        buy_signal = cross_up & (rsi > rsi_confirm)
        sell_signal = cross_down
        
        self._simulate_trades(buy_signal, sell_signal)

    def _strategy_volume_breakout(self, params: Dict[str, Any]):
        """
        Volume Breakout:
        - Compra: Preço sobe X% AND Volume explode > Y * Média
        - Venda: Preço cai abaixo da mínima de N candles (Trailing stop simples)
        """
        lookback = int(params.get("lookback", 20))
        vol_mult = float(params.get("volume_mult", 2.0))
        price_break = float(params.get("price_break_pct", 1.0))
        
        # Volume Spike
        vol_ratio = calc_volume_ratio(self.df['volume'], lookback)
        vol_spike = vol_ratio > vol_mult
        
        # Price Jump: (Close / Open - 1) * 100 > pct
        price_jump = ((self.df['close'] / self.df['open'] - 1) * 100) > price_break
        
        buy_signal = vol_spike & price_jump
        
        # Exit: Break low of last N candles (simplified trailing)
        low_n = self.df['low'].rolling(window=lookback).min()
        sell_signal = self.df['close'] < low_n.shift(1)
        
        self._simulate_trades(buy_signal, sell_signal)

    def _simulate_trades(self, buy_signal: pd.Series, sell_signal: pd.Series):
        """
        Simula execução de trades iterando sobre os sinais.
        """
        position = 0  # 0 = sem posição, 1 = comprado
        entry_price = 0.0
        
        for i in range(1, len(self.df)):
            if position == 0:
                if buy_signal.iloc[i]:
                    # Entrada
                    entry_price = self.df['close'].iloc[i]
                    position = 1
                    # Store entry size explicitly
                    # Definir tamanho da posição
                    if self.use_compound:
                        entry_balance = self.balance
                    else:
                        # Se não usar juros compostos, tenta usar o valor inicial fixo.
                        # MAS, se o saldo atual for menor que o inicial (prejuízo), só pode usar o que tem.
                        entry_balance = min(self.initial_balance, self.balance)

                    
                    self.trades.append({
                        "id": len(self.trades) + 1,
                        "type": "BUY",
                        "entry_date": self.df['timestamp'].iloc[i].isoformat(),
                        "entry_ts": int(self.df['timestamp'].iloc[i].timestamp()),
                        "entry_price": entry_price,
                        "size": entry_balance,  # Valor da banca usado
                        "status": "OPEN"
                    })
            
            elif position == 1:
                # Verificar saída
                if sell_signal.iloc[i]:
                    exit_price = self.df['close'].iloc[i]
                    
                    # Recuperar dados de entrada
                    last_trade = self.trades[-1]
                    entry_balance = last_trade["size"]
                    
                    # Custo com taxas (configurável, default 0.0)
                    fee_rate = self.fee_rate 
                    
                    # Cálculo de Taxas Absolutas (para exibição)
                    entry_fee = entry_balance * fee_rate
                    gross_exit_val = entry_balance * (exit_price / entry_price)
                    exit_fee = gross_exit_val * fee_rate
                    total_fee = entry_fee + exit_fee
                    
                    # PnL Líquido (usando lógica anterior de preços ajustados para consistência)
                    entry_with_fee = entry_price * (1 + fee_rate)
                    exit_with_fee = exit_price * (1 - fee_rate)
                    
                    pnl_pct = (exit_with_fee - entry_with_fee) / entry_with_fee * 100
                    pnl_value = (entry_balance * pnl_pct) / 100
                    
                    self.balance += pnl_value
                    position = 0
                    
                    # Atualizar trade anterior
                    last_trade.update({
                        "exit_date": self.df['timestamp'].iloc[i].isoformat(),
                        "exit_ts": int(self.df['timestamp'].iloc[i].timestamp()),
                        "exit_price": exit_price,
                        "pnl": pnl_value,
                        "pnl_pct": pnl_pct,
                        "fee": total_fee,
                        "exit_balance": self.balance,
                        "status": "CLOSED"
                    })
        
        # Calcular PnL não realizado para posição aberta no final
        if position == 1 and self.trades:
            last_trade = self.trades[-1]
            last_idx = len(self.df) - 1
            current_price = self.df['close'].iloc[last_idx]
            
            # Usar lógica similar de taxas para estimativa
            entry_price = last_trade["entry_price"]
            fee_rate = self.fee_rate
            
            entry_with_fee = entry_price * (1 + fee_rate)
            exit_with_fee = current_price * (1 - fee_rate)
            
            pnl_pct = (exit_with_fee - entry_with_fee) / entry_with_fee * 100
            
            # Calcular valor nominal baseado no tamanho da posição
            s_size = last_trade["size"]
            pnl_value = (s_size * pnl_pct) / 100
            
            # Calcular Taxas Estimadas (Entrada já paga + Saída estimada)
            entry_fee = s_size * fee_rate
            gross_exit_val = s_size * (current_price / entry_price)
            exit_fee = gross_exit_val * fee_rate
            total_fee = entry_fee + exit_fee

            # Atualizar trade (mantendo status OPEN e sem data de saída)
            last_trade.update({
                "exit_price": current_price,
                "pnl": pnl_value,
                "pnl_pct": pnl_pct,
                "fee": total_fee,
                "exit_balance": self.balance + pnl_value
            })

    def _calculate_metrics(self) -> Dict[str, float]:
        """Calcula métricas finais de performance (Baseado em Trades Fechados)."""
        
        # Filtrar apenas trades FECHADOS para métricas de resultado final
        closed_trades = [t for t in self.trades if t.get("status") == "CLOSED"]
        
        # Total PnL (Realizado)
        total_pnl = sum(t["pnl"] for t in closed_trades)
        
        # Saldo Final (Realizado) - Ignora flutuação de abertos
        final_balance = self.balance 
        
        # Win Rate
        wins = [t for t in closed_trades if t["pnl"] > 0]
        losses = [t for t in closed_trades if t["pnl"] < 0]
        win_rate = len(wins) / len(closed_trades) if closed_trades else 0.0
        
        # Profit Factor
        gross_profit = sum(t["pnl"] for t in wins)
        gross_loss = abs(sum(t["pnl"] for t in losses))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else (float('inf') if gross_profit > 0 else 0.0)

        # Calcular Equity Curve para Drawdown (Baseado em Realized Balance)
        equity = [self.initial_balance]
        current_bal = self.initial_balance
        
        # Ordenar trades fechados por data de saída (para curve de saldo realizado)
        sorted_closed = sorted(closed_trades, key=lambda x: x["exit_ts"] if x.get("exit_ts") else 0)
        
        equity_timestamps = []
        for t in sorted_closed:
            current_bal += t["pnl"]
            equity.append(current_bal)
            equity_timestamps.append(t["entry_ts"]) # Use entry ts for x-axis visual or exit? typically exit is when balance updates. 
            # But frontend might expect entry timestamp mapping.
            
        # Drawdown calculation
        equity_series = pd.Series(equity)
        rolling_max = equity_series.cummax()
        drawdown = (equity_series - rolling_max) / rolling_max * 100
        max_dd = abs(drawdown.min()) if not drawdown.empty else 0.0
        
        return {
            "total_pnl": total_pnl,
            "total_pnl_pct": ((final_balance - self.initial_balance) / self.initial_balance) * 100,
            "final_balance": final_balance,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "max_drawdown": max_dd,
            "total_trades": len(closed_trades), # Conta apenas fechados/realizados
            "equity_curve": equity,
            "equity_timestamps": equity_timestamps
        }

    def _strategy_custom(self, params: Dict[str, Any]):
        """Executa estratégia customizada baseada em regras JSON."""
        # Tenta encontrar as regras nos parâmetros
        rules = params.get("rules", None)
        if not rules and "params" in params:
             # Às vezes vem aninhado se passado via runStrategy(slug, {params: {...}})
             inner = params["params"]
             if isinstance(inner, dict) and "rules" in inner:
                 rules = inner["rules"]
             elif isinstance(inner, dict) and "buy" in inner:
                 rules = inner
        
        if not rules:
             # Tenta usar o próprio params se tiver estrutura de regras
             if "buy" in params:
                 rules = params

        if not rules or not isinstance(rules, dict):
            # Fallback seguro
            buy_signal = pd.Series([False] * len(self.df), index=self.df.index)
            sell_signal = pd.Series([False] * len(self.df), index=self.df.index)
            self._simulate_trades(buy_signal, sell_signal)
            return

        buy_signal = self._evaluate_rules_vectorized(rules.get("buy", []), rules.get("buyLogic", "OR"))
        sell_signal = self._evaluate_rules_vectorized(rules.get("sell", []), rules.get("sellLogic", "OR"))
        
        self._simulate_trades(buy_signal, sell_signal)

    def _evaluate_rules_vectorized(self, groups: List[Dict], group_logic: str) -> pd.Series:
        if not groups:
            return pd.Series([False] * len(self.df), index=self.df.index)

        final_signal = None 

        for group in groups:
            group_signal = None
            rules = group.get("rules", [])
            rule_logic = group.get("logic", "AND")

            for rule in rules:
                s_rule = self._evaluate_single_rule(rule)
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
             return pd.Series([False] * len(self.df), index=self.df.index)

        return final_signal.fillna(False)

    def _evaluate_single_rule(self, rule: Dict) -> pd.Series:
        ind_name = rule.get("indicator", "close")
        period = int(rule.get("period", 0))
        lhs = self._get_indicator_series(ind_name, period)
        
        val_type = rule.get("valueType", "constant")
        if val_type == "constant":
            rhs = float(rule.get("value", 0))
        else:
             rhs_name = str(rule.get("value", "close"))
             rhs_period = int(rule.get("valuePeriod", 0))
             rhs = self._get_indicator_series(rhs_name, rhs_period)

        op = rule.get("operator", "<")
        
        # Comparar
        res = pd.Series([False] * len(self.df), index=self.df.index)
        
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

    def _get_indicator_series(self, name: str, period: int) -> pd.Series:
        if name == "close": return self.df['close']
        if name == "volume": return self.df['volume']
        
        key = f"{name}_{period}"
        if key in self.df.columns:
            return self.df[key]

        # Cálculos dinâmicos
        params = self.df['close']
        
        if name == "rsi":
            self.df[key] = calc_rsi(params, period)
        elif name == "ema":
             self.df[key] = calc_ema(params, period)
        elif name == "sma":
             self.df[key] = params.rolling(window=period).mean()
        elif name == "avg_volume":
             self.df[key] = self.df['volume'].rolling(window=period).mean()
        elif name == "median":
             self.df[key] = params.rolling(window=period).median()
        elif name == "mad":
             # Rolling MAD: Median Absolute Deviation
             # 1. Rolling Median
             roll_median = params.rolling(window=period).median()
             # 2. Abs Deviation
             abs_dev = (params - roll_median).abs()
             # 3. Rolling Median of Deviation
             self.df[key] = abs_dev.rolling(window=period).median()
        elif name == "zscore_robust":
             # Robust Z-Score = (Price - Median) / (MAD * 1.4826)
             roll_median = params.rolling(window=period).median()
             abs_dev = (params - roll_median).abs()
             roll_mad = abs_dev.rolling(window=period).median()
             
             # Avoid division by zero
             roll_mad = roll_mad.replace(0, 0.0001)
             
             # Factor 1.4826 makes MAD consistent with Std Dev for normal distribution
             k = 1.4826
             self.df[key] = (params - roll_median) / (roll_mad * k)
        elif name == "bb_upper":
             std = 2.0
             u, m, l = calc_bollinger_bands(params, period, std)
             self.df[f"bb_upper_{period}"] = u
             self.df[f"bb_lower_{period}"] = l
             self.df[key] = u
        elif name == "bb_lower":
             if f"bb_lower_{period}" in self.df.columns: return self.df[f"bb_lower_{period}"]
             std = 2.0
             u, m, l = calc_bollinger_bands(params, period, std)
             self.df[f"bb_upper_{period}"] = u
             self.df[f"bb_lower_{period}"] = l
             self.df[key] = l
        
        if key in self.df.columns:
             return self.df[key]
        
        return self.df['close']
