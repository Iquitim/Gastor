
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
import pandas as pd

from core.database import SessionLocal
from core.models import PaperSession, PaperTrade, PaperPosition, PaperTransaction
from core.data_loader import fetch_binance_klines

from .strategies import calculate_triggers
from .signals import evaluate_signal

class PaperTradingEngine:
    """
    Motor de Paper Trading.
    
    Recebe candles em tempo real e executa a estratégia,
    simulando ordens sem enviar para a exchange.
    """
    
    def __init__(self, session_id: int, initial_balance: float, coin: str, timeframe: str, strategy_slug: str, strategy_params: Dict = None):
        self.session_id = session_id
        self.coin = coin
        self.timeframe = timeframe
        self.strategy_slug = strategy_slug
        self.strategy_params = strategy_params or {}
        
        # Estado em memória
        self.balance = initial_balance
        self.position = None  # {id, size, entry_price}
        self.candle_history: List[Dict] = []
        
        # Callbacks
        self.on_trade: Optional[Callable] = None
        self.on_signal: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
        # Sincronizar estado inicial
        self._sync_state()

    def _sync_state(self):
        """Sincroniza estado em memória com banco de dados"""
        try:
            with SessionLocal() as db:
                session = db.query(PaperSession).get(self.session_id)
                if not session:
                    return

                self.balance = session.current_balance
                
                # Carregar posição aberta, se houver
                pos_rec = db.query(PaperPosition).filter(
                    PaperPosition.session_id == self.session_id,
                    PaperPosition.status == "OPEN"
                ).first()
                
                if pos_rec:
                    self.position = {
                        "id": pos_rec.id,
                        "side": pos_rec.side,
                        "entry_price": pos_rec.entry_price,
                        "quantity": pos_rec.quantity,
                        "coin": session.coin
                    }
                else:
                    self.position = None
        except Exception as e:
            print(f"[PaperEngine] Error syncing state: {e}")

    async def warmup(self):
        """Carrega dados históricos iniciais para habilitar gatilhos imediatos."""
        try:
            symbol = self.coin.replace("/", "").upper()
            print(f"[PaperEngine] Warming up {self.session_id} for {symbol}...")
            
            # Calcular histórico necessário (simplificado para 150 candles)
            candles_needed = 150
            
            # Calcular dias
            interval_minutes = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240, "1d": 1440}
            minutes_per_candle = interval_minutes.get(self.timeframe, 60)
            days_needed = max(1, (candles_needed * minutes_per_candle) // 1440 + 1)
            
            print(f"[PaperEngine] Fetching {days_needed} days of history ({candles_needed} candles needed)")
            
            candles = await fetch_binance_klines(symbol, self.timeframe, days=days_needed)
            
            if candles:
                if len(candles) > candles_needed:
                     self.candle_history = candles[-candles_needed:]
                else:
                     self.candle_history = candles
                print(f"[PaperEngine] Warmed up with {len(self.candle_history)} candles")
        except Exception as e:
            print(f"[PaperEngine] Warmup failed: {e}")

    async def on_candle(self, candle: Dict[str, Any]):
        """
        Chamado quando um novo candle fecha.
        Avalia a estratégia e executa trades se necessário.
        """
        try:
            # Converter para formato padrão interno
            if "time" in candle and "close" in candle:
                c = candle.copy()
            else:
                c = {
                    "time": int(candle["t"] / 1000),
                    "open": float(candle["o"]),
                    "high": float(candle["h"]),
                    "low": float(candle["l"]),
                    "close": float(candle["c"]),
                    "volume": float(candle["v"]),
                }
            
            # Atualizar preço da posição aberta
            if self.position:
                self._update_position_price(c["close"])
            
            # Adicionar ao histórico
            self.candle_history.append(c)
            
            # Manter janela de histórico
            if len(self.candle_history) > 200:
                self.candle_history.pop(0)
            
            # Precisa de histórico mínimo para indicadores
            if len(self.candle_history) < 20:
                print(f"[PaperEngine {self.session_id}] ⏳ Waiting for history: {len(self.candle_history)}/20 candles")
                return
            
            # Avaliar estratégia
            signal = self._evaluate_signal()
            print(f"[PaperEngine {self.session_id}] 📊 Signal evaluated: {signal or 'None'} | Position: {'Yes' if self.position else 'No'}")
            
            if signal and self.on_signal:
                result = self.on_signal(signal, candle)
                if asyncio.iscoroutine(result):
                    await result
            
            # Executar trade se houver sinal válido
            if signal == "BUY" and not self.position:
                await self._execute_buy(c["close"], c["time"])
            elif signal == "SELL" and self.position:
                await self._execute_sell(c["close"], c["time"])
                
        except Exception as e:
            print(f"[PaperEngine] Error processing candle: {e}")
            if self.on_error:
                try:
                    result = self.on_error(e)
                    if asyncio.iscoroutine(result):
                        await result
                except:
                    pass

    def _evaluate_signal(self) -> Optional[str]:
        """Avalia sinais usando o módulo de signals."""
        try:
            triggers = self.get_triggers()
            return evaluate_signal(triggers, self.position is not None, self.session_id)
        except Exception as e:
            print(f"[PaperEngine {self.session_id}] Error evaluating signals: {e}")
            return None

    def get_triggers(self) -> Dict:
        """Retorna triggers usando o módulo de strategies."""
        return calculate_triggers(
            self.strategy_slug,
            self.strategy_params,
            self.candle_history,
            self.position is not None
        )
    
    async def _execute_buy(self, price: float, timestamp: int):
        """Simula ordem de compra."""
        if self.position:
            return
            
        print(f"[PaperEngine {self.session_id}] Executing BUY at ${price:.4f}...")
        try:
            with SessionLocal() as db:
                session = db.query(PaperSession).get(self.session_id)
                if not session: 
                    print(f"[PaperEngine {self.session_id}] Session not found in DB!")
                    return
                
                # Recalcular com saldo atual do banco
                current_balance = session.current_balance
                # Usar taxa correta do sistema (Exchange + Slippage)
                from core.config import get_total_fee
                fee_rate = get_total_fee(session.coin)
                
                # Usar 95% do saldo para a compra
                # Os 5% restantes ficam como reserva para:
                # - Taxas de trading (0.1% maker/taker)
                # - Slippage em mercados voláteis
                # - Margem de segurança para múltiplos trades
                amount_to_use = current_balance * 0.95
                fee = amount_to_use * fee_rate
                value = amount_to_use - fee
                quantity = value / price
                
                if quantity <= 0:
                    print(f"[PaperEngine {self.session_id}] Insufficient balance: ${current_balance:.2f}")
                    return
                
                # Atualizar Saldo
                new_balance = current_balance - amount_to_use
                session.current_balance = new_balance
                self.balance = new_balance 
                
                # Criar Trade Record
                trade = PaperTrade(
                    session_id=self.session_id,
                    side="BUY",
                    price=price,
                    quantity=quantity,
                    value=value,
                    fee=fee,
                    balance_after=new_balance,
                    pnl=0,
                    pnl_pct=0,
                    executed_at=datetime.fromtimestamp(timestamp)
                )
                db.add(trade)
                
                # Criar Posição
                pos = PaperPosition(
                    session_id=self.session_id,
                    coin=session.coin,
                    side="LONG",
                    entry_price=price,
                    current_price=price,
                    quantity=quantity,
                    unrealized_pnl=0,
                    status="OPEN"
                )
                db.add(pos)
                
                db.commit()
                db.refresh(pos)
                db.refresh(trade) # Ensure trade has ID
                
                # Atualizar Memória
                self.position = {
                    "id": pos.id,
                    "side": "LONG",
                    "entry_price": price,
                    "quantity": quantity,
                    "coin": session.coin,
                }
                
                print(f"[PaperEngine {self.session_id}] BUY SUCCESS: {quantity:.6f} @ ${price:.4f}")
                
                 # Notificar callback se existir (fora do contexto DB)
                if self.on_trade:
                    trade_info = {
                        "id": trade.id,
                        "type": "BUY",
                        "coin": session.coin,
                        "price": price,
                        "quantity": quantity,
                        "value": value,
                        "fee": fee,
                        "balance": new_balance,
                        "session_id": self.session_id,
                    }
                    result = self.on_trade(trade_info)
                    if asyncio.iscoroutine(result):
                        await result

        except Exception as e:
            print(f"[PaperEngine {self.session_id}] BUY ERROR: {e}")
            
    async def _execute_sell(self, price: float, timestamp: int):
        """Simula ordem de venda."""
        if not self.position:
            return
        
        try:
            with SessionLocal() as db:
                session = db.query(PaperSession).get(self.session_id)
                if not session: return
    
                # Recuperar posição do banco para garantir ID correto
                pos = db.query(PaperPosition).filter(PaperPosition.id == self.position["id"]).first()
                if not pos: return # Error state
    
                quantity = pos.quantity
                entry_price = pos.entry_price
                
                gross_value = quantity * price
                
                # Usar taxa correta do sistema
                from core.config import get_total_fee
                fee_rate = get_total_fee(session.coin)
                
                fee = gross_value * fee_rate
                net_value = gross_value - fee
                
                # PnL
                pnl = net_value - (quantity * entry_price)
                pnl_pct = (pnl / (quantity * entry_price)) * 100 if (quantity * entry_price) != 0 else 0

                new_balance = session.current_balance + net_value
                session.current_balance = new_balance
    
                self.balance = new_balance
    
                # Fechar Posição
                pos.status = "CLOSED"
                pos.exit_price = price
                pos.exit_at = datetime.fromtimestamp(timestamp)
                pos.realized_pnl = pnl
                
                # Trade Sell
                trade = PaperTrade(
                    session_id=self.session_id,
                    side="SELL",
                    price=price,
                    quantity=quantity,
                    value=net_value,
                    fee=fee,
                    balance_after=new_balance,
                    pnl=pnl,
                    pnl_pct=pnl_pct,
                    executed_at=datetime.fromtimestamp(timestamp)
                )
                db.add(trade)
                db.commit()
                db.refresh(trade)
    
                self.position = None
                print(f"[PaperEngine {self.session_id}] SELL: PnL ${pnl:.2f} ({pnl_pct:.2f}%). New Bal: ${new_balance:.2f}")
    
                if self.on_trade:
                    trade_info = {
                        "id": trade.id,
                        "type": "SELL",
                        "coin": session.coin,
                        "price": price,
                        "quantity": quantity,
                        "value": net_value,
                        "fee": fee,
                        "pnl": pnl,
                        "pnl_pct": pnl_pct,
                        "balance": new_balance,
                        "session_id": self.session_id,
                    }
                    result = self.on_trade(trade_info)
                    if asyncio.iscoroutine(result):
                        await result
        except Exception as e:
            print(f"[PaperEngine {self.session_id}] SELL ERROR: {e}")
    
    def _update_position_price(self, current_price: float):
        """Atualiza preço atual da posição aberta."""
        if not self.position:
            return
        
        try:
            with SessionLocal() as db:
                db.query(PaperPosition).filter(
                    PaperPosition.id == self.position["id"]
                ).update({
                    "current_price": current_price,
                    "unrealized_pnl": (current_price - self.position["entry_price"]) * self.position["quantity"],
                })
                db.commit()
        except Exception as e:
            print(f"[PaperEngine] Error updating position price: {e}")
    
    def deposit(self, amount: float, note: str = None) -> Dict:
        """Adiciona capital à sessão."""
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        
        with SessionLocal() as db:
            session = db.query(PaperSession).get(self.session_id)
            if not session: raise ValueError("Session not found")
            
            balance_before = session.current_balance
            balance_after = balance_before + amount
            
            transaction = PaperTransaction(
                session_id=self.session_id,
                type="deposit",
                amount=amount,
                balance_before=balance_before,
                balance_after=balance_after,
                note=note,
            )
            db.add(transaction)
            
            session.current_balance = balance_after
            db.commit()
            
            self.balance = balance_after 
            
            print(f"[PaperEngine] Deposit: +${amount:.2f} | Balance: ${balance_after:.2f}")
            
            return {
                "type": "deposit",
                "amount": amount,
                "balance_before": balance_before,
                "balance_after": balance_after,
            }
    
    def withdraw(self, amount: float, note: str = None) -> Dict:
        """Remove capital da sessão."""
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        
        with SessionLocal() as db:
            session = db.query(PaperSession).get(self.session_id)
            if not session: raise ValueError("Session not found")
            
            if amount > session.current_balance:
                raise ValueError(f"Insufficient balance. Available: ${session.current_balance:.2f}")
            
            balance_before = session.current_balance
            balance_after = balance_before - amount
            
            transaction = PaperTransaction(
                session_id=self.session_id,
                type="withdrawal",
                amount=amount,
                balance_before=balance_before,
                balance_after=balance_after,
                note=note,
            )
            db.add(transaction)
            
            session.current_balance = balance_after
            db.commit()
            
            self.balance = balance_after 
            
            print(f"[PaperEngine] Withdrawal: -${amount:.2f} | Balance: ${balance_after:.2f}")
            
            return {
                "type": "withdrawal",
                "amount": amount,
                "balance_before": balance_before,
                "balance_after": balance_after,
            }
    
    def reset(self) -> Dict:
        """Reseta a sessão para o saldo inicial."""
        with SessionLocal() as db:
            session = db.query(PaperSession).get(self.session_id)
            if not session: raise ValueError("Session not found")
            
            db.query(PaperTrade).filter(PaperTrade.session_id == self.session_id).delete()
            db.query(PaperPosition).filter(PaperPosition.session_id == self.session_id).delete()
            db.query(PaperTransaction).filter(PaperTransaction.session_id == self.session_id).delete()
            
            old_balance = session.current_balance
            session.current_balance = session.initial_balance
            db.commit()
            
            self.balance = session.initial_balance
            self.position = None
            self.candle_history = []
            
            print(f"[PaperEngine] Session reset | Balance: ${self.balance:.2f}")
            
            return {
                "old_balance": old_balance,
                "new_balance": self.balance,
                "message": "Session reset successfully",
            }
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas da sessão."""
        with SessionLocal() as db:
            session = db.query(PaperSession).get(self.session_id)
            if not session: return {}

            trades = db.query(PaperTrade).filter(
                PaperTrade.session_id == self.session_id
            ).all()
            
            total_trades = len(trades)
            sell_trades = [t for t in trades if t.side == "SELL"]
            
            total_pnl = sum(t.pnl or 0 for t in sell_trades)
            winning_trades = [t for t in sell_trades if (t.pnl or 0) > 0]
            win_rate = (len(winning_trades) / len(sell_trades) * 100) if sell_trades else 0
            
            unrealized_pnl = 0
            pos = db.query(PaperPosition).filter(
                PaperPosition.session_id == self.session_id,
                PaperPosition.status == "OPEN"
            ).first()
            
            if pos:
                unrealized_pnl = pos.unrealized_pnl or 0
                position_amount = pos.quantity
            else:
                position_amount = 0.0
            
            roi = ((self.balance + unrealized_pnl - session.initial_balance) / session.initial_balance) * 100
            
            return {
                "session_id": session.id,
                "strategy": session.strategy_slug,
                "coin": session.coin,
                "initial_balance": session.initial_balance,
                "current_balance": self.balance,
                "total_trades": total_trades,
                "completed_trades": len(sell_trades),
                "total_pnl": total_pnl,
                "unrealized_pnl": unrealized_pnl,
                "win_rate": win_rate,
                "roi": roi,
                "has_position": pos is not None,
                "position_amount": position_amount,
            }
