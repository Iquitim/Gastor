from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
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
