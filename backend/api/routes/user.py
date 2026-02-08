from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json

from core.database import get_db
from core.models import User, ExchangeKey, TelegramConfig, UserConfig
from core.auth import get_current_user
from core.security import encrypt_value
from core.notifications import send_telegram

router = APIRouter()

# --- SCHEMAS ---

class KeyCreate(BaseModel):
    label: str
    api_key: str
    api_secret: str
    exchange: str = "binance" 

class KeyResponse(BaseModel):
    id: int
    label: str
    exchange: str
    api_key_masked: str
    is_active: bool
    created_at: Any

class TelegramUpdate(BaseModel):
    chat_id: str
    bot_token: Optional[str] = None # Opcional
    is_active: bool = True



# --- ROUTES ---

# 1. Exchange Keys

@router.get("/keys", response_model=List[KeyResponse])
def list_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista chaves cadastradas (sem mostrar o segredo)."""
    keys = db.query(ExchangeKey).filter(ExchangeKey.user_id == current_user.id).all()
    
    return [
        {
            "id": k.id,
            "label": k.label,
            "exchange": k.exchange_name,
            "api_key_masked": f"****{k.api_key_encrypted[-4:]}" if k.api_key_encrypted else "****",
            "is_active": k.is_active,
            "created_at": k.created_at
        }
        for k in keys
    ]

@router.post("/keys", response_model=KeyResponse)
def add_key(
    key_data: KeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Adiciona nova chave criptografada."""
    # Encriptar antes de salvar
    enc_key = encrypt_value(key_data.api_key)
    enc_secret = encrypt_value(key_data.api_secret)
    
    new_key = ExchangeKey(
        user_id=current_user.id,
        exchange_name=key_data.exchange,
        api_key_encrypted=enc_key,
        api_secret_encrypted=enc_secret,
        label=key_data.label,
        is_active=True
    )
    
    db.add(new_key)
    db.commit()
    db.refresh(new_key)
    
    return {
        "id": new_key.id,
        "label": new_key.label,
        "exchange": new_key.exchange_name,
        "api_key_masked": f"****{key_data.api_key[-4:]}",
        "is_active": new_key.is_active,
        "created_at": new_key.created_at
    }

@router.delete("/keys/{key_id}")
def delete_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove uma chave."""
    key = db.query(ExchangeKey).filter(
        ExchangeKey.id == key_id,
        ExchangeKey.user_id == current_user.id
    ).first()
    
    if not key:
        raise HTTPException(status_code=404, detail="Chave não encontrada")
        
    db.delete(key)
    db.commit()
    return {"status": "success"}


# 2. Telegram Config

@router.get("/telegram")
def get_telegram_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    config = db.query(TelegramConfig).filter(TelegramConfig.user_id == current_user.id).first()
    if not config:
        return {"configured": False}
    
    return {
        "configured": True,
        "chat_id": config.chat_id,
        "is_active": config.is_active,
        "bot_token_masked": "****" if config.bot_token_encrypted else "Default Bot"
    }

@router.post("/telegram")
def update_telegram_config(
    config_data: TelegramUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    config = db.query(TelegramConfig).filter(TelegramConfig.user_id == current_user.id).first()
    
    enc_token = encrypt_value(config_data.bot_token) if config_data.bot_token else None
    
    if not config:
        config = TelegramConfig(
            user_id=current_user.id,
            chat_id=config_data.chat_id,
            bot_token_encrypted=enc_token,
            is_active=config_data.is_active
        )
        db.add(config)
    else:
        config.chat_id = config_data.chat_id
        config.is_active = config_data.is_active
        if enc_token:
            config.bot_token_encrypted = enc_token
            
    db.commit()
    return {"status": "success"}

@router.post("/telegram/test")
async def test_telegram(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Envia mensagem de teste."""
    config = db.query(TelegramConfig).filter(TelegramConfig.user_id == current_user.id).first()
    if not config or not config.chat_id:
        raise HTTPException(status_code=400, detail="Telegram não configurado")
        
    success = await send_telegram(config.chat_id, "🔔 <b>Teste Gastor:</b> Se você está lendo isso, a configuração deu certo!")
    
    if success:
        return {"status": "success"}
    else:
        raise HTTPException(status_code=500, detail="Falha ao enviar mensagem. Verifique o Chat ID.")


from core.models import User, ExchangeKey, TelegramConfig, UserConfig
# ... imports ...

class UserConfigResponse(BaseModel):
    # Fees
    exchange_fee: float
    slippage_overrides: Dict[str, float]
    
    # Backtest
    backtest_initial_balance: float
    backtest_use_compound: bool
    backtest_position_size: float
    
    # Paper Trading
    paper_initial_balance: float
    paper_default_coin: str
    paper_default_timeframe: str
    paper_use_compound: bool
    
    # System info
    system_defaults: Dict[str, float]
    supported_coins: List[str]

class UserConfigUpdate(BaseModel):
    # Fees
    exchange_fee: float
    slippage_overrides: Dict[str, float]
    
    # Backtest
    backtest_initial_balance: float
    backtest_use_compound: bool
    backtest_position_size: float
    
    # Paper Trading
    paper_initial_balance: float
    paper_default_coin: str
    paper_default_timeframe: str
    paper_use_compound: bool

# ... existing routes ...

# 3. User Config (Fees & Preferences)

from core.config import SLIPPAGE_BY_COIN, COINS

@router.get("/config", response_model=UserConfigResponse)
def get_user_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    config = db.query(UserConfig).filter(UserConfig.user_id == current_user.id).first()
    
    # Defaults
    data = {
        "exchange_fee": 0.001,
        "slippage_overrides": {},
        "backtest_initial_balance": 10000.0,
        "backtest_use_compound": True,
        "backtest_position_size": 1.0,
        "paper_initial_balance": 10000.0,
        "paper_default_coin": "SOL/USDT",
        "paper_default_timeframe": "1h",
        "paper_use_compound": True
    }
    
    if config:
        data["exchange_fee"] = config.exchange_fee
        data["slippage_overrides"] = json.loads(config.slippage_overrides) if config.slippage_overrides else {}
        data["backtest_initial_balance"] = config.backtest_initial_balance
        data["backtest_use_compound"] = config.backtest_use_compound
        data["backtest_position_size"] = config.backtest_position_size
        data["paper_initial_balance"] = config.paper_initial_balance
        data["paper_default_coin"] = config.paper_default_coin
        data["paper_default_timeframe"] = config.paper_default_timeframe
        data["paper_use_compound"] = config.paper_use_compound

    return {
        **data,
        "system_defaults": SLIPPAGE_BY_COIN,
        "supported_coins": COINS
    }

@router.post("/config")
def update_user_config(
    config_data: UserConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    config = db.query(UserConfig).filter(UserConfig.user_id == current_user.id).first()
    
    overrides_json = json.dumps(config_data.slippage_overrides)
    
    if not config:
        config = UserConfig(
            user_id=current_user.id,
            exchange_fee=config_data.exchange_fee,
            slippage_overrides=overrides_json,
            backtest_initial_balance=config_data.backtest_initial_balance,
            backtest_use_compound=config_data.backtest_use_compound,
            backtest_position_size=config_data.backtest_position_size,
            paper_initial_balance=config_data.paper_initial_balance,
            paper_default_coin=config_data.paper_default_coin,
            paper_default_timeframe=config_data.paper_default_timeframe,
            paper_use_compound=config_data.paper_use_compound
        )
        db.add(config)
    else:
        config.exchange_fee = config_data.exchange_fee
        config.slippage_overrides = overrides_json
        config.backtest_initial_balance = config_data.backtest_initial_balance
        config.backtest_use_compound = config_data.backtest_use_compound
        config.backtest_position_size = config_data.backtest_position_size
        config.paper_initial_balance = config_data.paper_initial_balance
        config.paper_default_coin = config_data.paper_default_coin
        config.paper_default_timeframe = config_data.paper_default_timeframe
        config.paper_use_compound = config_data.paper_use_compound
        
    db.commit()
    return {"status": "success"}
# 4. My Strategies

from core.models import Strategy

class StrategyResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    coin: str
    timeframe: str
    created_at: Any
    
    class Config:
        orm_mode = True

@router.get("/strategies", response_model=List[StrategyResponse])
def list_user_strategies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista as estratégias criadas pelo usuário."""
    strategies = db.query(Strategy).filter(Strategy.owner_id == current_user.id).all()
    return strategies
