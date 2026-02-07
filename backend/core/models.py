from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


# =============================================================================
# USER MODEL
# =============================================================================

class User(Base):
    """
    User account for authentication.
    
    Stores credentials and optional integrations (Telegram, Binance, Google OAuth).
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Nullable for OAuth-only users
    
    # OAuth providers
    google_id = Column(String, unique=True, nullable=True, index=True)
    
    # Optional integrations
    telegram_chat_id = Column(String, nullable=True)
    binance_api_key = Column(String, nullable=True)      # TODO: Encrypt in production
    binance_api_secret = Column(String, nullable=True)   # TODO: Encrypt in production
    
    # Account status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    strategies = relationship("Strategy", back_populates="owner")
    paper_sessions = relationship("PaperSession", back_populates="owner")
    
    # New Config Relationships
    keys = relationship("ExchangeKey", back_populates="user", cascade="all, delete-orphan")
    telegram_config = relationship("TelegramConfig", back_populates="user", uselist=False, cascade="all, delete-orphan")
    fee_config = relationship("UserConfig", back_populates="user", uselist=False, cascade="all, delete-orphan")
    config = relationship("UserConfig", back_populates="user", uselist=False, viewonly=True, sync_backref=False) # Alias for backward compat if needed, or just rename outright


class ExchangeKey(Base):
    __tablename__ = "exchange_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    exchange_name = Column(String, default="binance") # Enum: binance, binance_us
    api_key_encrypted = Column(String, nullable=False)
    api_secret_encrypted = Column(String, nullable=False)
    label = Column(String, default="Conta Principal")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="keys")


class TelegramConfig(Base):
    __tablename__ = "telegram_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    bot_token_encrypted = Column(String, nullable=True) # Opcional: Usuário pode usar bot próprio
    chat_id = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="telegram_config")


class UserConfig(Base):
    __tablename__ = "user_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # Fees (legacy but still needed)
    exchange_fee = Column(Float, default=0.001) # 0.1% padrão
    slippage_overrides = Column(String, default="{}") # JSON string
    
    # Backtest Settings
    backtest_initial_balance = Column(Float, default=10000.0)
    backtest_use_compound = Column(Boolean, default=True)
    backtest_position_size = Column(Float, default=1.0) # 100%
    
    # Paper Trading Settings
    paper_initial_balance = Column(Float, default=10000.0)
    paper_default_coin = Column(String, default="SOL/USDT")
    paper_default_timeframe = Column(String, default="1h")
    paper_use_compound = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="config")


# =============================================================================
# STRATEGY & BACKTEST MODELS
# =============================================================================

class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for backward compatibility
    
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    coin = Column(String)
    period = Column(String)
    timeframe = Column(String)
    rules = Column(JSON)  # Armazena a estrutura de regras (Groups/Logic)
    
    initial_balance = Column(Float, default=10000.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    owner = relationship("User", back_populates="strategies")

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
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for backward compatibility
    
    # Relationship
    owner = relationship("User", back_populates="paper_sessions")
    
    # Configuração da Estratégia
    strategy_slug = Column(String)  # "rsi_reversal" ou "custom_123"
    strategy_params = Column(JSON)
    coin = Column(String)           # "SOL/USDT"
    timeframe = Column(String)      # "1h"
    
    # Slot Management
    slot = Column(Integer, nullable=True) # 1-5, permite reuso de "espaços"
    
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
