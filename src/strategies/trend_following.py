"""
Trend Following Strategy - Seguidor de Tendência baseado em EMA.

Compra quando preço cruza a EMA para cima, vende quando cruza para baixo.
"""

import pandas as pd
from typing import List, Dict
from .base import BaseStrategy


class TrendFollowingStrategy(BaseStrategy):
    """
    Estratégia de Trend Following usando Média Móvel Exponencial (EMA).
    
    Compra quando o preço cruza a EMA para cima (início de tendência de alta).
    Vende quando o preço cruza a EMA para baixo (início de tendência de baixa).
    """
    
    name = "Trend Following"
    slug = "trend_following"
    category = "trend"
    icon = "🌊"
    
    description = "Segue a tendência usando cruzamento de preço com EMA"
    
    explanation = """
### 🌊 Estratégia de Tendência (Trend Following)
**Conceito:** "Surfando a Onda".

*   **Como Funciona?** Usa uma Média Móvel Exponencial (EMA) para identificar a direção do mercado.
*   🟢 **Compra:** Quando o preço cruza **ACIMA** da EMA (Tendência de Alta iniciando).
*   🔴 **Venda:** Quando o preço cruza **ABAIXO** da EMA (Tendência de Baixa iniciando).

**Vantagens:** Captura grandes movimentos direcionais. Funciona muito bem em mercados com tendências claras.

**Desvantagens:** Gera muitos sinais falsos (whipsaws) em mercados laterais. A entrada é sempre atrasada.

**Dica:** EMAs mais longas (50, 100) geram menos sinais mas mais confiáveis. EMAs curtas (9, 21) são mais responsivas mas geram mais ruído.
"""
    
    ideal_for = "Movimentos longos e explosivos (bull/bear markets)"
    
    parameters = {
        "ema_period": {
            "default": 50,
            "min": 9,
            "max": 200,
            "label": "Período da EMA",
            "help": "Número de períodos para calcular a média móvel"
        }
    }
    
    def apply(self, df: pd.DataFrame, **params) -> List[Dict]:
        """Aplica estratégia de Trend Following."""
        
        # Valida parâmetros
        p = self.validate_params(**params)
        ema_period = p["ema_period"]
        
        trades = []
        in_position = False
        
        # Tenta encontrar a coluna EMA correspondente
        col_name = f'ema{ema_period}'
        
        # Se não existir a EMA específica, tenta calcular ou usar alternativa
        if col_name not in df.columns:
            # Tenta usar EMA mais próxima disponível
            available_emas = [c for c in df.columns if c.startswith('ema')]
            if not available_emas:
                return []
            # Usa a primeira disponível
            col_name = available_emas[0]
        
        for i in range(1, len(df)):
            price = df['close'].iloc[i]
            ema = df[col_name].iloc[i]
            prev_price = df['close'].iloc[i-1]
            prev_ema = df[col_name].iloc[i-1]
            ts = df.index[i]
            
            # Skip se valores forem NaN
            if pd.isna(ema) or pd.isna(prev_ema):
                continue
            
            # Crossover Up: Preço cruza EMA para cima
            if prev_price < prev_ema and price > ema and not in_position:
                trades.append({
                    "action": "BUY",
                    "price": price,
                    "amount": 1.0,
                    "coin": "Fixed",
                    "timestamp": ts,
                    "reason": f"Trend ↑ (Price > {col_name.upper()})"
                })
                in_position = True
            
            # Crossover Down: Preço cruza EMA para baixo
            elif prev_price > prev_ema and price < ema and in_position:
                trades.append({
                    "action": "SELL",
                    "price": price,
                    "amount": 1.0,
                    "coin": "Fixed",
                    "timestamp": ts,
                    "reason": f"Trend ↓ (Price < {col_name.upper()})"
                })
                in_position = False
        
        return trades
