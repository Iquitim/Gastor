"""
Live Trading Routes
===================

Endpoints para Paper Trading.

Suporta:
- Múltiplas sessões simultâneas
- Depósitos e saques virtuais
- Reset de sessão a qualquer momento
- Notificações via Telegram (opcional)
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
import asyncio
import os
from datetime import datetime

from core.database import get_db
from core.models import PaperSession, PaperTrade, PaperPosition, PaperTransaction
from core.paper_trading import PaperTradingEngine
from core.binance_ws import get_multi_stream
from core.data_loader import fetch_binance_klines
from core import notifications

router = APIRouter()

# Armazena engines ativos em memória (por session_id)
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


# =============================================================================
# Helper Functions
# =============================================================================

def get_session_or_404(session_id: int, db: Session) -> PaperSession:
    """Busca sessão ou retorna 404."""
    session = db.query(PaperSession).filter(
        PaperSession.id == session_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail=f"Sessão {session_id} não encontrada")
    
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


# =============================================================================
# Session Management
# =============================================================================

@router.post("/start")
async def start_session(
    request: StartSessionRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Inicia uma nova sessão de Paper Trading.
    
    Permite múltiplas sessões simultâneas.
    """
    # Usar Chat ID padrão se não especificado
    chat_id = request.telegram_chat_id or os.getenv("TELEGRAM_DEFAULT_CHAT_ID", "")
    
    # Criar sessão no banco
    session = PaperSession(
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
    
    # Criar engine
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
    # engine.on_error = on_error # Not used in new class yet, but good to keep structure
    
    active_engines[session.id] = engine
    
    # Carregar dados históricos
    await engine.warmup()
    
    # Iniciar stream WebSocket
    symbol = request.coin.replace("/", "")
    
    # Iniciar stream WebSocket
    stream_id = f"session_{session.id}"
    
    multi_stream = get_multi_stream()
    await multi_stream.add_stream(
        stream_id=stream_id,
        symbol=symbol,
        interval=request.timeframe,
        on_candle=engine.on_candle,
        on_error=on_error,
    )
    
    # Notificar início
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
        "status": "running",
        "strategy": request.strategy_slug,
        "coin": request.coin,
        "balance": request.initial_balance,
    }



@router.delete("/sessions")
async def delete_all_sessions(db: Session = Depends(get_db)):
    """Deleta TODAS as sessões de Paper Trading, limpando trades, transações e posições."""
    
    # 1. Parar todos os streams
    multi_stream = get_multi_stream()
    active_ids = list(active_engines.keys())
    
    for session_id in active_ids:
        await multi_stream.remove_stream(f"session_{session_id}")
    
    active_engines.clear()
    
    # 2. Deletar dependências (já que não temos cascade garantido)
    try:
        # Nuke total das tabelas de Paper Trading
        db.query(PaperTrade).delete()
        db.query(PaperTransaction).delete()
        db.query(PaperPosition).delete()
        num_sessions = db.query(PaperSession).delete()
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao deletar dados: {str(e)}")

    return {"message": f"Limpeza completa realizada. {num_sessions} sessões removidas."}


@router.post("/stop/{session_id}")
async def stop_session(
    session_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Para uma sessão de Paper Trading."""
    session = get_session_or_404(session_id, db)
    
    if session.status != "running":
        raise HTTPException(status_code=400, detail="Sessão não está rodando")
    
    # Parar stream
    multi_stream = get_multi_stream()
    await multi_stream.remove_stream(f"session_{session_id}")
    
    # Remover engine
    if session_id in active_engines:
        del active_engines[session_id]
    
    # Contar trades
    total_trades = db.query(PaperTrade).filter(
        PaperTrade.session_id == session_id
    ).count()
    
    # Atualizar status
    session.status = "stopped"
    session.stopped_at = datetime.utcnow()
    db.commit()
    
    # Notificar encerramento
    if session.telegram_chat_id:
        await notifications.send_session_stopped(
            chat_id=session.telegram_chat_id,
            strategy=session.strategy_slug,
            initial_balance=session.initial_balance,
            final_balance=session.current_balance,
            total_trades=total_trades,
            session_id=session.id,
        )
    
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
    limit: int = 50,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Lista todas as sessões de Paper Trading.
    
    Args:
        status: Filtrar por status (running, stopped, paused)
        limit: Máximo de resultados
    """
    query = db.query(PaperSession)
    
    if status:
        query = query.filter(PaperSession.status == status)
    
    sessions = query.order_by(
        PaperSession.created_at.desc()
    ).limit(limit).all()
    
    result = []
    for s in sessions:
        # Contar trades
        total_trades = db.query(PaperTrade).filter(
            PaperTrade.session_id == s.id
        ).count()
        
        # Verificar posição aberta e calcular equity
        position = db.query(PaperPosition).filter(
            PaperPosition.session_id == s.id,
            PaperPosition.status == "OPEN"
        ).first()
        
        # Calcular valor da posição
        position_value = 0.0
        if position:
            # Usar triggers do engine ativo para preço atual, ou current_price da posição
            if s.id in active_engines:
                engine = active_engines[s.id]
                if engine.candle_history:
                    current_price = engine.candle_history[-1]["close"]
                else:
                    current_price = position.current_price or position.entry_price
            else:
                current_price = position.current_price or position.entry_price
            position_value = position.quantity * current_price
        
        # Equity = Cash + Position Value
        equity = s.current_balance + position_value
        pnl = equity - s.initial_balance
        
        result.append({
            "id": s.id,
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
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Retorna detalhes de uma sessão."""
    session = get_session_or_404(session_id, db)
    
    # Buscar posição ABERTA apenas
    position = db.query(PaperPosition).filter(
        PaperPosition.session_id == session_id,
        PaperPosition.status == "OPEN"
    ).first()
    
    # Buscar trades recentes
    trades = db.query(PaperTrade).filter(
        PaperTrade.session_id == session_id
    ).order_by(PaperTrade.executed_at.desc()).limit(20).all()
    
    # Buscar transações
    transactions = db.query(PaperTransaction).filter(
        PaperTransaction.session_id == session_id
    ).order_by(PaperTransaction.created_at.desc()).limit(10).all()
    
    # Métricas
    sell_trades = [t for t in trades if t.side == "SELL"]
    total_pnl = sum(t.pnl or 0 for t in sell_trades)
    winning = [t for t in sell_trades if (t.pnl or 0) > 0]
    win_rate = (len(winning) / len(sell_trades) * 100) if sell_trades else 0
    
    pnl = session.current_balance - session.initial_balance
    
    # Buscar triggers e price history se engine ativo
    triggers = None
    price_history = []
    if session_id in active_engines:
        engine = active_engines[session_id]
        try:
            triggers = engine.get_triggers()
        except Exception as e:
            print(f"Error getting triggers: {e}")
            triggers = {"status": "error", "message": str(e)}
        
        # Últimos 50 candles para gráfico (OHLC completo)
        if engine.candle_history:
            price_history = [
                {
                    "time": c["time"],
                    "open": c["open"],
                    "high": c["high"],
                    "low": c["low"],
                    "close": c["close"],
                }
                for c in engine.candle_history[-50:]
            ]
    
    return {
        "session": {
            "id": session.id,
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
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Adiciona capital a uma sessão."""
    session = get_session_or_404(session_id, db)
    
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Valor deve ser positivo")
    
    # Atualizar via engine se ativo, senão direto no banco
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
    
    # Notificar
    if session.telegram_chat_id:
        await notifications.send_deposit_alert(
            chat_id=session.telegram_chat_id,
            amount=request.amount,
            new_balance=result["balance_after"],
            session_id=session_id,
        )
    
    return {
        "message": "Depósito realizado com sucesso",
        **result,
    }


@router.post("/sessions/{session_id}/withdraw")
async def withdraw(
    session_id: int,
    request: TransactionRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Remove capital de uma sessão."""
    session = get_session_or_404(session_id, db)
    
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Valor deve ser positivo")
    
    if request.amount > session.current_balance:
        raise HTTPException(
            status_code=400, 
            detail=f"Saldo insuficiente. Disponível: ${session.current_balance:.2f}"
        )
    
    # Atualizar via engine se ativo, senão direto no banco
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
    
    # Notificar
    if session.telegram_chat_id:
        await notifications.send_withdrawal_alert(
            chat_id=session.telegram_chat_id,
            amount=request.amount,
            new_balance=result["balance_after"],
            session_id=session_id,
        )
    
    return {
        "message": "Saque realizado com sucesso",
        **result,
    }


@router.post("/sessions/{session_id}/reset")
async def reset_session(
    session_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Reseta uma sessão para o saldo inicial.
    
    Remove todos os trades, posições e transações.
    """
    session = get_session_or_404(session_id, db)
    
    old_balance = session.current_balance
    
    # Resetar via engine se ativo
    if session_id in active_engines:
        result = active_engines[session_id].reset()
    else:
        # Limpar dados
        db.query(PaperTrade).filter(
            PaperTrade.session_id == session_id
        ).delete()
        
        db.query(PaperPosition).filter(
            PaperPosition.session_id == session_id
        ).delete()
        
        db.query(PaperTransaction).filter(
            PaperTransaction.session_id == session_id
        ).delete()
        
        session.current_balance = session.initial_balance
        db.commit()
        
        result = {
            "old_balance": old_balance,
            "new_balance": session.initial_balance,
        }
    
    return {
        "message": "Sessão resetada com sucesso",
        "session_id": session_id,
        **result,
    }


# =============================================================================
# Status and Stats
# =============================================================================

@router.get("/status")
async def get_global_status(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Retorna status global do Paper Trading.
    
    Inclui todas as sessões ativas e streams conectados.
    """
    # Sessões ativas
    active_sessions = db.query(PaperSession).filter(
        PaperSession.status == "running"
    ).all()
    
    # Streams ativos
    multi_stream = get_multi_stream()
    active_streams = multi_stream.get_active_streams()
    
    # Telegram configurado
    telegram_configured = notifications.is_telegram_configured()
    
    sessions_summary = []
    for s in active_sessions:
        pnl = s.current_balance - s.initial_balance
        sessions_summary.append({
            "id": s.id,
            "strategy": s.strategy_slug,
            "coin": s.coin,
            "balance": s.current_balance,
            "pnl": pnl,
            "pnl_pct": (pnl / s.initial_balance) * 100 if s.initial_balance > 0 else 0,
        })
    
    return {
        "active_sessions_count": len(active_sessions),
        "active_streams_count": len(active_streams),
        "telegram_configured": telegram_configured,
        "sessions": sessions_summary,
        "streams": active_streams,
    }


@router.get("/stats")
async def get_stats(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Retorna estatísticas agregadas de todas as sessões.
    """
    # Total de sessões
    total_sessions = db.query(PaperSession).count()
    active_sessions = db.query(PaperSession).filter(
        PaperSession.status == "running"
    ).count()
    
    # Total de trades
    total_trades = db.query(PaperTrade).count()
    
    # PnL total de todas as sessões
    sessions = db.query(PaperSession).all()
    total_pnl = sum(s.current_balance - s.initial_balance for s in sessions)
    
    # Trades vencedores
    winning_trades = db.query(PaperTrade).filter(
        PaperTrade.side == "SELL",
        PaperTrade.pnl > 0
    ).count()
    
    losing_trades = db.query(PaperTrade).filter(
        PaperTrade.side == "SELL",
        PaperTrade.pnl < 0
    ).count()
    
    total_completed = winning_trades + losing_trades
    win_rate = (winning_trades / total_completed * 100) if total_completed > 0 else 0
    
    return {
        "total_sessions": total_sessions,
        "active_sessions": active_sessions,
        "total_trades": total_trades,
        "completed_trades": total_completed,
        "total_pnl": total_pnl,
        "win_rate": win_rate,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
    }


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Deleta uma sessão e todos os seus dados.
    
    A sessão deve estar parada antes de ser deletada.
    """
    session = get_session_or_404(session_id, db)
    
    if session.status == "running":
        raise HTTPException(
            status_code=400,
            detail="Pare a sessão antes de deletar"
        )
    
    # Limpar dados relacionados
    db.query(PaperTrade).filter(
        PaperTrade.session_id == session_id
    ).delete()
    
    db.query(PaperPosition).filter(
        PaperPosition.session_id == session_id
    ).delete()
    
    db.query(PaperTransaction).filter(
        PaperTransaction.session_id == session_id
    ).delete()
    
    # Deletar sessão
    db.delete(session)
    db.commit()
    
    return {
        "message": f"Sessão {session_id} deletada com sucesso",
    }


async def restore_active_sessions():
    """Restaura sessões ativas após reinício do servidor."""
    print("[Live] Restoring active sessions...")
    try:
        # Precisamos de uma sessão nova pois estamos fora do contexto de request
        from core.database import SessionLocal
        with SessionLocal() as db:
            sessions = db.query(PaperSession).filter(PaperSession.status == "running").all()
            print(f"[Live] Found {len(sessions)} active sessions to restore.")
            
            multi_stream = get_multi_stream()
            
            for session in sessions:
                # Criar engine
                print(f"[Live] Restoring session {session.id} ({session.strategy_slug})...")
                engine = PaperTradingEngine(
                    session_id=session.id,
                    initial_balance=session.initial_balance,
                    coin=session.coin,
                    timeframe=session.timeframe,
                    strategy_slug=session.strategy_slug,
                    strategy_params=session.strategy_params or {},
                )
                
                # Callbacks
                engine.on_trade = await create_trade_callback(session)
                engine.on_error = await create_error_callback(session)
                
                # Registrar
                active_engines[session.id] = engine
                
                # Warmup
                await engine.warmup()
                
                # Stream
                symbol = session.coin.replace("/", "")
                stream_id = f"session_{session.id}"
                
                await multi_stream.add_stream(
                    stream_id=stream_id,
                    symbol=symbol,
                    interval=session.timeframe,
                    on_candle=engine.on_candle,
                    on_error=engine.on_error,
                )
    except Exception as e:
        print(f"[Live] Error restoring sessions: {e}")
