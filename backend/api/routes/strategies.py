"""
Strategies Routes
=================

Endpoints for strategy management and backtesting.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from core.data_loader import get_market_data
from core.backtest import BacktestEngine
import json
import os
from pathlib import Path

router = APIRouter()


class StrategyParams(BaseModel):
    """Parâmetros para execução de estratégia."""
    coin: str = "SOL/USDT"
    days: int = 90
    timeframe: str = "1h"
    initial_balance: float = 10000.0
    use_compound: bool = False
    sizing_method: str = "fixo"
    include_fees: bool = True
    fee_rate: Optional[float] = None
    params: Dict[str, Any] = {}


class StrategyInfo(BaseModel):
    """Informações de uma estratégia."""
    slug: str
    name: str
    category: str
    icon: str
    description: str
    parameters: Dict[str, Dict[str, Any]]


@router.get("/")
async def list_strategies() -> List[Dict[str, Any]]:
    """
    Lista todas as estratégias disponíveis.
    
    Retorna lista com slug, nome, categoria, ícone e descrição de cada estratégia.
    """
    # TODO: Migrar STRATEGIES de src/strategies/__init__.py
    strategies = [
        {
            "slug": "rsi_reversal",
            "name": "RSI Reversal",
            "category": "reversal",
            "icon": "🔄",
            "description": "Compra em oversold, vende em overbought"
        },
        {
            "slug": "golden_cross",
            "name": "Golden Cross",
            "category": "trend",
            "icon": "✨",
            "description": "Cruzamento de médias móveis EMA 9/21"
        },
        {
            "slug": "macd_crossover",
            "name": "MACD Crossover",
            "category": "momentum",
            "icon": "📊",
            "description": "Sinais de cruzamento MACD/Signal"
        },
        {
            "slug": "bollinger_bounce",
            "name": "Bollinger Bounce",
            "category": "volatility",
            "icon": "🎢",
            "description": "Reversão nas bandas de Bollinger"
        }
    ]
    
    return strategies


# Persistência em arquivo para sobreviver a reloads
DATA_DIR = Path("data")
ACTIVE_STRATEGY_FILE = DATA_DIR / "active_strategy.json"

# Garantir que diretório existe
DATA_DIR.mkdir(exist_ok=True)

class ActiveStrategyRequest(BaseModel):
    strategy_slug: str
    params: Dict[str, Any]
    coin: str
    period: str
    timeframe: str
    initial_balance: float
    backtest_metrics: Dict[str, Any]

@router.post("/active/set")
async def set_active_strategy(data: ActiveStrategyRequest):
    """Define a estratégia ativa para visualização no Dashboard."""
    try:
        with open(ACTIVE_STRATEGY_FILE, "w") as f:
            json.dump(data.dict(), f, indent=4)
        return {"status": "success", "data": data.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar estratégia ativa: {str(e)}")

@router.get("/active")
async def get_active_strategy():
    """Retorna a estratégia ativa atual."""
    if not ACTIVE_STRATEGY_FILE.exists():
        return {}
    
    try:
        with open(ACTIVE_STRATEGY_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

@router.delete("/active")
async def clear_active_strategy():
    """Remove a estratégia ativa definida pelo usuário."""
    if ACTIVE_STRATEGY_FILE.exists():
        ACTIVE_STRATEGY_FILE.unlink()
    return {"status": "success", "message": "Estratégia ativa removida"}


@router.get("/{slug}")
async def get_strategy(slug: str) -> Dict[str, Any]:
    """
    Retorna detalhes de uma estratégia específica.
    
    Inclui parâmetros configuráveis com valores default, min e max.
    """
    # TODO: Buscar da lista real de estratégias
    if slug == "rsi_reversal":
        return {
            "slug": "rsi_reversal",
            "name": "RSI Reversal",
            "category": "reversal",
            "icon": "🔄",
            "description": "Compra quando RSI indica oversold, vende em overbought",
            "explanation": "O RSI (Relative Strength Index) mede a força do movimento de preço...",
            "parameters": {
                "rsi_buy": {"default": 30, "min": 10, "max": 40, "label": "RSI Compra"},
                "rsi_sell": {"default": 70, "min": 60, "max": 90, "label": "RSI Venda"},
                "rsi_period": {"default": 14, "min": 5, "max": 21, "label": "Período RSI"}
            }
        }
    
    raise HTTPException(status_code=404, detail=f"Estratégia '{slug}' não encontrada")


from core.data_loader import get_market_data
from core.backtest import BacktestEngine
from core.config import get_total_fee

# ...

@router.post("/{slug}/run")
async def run_strategy(slug: str, params: StrategyParams) -> Dict[str, Any]:
    """
    Executa backtest de uma estratégia.
    
    Busca dados reais (se disponíveis no cache/DB, senão busca agora) e roda a simulação.
    """
    try:
        # 1. Buscar dados de mercado
        market_data = await get_market_data(
            coin=params.coin,
            days=params.days,
            timeframe=params.timeframe
        )
        
        if not market_data["data"]:
            raise HTTPException(status_code=400, detail=f"Sem dados disponíveis para {params.coin}")
            
        # 2. Inicializar Engine
        # Priorizar fee_rate explícito se enviado (configurações globais do frontend)
        if params.fee_rate is not None:
            fee_rate = params.fee_rate
        else:
            fee_rate = get_total_fee(params.coin) if params.include_fees else 0.0
        
        engine = BacktestEngine(
            data=market_data["data"],
            initial_balance=params.initial_balance,
            fee_rate=fee_rate
        )
        
        # 3. Executar Backtest
        result = engine.run(slug, params.params)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        with open("error.log", "w") as f:
            f.write(traceback.format_exc())
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

