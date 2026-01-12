"""
Volume Breakout Strategy - Detecta movimentos com volume anormal.

Volume é o "combustível" das altas - sem volume, o preço não sustenta.
"""

import pandas as pd
import numpy as np
from typing import List, Dict
from .base import BaseStrategy


class VolumeBreakoutStrategy(BaseStrategy):
    """
    Estratégia de Breakout baseada em Volume anormal.
    
    Detecta quando o volume está significativamente acima da média,
    indicando entrada de "smart money" ou movimento institucional.
    """
    
    name = "Volume Breakout"
    slug = "volume_breakout"
    category = "volume"
    icon = "📊"
    
    description = "Detecta movimentos com volume anormalmente alto"
    
    explanation = """
### 📊 Volume Breakout
**Conceito:** "Volume é o Combustível"

O volume mostra a **força por trás do movimento**. Um preço subindo com alto volume é mais confiável que um movimento com volume baixo.

#### 📊 Lógica:
1. Calcula a **média móvel** do volume (ex: 20 períodos)
2. Define um **multiplicador** (ex: 2x a média)
3. Quando volume > média × multiplicador = **Spike de Volume**

#### 🎯 Sinais:
- 🟢 **Compra:** Volume spike + candle de **alta** (close > open)
- 🔴 **Venda:** Volume spike + candle de **baixa** (close < open)

#### ✅ Vantagens:
- Detecta entrada de **"smart money"** (institucionais)
- Volume precede o movimento de preço
I- Funciona muito bem em **cripto** (mercado 24/7)

#### ⚠️ Desvantagens:
- Pode haver spikes de volume por notícias irrelevantes
- Requer confirmação de direção (candle de alta/baixa)

#### 💡 Dica Pro:
Volume alto em **suporte** = acumulação (bullish).
Volume alto em **resistência** = distribuição (bearish).
"""
    
    ideal_for = "Cripto, ações de alta volatilidade, breakouts"
    
    parameters = {
        "volume_period": {
            "default": 20,
            "min": 5,
            "max": 50,
            "label": "Período Média Volume",
            "help": "Janela para calcular média do volume"
        },
        "volume_multiplier": {
            "default": 20,
            "min": 10,
            "max": 50,
            "label": "Multiplicador Volume (÷10)",
            "help": "Volume deve ser X/10 vezes a média (ex: 20 = 2.0x)"
        }
    }
    
    def apply(self, df: pd.DataFrame, **params) -> List[Dict]:
        """Aplica estratégia Volume Breakout."""
        
        p = self.validate_params(**params)
        volume_period = p["volume_period"]
        volume_mult = p["volume_multiplier"] / 10.0  # Converte de 20 para 2.0
        
        trades = []
        in_position = False
        
        if 'volume' not in df.columns:
            return []
        
        df = df.copy()
        
        # Calcula média móvel do volume
        df['volume_ma'] = df['volume'].rolling(window=volume_period).mean()
        df['volume_spike'] = df['volume'] > (df['volume_ma'] * volume_mult)
        
        # Identifica candles de alta e baixa
        df['bullish'] = df['close'] > df['open']
        df['bearish'] = df['close'] < df['open']
        
        for i in range(volume_period, len(df)):
            spike = df['volume_spike'].iloc[i]
            bullish = df['bullish'].iloc[i]
            bearish = df['bearish'].iloc[i]
            price = df['close'].iloc[i]
            volume = df['volume'].iloc[i]
            vol_ma = df['volume_ma'].iloc[i]
            ts = df.index[i]
            
            if pd.isna(vol_ma) or not spike:
                continue
            
            vol_ratio = volume / vol_ma if vol_ma > 0 else 0
            
            # Buy: Volume spike + candle bullish (fechou em alta)
            if spike and bullish and not in_position:
                trades.append({
                    "action": "BUY",
                    "price": price,
                    "amount": 1.0,
                    "coin": "Fixed",
                    "timestamp": ts,
                    "reason": f"📊 Volume Spike Bullish ({vol_ratio:.1f}x média)"
                })
                in_position = True
            
            # Sell: Volume spike + candle bearish (fechou em baixa)
            elif spike and bearish and in_position:
                trades.append({
                    "action": "SELL",
                    "price": price,
                    "amount": 1.0,
                    "coin": "Fixed",
                    "timestamp": ts,
                    "reason": f"📊 Volume Spike Bearish ({vol_ratio:.1f}x média)"
                })
                in_position = False
        
        return trades
