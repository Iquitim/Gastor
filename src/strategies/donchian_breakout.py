"""
Donchian Channel Breakout Strategy - Rompimento de máximas/mínimas.

Estratégia usada pelos lendários Turtle Traders nos anos 80.
"""

import pandas as pd
from typing import List, Dict
from .base import BaseStrategy


class DonchianBreakoutStrategy(BaseStrategy):
    """
    Estratégia de Breakout usando Donchian Channels.
    
    Compra quando preço rompe a máxima dos últimos N períodos.
    Vende quando preço rompe a mínima dos últimos N períodos.
    """
    
    name = "Donchian Breakout"
    slug = "donchian_breakout"
    category = "breakout"
    icon = "🚀"
    
    description = "Compra no rompimento de máximas, vende no rompimento de mínimas"
    
    explanation = """
### 🚀 Donchian Channel Breakout
**Conceito:** "Os Turtle Traders ficaram ricos com isso"

Esta é a estratégia usada pelo lendário experimento dos **Turtle Traders** nos anos 80, onde Richard Dennis transformou pessoas comuns em traders milionários.

#### 📊 O Canal de Donchian:
- **Banda Superior:** Máxima mais alta dos últimos N períodos
- **Banda Inferior:** Mínima mais baixa dos últimos N períodos

#### 🎯 Sinais:
- 🟢 **Compra:** Quando preço **rompe** a banda superior (novo high)
- 🔴 **Venda:** Quando preço **rompe** a banda inferior (novo low)

#### 🧠 Por que funciona?
Quando o preço faz um **novo high**, significa que:
- Resistências anteriores foram quebradas
- Há força compradora entrando
- Momentum está a favor

#### ✅ Vantagens:
- Captura movimentos **explosivos** (breakouts)
- Estratégia testada por décadas com resultados comprovados
- Funciona especialmente bem em cripto (volatilidade alta)

#### ⚠️ Desvantagens:
- Muitos "falsos breakouts" em mercados laterais
- Entrada nunca é no melhor preço (você compra em highs)
- Requer gestão de risco rigorosa

#### 💡 Dica Turtle Traders:
Os Turtles usavam período de **20 dias para entrada** e **10 dias para saída** (saída mais rápida que entrada).
"""
    
    ideal_for = "Mercados voláteis, capturar movimentos explosivos"
    
    parameters = {
        "entry_period": {
            "default": 20,
            "min": 5,
            "max": 100,
            "label": "Período de Entrada",
            "help": "Lookback para identificar breakout de entrada"
        },
        "exit_period": {
            "default": 10,
            "min": 3,
            "max": 50,
            "label": "Período de Saída",
            "help": "Lookback para identificar breakout de saída (geralmente menor)"
        }
    }
    
    def apply(self, df: pd.DataFrame, **params) -> List[Dict]:
        """Aplica estratégia Donchian Breakout."""
        
        p = self.validate_params(**params)
        entry_period = p["entry_period"]
        exit_period = p["exit_period"]
        
        trades = []
        in_position = False
        
        df = df.copy()
        
        # Calcula canais de Donchian
        # Entry channel (mais largo)
        df['donchian_high'] = df['high'].rolling(window=entry_period).max()
        df['donchian_low'] = df['low'].rolling(window=entry_period).min()
        
        # Exit channel (mais estreito)
        df['exit_high'] = df['high'].rolling(window=exit_period).max()
        df['exit_low'] = df['low'].rolling(window=exit_period).min()
        
        for i in range(max(entry_period, exit_period) + 1, len(df)):
            price = df['close'].iloc[i]
            high = df['high'].iloc[i]
            low = df['low'].iloc[i]
            
            # Usamos valores do período ANTERIOR para evitar look-ahead bias
            prev_donchian_high = df['donchian_high'].iloc[i-1]
            prev_donchian_low = df['donchian_low'].iloc[i-1]
            prev_exit_low = df['exit_low'].iloc[i-1]
            
            ts = df.index[i]
            
            # Skip NaN
            if pd.isna(prev_donchian_high) or pd.isna(prev_donchian_low):
                continue
            
            # === ENTRADA ===
            # Breakout de alta: Preço rompe a máxima dos últimos N períodos
            if not in_position:
                if high > prev_donchian_high:
                    trades.append({
                        "action": "BUY",
                        "price": price,
                        "amount": 1.0,
                        "coin": "Fixed",
                        "timestamp": ts,
                        "reason": f"🚀 Breakout! (High={high:.2f} > {entry_period}p Max={prev_donchian_high:.2f})"
                    })
                    in_position = True
            
            # === SAÍDA ===
            # Breakout de baixa: Preço rompe a mínima (usando exit period menor)
            if in_position:
                if low < prev_exit_low:
                    trades.append({
                        "action": "SELL",
                        "price": price,
                        "amount": 1.0,
                        "coin": "Fixed",
                        "timestamp": ts,
                        "reason": f"📉 Exit (Low={low:.2f} < {exit_period}p Min={prev_exit_low:.2f})"
                    })
                    in_position = False
        
        return trades
