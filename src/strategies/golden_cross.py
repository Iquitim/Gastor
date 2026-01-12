"""
Golden Cross / Death Cross Strategy - Cruzamento de EMAs de longo prazo.

Estratégia clássica para identificar grandes ciclos de mercado.
"""

import pandas as pd
from typing import List, Dict
from .base import BaseStrategy


class GoldenCrossStrategy(BaseStrategy):
    """
    Estratégia de tendência de longo prazo usando Golden Cross e Death Cross.
    
    Golden Cross: EMA curta cruza EMA longa para cima (bullish).
    Death Cross: EMA curta cruza EMA longa para baixo (bearish).
    """
    
    name = "Golden Cross"
    slug = "golden_cross"
    category = "trend"
    icon = "✨"
    
    description = "Detecta grandes mudanças de tendência usando cruzamento de EMAs"
    
    explanation = """
### ✨ Golden Cross / Death Cross
**Conceito:** "Identificando Grandes Ciclos"

Esta é uma das estratégias mais **respeitadas por investidores institucionais**. Identifica mudanças de tendência de longo prazo.

#### 📊 Os Cruzamentos:
- **✨ Golden Cross:** EMA rápida (ex: 50) cruza EMA lenta (ex: 200) **para cima**
  - Sinal de início de **Bull Market**
  - Historicamente precede grandes altas

- **💀 Death Cross:** EMA rápida cruza EMA lenta **para baixo**
  - Sinal de início de **Bear Market**
  - Historicamente precede grandes quedas

#### 🎯 Sinais:
- 🟢 **Compra:** No Golden Cross (EMA rápida > EMA lenta)
- 🔴 **Venda:** No Death Cross (EMA rápida < EMA lenta)

#### ✅ Vantagens:
- Captura movimentos **muito grandes** (meses de tendência)
- Poucos sinais = menos taxas e stress
- A EMA200 é respeitada como suporte/resistência importante

#### ⚠️ Desvantagens:
- Entrada muito atrasada (o preço já subiu bastante quando cruza)
- Não funciona em mercados laterais prolongados
- Poucos trades por ano

#### 💡 Dica:
Combine com outras estratégias: Use Golden Cross para definir a direção e estratégias de curto prazo para entradas.
"""
    
    ideal_for = "Investimento de longo prazo, identificar bull/bear markets"
    
    parameters = {
        "fast_period": {
            "default": 50,
            "min": 20,
            "max": 100,
            "label": "EMA Rápida (períodos)",
            "help": "Período da média móvel rápida"
        },
        "slow_period": {
            "default": 200,
            "min": 100,
            "max": 300,
            "label": "EMA Lenta (períodos)",
            "help": "Período da média móvel lenta"
        }
    }
    
    def apply(self, df: pd.DataFrame, **params) -> List[Dict]:
        """Aplica estratégia Golden Cross / Death Cross."""
        
        p = self.validate_params(**params)
        fast_period = p["fast_period"]
        slow_period = p["slow_period"]
        
        trades = []
        in_position = False
        
        # Tenta usar EMAs existentes ou calcula novas
        df = df.copy()
        
        fast_col = f'ema{fast_period}'
        slow_col = f'ema{slow_period}'
        
        # Calcula EMAs se não existirem
        if fast_col not in df.columns:
            df[fast_col] = df['close'].ewm(span=fast_period, adjust=False).mean()
        if slow_col not in df.columns:
            df[slow_col] = df['close'].ewm(span=slow_period, adjust=False).mean()
        
        for i in range(1, len(df)):
            fast_ema = df[fast_col].iloc[i]
            slow_ema = df[slow_col].iloc[i]
            prev_fast = df[fast_col].iloc[i-1]
            prev_slow = df[slow_col].iloc[i-1]
            price = df['close'].iloc[i]
            ts = df.index[i]
            
            # Skip NaN
            if pd.isna(fast_ema) or pd.isna(slow_ema) or pd.isna(prev_fast) or pd.isna(prev_slow):
                continue
            
            # Golden Cross: EMA rápida cruza EMA lenta para cima
            golden_cross = prev_fast <= prev_slow and fast_ema > slow_ema
            
            if golden_cross and not in_position:
                trades.append({
                    "action": "BUY",
                    "price": price,
                    "amount": 1.0,
                    "coin": "Fixed",
                    "timestamp": ts,
                    "reason": f"✨ Golden Cross (EMA{fast_period} > EMA{slow_period})"
                })
                in_position = True
            
            # Death Cross: EMA rápida cruza EMA lenta para baixo
            death_cross = prev_fast >= prev_slow and fast_ema < slow_ema
            
            if death_cross and in_position:
                trades.append({
                    "action": "SELL",
                    "price": price,
                    "amount": 1.0,
                    "coin": "Fixed",
                    "timestamp": ts,
                    "reason": f"💀 Death Cross (EMA{fast_period} < EMA{slow_period})"
                })
                in_position = False
        
        return trades
