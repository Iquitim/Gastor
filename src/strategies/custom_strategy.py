"""
CustomStrategy - Engine para estratégias dinâmicas criadas pelo usuário.

Permite criar estratégias combinando múltiplas regras com operadores lógicos (AND/OR).
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.core import indicators as ind


# =============================================================================
# DEFINIÇÃO DOS INDICADORES DISPONÍVEIS
# =============================================================================

AVAILABLE_INDICATORS = {
    # Preços (valor atual do candle)
    "close": {
        "label": "Preço de Fechamento",
        "category": "price",
        "params": [],
        "calc": lambda df, **p: df['close']
    },
    "high": {
        "label": "Preço Máximo",
        "category": "price",
        "params": [],
        "calc": lambda df, **p: df['high']
    },
    "low": {
        "label": "Preço Mínimo",
        "category": "price",
        "params": [],
        "calc": lambda df, **p: df['low']
    },
    "open": {
        "label": "Preço de Abertura",
        "category": "price",
        "params": [],
        "calc": lambda df, **p: df['open']
    },
    # Preços com período (máximo/mínimo de N candles)
    "highest": {
        "label": "Máximo N Candles",
        "category": "price",
        "params": [{"name": "period", "default": 20, "min": 2, "max": 200, "label": "Período"}],
        "calc": lambda df, period=20, **p: df['high'].rolling(window=period).max()
    },
    "lowest": {
        "label": "Mínimo N Candles",
        "category": "price",
        "params": [{"name": "period", "default": 20, "min": 2, "max": 200, "label": "Período"}],
        "calc": lambda df, period=20, **p: df['low'].rolling(window=period).min()
    },
    "close_avg": {
        "label": "Fechamento Médio",
        "category": "price",
        "params": [{"name": "period", "default": 20, "min": 2, "max": 200, "label": "Período"}],
        "calc": lambda df, period=20, **p: df['close'].rolling(window=period).mean()
    },
    "sma": {
        "label": "SMA (Média Simples)",
        "category": "moving_avg",
        "params": [{"name": "period", "default": 20, "min": 2, "max": 200, "label": "Período"}],
        "calc": lambda df, period=20, **p: ind.calc_sma(df['close'], period)
    },
    "ema": {
        "label": "EMA (Média Exponencial)",
        "category": "moving_avg",
        "params": [{"name": "period", "default": 20, "min": 2, "max": 200, "label": "Período"}],
        "calc": lambda df, period=20, **p: ind.calc_ema(df['close'], period)
    },
    "median": {
        "label": "Mediana Móvel",
        "category": "moving_avg",
        "params": [{"name": "period", "default": 50, "min": 5, "max": 200, "label": "Período"}],
        "calc": lambda df, period=50, **p: ind.calc_median(df['close'], period)
    },
    
    # Osciladores
    "rsi": {
        "label": "RSI (Índice de Força Relativa)",
        "category": "oscillator",
        "params": [{"name": "period", "default": 14, "min": 2, "max": 50, "label": "Período"}],
        "calc": lambda df, period=14, **p: ind.calc_rsi(df['close'], period)
    },
    "macd": {
        "label": "MACD (Linha)",
        "category": "oscillator",
        "params": [],
        "calc": lambda df, **p: ind.calc_macd(df['close'])[0]
    },
    "macd_signal": {
        "label": "MACD (Sinal)",
        "category": "oscillator",
        "params": [],
        "calc": lambda df, **p: ind.calc_macd(df['close'])[1]
    },
    "stoch_k": {
        "label": "Stochastic %K",
        "category": "oscillator",
        "params": [{"name": "period", "default": 14, "min": 5, "max": 50, "label": "Período"}],
        "calc": lambda df, period=14, **p: ind.calc_stochastic(df['close'], df['high'], df['low'], period)[0]
    },
    "stoch_d": {
        "label": "Stochastic %D",
        "category": "oscillator",
        "params": [{"name": "period", "default": 14, "min": 5, "max": 50, "label": "Período"}],
        "calc": lambda df, period=14, **p: ind.calc_stochastic(df['close'], df['high'], df['low'], period)[1]
    },
    
    # Volatilidade
    "atr": {
        "label": "ATR (Volatilidade)",
        "category": "volatility",
        "params": [{"name": "period", "default": 14, "min": 5, "max": 50, "label": "Período"}],
        "calc": lambda df, period=14, **p: ind.calc_atr(df['high'], df['low'], df['close'], period)
    },
    "bollinger_upper": {
        "label": "Bollinger Upper",
        "category": "volatility",
        "params": [{"name": "period", "default": 20, "min": 5, "max": 50, "label": "Período"}],
        "calc": lambda df, period=20, **p: ind.calc_bollinger_bands(df['close'], period)[0]
    },
    "bollinger_lower": {
        "label": "Bollinger Lower",
        "category": "volatility",
        "params": [{"name": "period", "default": 20, "min": 5, "max": 50, "label": "Período"}],
        "calc": lambda df, period=20, **p: ind.calc_bollinger_bands(df['close'], period)[2]
    },
    "bollinger_pctb": {
        "label": "Bollinger %B",
        "category": "volatility",
        "params": [{"name": "period", "default": 20, "min": 5, "max": 50, "label": "Período"}],
        "calc": lambda df, period=20, **p: ind.calc_bollinger_pctb(df['close'], period)
    },
    
    # Estatísticos
    "zscore": {
        "label": "Z-Score",
        "category": "stats",
        "params": [{"name": "period", "default": 20, "min": 5, "max": 100, "label": "Período"}],
        "calc": lambda df, period=20, **p: ind.calc_zscore(df['close'], period)
    },
    "zscore_robust": {
        "label": "Z-Score Robusto",
        "category": "stats",
        "params": [{"name": "period", "default": 20, "min": 5, "max": 100, "label": "Período"}],
        "calc": lambda df, period=20, **p: ind.calc_zscore_robust(df['close'], period)
    },
    "mad": {
        "label": "MAD (Desvio Mediano)",
        "category": "stats",
        "params": [{"name": "period", "default": 20, "min": 5, "max": 100, "label": "Período"}],
        "calc": lambda df, period=20, **p: ind.calc_mad(df['close'], period)
    },
    
    # Momentum
    "roc": {
        "label": "ROC (Rate of Change %)",
        "category": "momentum",
        "params": [{"name": "period", "default": 12, "min": 1, "max": 50, "label": "Período"}],
        "calc": lambda df, period=12, **p: ind.calc_roc(df['close'], period)
    },
    
    # Volume
    "volume": {
        "label": "Volume",
        "category": "volume",
        "params": [],
        "calc": lambda df, **p: df['volume']
    },
    "volume_ratio": {
        "label": "Volume Ratio",
        "category": "volume",
        "params": [{"name": "period", "default": 20, "min": 5, "max": 50, "label": "Período"}],
        "calc": lambda df, period=20, **p: ind.calc_volume_ratio(df['volume'], period)
    },
    
    # Canais
    "donchian_upper": {
        "label": "Donchian Upper",
        "category": "channel",
        "params": [{"name": "period", "default": 20, "min": 5, "max": 100, "label": "Período"}],
        "calc": lambda df, period=20, **p: ind.calc_donchian(df['high'], df['low'], period)[0]
    },
    "donchian_lower": {
        "label": "Donchian Lower",
        "category": "channel",
        "params": [{"name": "period", "default": 20, "min": 5, "max": 100, "label": "Período"}],
        "calc": lambda df, period=20, **p: ind.calc_donchian(df['high'], df['low'], period)[1]
    },
}

# Operadores disponíveis
AVAILABLE_OPERATORS = {
    ">": {"label": "Maior que", "func": lambda a, b: a > b},
    "<": {"label": "Menor que", "func": lambda a, b: a < b},
    ">=": {"label": "Maior ou igual", "func": lambda a, b: a >= b},
    "<=": {"label": "Menor ou igual", "func": lambda a, b: a <= b},
    "==": {"label": "Igual a", "func": lambda a, b: np.isclose(a, b, rtol=1e-3)},
    "crosses_above": {"label": "Cruza para cima", "func": lambda a, b: (a > b).astype(int).diff() == 1},
    "crosses_below": {"label": "Cruza para baixo", "func": lambda a, b: (a < b).astype(int).diff() == 1},
}

# Categorias para organização na UI
INDICATOR_CATEGORIES = {
    "price": "📈 Preço",
    "moving_avg": "📊 Médias Móveis",
    "oscillator": "🔄 Osciladores",
    "volatility": "📉 Volatilidade",
    "stats": "📐 Estatísticos",
    "momentum": "🚀 Momentum",
    "volume": "📦 Volume",
    "channel": "📏 Canais",
}


# =============================================================================
# ENGINE DE AVALIAÇÃO DE REGRAS
# =============================================================================

def evaluate_rule(df: pd.DataFrame, rule: Dict) -> pd.Series:
    """
    Avalia uma única regra e retorna uma série booleana.
    
    Args:
        df: DataFrame com dados OHLCV
        rule: Dicionário com definição da regra
            {
                "indicator": "rsi",
                "params": {"period": 14},
                "operator": "<",
                "value_type": "constant",  # ou "indicator"
                "value": 30,  # ou {"indicator": "sma", "params": {...}}
            }
    
    Returns:
        pd.Series booleana indicando onde a regra é satisfeita
    """
    # Calcula o indicador do lado esquerdo
    ind_config = AVAILABLE_INDICATORS.get(rule["indicator"])
    if not ind_config:
        raise ValueError(f"Indicador desconhecido: {rule['indicator']}")
    
    left_value = ind_config["calc"](df, **rule.get("params", {}))
    
    # Calcula o lado direito (constante ou outro indicador)
    if rule.get("value_type", "constant") == "constant":
        right_value = rule["value"]
    else:
        # É outro indicador
        right_config = AVAILABLE_INDICATORS.get(rule["value"]["indicator"])
        if not right_config:
            raise ValueError(f"Indicador desconhecido: {rule['value']['indicator']}")
        right_value = right_config["calc"](df, **rule["value"].get("params", {}))
    
    # Aplica o operador
    op_config = AVAILABLE_OPERATORS.get(rule["operator"])
    if not op_config:
        raise ValueError(f"Operador desconhecido: {rule['operator']}")
    
    return op_config["func"](left_value, right_value)


def evaluate_rules(df: pd.DataFrame, rules: List[Dict], logic: str = "AND") -> pd.Series:
    """
    Avalia múltiplas regras combinadas com AND ou OR.
    
    Args:
        df: DataFrame com dados OHLCV
        rules: Lista de regras
        logic: "AND" ou "OR"
    
    Returns:
        pd.Series booleana combinada
    """
    if not rules:
        return pd.Series([False] * len(df), index=df.index)
    
    results = [evaluate_rule(df, rule) for rule in rules]
    
    if logic == "AND":
        combined = results[0]
        for r in results[1:]:
            combined = combined & r
    else:  # OR
        combined = results[0]
        for r in results[1:]:
            combined = combined | r
    
    return combined.fillna(False)


def evaluate_group(df: pd.DataFrame, group: Dict) -> pd.Series:
    """
    Avalia um grupo de regras.
    
    Args:
        df: DataFrame com dados OHLCV
        group: {"rules": [...], "logic": "AND"|"OR"}
    
    Returns:
        pd.Series booleana do grupo
    """
    rules = group.get("rules", [])
    logic = group.get("logic", "AND")
    return evaluate_rules(df, rules, logic)


def evaluate_groups(df: pd.DataFrame, groups: List[Dict], groups_logic: str = "OR") -> pd.Series:
    """
    Avalia múltiplos grupos combinados com AND ou OR.
    
    Args:
        df: DataFrame com dados OHLCV
        groups: Lista de grupos [{"rules": [...], "logic": "AND"}, ...]
        groups_logic: Lógica entre grupos ("AND" ou "OR")
    
    Returns:
        pd.Series booleana combinada de todos os grupos
    """
    if not groups:
        return pd.Series([False] * len(df), index=df.index)
    
    results = [evaluate_group(df, group) for group in groups]
    
    if groups_logic == "AND":
        combined = results[0]
        for r in results[1:]:
            combined = combined & r
    else:  # OR
        combined = results[0]
        for r in results[1:]:
            combined = combined | r
    
    return combined.fillna(False)


# =============================================================================
# FORMATAÇÃO DE REGRAS (LINGUAGEM NATURAL)
# =============================================================================

def format_rule(rule: Dict) -> str:
    """
    Formata uma regra em linguagem natural legível.
    
    Exemplo: "RSI(14) < 30" ou "Close > SMA(20)"
    """
    # Indicador principal
    ind_key = rule.get("indicator", "close")
    ind_config = AVAILABLE_INDICATORS.get(ind_key, {})
    ind_label = ind_config.get("label", ind_key)
    
    # Simplifica o nome (pega só a primeira palavra ou sigla)
    if "(" in ind_label:
        ind_name = ind_label.split("(")[0].strip()
    else:
        ind_name = ind_label.split()[0] if len(ind_label.split()) > 2 else ind_label
    
    # Parâmetro do indicador
    params = rule.get("params", {})
    period = params.get("period", "")
    ind_str = f"{ind_name}({period})" if period else ind_name
    
    # Operador
    op = rule.get("operator", "<")
    op_symbols = {
        ">": ">",
        "<": "<",
        ">=": "≥",
        "<=": "≤",
        "==": "=",
        "crosses_above": "↗",
        "crosses_below": "↘"
    }
    op_str = op_symbols.get(op, op)
    
    # Valor
    value_type = rule.get("value_type", "constant")
    if value_type == "constant":
        value = rule.get("value", 0)
        value_str = f"{value:.1f}" if isinstance(value, float) else str(value)
    else:
        # É outro indicador
        val_ind = rule.get("value", {})
        val_ind_key = val_ind.get("indicator", "sma")
        val_ind_config = AVAILABLE_INDICATORS.get(val_ind_key, {})
        val_ind_label = val_ind_config.get("label", val_ind_key)
        
        if "(" in val_ind_label:
            val_ind_name = val_ind_label.split("(")[0].strip()
        else:
            val_ind_name = val_ind_label.split()[0] if len(val_ind_label.split()) > 2 else val_ind_label
        
        val_params = val_ind.get("params", {})
        val_period = val_params.get("period", "")
        value_str = f"{val_ind_name}({val_period})" if val_period else val_ind_name
    
    return f"{ind_str} {op_str} {value_str}"


def format_group(group: Dict) -> str:
    """Formata um grupo de regras."""
    rules = group.get("rules", [])
    logic = group.get("logic", "AND")
    
    if not rules:
        return "(vazio)"
    
    formatted = [format_rule(r) for r in rules]
    return f" {logic} ".join(formatted)


# =============================================================================
# MIGRAÇÃO DE ESTRATÉGIAS ANTIGAS
# =============================================================================

def migrate_old_config(config: Dict) -> Dict:
    """
    Migra configuração antiga (regras planas) para novo formato (grupos).
    
    Formato antigo:
        {"buy_rules": [...], "buy_logic": "AND"}
    
    Formato novo:
        {"buy_groups": [{"rules": [...], "logic": "AND"}], "buy_groups_logic": "OR"}
    """
    new_config = config.copy()
    
    # Migra regras de compra
    if "buy_rules" in config and "buy_groups" not in config:
        new_config["buy_groups"] = [{
            "rules": config.get("buy_rules", []),
            "logic": config.get("buy_logic", "AND")
        }]
        new_config["buy_groups_logic"] = "OR"
    
    # Migra regras de venda
    if "sell_rules" in config and "sell_groups" not in config:
        new_config["sell_groups"] = [{
            "rules": config.get("sell_rules", []),
            "logic": config.get("sell_logic", "AND")
        }]
        new_config["sell_groups_logic"] = "OR"
    
    return new_config


def create_empty_group() -> Dict:
    """Cria um grupo vazio para a UI."""
    return {
        "rules": [],
        "logic": "AND"
    }


# =============================================================================
# CLASSE DE ESTRATÉGIA CUSTOMIZADA
# =============================================================================

class CustomStrategy:
    """
    Estratégia construída dinamicamente pelo usuário.
    
    Suporta dois formatos:
    - Formato antigo: regras planas com buy_rules/sell_rules
    - Formato novo: grupos aninhados com buy_groups/sell_groups
    """
    
    def __init__(self, config: Dict):
        """
        Inicializa a estratégia com configuração.
        
        Args:
            config: Dicionário de configuração (formato antigo ou novo)
        """
        # Migra automaticamente se for formato antigo
        self.config = migrate_old_config(config)
        
        self.name = self.config.get("name", "Estratégia Customizada")
        
        # Novo formato com grupos
        self.buy_groups = self.config.get("buy_groups", [])
        self.sell_groups = self.config.get("sell_groups", [])
        self.buy_groups_logic = self.config.get("buy_groups_logic", "OR")
        self.sell_groups_logic = self.config.get("sell_groups_logic", "OR")
        
        # Mantém compatibilidade com formato antigo (para leitura)
        self.buy_rules = self.config.get("buy_rules", [])
        self.sell_rules = self.config.get("sell_rules", [])
        self.buy_logic = self.config.get("buy_logic", "AND")
        self.sell_logic = self.config.get("sell_logic", "AND")
    
    def apply(self, df: pd.DataFrame, coin: str = "SOL/USDT") -> List[Dict]:
        """
        Aplica a estratégia e retorna lista de trades.
        
        Args:
            df: DataFrame com dados OHLCV
            coin: Par de trading
        
        Returns:
            Lista de dicts com trades
        """
        trades = []
        
        # Usa grupos se disponível, senão usa regras planas
        if self.buy_groups:
            buy_signals = evaluate_groups(df, self.buy_groups, self.buy_groups_logic)
        else:
            buy_signals = evaluate_rules(df, self.buy_rules, self.buy_logic)
        
        if self.sell_groups:
            sell_signals = evaluate_groups(df, self.sell_groups, self.sell_groups_logic)
        else:
            sell_signals = evaluate_rules(df, self.sell_rules, self.sell_logic)
        
        # Gera trades alternando compra/venda
        position_open = False
        
        for i in range(len(df)):
            timestamp = df.index[i]
            price = df['close'].iloc[i]
            
            if not position_open and buy_signals.iloc[i]:
                trades.append({
                    "action": "BUY",
                    "price": price,
                    "amount": 0,  # Será ajustado pelo portfolio
                    "timestamp": timestamp,
                    "coin": coin,
                    "reason": f"[Custom] {self.name} - Regra de Compra"
                })
                position_open = True
                
            elif position_open and sell_signals.iloc[i]:
                trades.append({
                    "action": "SELL",
                    "price": price,
                    "amount": 0,
                    "timestamp": timestamp,
                    "coin": coin,
                    "reason": f"[Custom] {self.name} - Regra de Venda"
                })
                position_open = False
        
        return trades
    
    def get_total_rules_count(self) -> tuple:
        """Retorna contagem total de regras (buy, sell)."""
        buy_count = sum(len(g.get("rules", [])) for g in self.buy_groups)
        sell_count = sum(len(g.get("rules", [])) for g in self.sell_groups)
        return buy_count, sell_count
    
    def to_dict(self) -> Dict:
        """Converte para dicionário (para serialização)."""
        return self.config.copy()
    
    @classmethod
    def from_dict(cls, config: Dict) -> "CustomStrategy":
        """Cria instância a partir de dicionário."""
        return cls(config)
    
    def __repr__(self) -> str:
        buy_count, sell_count = self.get_total_rules_count()
        return f"<CustomStrategy: {self.name} ({buy_count} buy, {sell_count} sell rules)>"


# =============================================================================
# FUNÇÕES UTILITÁRIAS PARA A UI
# =============================================================================

def get_indicators_by_category() -> Dict[str, List[Dict]]:
    """Retorna indicadores organizados por categoria para a UI."""
    result = {}
    for cat_key, cat_label in INDICATOR_CATEGORIES.items():
        indicators = []
        for ind_key, ind_config in AVAILABLE_INDICATORS.items():
            if ind_config["category"] == cat_key:
                indicators.append({
                    "key": ind_key,
                    "label": ind_config["label"],
                    "params": ind_config["params"]
                })
        if indicators:
            result[cat_label] = indicators
    return result


def create_empty_rule() -> Dict:
    """Cria uma regra vazia para a UI."""
    return {
        "indicator": "rsi",
        "params": {"period": 14},
        "operator": "<",
        "value_type": "constant",
        "value": 30
    }


def create_empty_strategy_config() -> Dict:
    """Cria configuração vazia de estratégia no novo formato com grupos."""
    return {
        "name": "",
        "buy_groups": [{"rules": [], "logic": "AND"}],
        "sell_groups": [{"rules": [], "logic": "AND"}],
        "buy_groups_logic": "OR",
        "sell_groups_logic": "OR"
    }
