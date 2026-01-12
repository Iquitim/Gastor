"""
BaseStrategy - Classe abstrata para estratégias de trading.

Todas as estratégias devem herdar desta classe e implementar o método apply().
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
import pandas as pd


class BaseStrategy(ABC):
    """
    Classe base abstrata para todas as estratégias de trading.
    
    Cada estratégia deve definir seus metadados e implementar o método apply().
    O sistema descobre automaticamente todas as estratégias que herdam desta classe.
    """
    
    # === METADADOS (obrigatórios) ===
    name: str = "Unnamed Strategy"      # Nome para exibição
    slug: str = "unnamed"               # Identificador único (snake_case)
    category: str = "other"             # Categoria: reversal, trend, volatility, momentum
    icon: str = "📊"                    # Emoji para UI
    
    # === DOCUMENTAÇÃO ===
    description: str = ""               # Descrição curta (1 linha)
    explanation: str = ""               # Explicação detalhada (Markdown)
    ideal_for: str = ""                 # Quando usar esta estratégia
    
    # === PARÂMETROS CONFIGURÁVEIS ===
    # Formato: {"param_name": {"default": valor, "min": min, "max": max, "label": "Label UI"}}
    parameters: Dict[str, Dict[str, Any]] = {}
    
    @abstractmethod
    def apply(self, df: pd.DataFrame, **params) -> List[Dict]:
        """
        Aplica a estratégia ao DataFrame e retorna lista de trades.
        
        Args:
            df: DataFrame com dados OHLCV e indicadores calculados
            **params: Parâmetros configuráveis da estratégia
            
        Returns:
            Lista de dicts com trades gerados:
            [
                {
                    "action": "BUY" | "SELL",
                    "price": float,
                    "amount": float,
                    "timestamp": datetime,
                    "coin": str,
                    "reason": str
                },
                ...
            ]
        """
        pass
    
    def get_default_params(self) -> Dict[str, Any]:
        """Retorna os valores default de todos os parâmetros."""
        return {
            name: config.get("default", 0) 
            for name, config in self.parameters.items()
        }
    
    def validate_params(self, **params) -> Dict[str, Any]:
        """Valida e preenche parâmetros com defaults se necessário."""
        validated = self.get_default_params()
        
        for name, value in params.items():
            if name in self.parameters:
                config = self.parameters[name]
                # Aplica limites min/max se definidos
                if "min" in config:
                    value = max(config["min"], value)
                if "max" in config:
                    value = min(config["max"], value)
                validated[name] = value
                
        return validated
    
    def __repr__(self) -> str:
        return f"<Strategy: {self.name} ({self.slug})>"
