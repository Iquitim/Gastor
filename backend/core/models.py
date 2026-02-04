from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.sql import func
from .database import Base

class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    coin = Column(String)
    period = Column(String)
    timeframe = Column(String)
    rules = Column(JSON)  # Armazena a estrutura de regras (Groups/Logic)
    
    initial_balance = Column(Float, default=10000.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class BacktestResult(Base):
    __tablename__ = "backtest_results"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, nullable=True) # Pode ser null se for teste rápido
    
    total_pnl = Column(Float)
    win_rate = Column(Float)
    max_drawdown = Column(Float)
    total_trades = Column(Integer)
    
    metrics_json = Column(JSON) # Detalhes completos
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# =============================================================================
# PAPER TRADING MODELS
# =============================================================================

class PaperSession(Base):
    """
    Sessão de Paper Trading ativa.
    
    Permite múltiplas sessões simultâneas, cada uma rodando uma estratégia diferente.
    """
    __tablename__ = "paper_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, default="default")  # Para multi-user futuro
    
    # Configuração da Estratégia
    strategy_slug = Column(String)  # "rsi_reversal" ou "custom_123"
    strategy_params = Column(JSON)
    coin = Column(String)           # "SOL/USDT"
    timeframe = Column(String)      # "1h"
    
    # Capital
    initial_balance = Column(Float)
    current_balance = Column(Float)
    
    # Estado
    status = Column(String, default="running")  # running, paused, stopped
    
    # Notificações
    telegram_chat_id = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    stopped_at = Column(DateTime(timezone=True), nullable=True)


class PaperTrade(Base):
    """
    Trade executado no Paper Trading.
    
    Registra cada operação de compra/venda simulada.
    """
    __tablename__ = "paper_trades"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("paper_sessions.id"), index=True)
    
    side = Column(String)  # "BUY" ou "SELL"
    price = Column(Float)
    quantity = Column(Float)
    value = Column(Float)  # price * quantity
    fee = Column(Float)
    
    # PnL (preenchido apenas para SELL)
    pnl = Column(Float, nullable=True)
    pnl_pct = Column(Float, nullable=True)
    
    # Saldo após o trade
    balance_after = Column(Float)
    
    executed_at = Column(DateTime(timezone=True), server_default=func.now())


class PaperPosition(Base):
    """
    Posição aberta no Paper Trading.
    
    Representa uma posição LONG ou SHORT em andamento.
    """
    __tablename__ = "paper_positions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("paper_sessions.id"), index=True)
    
    coin = Column(String)
    side = Column(String)  # "LONG" ou "SHORT"
    entry_price = Column(Float)
    quantity = Column(Float)
    current_price = Column(Float)
    unrealized_pnl = Column(Float)
    
    # Status da posição
    status = Column(String, default="OPEN")  # "OPEN" ou "CLOSED"
    
    # Dados de saída (preenchidos ao fechar)
    exit_price = Column(Float, nullable=True)
    exit_at = Column(DateTime(timezone=True), nullable=True)
    realized_pnl = Column(Float, nullable=True)
    
    opened_at = Column(DateTime(timezone=True), server_default=func.now())


class PaperTransaction(Base):
    """
    Transação de depósito ou saque no Paper Trading.
    
    Permite ao usuário adicionar ou remover capital da sessão.
    """
    __tablename__ = "paper_transactions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("paper_sessions.id"), index=True)
    
    type = Column(String)  # "deposit" ou "withdrawal"
    amount = Column(Float)
    balance_before = Column(Float)
    balance_after = Column(Float)
    
    note = Column(String, nullable=True)  # Nota opcional do usuário
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
