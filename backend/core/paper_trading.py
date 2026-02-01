"""
Paper Trading Engine
====================

Motor de simulação de trades com preços ao vivo.
Reutiliza lógica do BacktestEngine para consistência.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List
from sqlalchemy.orm import Session

from core.backtest import BacktestEngine
from core.models import PaperSession, PaperTrade, PaperPosition, PaperTransaction, Strategy
from core.config import get_total_fee


class PaperTradingEngine:
    """
    Motor de Paper Trading.
    
    Recebe candles em tempo real e executa a estratégia,
    simulando ordens sem enviar para a exchange.
    
    Características:
    - Reutiliza lógica do BacktestEngine
    - Suporta estratégias pré-prontas e customizadas
    - Permite depósitos e saques virtuais
    - Callbacks para notificações
    """
    
    def __init__(
        self,
        session: PaperSession,
        db: Session,
        on_trade: Optional[Callable[[Dict], Any]] = None,
        on_signal: Optional[Callable[[str, Dict], Any]] = None,
        on_error: Optional[Callable[[Exception], Any]] = None,
    ):
        """
        Inicializa o engine.
        
        Args:
            session: Sessão de Paper Trading do banco
            db: Sessão do SQLAlchemy
            on_trade: Callback quando um trade é executado
            on_signal: Callback quando um sinal é gerado
            on_error: Callback para erros
        """
        self.session = session
        self.db = db
        self.on_trade = on_trade
        self.on_signal = on_signal
        self.on_error = on_error
        
        self.balance = session.current_balance
        self.position: Optional[Dict] = None
        self.candle_history: List[Dict] = []
        
        # Carregar posição existente se houver
        self._load_existing_position()
    
    def _load_existing_position(self):
        """Carrega posição existente do banco."""
        existing = self.db.query(PaperPosition).filter(
            PaperPosition.session_id == self.session.id
        ).first()
        
        if existing:
            self.position = {
                "id": existing.id,
                "side": existing.side,
                "entry_price": existing.entry_price,
                "quantity": existing.quantity,
                "coin": existing.coin,
            }
            print(f"[PaperEngine] Loaded existing position: {self.position}")
    
    async def on_candle(self, candle: Dict[str, Any]):
        """
        Chamado quando um novo candle fecha.
        
        Avalia a estratégia e executa trades se necessário.
        """
        try:
            # Atualizar preço da posição aberta
            if self.position:
                self._update_position_price(candle["close"])
            
            # Adicionar ao histórico
            self.candle_history.append(candle)
            
            # Manter janela de histórico (últimos 200 candles)
            if len(self.candle_history) > 200:
                self.candle_history.pop(0)
            
            # Precisa de histórico mínimo para indicadores
            if len(self.candle_history) < 50:
                print(f"[PaperEngine] Collecting history: {len(self.candle_history)}/50")
                return
            
            # Avaliar estratégia
            signal = self._evaluate_signal()
            
            if signal and self.on_signal:
                result = self.on_signal(signal, candle)
                if asyncio.iscoroutine(result):
                    await result
            
            # Executar trade se houver sinal válido
            if signal == "BUY" and not self.position:
                await self._execute_buy(candle)
            elif signal == "SELL" and self.position:
                await self._execute_sell(candle)
                
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
        """
        Usa o BacktestEngine para avaliar sinais.
        
        Returns:
            "BUY", "SELL" ou None
        """
        # Instanciar engine com histórico atual
        fee_rate = get_total_fee(self.session.coin)
        
        engine = BacktestEngine(
            data=self.candle_history,
            initial_balance=self.balance,
            fee_rate=fee_rate,
            use_compound=True,
        )
        
        # Preparar slug e params
        slug = self.session.strategy_slug
        params = dict(self.session.strategy_params or {})
        
        # Carregar regras se for estratégia customizada
        if slug.startswith("custom_"):
            custom_rules = self._load_custom_rules(slug)
            if custom_rules:
                params["rules"] = custom_rules
                slug = "custom"
            else:
                print(f"[PaperEngine] Failed to load custom rules for {slug}")
                return None
        
        # Rodar estratégia
        result = engine.run(slug, params)
        
        if "error" in result:
            print(f"[PaperEngine] Strategy error: {result['error']}")
            return None
        
        trades = result.get("trades", [])
        if not trades:
            return None
        
        # Verificar se há sinal no último candle
        last_candle_time = self.candle_history[-1]["time"]
        last_trade = trades[-1]
        
        # Sinal é válido se ocorreu no candle atual
        if last_trade.get("time") == last_candle_time:
            return last_trade.get("side")
        
        return None
    
    def _load_custom_rules(self, slug: str) -> Optional[Dict]:
        """Carrega regras de estratégia customizada do banco."""
        try:
            strat_id = int(slug.split("_")[1])
            strategy = self.db.query(Strategy).filter(
                Strategy.id == strat_id
            ).first()
            
            if strategy:
                return strategy.rules
        except Exception as e:
            print(f"[PaperEngine] Error loading custom rules: {e}")
        
        return None
    
    async def _execute_buy(self, candle: Dict):
        """Simula ordem de compra."""
        price = candle["close"]
        fee_rate = get_total_fee(self.session.coin)
        
        # Calcular quantidade (usar 95% do saldo para deixar margem)
        available = self.balance * 0.95
        fee = available * fee_rate
        quantity = (available - fee) / price
        value = quantity * price
        
        if quantity <= 0:
            print("[PaperEngine] Insufficient balance for buy")
            return
        
        # Atualizar saldo
        total_cost = value + fee
        new_balance = self.balance - total_cost
        
        # Registrar trade no banco
        trade = PaperTrade(
            session_id=self.session.id,
            side="BUY",
            price=price,
            quantity=quantity,
            value=value,
            fee=fee,
            balance_after=new_balance,
        )
        self.db.add(trade)
        
        # Criar posição
        position = PaperPosition(
            session_id=self.session.id,
            coin=self.session.coin,
            side="LONG",
            entry_price=price,
            quantity=quantity,
            current_price=price,
            unrealized_pnl=0,
        )
        self.db.add(position)
        
        # Atualizar sessão
        self.balance = new_balance
        self.session.current_balance = new_balance
        
        self.db.commit()
        self.db.refresh(position)
        
        # Atualizar estado local
        self.position = {
            "id": position.id,
            "side": "LONG",
            "entry_price": price,
            "quantity": quantity,
            "coin": self.session.coin,
        }
        
        print(f"[PaperEngine] BUY executed: {quantity:.6f} @ ${price:.4f}")
        
        # Callback para notificação
        if self.on_trade:
            trade_info = {
                "type": "BUY",
                "coin": self.session.coin,
                "price": price,
                "quantity": quantity,
                "value": value,
                "fee": fee,
                "balance": new_balance,
                "session_id": self.session.id,
            }
            result = self.on_trade(trade_info)
            if asyncio.iscoroutine(result):
                await result
    
    async def _execute_sell(self, candle: Dict):
        """Simula ordem de venda."""
        if not self.position:
            return
        
        price = candle["close"]
        quantity = self.position["quantity"]
        entry_price = self.position["entry_price"]
        fee_rate = get_total_fee(self.session.coin)
        
        value = quantity * price
        fee = value * fee_rate
        
        # Calcular PnL
        entry_value = quantity * entry_price
        pnl = value - entry_value - fee
        pnl_pct = ((price / entry_price) - 1) * 100
        
        # Atualizar saldo
        new_balance = self.balance + (value - fee)
        
        # Registrar trade no banco
        trade = PaperTrade(
            session_id=self.session.id,
            side="SELL",
            price=price,
            quantity=quantity,
            value=value,
            fee=fee,
            pnl=pnl,
            pnl_pct=pnl_pct,
            balance_after=new_balance,
        )
        self.db.add(trade)
        
        # Fechar posição
        self.db.query(PaperPosition).filter(
            PaperPosition.session_id == self.session.id
        ).delete()
        
        # Atualizar sessão
        self.balance = new_balance
        self.session.current_balance = new_balance
        
        self.db.commit()
        
        # Limpar estado local
        self.position = None
        
        pnl_emoji = "📈" if pnl > 0 else "📉"
        print(f"[PaperEngine] SELL executed: {quantity:.6f} @ ${price:.4f} | {pnl_emoji} PnL: ${pnl:.2f}")
        
        # Callback para notificação
        if self.on_trade:
            trade_info = {
                "type": "SELL",
                "coin": self.session.coin,
                "price": price,
                "quantity": quantity,
                "value": value,
                "fee": fee,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "balance": new_balance,
                "session_id": self.session.id,
            }
            result = self.on_trade(trade_info)
            if asyncio.iscoroutine(result):
                await result
    
    def _update_position_price(self, current_price: float):
        """Atualiza preço atual da posição aberta."""
        if not self.position:
            return
        
        self.db.query(PaperPosition).filter(
            PaperPosition.id == self.position["id"]
        ).update({
            "current_price": current_price,
            "unrealized_pnl": (current_price - self.position["entry_price"]) * self.position["quantity"],
        })
        self.db.commit()
    
    def deposit(self, amount: float, note: str = None) -> Dict:
        """
        Adiciona capital à sessão.
        
        Args:
            amount: Valor a depositar
            note: Nota opcional
            
        Returns:
            Informações da transação
        """
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        
        balance_before = self.balance
        balance_after = self.balance + amount
        
        transaction = PaperTransaction(
            session_id=self.session.id,
            type="deposit",
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            note=note,
        )
        self.db.add(transaction)
        
        self.balance = balance_after
        self.session.current_balance = balance_after
        
        self.db.commit()
        
        print(f"[PaperEngine] Deposit: +${amount:.2f} | Balance: ${balance_after:.2f}")
        
        return {
            "type": "deposit",
            "amount": amount,
            "balance_before": balance_before,
            "balance_after": balance_after,
        }
    
    def withdraw(self, amount: float, note: str = None) -> Dict:
        """
        Remove capital da sessão.
        
        Args:
            amount: Valor a sacar
            note: Nota opcional
            
        Returns:
            Informações da transação
        """
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        
        if amount > self.balance:
            raise ValueError(f"Insufficient balance. Available: ${self.balance:.2f}")
        
        balance_before = self.balance
        balance_after = self.balance - amount
        
        transaction = PaperTransaction(
            session_id=self.session.id,
            type="withdrawal",
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            note=note,
        )
        self.db.add(transaction)
        
        self.balance = balance_after
        self.session.current_balance = balance_after
        
        self.db.commit()
        
        print(f"[PaperEngine] Withdrawal: -${amount:.2f} | Balance: ${balance_after:.2f}")
        
        return {
            "type": "withdrawal",
            "amount": amount,
            "balance_before": balance_before,
            "balance_after": balance_after,
        }
    
    def reset(self) -> Dict:
        """
        Reseta a sessão para o saldo inicial.
        
        Remove todos os trades, posições e transações.
        
        Returns:
            Informações do reset
        """
        # Limpar trades
        self.db.query(PaperTrade).filter(
            PaperTrade.session_id == self.session.id
        ).delete()
        
        # Limpar posições
        self.db.query(PaperPosition).filter(
            PaperPosition.session_id == self.session.id
        ).delete()
        
        # Limpar transações
        self.db.query(PaperTransaction).filter(
            PaperTransaction.session_id == self.session.id
        ).delete()
        
        # Resetar saldo
        old_balance = self.balance
        self.balance = self.session.initial_balance
        self.session.current_balance = self.session.initial_balance
        self.position = None
        self.candle_history = []
        
        self.db.commit()
        
        print(f"[PaperEngine] Session reset | Balance: ${self.balance:.2f}")
        
        return {
            "old_balance": old_balance,
            "new_balance": self.balance,
            "message": "Session reset successfully",
        }
    
    def get_stats(self) -> Dict:
        """
        Retorna estatísticas da sessão.
        """
        trades = self.db.query(PaperTrade).filter(
            PaperTrade.session_id == self.session.id
        ).all()
        
        total_trades = len(trades)
        buy_trades = [t for t in trades if t.side == "BUY"]
        sell_trades = [t for t in trades if t.side == "SELL"]
        
        # Métricas de PnL
        total_pnl = sum(t.pnl or 0 for t in sell_trades)
        winning_trades = [t for t in sell_trades if (t.pnl or 0) > 0]
        win_rate = (len(winning_trades) / len(sell_trades) * 100) if sell_trades else 0
        
        # PnL não realizado
        unrealized_pnl = 0
        if self.position:
            pos = self.db.query(PaperPosition).filter(
                PaperPosition.session_id == self.session.id
            ).first()
            if pos:
                unrealized_pnl = pos.unrealized_pnl or 0
        
        # ROI
        roi = ((self.balance + unrealized_pnl - self.session.initial_balance) / self.session.initial_balance) * 100
        
        return {
            "session_id": self.session.id,
            "strategy": self.session.strategy_slug,
            "coin": self.session.coin,
            "initial_balance": self.session.initial_balance,
            "current_balance": self.balance,
            "total_trades": total_trades,
            "completed_trades": len(sell_trades),
            "total_pnl": total_pnl,
            "unrealized_pnl": unrealized_pnl,
            "win_rate": win_rate,
            "roi": roi,
            "has_position": self.position is not None,
        }
