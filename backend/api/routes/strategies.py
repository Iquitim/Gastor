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
    initial_balance: float
    use_compound: bool
    sizing_method: str
    include_fees: bool
    fee_rate: float
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
    from core.strategies_config import STRATEGIES as OFFICIAL_STRATEGIES
    # Deep copy to avoid modifying the original config in memory if needed, 
    # though here we are just appending custom ones.
    strategies = [s.copy() for s in OFFICIAL_STRATEGIES]
    

    
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
    use_compound: bool
    sizing_method: str
    include_fees: bool
    fee_rate: float
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

from core.auth import get_current_user
from core.models import User

@router.post("/custom")
def create_custom_strategy(
    strategy: CustomStrategyCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Salva uma estratégia customizada (Upsert: Atualiza se já existir com mesmo nome)."""
    
    # Verificar se já existe estratégia com esse nome para o usuário
    existing_strategy = db.query(Strategy).filter(
        Strategy.owner_id == current_user.id,
        Strategy.name == strategy.name
    ).first()
    
    if existing_strategy:
        # Atualizar existente
        existing_strategy.description = strategy.description
        existing_strategy.coin = strategy.coin
        existing_strategy.period = strategy.period
        existing_strategy.timeframe = strategy.timeframe
        existing_strategy.rules = strategy.rules
        
        db.commit()
        db.refresh(existing_strategy)
        return {"id": existing_strategy.id, "status": "updated", "message": "Estratégia atualizada com sucesso!"}
    
    else:
        # Criar nova
        db_strategy = Strategy(
            owner_id=current_user.id,
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
        return {"id": db_strategy.id, "status": "created", "message": "Estratégia criada com sucesso!"}

@router.get("/custom")
def list_custom_strategies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista todas as estratégias customizadas do usuário."""
    return db.query(Strategy).filter(Strategy.owner_id == current_user.id).order_by(Strategy.created_at.desc()).all()

@router.delete("/custom/{strategy_id}")
def delete_custom_strategy(
    strategy_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove uma estratégia customizada (Apenas se for dono)."""
    strategy = db.query(Strategy).filter(
        Strategy.id == strategy_id,
        Strategy.owner_id == current_user.id
    ).first()
    
    if not strategy:
        raise HTTPException(status_code=404, detail="Estratégia não encontrada ou acesso negado")
    
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
            fee_rate=fee_rate,
            use_compound=params.use_compound
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

