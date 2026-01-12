"""
RSI Reversal Strategy - Reversão à Média baseada em RSI.

Compra quando RSI indica sobrevendido, vende quando sobrecomprado.
"""

import pandas as pd
from typing import List, Dict
from .base import BaseStrategy


class RSIReversalStrategy(BaseStrategy):
    """
    Estratégia de Reversão baseada no RSI (Relative Strength Index).
    
    Compra quando o RSI cruza o limiar inferior para cima (sobrevendido → neutro).
    Vende quando o RSI cruza o limiar superior para baixo (sobrecomprado → neutro).
    """
    
    name = "RSI Reversal"
    slug = "rsi_reversal"
    category = "reversal"
    icon = "📉"
    
    description = "Compra quando RSI indica sobrevendido, vende quando sobrecomprado"
    
    explanation = """
### 📉 Estratégia de Reversão (RSI)
**Conceito:** "Comprar Barato, Vender Caro".

*   **Como Funciona?** O RSI (Índice de Força Relativa) mede se o preço subiu demais ou caiu demais nos últimos períodos.
*   🟢 **Compra:** Quando o RSI cruza o limiar inferior **para cima** (saindo da zona de sobrevendido).
*   🔴 **Venda:** Quando o RSI cruza o limiar superior **para baixo** (saindo da zona de sobrecomprado).

**Vantagens:** Funciona bem em mercados laterais onde o preço oscila entre suporte e resistência.

**Desvantagens:** Em tendências fortes, pode gerar sinais falsos (o preço continua subindo mesmo após RSI > 70).
"""
    
    ideal_for = "Mercados laterais ou fins de tendência"
    
    parameters = {
        "rsi_buy": {
            "default": 30,
            "min": 10,
            "max": 50,
            "label": "RSI Compra (Sobrevendido)",
            "help": "Valor abaixo do qual o ativo é considerado sobrevendido"
        },
        "rsi_sell": {
            "default": 70,
            "min": 50,
            "max": 90,
            "label": "RSI Venda (Sobrecomprado)",
            "help": "Valor acima do qual o ativo é considerado sobrecomprado"
        }
    }
    
    def apply(self, df: pd.DataFrame, **params) -> List[Dict]:
        """Aplica estratégia de RSI Reversal."""
        
        # Valida parâmetros
        p = self.validate_params(**params)
        rsi_buy = p["rsi_buy"]
        rsi_sell = p["rsi_sell"]
        
        trades = []
        in_position = False
        
        # Verifica se RSI existe no DataFrame
        if 'rsi' not in df.columns:
            return []
        
        for i in range(1, len(df)):
            curr_rsi = df['rsi'].iloc[i]
            prev_rsi = df['rsi'].iloc[i-1]
            price = df['close'].iloc[i]
            ts = df.index[i]
            
            # Skip se RSI for NaN
            if pd.isna(curr_rsi) or pd.isna(prev_rsi):
                continue
            
            # Buy: RSI cruza o limiar inferior para cima (reversão de sobrevendido)
            if prev_rsi < rsi_buy and curr_rsi >= rsi_buy and not in_position:
                trades.append({
                    "action": "BUY",
                    "price": price,
                    "amount": 1.0,
                    "coin": "Fixed",
                    "timestamp": ts,
                    "reason": f"RSI Reversal ↑ ({curr_rsi:.1f} > {rsi_buy})"
                })
                in_position = True
            
            # Sell: RSI cruza o limiar superior para baixo (reversão de sobrecomprado)
            elif prev_rsi > rsi_sell and curr_rsi <= rsi_sell and in_position:
                trades.append({
                    "action": "SELL",
                    "price": price,
                    "amount": 1.0,
                    "coin": "Fixed",
                    "timestamp": ts,
                    "reason": f"RSI Reversal ↓ ({curr_rsi:.1f} < {rsi_sell})"
                })
                in_position = False
        
        return trades
