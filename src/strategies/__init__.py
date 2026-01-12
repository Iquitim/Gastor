"""
Strategies Registry - Auto-descoberta e registro de estratégias.

Este módulo escaneia automaticamente todos os arquivos de estratégia
e expõe um dicionário STRATEGIES com todas as estratégias disponíveis.

Uso:
    from src.strategies import STRATEGIES, get_strategy
    
    # Lista todas as estratégias
    for slug, strategy_class in STRATEGIES.items():
        print(f"{strategy_class.icon} {strategy_class.name}")
    
    # Obtém uma estratégia específica
    strategy = get_strategy("rsi_reversal")
    trades = strategy.apply(df, rsi_buy=25, rsi_sell=75)
"""

import importlib
import pkgutil
from pathlib import Path
from typing import Dict, Type, Optional

from .base import BaseStrategy


# Dicionário global de estratégias registradas
STRATEGIES: Dict[str, Type[BaseStrategy]] = {}


def _discover_strategies():
    """
    Descobre automaticamente todas as estratégias no diretório.
    
    Escaneia todos os arquivos .py (exceto __init__.py e base.py),
    importa os módulos e registra classes que herdam de BaseStrategy.
    """
    package_dir = Path(__file__).parent
    
    for module_info in pkgutil.iter_modules([str(package_dir)]):
        # Pula arquivos especiais
        if module_info.name in ('base', '__init__'):
            continue
        
        try:
            # Importa o módulo
            module = importlib.import_module(f'.{module_info.name}', package=__name__)
            
            # Procura classes que herdam de BaseStrategy
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                
                # Verifica se é uma classe que herda de BaseStrategy
                if (isinstance(attr, type) and 
                    issubclass(attr, BaseStrategy) and 
                    attr is not BaseStrategy):
                    
                    # Registra a estratégia pelo slug
                    STRATEGIES[attr.slug] = attr
                    
        except Exception as e:
            # Log de erro mas não quebra o sistema
            print(f"⚠️ Erro ao carregar estratégia '{module_info.name}': {e}")


def get_strategy(slug: str) -> Optional[BaseStrategy]:
    """
    Retorna uma instância da estratégia pelo slug.
    
    Args:
        slug: Identificador único da estratégia (ex: "rsi_reversal")
        
    Returns:
        Instância da estratégia ou None se não encontrada
    """
    strategy_class = STRATEGIES.get(slug)
    if strategy_class:
        return strategy_class()
    return None


def list_strategies() -> Dict[str, dict]:
    """
    Retorna um dicionário com informações de todas as estratégias.
    
    Útil para exibir na UI.
    
    Returns:
        Dict com slug como chave e metadados como valor
    """
    return {
        slug: {
            "name": cls.name,
            "icon": cls.icon,
            "category": cls.category,
            "description": cls.description,
            "ideal_for": cls.ideal_for,
            "parameters": cls.parameters
        }
        for slug, cls in STRATEGIES.items()
    }


def get_strategies_by_category(category: str) -> Dict[str, Type[BaseStrategy]]:
    """
    Filtra estratégias por categoria.
    
    Args:
        category: "reversal", "trend", "volatility", "momentum", etc.
        
    Returns:
        Dict com estratégias da categoria especificada
    """
    return {
        slug: cls 
        for slug, cls in STRATEGIES.items() 
        if cls.category == category
    }


# Auto-descoberta ao importar o módulo
_discover_strategies()


# Expõe a classe base para quem quiser criar novas estratégias
__all__ = [
    'BaseStrategy',
    'STRATEGIES',
    'get_strategy',
    'list_strategies',
    'get_strategies_by_category'
]
