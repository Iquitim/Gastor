"""
Testes Unitários - Módulo de Configuração (config.py)

Testa funções de taxas de trading e configurações.
"""

import pytest
from src.core.config import (
    EXCHANGE_FEE,
    SLIPPAGE_BY_COIN,
    DEFAULT_SLIPPAGE,
    COINS,
    get_total_fee,
    get_fee_breakdown
)


class TestConfigConstants:
    """Testes para constantes de configuração."""
    
    def test_exchange_fee_is_positive(self):
        """Taxa de exchange deve ser positiva."""
        assert EXCHANGE_FEE > 0
        assert EXCHANGE_FEE < 0.1  # Menos de 10%
    
    def test_default_slippage_is_positive(self):
        """Slippage padrão deve ser positivo."""
        assert DEFAULT_SLIPPAGE > 0
        assert DEFAULT_SLIPPAGE < 0.1  # Menos de 10%
    
    def test_slippage_by_coin_not_empty(self):
        """Dicionário de slippage por moeda não deve estar vazio."""
        assert len(SLIPPAGE_BY_COIN) > 0
    
    def test_coins_list_not_empty(self):
        """Lista de moedas não deve estar vazia."""
        assert len(COINS) > 0
        assert 'SOL/USDT' in COINS


class TestGetTotalFee:
    """Testes para função get_total_fee."""
    
    def test_known_coin_returns_correct_fee(self):
        """Moeda conhecida deve retornar taxa correta."""
        fee = get_total_fee('SOL/USDT')
        expected = EXCHANGE_FEE + SLIPPAGE_BY_COIN['SOL/USDT']
        assert fee == pytest.approx(expected, rel=1e-6)
    
    def test_unknown_coin_uses_default_slippage(self):
        """Moeda desconhecida deve usar slippage padrão."""
        fee = get_total_fee('UNKNOWN/USDT')
        expected = EXCHANGE_FEE + DEFAULT_SLIPPAGE
        assert fee == pytest.approx(expected, rel=1e-6)
    
    def test_fee_is_always_positive(self):
        """Taxa deve ser sempre positiva."""
        for coin in COINS:
            fee = get_total_fee(coin)
            assert fee > 0
    
    def test_fee_is_reasonable(self):
        """Taxa deve ser razoável (menos de 5%)."""
        for coin in COINS:
            fee = get_total_fee(coin)
            assert fee < 0.05  # Menos de 5%


class TestGetFeeBreakdown:
    """Testes para função get_fee_breakdown."""
    
    def test_returns_dict_with_required_keys(self):
        """Deve retornar dicionário com todas as chaves necessárias."""
        breakdown = get_fee_breakdown('SOL/USDT')
        
        assert 'exchange_fee' in breakdown
        assert 'slippage' in breakdown
        assert 'total_fee' in breakdown
        assert 'total_fee_pct' in breakdown
    
    def test_total_equals_sum_of_parts(self):
        """Total deve ser igual a exchange + slippage."""
        breakdown = get_fee_breakdown('SOL/USDT')
        
        expected_total = breakdown['exchange_fee'] + breakdown['slippage']
        assert breakdown['total_fee'] == pytest.approx(expected_total, rel=1e-6)
    
    def test_percentage_format_is_correct(self):
        """Formato de porcentagem deve estar correto."""
        breakdown = get_fee_breakdown('SOL/USDT')
        
        # Deve ser string com formato "X.XX%"
        assert isinstance(breakdown['total_fee_pct'], str)
        assert '%' in breakdown['total_fee_pct']
    
    def test_all_coins_have_valid_breakdown(self):
        """Todas as moedas devem ter breakdown válido."""
        for coin in COINS:
            breakdown = get_fee_breakdown(coin)
            
            assert breakdown['exchange_fee'] > 0
            assert breakdown['slippage'] > 0
            assert breakdown['total_fee'] > 0
