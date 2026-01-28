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
from sqlalchemy.orm import Session
from fastapi import Depends
from core.database import get_db
from core.models import Strategy

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
    # Lista Oficial de Estratégias do Sistema
    strategies = [
        {
            "slug": "rsi_reversal",
            "name": "RSI Reversal",
            "category": "reversal",
            "icon": "🔄",
            "description": "Compra quando RSI indica sobrevendido, vende quando sobrecomprado",
            "idealFor": "Mercados laterais ou fins de tendência",
            "parameters": {
                "rsi_buy": {"default": 30, "min": 10, "max": 50, "label": "RSI Compra (Sobrevendido)"},
                "rsi_sell": {"default": 70, "min": 50, "max": 90, "label": "RSI Venda (Sobrecomprado)"},
                "rsi_period": {"default": 14, "min": 5, "max": 21, "label": "Período RSI"}
            }
        },
        {
            "slug": "golden_cross",
            "name": "Golden Cross",
            "category": "trend",
            "icon": "✨",
            "description": "Detecta cruzamentos de médias móveis EMA rápida/lenta",
            "idealFor": "Mercados em tendência clara",
            "parameters": {
                "fast_period": {"default": 9, "min": 5, "max": 20, "label": "EMA Rápida"},
                "slow_period": {"default": 21, "min": 15, "max": 50, "label": "EMA Lenta"}
            }
        },
        {
            "slug": "macd_crossover",
            "name": "MACD Crossover",
            "category": "momentum",
            "icon": "📊",
            "description": "Sinais de cruzamento entre linha MACD e Signal",
            "idealFor": "Identificar mudanças de momentum",
            "parameters": {
                "fast": {"default": 12, "min": 8, "max": 16, "label": "EMA Rápida (MACD)"},
                "slow": {"default": 26, "min": 20, "max": 35, "label": "EMA Lenta (MACD)"},
                "signal": {"default": 9, "min": 5, "max": 12, "label": "Signal Period"}
            }
        },
        {
            "slug": "bollinger_bounce",
            "name": "Bollinger Bounce",
            "category": "volatility",
            "icon": "🎢",
            "description": "Compra na banda inferior, vende na banda superior",
            "idealFor": "Mercados com volatilidade definida",
            "parameters": {
                "bb_period": {"default": 20, "min": 10, "max": 50, "label": "Período BB"},
                "bb_std": {"default": 2, "min": 1, "max": 3, "label": "Desvio Padrão"}
            }
        },
        {
            "slug": "trend_following",
            "name": "Trend Following",
            "category": "trend",
            "icon": "📈",
            "description": "Segue tendência com EMA e confirma com volume",
            "idealFor": "Tendências fortes de longo prazo",
            "parameters": {
                "ema_period": {"default": 20, "min": 10, "max": 50, "label": "Período EMA"},
                "volume_mult": {"default": 1.5, "min": 1.0, "max": 3.0, "label": "Multiplicador Volume"}
            }
        },
        {
            "slug": "stochastic_rsi",
            "name": "Stochastic RSI",
            "category": "reversal",
            "icon": "📉",
            "description": "Combina Stochastic com RSI para sinais mais precisos",
            "idealFor": "Identificar extremos de sobrecompra/venda",
            "parameters": {
                "stoch_period": {"default": 14, "min": 5, "max": 21, "label": "Período Stochastic"},
                "stoch_buy": {"default": 20, "min": 10, "max": 30, "label": "Limiar Compra"},
                "stoch_sell": {"default": 80, "min": 70, "max": 90, "label": "Limiar Venda"}
            }
        },
        {
            "slug": "donchian_breakout",
            "name": "Donchian Breakout",
            "category": "trend",
            "icon": "🏰",
            "description": "Compra no rompimento do topo, vende no fundo do canal",
            "idealFor": "Breakouts e início de tendências",
            "parameters": {
                "period": {"default": 20, "min": 10, "max": 55, "label": "Período Canal"}
            }
        },
        {
            "slug": "ema_rsi_combo",
            "name": "EMA + RSI Combo",
            "category": "hybrid",
            "icon": "🧬",
            "description": "Combina cruzamento de EMAs com filtro RSI",
            "idealFor": "Reduzir sinais falsos em tendências",
            "parameters": {
                "fast_ema": {"default": 9, "min": 5, "max": 15, "label": "EMA Rápida"},
                "slow_ema": {"default": 21, "min": 15, "max": 50, "label": "EMA Lenta"},
                "rsi_filter": {"default": 50, "min": 30, "max": 70, "label": "Filtro RSI"}
            }
        },
        {
            "slug": "macd_rsi_combo",
            "name": "MACD + RSI Combo",
            "category": "hybrid",
            "icon": "⚡",
            "description": "MACD para timing, RSI para confirmação",
            "idealFor": "Entradas mais seguras em momentum",
            "parameters": {
                "rsi_confirm": {"default": 50, "min": 30, "max": 70, "label": "RSI Confirmação"},
                "macd_threshold": {"default": 0, "min": -0.5, "max": 0.5, "label": "MACD Threshold"}
            }
        },
        {
            "slug": "volume_breakout",
            "name": "Volume Breakout",
            "category": "momentum",
            "icon": "📢",
            "description": "Breakout confirmado por explosão de volume",
            "idealFor": "Movimentos explosivos com volume alto",
            "parameters": {
                "lookback": {"default": 20, "min": 10, "max": 50, "label": "Período Lookback"},
                "volume_mult": {"default": 2.0, "min": 1.5, "max": 5.0, "label": "Mult. Volume"},
                "price_break_pct": {"default": 1.0, "min": 0.5, "max": 3.0, "label": "% Breakout Preço"}
            }
        }
    ]
    

    
    # Adicionar estratégias customizadas do banco
    try:
        # Criar nova sessão apenas para leitura (se não injetada)
        db = next(get_db())
        custom = db.query(Strategy).all()
        for s in custom:
            strategies.append({
                "slug": f"custom_{s.id}",
                "name": s.name,
                "category": "custom",
                "icon": "🛠️",
                "description": s.description or "Estratégia Customizada"
            })
    except Exception as e:
        print(f"Erro ao carregar estratégias customizadas: {e}")
        
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


# --- Persistência de Estratégias Customizadas (Banco de Dados) ---

class CustomStrategyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    coin: str
    period: str
    timeframe: str
    rules: Dict[str, Any]

@router.post("/custom")
def create_custom_strategy(strategy: CustomStrategyCreate, db: Session = Depends(get_db)):
    """Salva uma estratégia customizada no banco de dados."""
    db_strategy = Strategy(
        name=strategy.name,
        description=strategy.description,
        coin=strategy.coin,
        period=strategy.period,
        timeframe=strategy.timeframe,
        rules=strategy.rules
    )
    db.add(db_strategy)
    db.commit()
    db.refresh(db_strategy)
    return {"id": db_strategy.id, "status": "success"}

@router.get("/custom")
def list_custom_strategies(db: Session = Depends(get_db)):
    """Lista todas as estratégias customizadas salvas."""
    return db.query(Strategy).order_by(Strategy.created_at.desc()).all()

@router.delete("/custom/{strategy_id}")
def delete_custom_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """Remove uma estratégia customizada."""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Estratégia não encontrada")
    
    db.delete(strategy)
    db.commit()
    return {"status": "success"}



@router.get("/{slug}")
async def get_strategy(slug: str) -> Dict[str, Any]:
    """
    Retorna detalhes de uma estratégia específica.
    
    Inclui parâmetros configuráveis com valores default, min e max.
    """
    # TODO: Buscar da lista real de estratégias
    # Buscar na lista oficial
    all_strategies = await list_strategies()
    for s in all_strategies:
        if s["slug"] == slug:
            return s
    
    # Tentar buscar no banco se for custom_
    if slug.startswith("custom_"):
        try:
            strat_id = int(slug.split("_")[1])
            db = next(get_db())
            s = db.query(Strategy).filter(Strategy.id == strat_id).first()
            if s:
                 return {
                    "slug": slug,
                    "name": s.name,
                    "category": "custom",
                    "icon": "🛠️",
                    "description": s.description,
                    "explanation": "Estratégia criada via Construtor.",
                    "parameters": {} # Sem parâmetros ajustáveis por enquanto
                }
        except:
             pass

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
    # Se for custom strategy do banco, carregar regras
    if slug.startswith("custom_"):
        try:
            strat_id = int(slug.split("_")[1])
            db = next(get_db())
            s = db.query(Strategy).filter(Strategy.id == strat_id).first()
            if s:
                # Injetar regras nos params
                params.params["rules"] = s.rules
                slug = "custom" # Engine conhece como 'custom'
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Erro ao carregar estratégia custom: {e}")

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

