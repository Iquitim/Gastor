"""
Stochastic RSI Strategy - Versão mais responsiva do RSI tradicional.

Combina Stochastic Oscillator com RSI para sinais mais rápidos.
"""

import pandas as pd
import numpy as np
from typing import List, Dict
from .base import BaseStrategy


class StochasticRSIStrategy(BaseStrategy):
    """
    Estratégia usando Stochastic RSI - versão mais sensível do RSI.
    
    O Stochastic RSI aplica a fórmula do Stochastic no RSI,
    criando um oscilador mais responsivo que detecta extremos mais cedo.
    """
    
    name = "Stochastic RSI"
    slug = "stochastic_rsi"
    category = "oscillator"
    icon = "🎢"
    
    description = "RSI mais sensível que detecta reversões mais cedo"
    
    explanation = """
### 🎢 Stochastic RSI
**Conceito:** "RSI Turbinado"

O **Stochastic RSI** é um indicador de indicador: aplica a fórmula do Stochastic Oscillator ao RSI, criando um oscilador que se move mais rápido entre 0 e 100.

#### 📊 Fórmula:
```
StochRSI = (RSI - RSI_min) / (RSI_max - RSI_min)
```
Onde min/max são dos últimos N períodos.

#### 🎯 Sinais:
- 🟢 **Compra:** StochRSI cruza **20** para cima (saindo de sobrevendido)
- 🔴 **Venda:** StochRSI cruza **80** para baixo (saindo de sobrecomprado)

#### ✅ Vantagens:
- **Mais responsivo** que RSI tradicional
- Detecta reversões **mais cedo**
- Oscila entre 0 e 100 (normalizado)

#### ⚠️ Desvantagens:
- Pode ser **muito sensível** (mais sinais falsos)
- Requer confirmação de outros indicadores

#### 💡 Dica:
Use em conjunto com EMA para filtrar: só compre se preço > EMA.
"""
    
    ideal_for = "Day trading, scalping, mercados rápidos"
    
    parameters = {
        "stoch_period": {
            "default": 14,
            "min": 5,
            "max": 30,
            "label": "Período Stochastic",
            "help": "Janela para calcular min/max do RSI"
        },
        "oversold": {
            "default": 20,
            "min": 5,
            "max": 40,
            "label": "Zona Sobrevendido",
            "help": "Abaixo deste valor está sobrevendido"
        },
        "overbought": {
            "default": 80,
            "min": 60,
            "max": 95,
            "label": "Zona Sobrecomprado",
            "help": "Acima deste valor está sobrecomprado"
        }
    }
    
    def apply(self, df: pd.DataFrame, **params) -> List[Dict]:
        """Aplica estratégia Stochastic RSI."""
        
        p = self.validate_params(**params)
        stoch_period = p["stoch_period"]
        oversold = p["oversold"]
        overbought = p["overbought"]
        
        trades = []
        in_position = False
        
        if 'rsi' not in df.columns:
            return []
        
        df = df.copy()
        
        # Calcula Stochastic RSI
        rsi_min = df['rsi'].rolling(window=stoch_period).min()
        rsi_max = df['rsi'].rolling(window=stoch_period).max()
        
        # Evita divisão por zero
        rsi_range = rsi_max - rsi_min
        rsi_range = rsi_range.replace(0, np.nan)
        
        df['stoch_rsi'] = ((df['rsi'] - rsi_min) / rsi_range) * 100
        
        for i in range(1, len(df)):
            stoch = df['stoch_rsi'].iloc[i]
            prev_stoch = df['stoch_rsi'].iloc[i-1]
            price = df['close'].iloc[i]
            ts = df.index[i]
            
            if pd.isna(stoch) or pd.isna(prev_stoch):
                continue
            
            # Buy: Stoch RSI cruza oversold para cima
            if prev_stoch < oversold and stoch >= oversold and not in_position:
                trades.append({
                    "action": "BUY",
                    "price": price,
                    "amount": 1.0,
                    "coin": "Fixed",
                    "timestamp": ts,
                    "reason": f"StochRSI ↑ ({stoch:.1f} > {oversold})"
                })
                in_position = True
            
            # Sell: Stoch RSI cruza overbought para baixo
            elif prev_stoch > overbought and stoch <= overbought and in_position:
                trades.append({
                    "action": "SELL",
                    "price": price,
                    "amount": 1.0,
                    "coin": "Fixed",
                    "timestamp": ts,
                    "reason": f"StochRSI ↓ ({stoch:.1f} < {overbought})"
                })
                in_position = False
        
        return trades
