
"""
Strategies Configuration
========================

Single Source of Truth (SSOT) for all available strategies in the system.
Defines metadata, parameter ranges, and descriptions.
"""

from typing import List, Dict, Any

STRATEGIES: List[Dict[str, Any]] = [
    {
        "slug": "rsi_reversal",
        "name": "RSI Reversal",
        "category": "reversal",
        "icon": "arrow-right-left",
        "description": "Compra quando RSI indica sobrevendido, vende quando sobrecomprado",
        "idealFor": "Mercados laterais ou fins de tendência",
        "parameters": {
            "rsi_buy": {"default": 30, "min": 10, "max": 50, "label": "RSI Compra (Sobrevendido)"},
            "rsi_sell": {"default": 70, "min": 50, "max": 90, "label": "RSI Venda (Sobrecomprado)"},
            "rsi_period": {"default": 14, "min": 5, "max": 21, "label": "Período RSI"}
        }
    },
    {
        "slug": "golden_cross",
        "name": "Golden Cross",
        "category": "trend",
        "icon": "activity",
        "description": "Detecta cruzamentos de médias móveis EMA rápida/lenta",
        "idealFor": "Mercados em tendência clara",
        "parameters": {
            "fast_period": {"default": 9, "min": 5, "max": 20, "label": "EMA Rápida"},
            "slow_period": {"default": 21, "min": 15, "max": 50, "label": "EMA Lenta"}
        }
    },
    {
        "slug": "macd_crossover",
        "name": "MACD Crossover",
        "category": "momentum",
        "icon": "bar-chart-2",
        "description": "Sinais de cruzamento entre linha MACD e Signal",
        "idealFor": "Identificar mudanças de momentum",
        "parameters": {
            "fast": {"default": 12, "min": 8, "max": 16, "label": "EMA Rápida (MACD)"},
            "slow": {"default": 26, "min": 20, "max": 35, "label": "EMA Lenta (MACD)"},
            "signal": {"default": 9, "min": 5, "max": 12, "label": "Signal Period"}
        }
    },
    {
        "slug": "bollinger_bounce",
        "name": "Bollinger Bounce",
        "category": "volatility",
        "icon": "layers",
        "description": "Compra na banda inferior, vende na banda superior",
        "idealFor": "Mercados com volatilidade definida",
        "parameters": {
            "bb_period": {"default": 20, "min": 10, "max": 50, "label": "Período BB"},
            "bb_std": {"default": 2, "min": 1, "max": 3, "label": "Desvio Padrão"}
        }
    },
    {
        "slug": "trend_following",
        "name": "Trend Following",
        "category": "trend",
        "icon": "trending-up",
        "description": "Segue tendência com EMA e confirma com volume",
        "idealFor": "Tendências fortes de longo prazo",
        "parameters": {
            "ema_period": {"default": 20, "min": 10, "max": 50, "label": "Período EMA"},
            "volume_mult": {"default": 1.5, "min": 1.0, "max": 3.0, "label": "Multiplicador Volume"}
        }
    },
    {
        "slug": "stochastic_rsi",
        "name": "Stochastic RSI",
        "category": "reversal",
        "icon": "arrow-right-left",
        "description": "Combina Stochastic com RSI para sinais mais precisos",
        "idealFor": "Identificar extremos de sobrecompra/venda",
        "parameters": {
            "stoch_period": {"default": 14, "min": 5, "max": 21, "label": "Período Stochastic"},
            "stoch_buy": {"default": 20, "min": 10, "max": 30, "label": "Limiar Compra"},
            "stoch_sell": {"default": 80, "min": 70, "max": 90, "label": "Limiar Venda"}
        }
    },
    {
        "slug": "donchian_breakout",
        "name": "Donchian Breakout",
        "category": "trend",
        "icon": "shield-check",
        "description": "Compra no rompimento do topo, vende no fundo do canal",
        "idealFor": "Breakouts e início de tendências",
        "parameters": {
            "period": {"default": 20, "min": 10, "max": 55, "label": "Período Canal"}
        }
    },
    {
        "slug": "ema_rsi_combo",
        "name": "EMA + RSI Combo",
        "category": "hybrid",
        "icon": "cpu",
        "description": "Combina cruzamento de EMAs com filtro RSI",
        "idealFor": "Reduzir sinais falsos em tendências",
        "parameters": {
            "fast_ema": {"default": 9, "min": 5, "max": 15, "label": "EMA Rápida"},
            "slow_ema": {"default": 21, "min": 15, "max": 50, "label": "EMA Lenta"},
            "rsi_filter": {"default": 50, "min": 30, "max": 70, "label": "Filtro RSI"}
        }
    },
    {
        "slug": "macd_rsi_combo",
        "name": "MACD + RSI Combo",
        "category": "hybrid",
        "icon": "zap",
        "description": "MACD para timing, RSI para confirmação",
        "idealFor": "Entradas mais seguras em momentum",
        "parameters": {
            "rsi_confirm": {"default": 50, "min": 30, "max": 70, "label": "RSI Confirmação"},
            "macd_threshold": {"default": 0, "min": -0.5, "max": 0.5, "label": "MACD Threshold"}
        }
    },
    {
        "slug": "volume_breakout",
        "name": "Volume Breakout",
        "category": "momentum",
        "icon": "anchor",
        "description": "Breakout confirmado por explosão de volume",
        "idealFor": "Movimentos explosivos com volume alto",
        "parameters": {
            "lookback": {"default": 20, "min": 10, "max": 50, "label": "Período Lookback"},
            "volume_mult": {"default": 2.0, "min": 1.5, "max": 5.0, "label": "Mult. Volume"},
            "price_break_pct": {"default": 1.0, "min": 0.5, "max": 3.0, "label": "% Breakout Preço"}
        }
    }
]

def get_strategy_config(slug: str) -> Dict[str, Any]:
    """Retorna configuração de uma estratégia pelo slug."""
    for s in STRATEGIES:
        if s["slug"] == slug:
            return s
    return {}
