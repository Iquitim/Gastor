"""
Bollinger Bounce Strategy - Reversão nas Bandas de Bollinger.

Compra quando preço toca banda inferior, vende quando toca banda superior.
"""

import pandas as pd
from typing import List, Dict
from .base import BaseStrategy


class BollingerBounceStrategy(BaseStrategy):
    """
    Estratégia de Reversão usando Bandas de Bollinger.
    
    Compra quando o preço toca ou ultrapassa a banda inferior.
    Vende quando o preço toca ou ultrapassa a banda superior.
    """
    
    name = "Bollinger Bounce"
    slug = "bollinger_bounce"
    category = "volatility"
    icon = "⚡"
    
    description = "Compra na banda inferior, vende na banda superior"
    
    explanation = """
### ⚡ Estratégia de Volatilidade (Bollinger Bounce)
**Conceito:** "Ping-Pong dentro do Canal".

*   **Como Funciona?** As Bandas de Bollinger criam um "canal" elástico em volta do preço baseado na volatilidade.
*   🟢 **Compra:** Quando o preço toca a banda **INFERIOR** (preço está "barato" em relação à volatilidade recente).
*   🔴 **Venda:** Quando o preço toca a banda **SUPERIOR** (preço está "caro" em relação à volatilidade recente).

**Vantagens:** Funciona muito bem em mercados laterais/consolidação. As bandas se adaptam automaticamente à volatilidade.

**Desvantagens:** Em tendências fortes, o preço pode "andar" nas bandas por longos períodos, gerando prejuízos.

**Dica:** Um toque na banda não é breakout garantido. Espere confirmação (reversão do candle) para maior precisão.
"""
    
    ideal_for = "Mercados sem direção definida (consolidação/range)"
    
    parameters = {
        "touch_threshold": {
            "default": 0.0,
            "min": -2.0,
            "max": 2.0,
            "label": "Sensibilidade (%)",
            "help": "0 = toque exato na banda, valores negativos = mais agressivo, positivos = mais conservador"
        }
    }
    
    def apply(self, df: pd.DataFrame, **params) -> List[Dict]:
        """Aplica estratégia de Bollinger Bounce."""
        
        # Valida parâmetros
        p = self.validate_params(**params)
        threshold = p["touch_threshold"] / 100  # Converte % para decimal
        
        trades = []
        in_position = False
        
        # Verifica se Bollinger Bands existem
        if 'bb_lower' not in df.columns or 'bb_upper' not in df.columns:
            return []
        
        for i in range(len(df)):
            price = df['close'].iloc[i]
            lower = df['bb_lower'].iloc[i]
            upper = df['bb_upper'].iloc[i]
            ts = df.index[i]
            
            # Skip se valores forem NaN
            if pd.isna(lower) or pd.isna(upper):
                continue
            
            # Calcula limiares ajustados
            lower_threshold = lower * (1 + threshold)
            upper_threshold = upper * (1 - threshold)
            
            # Buy: Preço toca ou ultrapassa banda inferior
            if price <= lower_threshold and not in_position:
                trades.append({
                    "action": "BUY",
                    "price": price,
                    "amount": 1.0,
                    "coin": "Fixed",
                    "timestamp": ts,
                    "reason": f"BB Bounce ↑ (Price ≤ Lower Band)"
                })
                in_position = True
            
            # Sell: Preço toca ou ultrapassa banda superior
            elif price >= upper_threshold and in_position:
                trades.append({
                    "action": "SELL",
                    "price": price,
                    "amount": 1.0,
                    "coin": "Fixed",
                    "timestamp": ts,
                    "reason": f"BB Bounce ↓ (Price ≥ Upper Band)"
                })
                in_position = False
        
        return trades
