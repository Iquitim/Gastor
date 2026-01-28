"""
Metrics Core Module
===================

Funções para cálculo de métricas de performance e validação de regras (FTMO).
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple

def calculate_trade_metrics(trades_pnl: List[float], initial_balance: float) -> Dict[str, float]:
    """
    Calcula métricas básicas baseadas em lista de PnL de trades.
    """
    if not trades_pnl:
        return {
            "total_pnl": 0.0,
            "total_pnl_pct": 0.0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "avg_trade": 0.0,
            "best_trade": 0.0,
            "worst_trade": 0.0,
            "final_balance": initial_balance
        }

    total_pnl = sum(trades_pnl)
    wins = [p for p in trades_pnl if p > 0]
    losses = [p for p in trades_pnl if p <= 0]
    
    win_rate = len(wins) / len(trades_pnl) if trades_pnl else 0.0
    
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0.0
    
    return {
        "total_pnl": total_pnl,
        "total_pnl_pct": (total_pnl / initial_balance) * 100,
        "win_rate": win_rate * 100,
        "profit_factor": profit_factor,
        "avg_trade": np.mean(trades_pnl),
        "best_trade": max(trades_pnl),
        "worst_trade": min(trades_pnl),
        "final_balance": initial_balance + total_pnl
    }


def calculate_drawdown(equity_curve: List[float], timestamps: List[str]) -> Dict[str, Any]:
    """
    Calcula estatísticas de Drawdown e Perda Diária.
    
    Args:
        equity_curve: Lista de valores do patrimônio (saldo) após cada trade.
        timestamps: Lista de datas correspondentes a cada ponto da curva.
    """
    if not equity_curve:
        return {
            "max_drawdown_pct": 0.0,
            "max_drawdown_date": None,
            "max_daily_loss_pct": 0.0,
            "max_daily_loss_date": None
        }

    # Converter para Series para facilitar
    ts = pd.to_datetime(timestamps)
    equity = pd.Series(equity_curve, index=ts)
    
    # High Water Mark
    hwm = equity.cummax()
    
    # Drawdown Curve
    dd = (equity - hwm) / hwm * 100
    
    # Max Drawdown
    max_dd = dd.min() # É negativo
    max_dd_idx = dd.idxmin()
    
    # Daily Loss
    # Resample para diário pegando o valor de fechamento do dia (ou mínimo do dia para ser mais conservador)
    # Como equity muda trade a trade, vamos pegar a variação do saldo início dia vs mínimo dia
    daily = equity.resample('D').ohlc() # Open, High, Low, Close do equity no dia
    
    # Daily Loss = (Low do dia - Close dia anterior) / Close dia anterior
    # Mas o start balance do dia é o close do dia anterior
    prev_close = daily['close'].shift(1)
    daily_loss = (daily['low'] - prev_close) / prev_close * 100
    
    # Para o primeiro dia, usar equity inicial (que deve ser o primeiro valor da curva se incluírmos saldo inicial)
    # Assumindo que equity_curve começa COM o valor inicial
    
    max_daily_loss = daily_loss.min() # Negativo
    max_daily_loss_idx = daily_loss.idxmin()
    
    return {
        "max_drawdown_pct": abs(max_dd),
        "max_drawdown_date": max_dd_idx.isoformat() if pd.notnull(max_dd_idx) else None,
        "max_daily_loss_pct": abs(max_daily_loss) if pd.notnull(max_daily_loss) else 0.0,
        "max_daily_loss_date": max_daily_loss_idx.isoformat() if pd.notnull(max_daily_loss_idx) else None
    }


def validate_ftmo(
    initial_balance: float, 
    final_balance: float, 
    max_dd_pct: float, 
    max_daily_loss_pct: float, 
    days_traded: int
) -> Dict[str, bool]:
    """Verifica regras do FTMO Challenge."""
    
    target_profit = initial_balance * 0.10 # 10%
    min_days = 4
    limit_dd = 10.0 # 10%
    limit_daily = 5.0 # 5%
    
    profit = final_balance - initial_balance
    
    return {
        "passed_profit": profit >= target_profit,
        "passed_drawdown": max_dd_pct < limit_dd,
        "passed_daily_loss": max_daily_loss_pct < limit_daily,
        "passed_days": days_traded >= min_days,
        "all_passed": (
            profit >= target_profit and 
            max_dd_pct < limit_dd and 
            max_daily_loss_pct < limit_daily and 
            days_traded >= min_days
        )
    }
