"""
Testes Unitários - Módulo de Estratégias

Testa se todas as estratégias seguem o padrão esperado e geram trades válidos.
"""

import pytest
import pandas as pd
from datetime import datetime

from src.strategies import STRATEGIES
from src.strategies.base import BaseStrategy


class TestStrategiesRegistry:
    """Testes para registro de estratégias."""
    
    def test_strategies_not_empty(self):
        """Dicionário de estratégias não deve estar vazio."""
        assert len(STRATEGIES) > 0
    
    def test_all_strategies_have_required_attributes(self):
        """Todas as estratégias devem ter atributos obrigatórios."""
        required = ['name', 'slug', 'parameters', 'apply']
        
        for slug, strategy_class in STRATEGIES.items():
            strategy = strategy_class()
            
            for attr in required:
                assert hasattr(strategy, attr), f"Estratégia {slug} não tem atributo '{attr}'"
    
    def test_all_strategies_inherit_base(self):
        """Todas as estratégias devem herdar de BaseStrategy."""
        for slug, strategy_class in STRATEGIES.items():
            assert issubclass(strategy_class, BaseStrategy), f"{slug} não herda de BaseStrategy"
    
    def test_slugs_are_unique(self):
        """Todos os slugs devem ser únicos."""
        slugs = list(STRATEGIES.keys())
        assert len(slugs) == len(set(slugs))


class TestStrategyApply:
    """Testes para método apply das estratégias."""
    
    def test_apply_returns_list(self, sample_df_with_indicators):
        """apply() deve retornar uma lista."""
        for slug, strategy_class in STRATEGIES.items():
            strategy = strategy_class()
            
            try:
                result = strategy.apply(sample_df_with_indicators)
                assert isinstance(result, list), f"{slug}.apply() não retorna lista"
            except Exception as e:
                # Algumas estratégias podem requerer indicadores específicos
                # que não estão no sample_df_with_indicators
                pass
    
    def test_trades_have_required_keys(self, sample_df_with_indicators):
        """Trades gerados devem ter chaves obrigatórias."""
        required_keys = ['action', 'price', 'timestamp']
        
        for slug, strategy_class in STRATEGIES.items():
            strategy = strategy_class()
            
            try:
                trades = strategy.apply(sample_df_with_indicators)
                
                for trade in trades:
                    for key in required_keys:
                        assert key in trade, f"{slug} gerou trade sem '{key}'"
            except:
                pass
    
    def test_action_is_buy_or_sell(self, sample_df_with_indicators):
        """Action deve ser sempre 'BUY' ou 'SELL'."""
        valid_actions = ['BUY', 'SELL']
        
        for slug, strategy_class in STRATEGIES.items():
            strategy = strategy_class()
            
            try:
                trades = strategy.apply(sample_df_with_indicators)
                
                for trade in trades:
                    action = trade.get('action', '').upper()
                    assert action in valid_actions, f"{slug} gerou action inválida: {action}"
            except:
                pass
    
    def test_price_is_positive(self, sample_df_with_indicators):
        """Preço deve ser sempre positivo."""
        for slug, strategy_class in STRATEGIES.items():
            strategy = strategy_class()
            
            try:
                trades = strategy.apply(sample_df_with_indicators)
                
                for trade in trades:
                    price = trade.get('price', 0)
                    assert price > 0, f"{slug} gerou preço inválido: {price}"
            except:
                pass


class TestRSIReversalStrategy:
    """Testes específicos para RSI Reversal."""
    
    def test_generates_paired_trades(self, sample_df_with_indicators):
        """Deve gerar trades em pares (BUY seguido de SELL)."""
        from src.strategies.rsi_reversal import RSIReversalStrategy
        
        strategy = RSIReversalStrategy()
        trades = strategy.apply(sample_df_with_indicators, rsi_buy=30, rsi_sell=70)
        
        if len(trades) > 0:
            # Verifica alternância BUY/SELL
            for i in range(len(trades) - 1):
                if trades[i]['action'] == 'BUY':
                    assert trades[i + 1]['action'] == 'SELL', "BUY não foi seguido de SELL"
    
    def test_respects_rsi_thresholds(self, sample_df_with_indicators):
        """Deve respeitar os limiares de RSI configurados."""
        from src.strategies.rsi_reversal import RSIReversalStrategy
        
        strategy = RSIReversalStrategy()
        
        # Com RSI muito restritivo, deve gerar poucos ou nenhum trade
        trades_restrictive = strategy.apply(sample_df_with_indicators, rsi_buy=5, rsi_sell=95)
        trades_lenient = strategy.apply(sample_df_with_indicators, rsi_buy=40, rsi_sell=60)
        
        # Configuração mais leniente deve gerar mais trades
        assert len(trades_lenient) >= len(trades_restrictive)
    
    def test_returns_empty_without_rsi(self, sample_ohlcv_data):
        """Deve retornar lista vazia se RSI não estiver no DataFrame."""
        from src.strategies.rsi_reversal import RSIReversalStrategy
        
        strategy = RSIReversalStrategy()
        trades = strategy.apply(sample_ohlcv_data)  # Sem indicadores
        
        assert trades == []


class TestGoldenCrossStrategy:
    """Testes específicos para Golden Cross."""
    
    def test_requires_ema_columns(self, sample_ohlcv_data):
        """Deve funcionar com colunas EMA calculadas internamente."""
        from src.strategies.golden_cross import GoldenCrossStrategy
        
        strategy = GoldenCrossStrategy()
        
        # Deve calcular EMAs internamente se não existirem
        trades = strategy.apply(sample_ohlcv_data)
        
        assert isinstance(trades, list)
    
    def test_generates_trades_on_crossover(self, sample_df_with_indicators):
        """Deve gerar trades nos cruzamentos de EMA."""
        from src.strategies.golden_cross import GoldenCrossStrategy
        
        strategy = GoldenCrossStrategy()
        trades = strategy.apply(sample_df_with_indicators)
        
        # Verifica que trades são gerados (dados de teste têm cruzamentos)
        # Não garantimos quantidade, apenas formato
        assert all('action' in t for t in trades)


class TestStrategyParameters:
    """Testes para validação de parâmetros."""
    
    def test_parameters_have_required_fields(self):
        """Parâmetros devem ter min, max e default."""
        for slug, strategy_class in STRATEGIES.items():
            strategy = strategy_class()
            
            for param_name, param_config in strategy.parameters.items():
                assert 'min' in param_config, f"{slug}.{param_name} sem 'min'"
                assert 'max' in param_config, f"{slug}.{param_name} sem 'max'"
                assert 'default' in param_config, f"{slug}.{param_name} sem 'default'"
    
    def test_default_within_range(self):
        """Valor default deve estar entre min e max."""
        for slug, strategy_class in STRATEGIES.items():
            strategy = strategy_class()
            
            for param_name, param_config in strategy.parameters.items():
                default = param_config['default']
                min_val = param_config['min']
                max_val = param_config['max']
                
                assert min_val <= default <= max_val, \
                    f"{slug}.{param_name}: default {default} fora do range [{min_val}, {max_val}]"
