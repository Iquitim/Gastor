"""
Results Routes
==============

Endpoints for performance metrics and FTMO validation.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
from core.metrics import calculate_trade_metrics, calculate_drawdown, validate_ftmo

router = APIRouter()


class Trade(BaseModel):
    """Representação de um trade."""
    action: str  # BUY ou SELL
    price: float
    amount: float
    timestamp: str
    coin: str
    reason: Optional[str] = None


class ResultsRequest(BaseModel):
    """Request body para cálculo de resultados."""
    trades: List[Trade]
    initial_balance: float = 10000.0
    coin: str = "SOL/USDT"


class FTMOStatus(BaseModel):
    """Status de aprovação no FTMO Challenge."""
    passed_profit: bool
    passed_drawdown: bool
    passed_daily_loss: bool
    passed_days: bool
    all_passed: bool
class ActiveStrategy(BaseModel):
    """Configuração da estratégia ativa."""
    strategy_slug: str
    params: Dict[str, Any]
    coin: str
    period: str
    timeframe: str
    initial_balance: float
    # Snapshot dos resultados do backtest para exibir como referência
    backtest_metrics: Optional[Dict[str, Any]] = None
    started_at: Optional[str] = None

class MarketContext(BaseModel):
    """Contexto do mercado ativo (moeda carregada)."""
    coin: str
    days: int
    timeframe: str

# Armazenamento em memória (simples)
ACTIVE_STRATEGY: Optional[ActiveStrategy] = None
ACTIVE_MARKET_CONTEXT: Optional[MarketContext] = None

@router.post("/context")
async def set_market_context(context: MarketContext) -> Dict[str, str]:
    """Define o contexto de mercado atual (para persistir no reload)."""
    global ACTIVE_MARKET_CONTEXT
    ACTIVE_MARKET_CONTEXT = context
    return {"message": "Contexto salvo"}

@router.get("/context")
async def get_market_context() -> Optional[MarketContext]:
    """Retorna o contexto de mercado salvo."""
    return ACTIVE_MARKET_CONTEXT

@router.delete("/context")
async def clear_market_context() -> Dict[str, str]:
    """Limpa o contexto de mercado salvo em memória."""
    global ACTIVE_MARKET_CONTEXT
    ACTIVE_MARKET_CONTEXT = None
    return {"message": "Contexto de mercado limpo"}

@router.post("/active")
async def set_active_strategy(strategy: ActiveStrategy) -> Dict[str, str]:
    """Define a estratégia atual como oficial/ativa."""
    global ACTIVE_STRATEGY
    import datetime
    strategy.started_at = datetime.datetime.now().isoformat()
    ACTIVE_STRATEGY = strategy
    return {"message": "Estratégia ativada com sucesso"}

@router.get("/active")
async def get_active_strategy() -> Optional[ActiveStrategy]:
    """Retorna a estratégia ativa atual."""
    return ACTIVE_STRATEGY

@router.post("/calculate")
async def calculate_results(request: ResultsRequest) -> Dict[str, Any]:
    """
    Calcula métricas de performance para uma lista de trades.
    """
    if not request.trades:
        return {
            "metrics": {},
            "drawdown": {},
            "ftmo": {},
            "message": "Nenhum trade fornecido"
        }
        
    # Ordenar trades por timestamp
    sorted_trades = sorted(request.trades, key=lambda t: t.timestamp)
    
    # Simular evolução do saldo Trade a Trade
    # Assumindo que trades são transações (execuções)
    # Lógica simplificada: FIFO para calc PnL se necessário, 
    # mas para métricas gerais, precisamos saber o PnL realizado.
    
    # Se os trades vierem como "Transações", precisamos reconstruir.
    # Se vierem como "Trades Fechados" (como o BacktestEngine gera), melhor.
    # O modelo Trade tem 'action'. Vamos assumir fluxo: BUY -> SELL
    
    balance = request.initial_balance
    equity_curve = [balance] # Começa com saldo inicial
    timestamps = [sorted_trades[0].timestamp] if sorted_trades else []
    
    trades_pnl = []
    
    # Controle de posição simplificado (apenas 1 ativo por vez por simplicidade deste endpoint)
    # Se quiser suportar múltiplas posições, precisaria de lógica mais complexa
    position_amt = 0.0
    avg_price = 0.0
    
    cost_basis = 0.0 # Valor gasto na compra atual
    
    for t in sorted_trades:
        if t.action.upper() == "BUY":
            cost = t.price * t.amount
            if position_amt == 0:
                avg_price = t.price
            else:
                # Preço médio ponderado
                total_val = (avg_price * position_amt) + cost
                avg_price = total_val / (position_amt + t.amount)
                
            position_amt += t.amount
            cost_basis += cost
            # Saldo diminui na compra? Em spot sim, mas para métricas de performance de estratégia,
            # geralmente olhamos para Equity (Saldo + Valor Posição).
            # Vamos manter 'balance' como Caixa Disponível.
            balance -= cost
            
        elif t.action.upper() == "SELL":
            revenue = t.price * t.amount
            
            # Calcular PnL Proporcional
            # Custo da parte vendida
            cost_portion = avg_price * t.amount
            pnl = revenue - cost_portion
            trades_pnl.append(pnl)
            
            balance += revenue
            position_amt -= t.amount
            if position_amt <= 0.00000001: # Zero float tolerance
                position_amt = 0
                avg_price = 0
                
        # Atualizar Equity Curve
        # Equity = Caixa + Valor de Mercado da Posição Atual
        current_position_value = position_amt * t.price
        current_equity = balance + current_position_value
        
        equity_curve.append(current_equity)
        timestamps.append(t.timestamp)

    # Calcular Métricas
    metrics = calculate_trade_metrics(trades_pnl, request.initial_balance)
    
    # Calcular Drawdown
    dd_stats = calculate_drawdown(equity_curve, timestamps)
    
    # Validar FTMO
    # Dias operados = dias únicos nos timestamps
    unique_days = len(set(pd.to_datetime(timestamps).date))
    
    ftmo_stats = validate_ftmo(
        initial_balance=request.initial_balance,
        final_balance=metrics["final_balance"],
        max_dd_pct=dd_stats["max_drawdown_pct"],
        max_daily_loss_pct=dd_stats["max_daily_loss_pct"],
        days_traded=unique_days
    )
    
    # Preparar dados de evolução para gráfico
    evolution = [
        {"time": ts, "value": val} 
        for ts, val in zip(timestamps, equity_curve)
    ]
    
    return {
        "metrics": metrics,
        "drawdown": dd_stats,
        "ftmo": ftmo_stats,
        "evolution": evolution,
        "message": "Cálculo realizado com sucesso"
    }

@router.post("/ftmo-check")
async def ftmo_quick_check(request: ResultsRequest) -> FTMOStatus:
    """Verificação rápida."""
    # Reutiliza a lógica completa pois precisa calcular DD
    result = await calculate_results(request)
    return result["ftmo"]
