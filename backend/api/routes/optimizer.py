"""
Optimizer Routes
================

Endpoints for strategy optimization (grid search).
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import time
import itertools
import numpy as np

from core.data_loader import get_market_data
from core.backtest import BacktestEngine
from core.config import get_total_fee
from core.database import get_db
from core.models import Strategy

router = APIRouter()


class OptimizerRequest(BaseModel):
    """Request body para otimização."""
    strategies: List[str]  # Lista de slugs
    coin: str = "SOL/USDT"
    days: int = 90
    timeframe: str = "1h"
    initial_balance: float = 10000.0
    param_steps: int = 3  # Granularidade do grid search
    optimize_execution: bool = False  # Testar compound + sizing
    min_pairs: int = 1  # Mínimo de trades completos
    include_fees: bool = False  # Default False for optimization? Or True? User complained it was considering fees.
    fee_rate: Optional[float] = None


class OptimizationResult(BaseModel):
    """Resultado de uma combinação testada."""
    strategy: str
    params: Dict[str, Any]
    execution_config: Dict[str, Any]
    metrics: Dict[str, float]
    rank: int


def generate_param_grid(strategy_slug: str, steps: int) -> List[Dict[str, Any]]:
    """Gera grade de parâmetros para teste baseado na estratégia."""
    grid = []
    
    if strategy_slug == "rsi_reversal":
        # RSI: Period (10-20), Buy (20-40), Sell (60-80)
        periods = np.linspace(10, 20, steps, dtype=int).tolist()
        buys = np.linspace(20, 40, steps, dtype=int).tolist()
        sells = np.linspace(60, 80, steps, dtype=int).tolist()
        
        for p, b, s in itertools.product(periods, buys, sells):
            grid.append({"rsi_period": int(p), "rsi_buy": int(b), "rsi_sell": int(s)})
            
    elif strategy_slug == "golden_cross":
        # EMA: Fast (5-15), Slow (20-60)
        fasts = np.linspace(5, 15, steps, dtype=int).tolist()
        slows = np.linspace(20, 60, steps, dtype=int).tolist()
        
        for f, s in itertools.product(fasts, slows):
            if f < s:  # Garantir fast < slow
                grid.append({"fast": int(f), "slow": int(s)})
                
    elif strategy_slug == "bollinger_bounce":
        # BB: Period (15-30), Std (1.5-2.5)
        periods = np.linspace(15, 30, steps, dtype=int).tolist()
        stds = np.linspace(1.5, 2.5, steps).tolist()
        
        for p, s in itertools.product(periods, stds):
            grid.append({"bb_period": int(p), "bb_std": round(float(s), 2)})
            
    elif strategy_slug == "macd_crossover":
        # MACD: Padrão (12, 26, 9) é muito bom, mas podemos variar Signal (7-11)
        signals = np.linspace(7, 11, steps, dtype=int).tolist()
        for s in signals:
            grid.append({"signal_period": int(s)})

    elif strategy_slug.startswith("custom_"):
        # Custom strategies have fixed rules (already optimized by user in Builder)
        # So we just test them "as is"
        grid.append({})
    
    # Remover duplicatas que podem surgir do np.linspace com poucos steps
    unique_grid = []
    seen = set()
    for params in grid:
        # Converter para tupla ordenável para set
        key = tuple(sorted(params.items()))
        if key not in seen:
            seen.add(key)
            unique_grid.append(params)
            
    return unique_grid if unique_grid else [{}]  # Retorna params vazios se não definido


@router.post("/run")
async def run_optimization(request: OptimizerRequest) -> Dict[str, Any]:
    """
    Executa Grid Search nas estratégias selecionadas.
    """
    start_time = time.time()
    
    # 1. Carregar dados de mercado (uma vez para todos)
    try:
        market_data = await get_market_data(
            coin=request.coin,
            days=request.days,
            timeframe=request.timeframe
        )
        
        if not market_data["data"]:
            raise HTTPException(status_code=404, detail="Dados de mercado não encontrados")
            
        data = market_data["data"]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar dados: {str(e)}")

    results = []
    
    # 2. Iterar sobre estratégias
    if request.fee_rate is not None:
        fee_rate = request.fee_rate
    else:
        fee_rate = get_total_fee(request.coin) if request.include_fees else 0.0

    engine = BacktestEngine(data, request.initial_balance, fee_rate=fee_rate)
    
    for slug in request.strategies:
        # Gerar grid de parâmetros
        param_grid = generate_param_grid(slug, request.param_steps)
        
        for params in param_grid:
            # Executar backtest
            # Reset engine balance? 
            # A classe BacktestEngine mantém estado em 'balance', então idealmente instanciar nova ou resetar
            # Vamos instanciar nova para garantir isolamento limpo ou refatorar BacktestEngine
            # Para performance, melhor resetar:
            engine.balance = request.initial_balance
            engine.trades = []
            
            # Special handling for custom strategies to inject rules
            run_params = params.copy()
            run_slug = slug
            
            if slug.startswith("custom_"):
                try:
                    strat_id = int(slug.split("_")[1])
                    db = next(get_db())
                    s = db.query(Strategy).filter(Strategy.id == strat_id).first()
                    if s:
                        run_params["rules"] = s.rules
                        run_slug = "custom"
                except Exception as e:
                    print(f"Error loading custom strat {slug}: {e}")
                    continue

            result = engine.run(run_slug, run_params)
            
            if "error" in result:
                continue
                
            metrics = result["metrics"]
            
            # Filtrar resultados irrelevantes
            if metrics["total_trades"] < request.min_pairs:
                continue
                
            results.append({
                "strategy": slug,
                "params": params,
                "execution_config": {"compound": False}, # TODO: Implementar compound
                "metrics": metrics
            })

    # 3. Ordenar resultados (Ranking)
    # Critério: Total PnL descendente
    results.sort(key=lambda x: x["metrics"]["total_pnl"], reverse=True)
    
    # Adicionar rank
    for i, res in enumerate(results):
        res["rank"] = i + 1

    execution_time = (time.time() - start_time) * 1000

    return {
        "request": request.model_dump(),
        "total_combinations": len(results),
        "results": results[:50],  # Top 50 para não sobrecarregar
        "champion": results[0] if results else None,
        "execution_time_ms": execution_time,
        "message": "Otimização concluída com sucesso"
    }


@router.get("/status/{job_id}")
async def get_optimization_status(job_id: str) -> Dict[str, Any]:
    """
    Verifica status de uma otimização em andamento.
    """
    return {
        "job_id": job_id,
        "status": "not_implemented",
        "progress": 0,
        "message": "Background jobs serão implementados na Fase 3"
    }
