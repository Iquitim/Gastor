"""
MACD + RSI Combo Strategy - Confluência de dois indicadores clássicos.

Só entra quando MACD e RSI concordam, reduzindo sinais falsos.
"""

import pandas as pd
from typing import List, Dict
from .base import BaseStrategy


class MACDRSIComboStrategy(BaseStrategy):
    """
    Estratégia de Confluência combinando MACD e RSI.
    
    Exige que ambos os indicadores concordem antes de entrar,
    reduzindo drasticamente os sinais falsos.
    """
    
    name = "MACD + RSI Combo"
    slug = "macd_rsi_combo"
    category = "hybrid"
    icon = "🔗"
    
    description = "Só entra quando MACD e RSI concordam - menos sinais, mais precisos"
    
    explanation = """
### 🔗 MACD + RSI Combo
**Conceito:** "Duas Confirmações, Um Trade"

Esta estratégia exige **confluência** entre dois indicadores clássicos:
- **MACD** (momentum/tendência)
- **RSI** (sobrecompra/sobrevenda)

#### 🎯 Condições de COMPRA:
1. ✅ MACD cruza Signal **para cima** (momentum bullish)
2. ✅ RSI está **abaixo do limiar** de sobrecompra (ainda tem espaço para subir)

#### 🎯 Condições de VENDA:
1. ✅ MACD cruza Signal **para baixo** (momentum bearish)
2. ✅ RSI está **acima do limiar** de sobrevenda (ainda tem espaço para cair)

#### ✅ Vantagens:
- **Muito menos sinais falsos** que usar um indicador só
- Combina momentum (MACD) com extremos (RSI)
- Trades mais **confiantes** e precisos

#### ⚠️ Desvantagens:
- **Menos trades** no total (pode perder oportunidades)
- Entrada pode ser um pouco atrasada

#### 💡 Por que funciona?
- MACD pega a **direção** (tendência)
- RSI filtra entradas em **extremos** (evita comprar no topo)
"""
    
    ideal_for = "Traders conservadores, swing trading, reduzir ruído"
    
    parameters = {
        "rsi_max_buy": {
            "default": 65,
            "min": 50,
            "max": 80,
            "label": "RSI Máximo para Compra",
            "help": "Só compra se RSI estiver ABAIXO deste valor"
        },
        "rsi_min_sell": {
            "default": 35,
            "min": 20,
            "max": 50,
            "label": "RSI Mínimo para Venda",
            "help": "Só vende se RSI estiver ACIMA deste valor"
        }
    }
    
    def apply(self, df: pd.DataFrame, **params) -> List[Dict]:
        """Aplica estratégia MACD + RSI Combo."""
        
        p = self.validate_params(**params)
        rsi_max_buy = p["rsi_max_buy"]
        rsi_min_sell = p["rsi_min_sell"]
        
        trades = []
        in_position = False
        
        # Verifica indicadores necessários
        if 'macd' not in df.columns or 'macd_signal' not in df.columns:
            return []
        if 'rsi' not in df.columns:
            return []
        
        for i in range(1, len(df)):
            macd = df['macd'].iloc[i]
            signal = df['macd_signal'].iloc[i]
            prev_macd = df['macd'].iloc[i-1]
            prev_signal = df['macd_signal'].iloc[i-1]
            rsi = df['rsi'].iloc[i]
            price = df['close'].iloc[i]
            ts = df.index[i]
            
            # Skip NaN
            if pd.isna(macd) or pd.isna(signal) or pd.isna(rsi):
                continue
            if pd.isna(prev_macd) or pd.isna(prev_signal):
                continue
            
            # MACD Crossovers
            macd_cross_up = prev_macd <= prev_signal and macd > signal
            macd_cross_down = prev_macd >= prev_signal and macd < signal
            
            # === COMPRA ===
            # MACD cruza para cima + RSI não está sobrecomprado
            if macd_cross_up and rsi < rsi_max_buy and not in_position:
                trades.append({
                    "action": "BUY",
                    "price": price,
                    "amount": 1.0,
                    "coin": "Fixed",
                    "timestamp": ts,
                    "reason": f"🔗 MACD↑ + RSI OK ({rsi:.0f} < {rsi_max_buy})"
                })
                in_position = True
            
            # === VENDA ===
            # MACD cruza para baixo + RSI não está sobrevendido
            elif macd_cross_down and rsi > rsi_min_sell and in_position:
                trades.append({
                    "action": "SELL",
                    "price": price,
                    "amount": 1.0,
                    "coin": "Fixed",
                    "timestamp": ts,
                    "reason": f"🔗 MACD↓ + RSI OK ({rsi:.0f} > {rsi_min_sell})"
                })
                in_position = False
        
        return trades
