#!/usr/bin/env python3
"""
Teste Controlado do Paper Trading Engine
=========================================

Simula o fluxo completo sem depender de WebSocket ou sinais reais.
Útil para identificar bugs na lógica de execução.

Como rodar:
    cd backend
    source venv/bin/activate
    python test_paper_engine.py
"""

import asyncio
import sys
from datetime import datetime, timedelta

# Adicionar path do projeto
sys.path.insert(0, '.')

from core.database import SessionLocal, engine as db_engine, Base
from core.models import PaperSession, PaperTrade, PaperPosition

# Criar tabelas se não existirem
Base.metadata.create_all(bind=db_engine)


def create_test_candles(base_price: float = 100.0, count: int = 50, trend: str = "down"):
    """
    Cria candles simulados com tendência clara.
    
    Args:
        base_price: Preço inicial
        count: Quantidade de candles
        trend: "down" para quedas consecutivas (RSI baixo), "up" para altas (RSI alto)
    """
    candles = []
    price = base_price
    timestamp = int((datetime.now() - timedelta(hours=count)).timestamp())
    
    for i in range(count):
        # Simular tendência consistente para afetar RSI
        if trend == "down":
            # Queda consistente de 1-2% por candle para RSI < 30
            change_pct = -1.5 - (0.5 * (i % 3))  # Varia entre -1.5% e -2.5%
        elif trend == "up":
            # Alta consistente de 1-2% por candle para RSI > 70
            change_pct = 1.5 + (0.5 * (i % 3))  # Varia entre 1.5% e 2.5%
        else:
            change_pct = 0
        
        new_price = price * (1 + change_pct / 100)
        
        candles.append({
            "time": timestamp + (i * 3600),  # 1h cada
            "open": price,
            "high": max(price, new_price) * 1.001,
            "low": min(price, new_price) * 0.999,
            "close": new_price,
            "volume": 1000 + i * 10,
        })
        
        price = new_price
    
    return candles


async def test_engine():
    """Testa o engine com cenários controlados."""
    
    print("\n" + "="*60)
    print("🧪 TESTE CONTROLADO DO PAPER TRADING ENGINE")
    print("="*60)
    
    # Importar engine aqui para evitar problemas de import circular
    from core.paper_trading.engine import PaperTradingEngine
    from core.paper_trading.strategies import calculate_triggers
    from core.paper_trading.signals import evaluate_signal
    
    # 1. Criar sessão de teste no banco
    print("\n📋 Criando sessão de teste...")
    with SessionLocal() as db:
        # Limpar sessões de teste anteriores
        db.query(PaperSession).filter(PaperSession.strategy_slug == "test_controlled").delete()
        db.commit()
        
        session = PaperSession(
            strategy_slug="rsi_reversal",  # Usar RSI Reversal para teste
            strategy_params={"rsi_period": 14, "rsi_buy": 30, "rsi_sell": 70},
            coin="TEST/USDT",
            timeframe="1h",
            initial_balance=10000.0,
            current_balance=10000.0,
            status="running",
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        session_id = session.id
        print(f"   ✅ Sessão criada: ID={session_id}")
    
    # 2. Criar engine
    print("\n🔧 Inicializando engine...")
    engine = PaperTradingEngine(
        session_id=session_id,
        initial_balance=10000.0,
        coin="TEST/USDT",
        timeframe="1h",
        strategy_slug="rsi_reversal",
        strategy_params={"rsi_period": 14, "rsi_buy": 30, "rsi_sell": 70},
    )
    print(f"   ✅ Engine criado | Balance: ${engine.balance:.2f}")
    
    # 3. Simular cenário de COMPRA (RSI baixo)
    print("\n📉 TESTE 1: Cenário de COMPRA (tendência de baixa)")
    print("-" * 40)
    
    # Carregar candles de queda
    candles_down = create_test_candles(base_price=100.0, count=50, trend="down")
    engine.candle_history = candles_down[:-1]  # Histórico
    
    print(f"   📊 Histórico carregado: {len(engine.candle_history)} candles")
    
    # Calcular triggers manualmente para ver valores
    triggers = calculate_triggers(
        "rsi_reversal",
        {"rsi_period": 14, "rsi_buy": 30, "rsi_sell": 70},
        engine.candle_history,
        False
    )
    print(f"   🎯 Triggers: status={triggers['status']}")
    for rule in triggers.get("buy_rules", []):
        print(f"      BUY: {rule['indicator']} = {rule['current']} {rule['operator']} {rule['threshold']} → {'✅' if rule['active'] else '❌'}")
    
    # Simular chegada do último candle
    last_candle = candles_down[-1]
    print(f"\n   📨 Processando candle @ ${last_candle['close']:.4f}...")
    await engine.on_candle(last_candle)
    
    # Verificar se comprou
    print(f"\n   📦 Posição: {engine.position}")
    print(f"   💰 Balance: ${engine.balance:.2f}")
    
    if engine.position:
        print("   ✅ COMPRA EXECUTADA!")
    else:
        print("   ❌ COMPRA NÃO EXECUTADA - Verificar logs acima")
    
    # 4. Simular cenário de VENDA (RSI alto)
    if engine.position:
        print("\n📈 TESTE 2: Cenário de VENDA (tendência de alta)")
        print("-" * 40)
        
        # Adicionar candles de alta ao histórico
        price = last_candle["close"]
        for i in range(30):
            price = price * 1.02  # Alta de 2% por candle
            engine.candle_history.append({
                "time": last_candle["time"] + ((i + 1) * 3600),
                "open": price * 0.99,
                "high": price * 1.01,
                "low": price * 0.98,
                "close": price,
                "volume": 1000,
            })
        
        # Manter janela
        if len(engine.candle_history) > 200:
            engine.candle_history = engine.candle_history[-200:]
        
        # Calcular triggers
        triggers = calculate_triggers(
            "rsi_reversal",
            {"rsi_period": 14, "rsi_buy": 30, "rsi_sell": 70},
            engine.candle_history,
            True
        )
        print(f"   🎯 Triggers: status={triggers['status']}")
        for rule in triggers.get("sell_rules", []):
            print(f"      SELL: {rule['indicator']} = {rule['current']} {rule['operator']} {rule['threshold']} → {'✅' if rule['active'] else '❌'}")
        
        # Processar mais um candle
        sell_candle = {
            "time": engine.candle_history[-1]["time"] + 3600,
            "open": price,
            "high": price * 1.01,
            "low": price * 0.99,
            "close": price * 1.01,
            "volume": 1000,
        }
        print(f"\n   📨 Processando candle @ ${sell_candle['close']:.4f}...")
        await engine.on_candle(sell_candle)
        
        print(f"\n   📦 Posição: {engine.position}")
        print(f"   💰 Balance: ${engine.balance:.2f}")
        
        if not engine.position:
            print("   ✅ VENDA EXECUTADA!")
        else:
            print("   ❌ VENDA NÃO EXECUTADA - Verificar logs acima")
    
    # 5. Limpar sessão de teste
    print("\n🧹 Limpando dados de teste...")
    with SessionLocal() as db:
        db.query(PaperTrade).filter(PaperTrade.session_id == session_id).delete()
        db.query(PaperPosition).filter(PaperPosition.session_id == session_id).delete()
        db.query(PaperSession).filter(PaperSession.id == session_id).delete()
        db.commit()
    print("   ✅ Dados limpos")
    
    print("\n" + "="*60)
    print("🏁 TESTE CONCLUÍDO")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(test_engine())
