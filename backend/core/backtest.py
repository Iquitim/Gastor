"""
Backtest Engine Module
======================

Motor de execução de backtests vectorizados.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from core.strategies.factory import get_strategy_class


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

        # Tenta usar o novo sistema de Estratégias Compartilhadas (Phase 1 Refactor)
        strategy_cls = get_strategy_class(strategy_slug)
        if not strategy_cls:
             return {"error": f"Estratégia '{strategy_slug}' não encontrada ou não implementada."}

        strategy = strategy_cls(params)
        # Modifica o DF in-place adicionando indicators e signals
        self.df = strategy.generate_signals(self.df)
        
        # Executa simulação com os sinais gerados
        if 'buy_signal' in self.df.columns and 'sell_signal' in self.df.columns:
             self._simulate_trades(self.df['buy_signal'], self.df['sell_signal'])
        else:
             return {"error": f"Estratégia {strategy_slug} não gerou sinais válidos."}

        # Simular trades
        metrics = self._calculate_metrics()
        
        return {
            "slug": strategy_slug,
            "params": params,
            "trades": self.trades,
            "metrics": metrics
        }


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


