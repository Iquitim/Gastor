"""
Testes Unitários - Módulo de Portfólio (portfolio.py)

Testa funções de gestão de portfólio: sanitização, ajuste de amounts, cálculo de P&L.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from src.core.portfolio import (
    sanitize_trades,
    adjust_trade_amounts,
    apply_risk_management
)


class TestSanitizeTrades:
    """Testes para função sanitize_trades."""
    
    def test_removes_sell_without_holdings(self):
        """Venda sem compra prévia deve ser removida."""
        trades = [
            {'action': 'SELL', 'price': 100.0, 'amount': 10.0, 'timestamp': datetime(2025, 1, 1, 10)},
        ]
        
        result = sanitize_trades(trades)
        
        assert len(result) == 0
    
    def test_keeps_valid_buy_sell_pair(self, sample_trades):
        """Pares BUY/SELL válidos devem ser mantidos."""
        result = sanitize_trades(sample_trades)
        
        # Deve manter todos os 4 trades válidos
        assert len(result) == 4
    
    def test_orders_by_timestamp(self):
        """Trades devem ser ordenados por timestamp."""
        base_time = datetime(2025, 1, 1, 10)
        trades = [
            {'action': 'SELL', 'price': 110.0, 'amount': 10.0, 'timestamp': base_time + timedelta(hours=5)},
            {'action': 'BUY', 'price': 100.0, 'amount': 10.0, 'timestamp': base_time},
        ]
        
        result = sanitize_trades(trades)
        
        # Deve ordenar: BUY primeiro, SELL depois
        assert result[0]['action'] == 'BUY'
        assert result[1]['action'] == 'SELL'
    
    def test_empty_list_returns_empty(self):
        """Lista vazia deve retornar lista vazia."""
        result = sanitize_trades([])
        assert result == []
    
    def test_prevents_double_buy(self):
        """Não deve permitir compra duplicada sem venda intermediária."""
        base_time = datetime(2025, 1, 1, 10)
        trades = [
            {'action': 'BUY', 'price': 100.0, 'amount': 10.0, 'timestamp': base_time},
            {'action': 'BUY', 'price': 105.0, 'amount': 10.0, 'timestamp': base_time + timedelta(hours=1)},
            {'action': 'SELL', 'price': 110.0, 'amount': 10.0, 'timestamp': base_time + timedelta(hours=2)},
        ]
        
        result = sanitize_trades(trades)
        
        # Deve ter apenas 1 BUY e 1 SELL
        buys = [t for t in result if t['action'] == 'BUY']
        sells = [t for t in result if t['action'] == 'SELL']
        
        assert len(buys) == 1
        assert len(sells) == 1


class TestAdjustTradeAmounts:
    """Testes para função adjust_trade_amounts."""
    
    def test_respects_initial_balance(self):
        """Não deve gastar mais que o saldo inicial."""
        trades = [
            {'action': 'BUY', 'price': 100.0, 'amount': 1.0, 'timestamp': datetime(2025, 1, 1)},
        ]
        
        result = adjust_trade_amounts(
            trades,
            initial_balance=10000.0,
            position_size_pct=100.0,
            use_compound=False
        )
        
        # Amount ajustado não deve exceder saldo/preço
        if len(result) > 0:
            assert result[0]['amount'] <= 10000.0 / 100.0
    
    def test_empty_trades_returns_empty(self):
        """Lista vazia deve retornar lista vazia."""
        result = adjust_trade_amounts([], 10000.0, 100.0)
        assert result == []
    
    def test_compound_mode_reinvests_profits(self):
        """Modo composto deve reinvestir lucros."""
        base_time = datetime(2025, 1, 1, 10)
        
        # Trade lucrativo seguido de novo trade
        trades = [
            {'action': 'BUY', 'price': 100.0, 'amount': 1.0, 'timestamp': base_time},
            {'action': 'SELL', 'price': 120.0, 'amount': 1.0, 'timestamp': base_time + timedelta(hours=5)},
            {'action': 'BUY', 'price': 100.0, 'amount': 1.0, 'timestamp': base_time + timedelta(hours=10)},
        ]
        
        result_compound = adjust_trade_amounts(
            trades.copy(),
            initial_balance=10000.0,
            position_size_pct=100.0,
            use_compound=True
        )
        
        result_fixed = adjust_trade_amounts(
            trades.copy(),
            initial_balance=10000.0,
            position_size_pct=100.0,
            use_compound=False
        )
        
        # Em modo composto, segundo BUY deve ter amount maior (reinvestiu lucro)
        # Em modo fixo, amounts devem ser equivalentes
        if len(result_compound) >= 3 and len(result_fixed) >= 3:
            assert result_compound[2]['amount'] >= result_fixed[2]['amount']
    
    def test_force_close_adds_sell_at_end(self):
        """force_close deve adicionar SELL se houver posição aberta."""
        trades = [
            {'action': 'BUY', 'price': 100.0, 'amount': 1.0, 'timestamp': datetime(2025, 1, 1)},
        ]
        
        result = adjust_trade_amounts(
            trades,
            initial_balance=10000.0,
            position_size_pct=100.0,
            force_close=True,
            last_price=110.0,
            last_timestamp=datetime(2025, 1, 2)
        )
        
        # Deve ter BUY + SELL forçado
        assert len(result) == 2
        assert result[-1]['action'] == 'SELL'
        assert result[-1]['price'] == 110.0


class TestApplyRiskManagement:
    """Testes para função apply_risk_management."""
    
    def test_fixo_returns_unchanged(self, sample_trades, sample_ohlcv_data):
        """Método 'fixo' não deve alterar os trades."""
        result = apply_risk_management(sample_trades, sample_ohlcv_data, 'fixo')
        
        # Deve retornar mesma lista
        assert result == sample_trades
    
    def test_conservador_reduces_size(self, sample_ohlcv_data):
        """Método 'conservador' deve reduzir tamanho das posições."""
        trades = [
            {'action': 'BUY', 'price': 100.0, 'amount': 1.0, 'timestamp': sample_ohlcv_data.index[10]},
        ]
        
        result = apply_risk_management(trades, sample_ohlcv_data, 'conservador')
        
        # Deve adicionar size_factor < 1
        assert 'size_factor' in result[0]
        assert result[0]['size_factor'] < 1.0
    
    def test_adds_size_factor_to_trades(self, sample_df_with_indicators):
        """Todos os métodos devem adicionar size_factor."""
        trades = [
            {'action': 'BUY', 'price': 100.0, 'amount': 1.0, 'timestamp': sample_df_with_indicators.index[50]},
        ]
        
        for method in ['conservador', 'volatilidade_atr', 'agressivo_rsi']:
            result = apply_risk_management(trades.copy(), sample_df_with_indicators, method)
            assert 'size_factor' in result[0]
