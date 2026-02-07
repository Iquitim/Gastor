"""
Live Trading Routes
===================

Endpoints para Paper Trading.

Suporta:
- Múltiplas sessões simultâneas (slots)
- Depósitos e saques virtuais
- Reset de sessão a qualquer momento
- Notificações via Telegram (opcional)
- Segurança e Isolamento de Usuários
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
import asyncio
import os
from datetime import datetime

from core.database import get_db
from core.models import PaperSession, PaperTrade, PaperPosition, PaperTransaction, User
from core.paper_trading import PaperTradingEngine
from core.binance_ws import get_multi_stream
from core.data_loader import fetch_binance_klines
from core import notifications
from core.auth import get_current_user  # Auth dependency

router = APIRouter()

# Armazena engines ativos em memória (por session_id)
# TODO: Em produção real, isso deveria ser um serviço separado (Redis/Celery)
# Para este MVP, memória funciona se houver apenas 1 instância da API.
active_engines: Dict[int, PaperTradingEngine] = {}


# =============================================================================
# Request/Response Models
# =============================================================================

class StartSessionRequest(BaseModel):
    """Request para iniciar sessão de Paper Trading."""
    strategy_slug: str
    strategy_params: Dict[str, Any] = {}
    coin: str = "SOL/USDT"
    timeframe: str = "1h"
    initial_balance: float = 10000.0
    telegram_chat_id: Optional[str] = None
    slot: int = Field(1, ge=1, le=5, description="Slot da sessão (1-5)")


class TransactionRequest(BaseModel):
    """Request para depósito ou saque."""
    amount: float
    note: Optional[str] = None


class SessionSummary(BaseModel):
    """Resumo de uma sessão."""
    id: int
    status: str
    strategy_slug: str
    coin: str
    timeframe: str
    initial_balance: float
    current_balance: float
    pnl: float
    pnl_pct: float
    total_trades: int
    has_position: bool
    started_at: Optional[str]
    slot: Optional[int]


# =============================================================================
# Helper Functions
# =============================================================================

def get_session_or_404(session_id: int, db: Session, user: User) -> PaperSession:
    """
    Busca sessão ou retorna 404.
    Garante que a sessão pertence ao usuário logado.
    """
    session = db.query(PaperSession).filter(
        PaperSession.id == session_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail=f"Sessão {session_id} não encontrada")
    
    # Security Check
    if session.user_id != user.id:
        raise HTTPException(status_code=403, detail="Acesso negado a esta sessão")
    
    return session


async def create_trade_callback(session: PaperSession):
    """Cria callback para notificações de trade."""
    async def on_trade(trade: Dict):
        if session.telegram_chat_id:
            await notifications.send_trade_alert(
                chat_id=session.telegram_chat_id,
                trade_type=trade["type"],
                symbol=trade["coin"],
                price=trade["price"],
                quantity=trade["quantity"],
                value=trade["value"],
                balance=trade["balance"],
                pnl=trade.get("pnl"),
                pnl_pct=trade.get("pnl_pct"),
                session_id=session.id,
                strategy_name=session.strategy_slug,
            )
    return on_trade


async def create_error_callback(session: PaperSession):
    """Cria callback para notificações de erro."""
    async def on_error(error: Exception):
        if session.telegram_chat_id:
            await notifications.send_error_alert(
                chat_id=session.telegram_chat_id,
                error_message=str(error),
                session_id=session.id,
            )
    return on_error


async def _stop_session_internal(session_id: int, db: Session, user_id_check: Optional[int] = None):
    """
    Lógica interna para parar sessão.
    Não faz commit no DB, caller deve fazer.
    """
    session = db.query(PaperSession).get(session_id)
    if not session:
        return
        
    if user_id_check and session.user_id != user_id_check:
        raise HTTPException(status_code=403, detail="Acesso negado")

    if session.status == "running":
        # Parar stream
        multi_stream = get_multi_stream()
        await multi_stream.remove_stream(f"session_{session.id}")
        
        # Remover engine
        if session.id in active_engines:
            del active_engines[session.id]
        
        # Atualizar status
        session.status = "stopped"
        session.stopped_at = datetime.utcnow()
        
        # Notificar (se possível)
        if session.telegram_chat_id:
            # Recalcular trades
            total_trades = db.query(PaperTrade).filter(PaperTrade.session_id == session.id).count()
            await notifications.send_session_stopped(
                chat_id=session.telegram_chat_id,
                strategy=session.strategy_slug,
                initial_balance=session.initial_balance,
                final_balance=session.current_balance,
                total_trades=total_trades,
                session_id=session.id,
            )


# =============================================================================
# Session Management
# =============================================================================

@router.post("/start")
async def start_session(
    request: StartSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Inicia uma nova sessão de Paper Trading.
    
    - Enforced: Usuário Autenticado.
    - Slot System: Se já existir sessão rodando no slot, ela é parada e arquivada.
    """
    
    # 1. Verificar Slot
    existing_session = db.query(PaperSession).filter(
        PaperSession.user_id == current_user.id,
        PaperSession.slot == request.slot,
        PaperSession.status == "running"
    ).first()
    
    if existing_session:
        print(f"[Live] Stopping existing session {existing_session.id} in slot {request.slot}")
        await _stop_session_internal(existing_session.id, db, current_user.id)
        # Commit intermediário para garantir status update antes de criar nova
        db.commit() 
    
    # 2. Configurar Chat ID
    # Prioridade: Request > User Profile > Env Var
    chat_id = request.telegram_chat_id or current_user.telegram_chat_id or os.getenv("TELEGRAM_DEFAULT_CHAT_ID", "")
    
    # 3. Criar Nova Sessão
    session = PaperSession(
        user_id=current_user.id,  # OWNERSHIP ENFORCEMENT
        slot=request.slot,
        strategy_slug=request.strategy_slug,
        strategy_params=request.strategy_params,
        coin=request.coin,
        timeframe=request.timeframe,
        initial_balance=request.initial_balance,
        current_balance=request.initial_balance,
        status="running",
        telegram_chat_id=chat_id,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # 4. Criar Engine e Callbacks
    on_trade = await create_trade_callback(session)
    on_error = await create_error_callback(session)
    
    engine = PaperTradingEngine(
        session_id=session.id,
        initial_balance=session.initial_balance,
        coin=session.coin,
        timeframe=session.timeframe,
        strategy_slug=request.strategy_slug,
        strategy_params=request.strategy_params,
    )
    engine.on_trade = on_trade
    # engine.on_error = on_error
    
    active_engines[session.id] = engine
    
    # 5. Warmup e Stream
    await engine.warmup()
    
    symbol = request.coin.replace("/", "")
    stream_id = f"session_{session.id}"
    
    multi_stream = get_multi_stream()
    await multi_stream.add_stream(
        stream_id=stream_id,
        symbol=symbol,
        interval=request.timeframe,
        on_candle=engine.on_candle,
        on_error=on_error,
    )
    
    # 6. Notificar
    if session.telegram_chat_id:
        await notifications.send_session_started(
            chat_id=session.telegram_chat_id,
            strategy=request.strategy_slug,
            coin=request.coin,
            timeframe=request.timeframe,
            balance=request.initial_balance,
            session_id=session.id,
        )
    
    return {
        "message": "Sessão iniciada com sucesso",
        "session_id": session.id,
        "slot": session.slot,
        "status": "running",
        "strategy": request.strategy_slug,
        "coin": request.coin,
        "balance": request.initial_balance,
    }


@router.delete("/sessions")
async def delete_all_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deleta TODAS as sessões DO USUÁRIO.
    Não afeta sessões de outros usuários.
    """
    
    # Buscar sessões do usuário
    user_sessions = db.query(PaperSession).filter(
        PaperSession.user_id == current_user.id
    ).all()
    
    session_ids = [s.id for s in user_sessions]
    
    if not session_ids:
        return {"message": "Nenhuma sessão encontrada."}
    
    # 1. Parar streams e engines ativos do usuário
    multi_stream = get_multi_stream()
    
    for sid in session_ids:
        if sid in active_engines:
            await multi_stream.remove_stream(f"session_{sid}")
            del active_engines[sid]
    
    # 2. Deletar (com cuidado no DB)
    try:
        # Bulk delete trades/transações/posições dessas sessões
        # SQLite não suporta DELETE com JOIN direito em algumas versões, então usando IN
        db.query(PaperTrade).filter(PaperTrade.session_id.in_(session_ids)).delete(synchronize_session=False)
        db.query(PaperTransaction).filter(PaperTransaction.session_id.in_(session_ids)).delete(synchronize_session=False)
        db.query(PaperPosition).filter(PaperPosition.session_id.in_(session_ids)).delete(synchronize_session=False)
        
        # Deletar sessões
        num_sessions = db.query(PaperSession).filter(PaperSession.id.in_(session_ids)).delete(synchronize_session=False)
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao deletar dados: {str(e)}")

    return {"message": f"Limpeza completa realizada. {num_sessions} sessões removidas."}


@router.post("/stop/{session_id}")
async def stop_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Para uma sessão de Paper Trading (apenas do usuário)."""
    
    session = get_session_or_404(session_id, db, current_user)
    
    if session.status != "running":
        raise HTTPException(status_code=400, detail="Sessão não está rodando")
    
    await _stop_session_internal(session.id, db)
    db.commit() # Commit final
    
    total_trades = db.query(PaperTrade).filter(PaperTrade.session_id == session_id).count()
    pnl = session.current_balance - session.initial_balance
    
    return {
        "message": "Sessão parada com sucesso",
        "session_id": session_id,
        "final_balance": session.current_balance,
        "pnl": pnl,
        "pnl_pct": (pnl / session.initial_balance) * 100,
        "total_trades": total_trades,
    }


@router.get("/sessions")
async def list_sessions(
    status: Optional[str] = None,
    # slot: Optional[int] = None, # Future filter
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Lista sessões de Paper Trading DO USUÁRIO.
    """
    query = db.query(PaperSession).filter(PaperSession.user_id == current_user.id)
    
    if status:
        query = query.filter(PaperSession.status == status)
    
    sessions = query.order_by(
        PaperSession.created_at.desc()
    ).limit(limit).all()
    
    result = []
    for s in sessions:
        # Calcular Equity
        position = db.query(PaperPosition).filter(
            PaperPosition.session_id == s.id,
            PaperPosition.status == "OPEN"
        ).first()
        
        position_value = 0.0
        if position:
            if s.id in active_engines and active_engines[s.id].candle_history:
                 current_price = active_engines[s.id].candle_history[-1]["close"]
            else:
                 current_price = position.current_price or position.entry_price
            position_value = position.quantity * current_price
        
        equity = s.current_balance + position_value
        pnl = equity - s.initial_balance
        
        total_trades = db.query(PaperTrade).filter(PaperTrade.session_id == s.id).count()
        
        result.append({
            "id": s.id,
            "slot": s.slot,
            "status": s.status,
            "strategy_slug": s.strategy_slug,
            "coin": s.coin,
            "timeframe": s.timeframe,
            "initial_balance": s.initial_balance,
            "current_balance": s.current_balance,
            "equity": equity,
            "pnl": pnl,
            "pnl_pct": (pnl / s.initial_balance) * 100 if s.initial_balance > 0 else 0,
            "total_trades": total_trades,
            "has_position": position is not None,
            "started_at": s.created_at.isoformat() if s.created_at else None,
            "stopped_at": s.stopped_at.isoformat() if s.stopped_at else None,
        })
    
    return result


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Retorna detalhes de uma sessão (apenas do usuário)."""
    
    session = get_session_or_404(session_id, db, current_user)
    
    # ... Resto da lógica é igual, mas segura porque `get_session_or_404` verifica dono
    
    position = db.query(PaperPosition).filter(
        PaperPosition.session_id == session_id,
        PaperPosition.status == "OPEN"
    ).first()
    
    trades = db.query(PaperTrade).filter(
        PaperTrade.session_id == session_id
    ).order_by(PaperTrade.executed_at.desc()).limit(20).all()
    
    transactions = db.query(PaperTransaction).filter(
        PaperTransaction.session_id == session_id
    ).order_by(PaperTransaction.created_at.desc()).limit(10).all()
    
    sell_trades = [t for t in trades if t.side == "SELL"]
    total_pnl = sum(t.pnl or 0 for t in sell_trades)
    winning = [t for t in sell_trades if (t.pnl or 0) > 0]
    win_rate = (len(winning) / len(sell_trades) * 100) if sell_trades else 0
    
    pnl = session.current_balance - session.initial_balance
    
    triggers = None
    price_history = []
    if session_id in active_engines:
        engine = active_engines[session_id]
        try:
            triggers = engine.get_triggers()
        except Exception as e:
            triggers = {"status": "error", "message": str(e)}
        
        if engine.candle_history:
            price_history = [
                {"time": c["time"], "open": c["open"], "high": c["high"], "low": c["low"], "close": c["close"]}
                for c in engine.candle_history[-50:]
            ]
    
    return {
        "session": {
            "id": session.id,
            "slot": session.slot,
            "status": session.status,
            "strategy_slug": session.strategy_slug,
            "strategy_params": session.strategy_params,
            "coin": session.coin,
            "timeframe": session.timeframe,
            "initial_balance": session.initial_balance,
            "current_balance": session.current_balance,
            "pnl": pnl,
            "pnl_pct": (pnl / session.initial_balance) * 100 if session.initial_balance > 0 else 0,
            "telegram_configured": bool(session.telegram_chat_id),
            "started_at": session.created_at.isoformat() if session.created_at else None,
            "stopped_at": session.stopped_at.isoformat() if session.stopped_at else None,
        },
        "position": {
            "side": position.side,
            "coin": position.coin,
            "entry_price": position.entry_price,
            "quantity": position.quantity,
            "current_price": position.current_price,
            "unrealized_pnl": position.unrealized_pnl,
            "opened_at": position.opened_at.isoformat() if position.opened_at else None,
        } if position else None,
        "triggers": triggers,
        "metrics": {
            "total_trades": len(trades),
            "completed_trades": len(sell_trades),
            "total_pnl": total_pnl,
            "win_rate": win_rate,
        },
        "recent_trades": [
            {
                "id": t.id,
                "side": t.side,
                "price": t.price,
                "quantity": t.quantity,
                "value": t.value,
                "fee": t.fee,
                "pnl": t.pnl,
                "pnl_pct": t.pnl_pct,
                "balance_after": t.balance_after,
                "executed_at": t.executed_at.isoformat() if t.executed_at else None,
            }
            for t in trades
        ],
        "recent_transactions": [
            {
                "id": tx.id,
                "type": tx.type,
                "amount": tx.amount,
                "balance_before": tx.balance_before,
                "balance_after": tx.balance_after,
                "note": tx.note,
                "created_at": tx.created_at.isoformat() if tx.created_at else None,
            }
            for tx in transactions
        ],
        "price_history": price_history,
    }


# =============================================================================
# Session Actions
# =============================================================================

@router.post("/sessions/{session_id}/deposit")
async def deposit(
    session_id: int,
    request: TransactionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Adiciona capital (auth enforced)."""
    session = get_session_or_404(session_id, db, current_user)
    
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Valor deve ser positivo")
    
    if session_id in active_engines:
        result = active_engines[session_id].deposit(request.amount, request.note)
    else:
        balance_before = session.current_balance
        balance_after = balance_before + request.amount
        
        transaction = PaperTransaction(
            session_id=session_id,
            type="deposit",
            amount=request.amount,
            balance_before=balance_before,
            balance_after=balance_after,
            note=request.note,
        )
        db.add(transaction)
        
        session.current_balance = balance_after
        db.commit()
        
        result = {
            "type": "deposit",
            "amount": request.amount,
            "balance_before": balance_before,
            "balance_after": balance_after,
        }
    
    if session.telegram_chat_id:
        await notifications.send_deposit_alert(
            chat_id=session.telegram_chat_id,
            amount=request.amount,
            new_balance=result["balance_after"],
            session_id=session_id,
        )
    
    return {"message": "Depósito realizado com sucesso", **result}


@router.post("/sessions/{session_id}/withdraw")
async def withdraw(
    session_id: int,
    request: TransactionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Remove capital (auth enforced)."""
    session = get_session_or_404(session_id, db, current_user)
    
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Valor deve ser positivo")
    
    if request.amount > session.current_balance:
        raise HTTPException(status_code=400, detail=f"Saldo insuficiente.")
    
    if session_id in active_engines:
        result = active_engines[session_id].withdraw(request.amount, request.note)
    else:
        balance_before = session.current_balance
        balance_after = balance_before - request.amount
        
        transaction = PaperTransaction(
            session_id=session_id,
            type="withdrawal",
            amount=request.amount,
            balance_before=balance_before,
            balance_after=balance_after,
            note=request.note,
        )
        db.add(transaction)
        
        session.current_balance = balance_after
        db.commit()
        
        result = {
            "type": "withdrawal",
            "amount": request.amount,
            "balance_before": balance_before,
            "balance_after": balance_after,
        }
    
    if session.telegram_chat_id:
        await notifications.send_withdrawal_alert(
            chat_id=session.telegram_chat_id,
            amount=request.amount,
            new_balance=result["balance_after"],
            session_id=session_id,
        )
    
    return {"message": "Saque realizado com sucesso", **result}


@router.post("/sessions/{session_id}/reset")
async def reset_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Reseta a sessão (auth enforced)."""
    session = get_session_or_404(session_id, db, current_user)
    
    old_balance = session.current_balance
    
    if session_id in active_engines:
        result = active_engines[session_id].reset()
    else:
        db.query(PaperTrade).filter(PaperTrade.session_id == session_id).delete()
        db.query(PaperPosition).filter(PaperPosition.session_id == session_id).delete()
        db.query(PaperTransaction).filter(PaperTransaction.session_id == session_id).delete()
        
        session.current_balance = session.initial_balance
        db.commit()
        
        result = {"old_balance": old_balance, "new_balance": session.initial_balance}
    
    return {"message": "Sessão resetada com sucesso", "session_id": session_id, **result}


# =============================================================================
# Status and Stats - GLOBAL (Admin or System view? For now let's keep restricted)
# =============================================================================

@router.get("/status")
async def get_global_status(
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user) # Allow public for health check? Or restrict? Be safe.
) -> Dict[str, Any]:
    """
    Retorna status global do Paper Trading.
    TODO: Em produção, isso deveria ser rota ADMIN apenas.
    """
    active_sessions = db.query(PaperSession).filter(PaperSession.status == "running").all()
    multi_stream = get_multi_stream()
    active_streams = multi_stream.get_active_streams()
    
    return {
        "active_sessions_count": len(active_sessions),
        "active_streams_count": len(active_streams),
    }


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Deleta sessão (Auth enforced)."""
    session = get_session_or_404(session_id, db, current_user)
    
    if session.status == "running" and not force:
        raise HTTPException(status_code=400, detail="Pare a sessão antes de deletar")
    
    # Se estiver rodando (Force Delete), parar primeiro
    if session.status == "running":
         await _stop_session_internal(session.id, db)
         # Não commitar ainda, vamos deletar

    # Delete Cascade Manual
    db.query(PaperTrade).filter(PaperTrade.session_id == session_id).delete()
    db.query(PaperPosition).filter(PaperPosition.session_id == session_id).delete()
    db.query(PaperTransaction).filter(PaperTransaction.session_id == session_id).delete()
    
    db.delete(session)
    db.commit()
    
    return {"message": f"Sessão {session_id} deletada com sucesso"}


async def restore_active_sessions():
    """Restaura sessões ativas após reinício do servidor."""
    print("[Live] Restoring active sessions...")
    try:
        from core.database import SessionLocal
        with SessionLocal() as db:
            # Restaurar SÓ running e de usuários ativos
            # Como não temos user join aqui fácil sem circular imports ou complexidade,
            # confiamos no status 'running'.
            sessions = db.query(PaperSession).filter(PaperSession.status == "running").all()
            print(f"[Live] Found {len(sessions)} active sessions to restore.")
            
            multi_stream = get_multi_stream()
            
            for session in sessions:
                print(f"[Live] Restoring session {session.id} (Slot {session.slot})...")
                
                # Prevenir duplicatas se chamado 2x
                if session.id in active_engines:
                    continue
                
                engine = PaperTradingEngine(
                    session_id=session.id,
                    initial_balance=session.initial_balance,
                    coin=session.coin,
                    timeframe=session.timeframe,
                    strategy_slug=session.strategy_slug,
                    strategy_params=session.strategy_params or {},
                )
                
                engine.on_trade = await create_trade_callback(session)
                engine.on_error = await create_error_callback(session)
                
                active_engines[session.id] = engine
                await engine.warmup()
                
                await multi_stream.add_stream(
                    stream_id=f"session_{session.id}",
                    symbol=session.coin.replace("/", ""),
                    interval=session.timeframe,
                    on_candle=engine.on_candle,
                    on_error=engine.on_error,
                )
    except Exception as e:
        print(f"[Live] Error restoring sessions: {e}")
